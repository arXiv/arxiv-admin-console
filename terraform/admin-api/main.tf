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

resource "google_secret_manager_secret_iam_member" "admin_api_shared_secret_accessor" {
  secret_id = var.admin_api_shared_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.account.email}"
}

resource "google_secret_manager_secret_iam_member" "pwc_secret_accessor" {
  secret_id = var.pwc_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.account.email}"
}

resource "google_secret_manager_secret_iam_member" "pwc_arxiv_user_secret_accessor" {
  secret_id = var.pwc_arxiv_user_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.account.email}"
}

resource "google_secret_manager_secret_iam_member" "arxiv_document_bucket_name_accessor" {
  secret_id = var.arxiv_document_bucket_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.account.email}"
}

resource "google_secret_manager_secret_iam_member" "admin_api_smtp_url_accessor" {
  secret_id = var.admin_api_smtp_url_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.account.email}"
}

resource "google_secret_manager_secret_iam_member" "modapi_modkey_accessor" {
  secret_id = var.modapi_modkey_secret_name
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
        name = "ADMIN_API_SHARED_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.admin_api_shared_secret_name
            version = "latest"
          }
        }
      }
      env {
        name = "ADMIN_API_SMTP_URL"
        value_source {
          secret_key_ref {
            secret  = var.admin_api_smtp_url_secret_name
            version = "latest"
          }
        }
      }
      env {
        name  = "ADMIN_APP_URL"
        value = var.admin_app_url
      }
      env {
        name  = "AAA_LOGIN_REDIRECT_URL"
        value = var.aaa_login_redirect_url
      }
      env {
        name  = "AAA_TOKEN_REFRESH_URL"
        value = var.aaa_token_refresh_url
      }
      env {
        name  = "ARXIV_CHECK_URL"
        value = var.arxiv_check_url
      }
      env {
        name  = "ARXIV_DOCUMENT_BUCKET_NAME"
        value = var.arxiv_document_bucket_name
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
        name  = "SESSION_DURATION"
        value = var.session_duration
      }
      env {
        name  = "GCP_PROJECT"
        value = var.gcp_project_id
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.gcp_project_id
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
      env {
        name  = "MODAPI_URL"
        value = var.modapi_url
      }
      env {
        name = "MODAPI_MODKEY"
        value_source {
          secret_key_ref {
            secret  = var.modapi_modkey_secret_name
            version = "latest"
          }
        }
      }
      env {
        name = "PWC_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.pwc_secret_name
            version = "latest"
          }
        }
      }
      env {
        name = "PWC_ARXIV_USER_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.pwc_arxiv_user_secret_name
            version = "latest"
          }
        }
      }
      env {
        name  = "USER_ACTION_SITE"
        value = var.user_action_site
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