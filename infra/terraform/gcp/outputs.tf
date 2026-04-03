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

output "artifact_registry_repository_name" {
  value       = google_artifact_registry_repository.containers.name
  description = "Artifact Registry repository for dashboard and pipeline images."
}

output "artifact_registry_repository_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}"
  description = "Base URL for pushing container images to Artifact Registry."
}

output "dashboard_service_url" {
  value       = try(google_cloud_run_v2_service.dashboard[0].uri, null)
  description = "Cloud Run URL for the Streamlit dashboard."
}
