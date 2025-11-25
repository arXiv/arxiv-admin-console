variable "gcp_project_id" {
  description = "GCP Project ID corresponding to environment"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region for resource deployments"
  type        = string
}

variable "env" {
  description = "Deployment environment - DEV or PROD"
  type        = string
}

variable "image_path" {
  description = "Path to the container image in Artifact Registry"
  type        = string
}

variable "read_db_instance" {
  description = "Connection name for read database"
  type        = string
}

variable "read_db_secret_name" {
  description = "Reference to uri in Secret Manager for the read database"
  type        = string
}
