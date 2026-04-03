output "platform_service_account_email" {
  value       = google_service_account.platform_runtime.email
  description = "Service account email for pipeline runtimes."
}

output "raw_bucket_name" {
  value       = google_storage_bucket.raw.name
  description = "Raw data bucket name."
}

output "processed_bucket_name" {
  value       = google_storage_bucket.processed.name
  description = "Processed data bucket name."
}

output "raw_dataset_id" {
  value       = google_bigquery_dataset.raw.dataset_id
  description = "BigQuery raw dataset id."
}

output "staging_dataset_id" {
  value       = google_bigquery_dataset.staging.dataset_id
  description = "BigQuery staging dataset id."
}

output "marts_dataset_id" {
  value       = google_bigquery_dataset.marts.dataset_id
  description = "BigQuery marts dataset id."
}
