provider "google" {
  project = var.project_id
  region  = var.region

  # TODO: authenticate via ADC, workload identity, or CI-managed service account.
}

