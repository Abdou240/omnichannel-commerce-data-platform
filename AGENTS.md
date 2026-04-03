# AGENTS.md

Guidance for contributors and AI coding agents working in this repository.

## Purpose

This repository is a production-style Data Engineering portfolio scaffold.
At this stage, structure matters more than feature completeness.

## Working Rules

- Keep folder boundaries clear between batch, streaming, warehouse, quality, NoSQL, and orchestration layers.
- Prefer realistic placeholders and TODOs over fake or overly polished business logic.
- Do not collapse unrelated concerns into one folder or one script.
- When adding code later, keep the first version small, runnable, and easy to replace.
- Preserve recruiter readability: obvious naming, clear docs, and consistent layout.

## File Placement

- Put environment and runtime configuration under `config/`
- Put Python application code under `src/omnichannel_platform/`
- Put source-system SQL under `sql/postgres/`
- Put warehouse modeling assets under `warehouse/dbt/` and `sql/warehouse/`
- Put Kestra orchestration definitions under `orchestration/kestra/`
- Put data quality assets under `quality/`
- Put serving-store assets under `nosql/`
- Put Kafka platform assets under `kafka/`
- Put Spark starter assets under `spark/`

## Placeholder Policy

- Use `TODO:` markers for unfinished connectors, pipeline steps, tests, and deployment details.
- Avoid adding mock “completed” pipelines that do not reflect real implementation work.
- If a folder exists without logic yet, keep it empty until the first real artifact is ready.

## Documentation Expectations

- Update `README.md` when the structure or setup flow changes.
- Add ADRs in `docs/adr/` when a major architecture decision is introduced.
- Keep setup instructions accurate and brief.

## Initial Scope Reminder

This step is scaffold-only.
Business logic, SQL transformations, orchestration code, and data tests should be added in later steps.
