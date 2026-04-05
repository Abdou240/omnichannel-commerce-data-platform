# AGENTS.md

Guidance for AI coding agents (Claude, Codex, GPT, Gemini) and human contributors.
Last updated: 2026-04-05.

---

## Project Overview

Production-style **Data Engineering portfolio** for the DataTalks Zoomcamp (target: 28/28 points).
Omnichannel Commerce Analytics with batch, streaming, warehouse, quality, API, and dashboard layers.

**Status:** Feature-complete. Focus on CI stability, polish, and documentation.

---

## Critical Rules

1. **Never break CI.** Run `ruff check . && ruff format --check . && pytest` before committing.
2. **DVC-tracked files** live in `data/sample/`. Do NOT inline them into Git. They are tracked via `.dvc` pointer files. If you need to modify sample data, use `dvc add` + `dvc push`.
3. **Python 3.11** is the CI and Docker target. Locally Python 3.14 may be installed — Great Expectations and dbt do NOT work on 3.14. Guard imports accordingly.
4. **Mart tables live in `marts` schema**, not `staging`. The dbt_project.yml defines `+schema: marts` for mart models. All references to `fct_commerce_orders` etc. must use `marts.*`.
5. **pre-commit hooks** enforce `ruff check` + `ruff format`. Always run `ruff format .` before committing to avoid CI failures.
6. **German in comments/docs, English in code.** README uses German (with umlauts ä, ö, ü). Python code, SQL, YAML keys, and variable names use English.
7. **Do not create empty placeholder directories.** If a folder has no files, don't create it.
8. **Do not add features beyond what was asked.** No speculative abstractions, no extra docstrings on untouched code.

---

## Architecture

```
Sources → Raw (PostgreSQL) → Staging (dbt views) → Marts (dbt tables) → API (FastAPI) → Dashboard (Streamlit)
```

### Data Flow

```
Olist Seeds ──────┐
Open Food Facts ──┤                    ┌─ staging.stg_* (9 views)
Open-Meteo ───────┼── raw.* (9 tables) ┼─ staging.int_* (2 views)
Frankfurter FX ───┤                    └─ marts.fct_*/dim_* (3 tables)
Retailrocket ─────┘                                │
                                                   ▼
                                          FastAPI REST API ──► Streamlit Dashboard
```

### Schema Layout

| Schema | Content | Materialization |
|--------|---------|-----------------|
| `raw` | 9 source tables + `ingestion_audit` | Loaded by Python pipelines |
| `staging` | 9 staging views + 2 intermediate views | dbt views |
| `marts` | `fct_commerce_orders`, `fct_retailrocket_sessions`, `dim_products` | dbt tables |

---

## File Placement Rules

| What | Where |
|------|-------|
| Python application code | `src/omnichannel_platform/<layer>/` |
| Tests | `tests/unit/` or `tests/integration/` |
| Test fixtures | `tests/fixtures/` |
| SQL DDL (schema init) | `sql/postgres/init/` |
| dbt models | `warehouse/dbt/models/<staging\|intermediate\|marts>/` |
| dbt macros | `warehouse/dbt/macros/` |
| dbt tests | `warehouse/dbt/tests/` |
| Quality contracts | `quality/contracts/` (YAML) |
| Quality SQL expectations | `quality/expectations/` (SQL) |
| Kestra flows | `orchestration/kestra/flows/` |
| Bruin pipeline assets | `pipeline/` |
| Kafka config | `kafka/` |
| Spark jobs | `spark/jobs/` |
| Config | `config/base.yaml`, `config/dev.yaml`, `config/prod.yaml` |
| Terraform | `infra/terraform/gcp/` |
| Dashboard | `dashboard/app.py` (UI), `src/omnichannel_platform/dashboard/logic.py` (logic) |
| DVC-tracked data | `data/sample/` (`.dvc` pointers in Git, actual files in DVC cache) |
| CI/CD | `.github/workflows/` |

---

## Entry Points (CLI)

```bash
# Batch ingestion (all sources or specific)
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev [--source olist]

# Streaming replay
python -m omnichannel_platform.streaming.clickstream_consumer --env dev --mode replay

# Warehouse layer catalog
python -m omnichannel_platform.warehouse.layer_catalog --env dev

# Quality checks (custom SQL)
python -m omnichannel_platform.quality.rules_catalog [--non-strict]

# Quality checks (Great Expectations, Python <3.14 only)
python -m omnichannel_platform.quality.gx_validation [--non-strict]

# FastAPI server
uvicorn omnichannel_platform.api.main:app --host 0.0.0.0 --port 8000

# Dashboard
streamlit run dashboard/app.py --server.port 8501
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/orders` | Orders (filters: status, category, state, date, pagination) |
| GET | `/api/v1/orders/kpis` | Order KPIs (revenue, avg value, delivery rate) |
| GET | `/api/v1/sessions` | Sessions (pagination) |
| GET | `/api/v1/sessions/funnel` | Conversion funnel |
| GET | `/api/v1/products` | Products (filter by source) |
| GET | `/api/v1/weather` | Weather (city, date range) |
| GET | `/api/v1/fx-rates` | FX rates (currency, date range) |
| GET | `/api/v1/pipeline/status` | Pipeline audit + table stats |

---

## Docker Services (10)

| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | PostgreSQL 18 warehouse |
| pgadmin | 8085 | DB admin UI |
| redpanda | 9092 | Kafka-compatible broker |
| redpanda-console | 8484 | Broker UI |
| mongo | 27017 | Document store |
| minio | 9000/9001 | S3-compatible storage |
| kestra | 8080/8081 | Orchestration |
| platform-runner | — | Idle CLI container |
| api | 8000 | FastAPI REST API |
| dashboard | 8501 | Streamlit frontend |

---

## CI/CD Workflows

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `lint.yml` | PR, push/main | pre-commit hooks (ruff check + format) |
| `tests.yml` | PR, push/main | pytest (32 tests, no DB needed) |
| `dbt-checks.yml` | PR, push/main | dbt parse + build (DuckDB CI profile) |
| `integration.yml` | PR, push/main | Full E2E: PostgreSQL service → schemas → lint → tests → batch → streaming → quality → dbt → verify marts → Docker builds |
| `deploy-gcp.yml` | Manual | Build API + Dashboard images → Artifact Registry → 2 Cloud Run services |

### CI-specific notes

- `integration.yml` has a **DVC checkout step with fallback** — if DVC remote is unreachable, it creates minimal sample data inline.
- All workflows use **Python 3.11** on `ubuntu-latest`.
- The integration workflow installs `[dev,batch,streaming,quality,warehouse,api]` extras.
- Docker build smoke test builds all 3 targets: pipeline, api, dashboard.

---

## DVC Data Versioning

3 files tracked via DVC (small sample data for pipelines):

```
data/sample/batch/olist_manifest.yaml.dvc
data/sample/batch/open_food_facts_products_sample.json.dvc
data/sample/streaming/retailrocket_events.jsonl.dvc
```

- **Remote:** Local cache at `storage/dvc-cache/`
- **In CI:** `dvc checkout` with Python fallback if remote unavailable
- **To modify:** Edit the file → `dvc add <file>` → `dvc push` → commit `.dvc` pointer

---

## pyproject.toml Extras

```
dev       = [pre-commit, pytest, ruff]
batch     = [click, pandas, psycopg, pyarrow, requests, sqlalchemy, tqdm]
streaming = [kafka-python-ng, psycopg, sqlalchemy]
warehouse = [dbt-bigquery, dbt-duckdb, dbt-postgres]
nosql     = [pymongo]
quality   = [great_expectations (py<3.14), psycopg, sqlalchemy]
spark     = [pyspark]
dashboard = [pandas, requests, streamlit, plotly, psycopg, sqlalchemy]
api       = [fastapi, uvicorn, httpx, pandas, psycopg, sqlalchemy]
```

---

## Coding Conventions

- **Imports:** Always `from __future__ import annotations`. Absolute imports from `omnichannel_platform.*`.
- **Logging:** `from omnichannel_platform.common.logging import get_logger; LOGGER = get_logger(__name__)`
- **Config:** `from omnichannel_platform.common.settings import load_settings, repo_root`
- **DB clients:** `from omnichannel_platform.common.clients import create_postgres_engine`
- **Error handling:** Graceful degradation for optional services (MongoDB, Kafka, GX). Hard fail for PostgreSQL.
- **dbt model naming:** `stg_` (staging), `int_` (intermediate), `fct_` (fact), `dim_` (dimension)
- **Line length:** 100 (ruff config)
- **Target Python:** 3.11 (ruff target-version)

---

## Known Constraints

| Constraint | Impact | Workaround |
|-----------|--------|------------|
| dbt on Python 3.14 | mashumaro `UnserializableField` error | CI uses Python 3.11; local: use venv with 3.11 |
| Great Expectations on Python 3.14 | Import fails | `gx_validation.py` catches ImportError, skips gracefully |
| DVC local remote in CI | Remote path doesn't exist on GitHub runner | `integration.yml` has fallback that creates inline sample data |
| Frankfurter API v2 | Flat list response (not nested dict) | `normalize_frankfurter_payload()` handles both formats |

---

## Default Dev Credentials (docker-compose only)

| Service | User | Password |
|---------|------|----------|
| PostgreSQL | commerce | commerce |
| pgAdmin | admin@admin.com | root |
| MinIO | minio | minio123 |
| MongoDB | (no auth) | — |
| Kestra | (no auth) | — |

---

## Quick Verification

```bash
# Lint + format + tests (must all pass before any commit)
ruff check . && ruff format --check . && pytest

# Full local pipeline (requires docker compose up)
make run-batch && make run-streaming && make run-warehouse && make run-quality-all
```
