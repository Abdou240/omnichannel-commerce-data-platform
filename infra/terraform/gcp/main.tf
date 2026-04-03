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
  uniform_bucket_level_access = true
  force_destroy               = false
  labels                      = local.common_labels

  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "processed" {
  name                        = var.processed_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
  labels                      = local.common_labels

  versioning {
    enabled = true
  }
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = var.bigquery_dataset_id
  location                    = var.region
  delete_contents_on_destroy  = false
  labels                      = local.common_labels

  # TODO: create separate raw, staging, and mart datasets if warehouse scope expands.
}

# TODO:
# - add IAM bindings for Kestra, dbt, and Spark runtimes
# - add remote state backend configuration once the shared GCP project is ready

