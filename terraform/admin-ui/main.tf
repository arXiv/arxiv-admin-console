terraform {
  required_version = "~> 1.13"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
  backend "gcs" {
    prefix = "admin-ui-console"
  }
}

provider "google" {
  project = var.gcp_project_id # default inherited by all resources
  region  = var.gcp_region     # default inherited by all resources
}

locals {
  # Bucket name: lowercase(env)-admin-console-test (e.g. dev-admin-console-test, prod-admin-console-test)
  storage_bucket_name = "${lower(var.env)}-admin-console-test2"
}

### service account ###

# resource "google_service_account" "account" {
#   account_id   = "admin-ui"
#   display_name = "Service account to deploy admin ui cloud run instance"
# }

# resource "google_project_iam_member" "logs_writer" {
#   project = var.gcp_project_id
#   role    = "roles/logging.logWriter"
#   member  = "serviceAccount:${google_service_account.account.email}"
# }

# resource "google_project_iam_member" "service_account_user" {
#   project = var.gcp_project_id
#   role    = "roles/iam.serviceAccountUser"
#   member  = "serviceAccount:${google_service_account.account.email}"
# }

# ### cloud run instance ###

# resource "google_cloud_run_v2_service" "admin_ui" {
#   name     = "admin-ui"
#   location = var.gcp_region

#   template {
#     containers {
#       image = var.image_path
#       env {
#         name  = "ENV"
#         value = var.env
#       }
#     }
#   }

#   traffic {
#     type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
#     percent = 100
#   }
# }

### GCS bucket for static assets ###
# Bucket name is lowercase(env)-admin-console-test. Import existing: terraform import -var-file=envs/dev.tfvars 'google_storage_bucket.admin_ui_assets' dev-admin-console-test

resource "google_storage_bucket" "admin_ui_assets" {
  name     = local.storage_bucket_name
  location = var.gcp_region
  project  = var.gcp_project_id

  public_access_prevention = "inherited"

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age                                     = 0
      days_since_custom_time                  = 0
      days_since_noncurrent_time              = 14
      matches_prefix                          = []
      matches_storage_class                   = []
      matches_suffix                          = []
      num_newer_versions                      = 5
      send_age_if_zero                        = false
      send_days_since_custom_time_if_zero     = false
      send_days_since_noncurrent_time_if_zero = false
      send_num_newer_versions_if_zero         = false
      with_state                              = "ARCHIVED"
    }
  }

  hierarchical_namespace {
    enabled = true
  }

  soft_delete_policy {
    retention_duration_seconds = 604800
  }

  # Versioning is not supported for hierarchical namespace buckets; do not enable both.
  uniform_bucket_level_access = true
}

# Allow public read access for static website hosting
resource "google_storage_bucket_iam_member" "admin_ui_public" {
  bucket = google_storage_bucket.admin_ui_assets.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
