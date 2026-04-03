output "platform_service_account_email" {
  value       = google_service_account.platform_runtime.email
  description = "Service account email for future pipeline runtimes."
}

output "raw_bucket_name" {
  value       = google_storage_bucket.raw.name
  description = "Raw data bucket name."
}

output "processed_bucket_name" {
  value       = google_storage_bucket.processed.name
  description = "Processed data bucket name."
}

output "analytics_dataset_id" {
  value       = google_bigquery_dataset.analytics.dataset_id
  description = "Starter BigQuery dataset id."
}

