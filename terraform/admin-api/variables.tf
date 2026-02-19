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

variable "pwc_secret_name" {
  description = "Name of the PWC secret"
  type        = string
}

variable "pwc_arxiv_user_secret_name" {
  description = "Name of the PWC arXiv user secret"
  type        = string
}

variable "arxiv_check_url" {
  description = "URL of the arXiv check service"
  type        = string
}

variable "arxiv_document_bucket_name" {
  description = "Name of the arXiv document bucket"
  type        = string
}

variable "admin_api_shared_secret_name" {
  description = "Name of the admin API shared secret"
  type        = string
}

variable "admin_api_smtp_url_secret_name" {
  description = "Name of the admin API SMTP URL secret"
  type        = string
}

variable "admin_app_url" {
  description = "URL of the admin app"
  type        = string
}

variable "aaa_login_redirect_url" {
  description = "URL of the AAA login redirect"
  type        = string
}

variable "aaa_token_refresh_url" {
  description = "URL of the AAA token refresh"
  type        = string
}

variable "modapi_url" {
  description = "URL of the moderation API"
  type        = string
}

variable "modapi_modkey_secret_name" {
  description = "Name of the moderation API modkey secret"
  type        = string
}

variable "user_action_site" {
  description = "Site of the user action"
  type        = string
}