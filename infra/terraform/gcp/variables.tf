variable "credentials" {
  description = "Path to the GCP service account JSON key file."
  type        = string
}

variable "project_id" {
  description = "GCP project id for the platform."
  type        = string
}

variable "region" {
  description = "Primary region for platform resources."
  type        = string
  default     = "us-central1"
}

variable "location" {
  description = "Location for BigQuery datasets."
  type        = string
  default     = "US"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "gcs_storage_class" {
  description = "Storage class for GCS buckets."
  type        = string
  default     = "STANDARD"
}

variable "raw_bucket_name" {
  description = "Bucket for raw landed data."
  type        = string
}

variable "processed_bucket_name" {
  description = "Bucket for processed and curated data."
  type        = string
}

variable "artifact_registry_repository_id" {
  description = "Artifact Registry repository id for dashboard and pipeline images."
  type        = string
  default     = "omnichannel-platform"
}

variable "dashboard_service_name" {
  description = "Cloud Run service name for the Streamlit dashboard."
  type        = string
  default     = "omnichannel-dashboard"
}

variable "dashboard_container_image" {
  description = "Fully qualified container image for the dashboard deployment."
  type        = string
  default     = ""
}

variable "dashboard_container_port" {
  description = "Container port exposed by the Streamlit dashboard."
  type        = number
  default     = 8080
}

variable "dashboard_allow_unauthenticated" {
  description = "Whether the dashboard should be publicly invokable."
  type        = bool
  default     = true
}

variable "dashboard_min_instance_count" {
  description = "Minimum Cloud Run instances for the dashboard."
  type        = number
  default     = 0
}

variable "dashboard_max_instance_count" {
  description = "Maximum Cloud Run instances for the dashboard."
  type        = number
  default     = 2
}

variable "dashboard_env_vars" {
  description = "Environment variables passed to the dashboard container."
  type        = map(string)
  default = {
    DASHBOARD_WAREHOUSE_SCHEMA = "staging"
    DASHBOARD_RAW_SCHEMA       = "raw"
    POSTGRES_DB                = "commerce_platform"
    POSTGRES_PORT              = "5432"
  }
}
