# GCP Terraform Foundation

This directory contains the starter GCP foundation for the deployed warehouse target.

Current scope:

- Google provider pinned to `5.6.0`
- platform service account
- raw and processed GCS buckets
- BigQuery datasets for `commerce_raw`, `commerce_staging`, and `commerce_marts`
- example variables for credentials, project, region, and bucket naming

TODO:

- configure remote Terraform state before shared usage
- enable required GCP APIs in the target project
- add workload identity, secret handling, and environment modules
- wire CI/CD deployment and state promotion
