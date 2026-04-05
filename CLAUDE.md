# CLAUDE.md

Project-specific instructions for Claude Code. See AGENTS.md for the full reference.

## Before every commit

```bash
ruff check . && ruff format . && pytest
```

All three must pass. pre-commit hooks enforce ruff check + ruff format.

## Key rules

- **Mart tables are in `marts` schema**, not `staging`. Always use `marts.fct_commerce_orders`, `marts.fct_retailrocket_sessions`, `marts.dim_products`.
- **DVC-tracked files** in `data/sample/` must NOT be inlined into Git. Use `.dvc` pointer files. If modifying: `dvc add <file>` → `dvc push` → commit the `.dvc` file.
- **Python 3.11** is the CI/Docker target. dbt and Great Expectations fail on 3.14. Guard with `try/except ImportError`.
- **German comments, English code.** README uses German umlauts (ä, ö, ü). Variable names, function names, SQL in English.
- **Do not create empty directories.** No placeholder folders without files.
- **Do not add unnecessary features.** No speculative abstractions. Fix what's asked, nothing more.

## Common tasks

| Task | Command |
|------|---------|
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Test | `pytest` |
| Full pipeline | `make run-batch && make run-streaming && make run-warehouse && make run-quality-all` |
| Start stack | `make up` |
| API | `make run-api` (port 8000) |
| Dashboard | `make run-dashboard` (port 8501) |

## Architecture layers

```
raw (PostgreSQL) → staging (dbt views) → marts (dbt tables) → FastAPI → Streamlit
```

9 raw tables, 9 staging views, 2 intermediate views, 3 mart tables.

## Gotchas

- `integration.yml` has a DVC checkout fallback step — creates sample data inline if DVC remote unreachable.
- Dashboard has dual mode: `API_BASE_URL` set → API mode, unset → direct DB mode.
- `deploy-gcp.yml` deploys API first, then Dashboard with `API_BASE_URL` pointing to the API Cloud Run URL.
- Frankfurter API v2 returns flat list (not nested dict). `normalize_frankfurter_payload()` handles both.
- The `quality` extra includes `great_expectations` only for `python_version < '3.14'`.
