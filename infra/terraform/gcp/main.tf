locals {
  common_labels = {
    project     = "omnichannel-commerce-data-platform"
    environment = var.environment
    managed_by  = "terraform"
  }

  required_services = toset([
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  for_each           = local.required_services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "platform_runtime" {
  account_id   = "omnichannel-platform-${var.environment}"
  display_name = "Omnichannel Platform Runtime (${var.environment})"
}

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = var.artifact_registry_repository_id
  format        = "DOCKER"
  description   = "Container images for Omnichannel Commerce dashboard and runtimes."
  labels        = local.common_labels

  depends_on = [google_project_service.required]
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

resource "google_project_iam_member" "sa_artifact_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.platform_runtime.email}"
}

resource "google_cloud_run_v2_service" "dashboard" {
  count    = var.dashboard_container_image != "" ? 1 : 0
  name     = var.dashboard_service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  labels   = local.common_labels

  template {
    service_account = google_service_account.platform_runtime.email

    scaling {
      min_instance_count = var.dashboard_min_instance_count
      max_instance_count = var.dashboard_max_instance_count
    }

    containers {
      image = var.dashboard_container_image

      ports {
        container_port = var.dashboard_container_port
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "PORT"
        value = tostring(var.dashboard_container_port)
      }

      dynamic "env" {
        for_each = var.dashboard_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  depends_on = [
    google_project_service.required,
    google_artifact_registry_repository.containers,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "dashboard_invoker" {
  count    = var.dashboard_container_image != "" && var.dashboard_allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = google_cloud_run_v2_service.dashboard[0].location
  name     = google_cloud_run_v2_service.dashboard[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
