# Quality Foundations

This directory contains the starter data quality layer for the Omnichannel Commerce platform.

Current scope:

- YAML contracts for raw and mart expectations
- SQL assertions for raw and mart validation
- dbt tests for staging and mart models
- Python execution runner in `src/omnichannel_platform/quality/rules_catalog.py`

Local usage:

```bash
make run-quality
```

Behavior:

- executes SQL expectations against PostgreSQL when available
- skips SQL execution cleanly when PostgreSQL is not reachable
- writes the latest quality report to `storage/checkpoints/quality/last_run.json`

TODO:

- add freshness, SLA, and reconciliation checks
- push failing expectations into orchestration alerts
- connect declarative contracts to broader metadata tooling
