locals {
  common_labels = {
    project     = "omnichannel-commerce-data-platform"
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_service_account" "platform_runtime" {
  account_id   = "omnichannel-platform-${var.environment}"
  display_name = "Omnichannel Platform Runtime (${var.environment})"
}

resource "google_storage_bucket" "raw" {
  name                        = var.raw_bucket_name
  location                    = var.region
  storage_class               = var.gcs_storage_class
  uniform_bucket_level_access = true
  force_destroy               = true
  labels                      = local.common_labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      days_since_noncurrent_time = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_storage_bucket" "processed" {
  name                        = var.processed_bucket_name
  location                    = var.region
  storage_class               = var.gcs_storage_class
  uniform_bucket_level_access = true
  force_destroy               = true
  labels                      = local.common_labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_bigquery_dataset" "raw" {
  dataset_id                 = "commerce_raw"
  location                   = var.location
  delete_contents_on_destroy = true
  labels                     = local.common_labels
}

resource "google_bigquery_dataset" "staging" {
  dataset_id                 = "commerce_staging"
  location                   = var.location
  delete_contents_on_destroy = true
  labels                     = local.common_labels
}

resource "google_bigquery_dataset" "marts" {
  dataset_id                 = "commerce_marts"
  location                   = var.location
  delete_contents_on_destroy = true
  labels                     = local.common_labels
}

resource "google_project_iam_member" "sa_bigquery" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.platform_runtime.email}"
}

resource "google_project_iam_member" "sa_storage" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.platform_runtime.email}"
}
