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
