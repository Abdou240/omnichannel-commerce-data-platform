variable "project_id" {
  description = "GCP project id for the platform."
  type        = string
}

variable "region" {
  description = "Primary region for platform resources."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "raw_bucket_name" {
  description = "Bucket for raw landed data."
  type        = string
}

variable "processed_bucket_name" {
  description = "Bucket for processed and curated data."
  type        = string
}

variable "bigquery_dataset_id" {
  description = "Starter analytics dataset id."
  type        = string
  default     = "analytics"
}

