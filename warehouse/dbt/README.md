# dbt Starter Project

This dbt project is intentionally minimal.

Current scope:

- project configuration
- local PostgreSQL profile example
- BigQuery production target example
- empty-safe starter models for raw-to-staging-to-marts flow
- schema and singular test scaffolding
- CI-safe DuckDB profile for GitHub Actions

TODO:

- replace placeholder SQL with source-backed models
- add source tests, freshness, and exposures
- finalize PostgreSQL local raw table loading and BigQuery deployed dataset strategy
