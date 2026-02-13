variable "gcp_project_id" {
  description = "GCP Project ID corresponding to environment"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region for resource deployments"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Deployment environment - DEV or PROD"
  type        = string
}

# variable "image_path" {
#   description = "Path to the container image in Artifact Registry (required for apply, not for import)"
#   type        = string
#   default     = ""
# }
