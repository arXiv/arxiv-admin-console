variable "gcp_project_id" {
  description = "GCP Project ID corresponding to environment"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region for resource deployments"
  type        = string
}

variable "admin_api_root_path" {
  description = "Root path of the admin API"
  type        = string
  default     = "/services/admin"
}

variable "classic_cookie_name" {
  description = "Name of the classic cookie"
  type        = string
  default     = "tapir_session"
}

variable "classic_db_secret_name" {
  description = "Name of the classic database secret"
  type        = string
}

variable "classic_db_instance" {
  description = "Instance of the classic database"
  type        = string
}

variable "classic_session_hash" {
  description = "Hash of the classic session"
  type        = string
  default     = "classic-secret"
}

variable "session_duration" {
  description = "Duration of the session"
  type        = string
  default     = "36000"
}

variable "jwt_secret_name" {
  description = "Name of the JWT secret"
  type        = string
  default     = "jwt-secret"
}

variable "port" {
  description = "Port for the admin API"
  type        = string
  default     = "8080"
}

variable "image_path" {
  description = "Path to the container image in Artifact Registry"
  type        = string
}
