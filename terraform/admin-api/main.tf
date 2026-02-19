terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
  backend "gcs" {
    prefix = "admin-api"
  }
}

provider "google" {
  project = var.gcp_project_id # default inherited by all resources
  region  = var.gcp_region     # default inherited by all resources
}

### service account ###

resource "google_service_account" "account" {
  account_id   = "admin-api"
  display_name = "Service account to deploy admin api cloud run instance"
}

resource "google_secret_manager_secret_iam_member" "classic_db_secret_accessor" {
  secret_id = var.classic_db_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.account.email}"
}

resource "google_secret_manager_secret_iam_member" "jwt_secret_accessor" {
  secret_id = var.jwt_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.account.email}"
}

resource "google_project_iam_member" "ar_writer" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.createOnPushWriter"
  member  = "serviceAccount:${google_service_account.account.email}"
}

resource "google_project_iam_member" "cloud_run_admin" {
  project = var.gcp_project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.account.email}"
}

resource "google_project_iam_member" "logs_writer" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.account.email}"
}

resource "google_project_iam_member" "service_account_user" {
  project = var.gcp_project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.account.email}"
}

### cloud run instance ###

resource "google_cloud_run_v2_service" "admin_api" {
  name     = "admin-api"
  location = var.gcp_region

  deletion_protection = false

  template {
    service_account = google_service_account.account.email
    containers {
      image = var.image_path
      resources {
        limits = {
          memory = "1024Mi"
        }
      }
      env {
        name  = "ADMIN_API_ROOT_PATH"
        value = var.admin_api_root_path
      }
      env {
        name  = "CLASSIC_COOKIE_NAME"
        value = var.classic_cookie_name
      }
      env {
        name = "CLASSIC_DB_URI"
        value_source {
          secret_key_ref {
            secret  = var.classic_db_secret_name
            version = "latest"
          }
        }
      }
      env {
        name  = "CLASSIC_SESSION_HASH"
        value = var.classic_session_hash
      }
      env {
        name  = "CLASSIC_SESSION_DURATION"
        value = var.session_duration
      }
      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.jwt_secret_name
            version = "latest"
          }
        }
      }
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [var.classic_db_instance]
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}