# omnichannel-commerce-data-platform

Production-style Data Engineering portfolio scaffold for an Omnichannel Commerce Data Platform.

This repository is still intentionally scaffold-first, but it now includes platform foundations
aligned to a concrete domain stack:
Olist batch commerce data, Retailrocket clickstream replay, DummyJSON product API data,
Open-Meteo weather enrichment, Frankfurter FX rates, MongoDB raw documents,
PostgreSQL for local warehouse work, and BigQuery as the cloud warehouse target.

## Project Goals

- Keep the repository easy to navigate for recruiters and collaborators
- Separate batch, streaming, warehouse, quality, NoSQL, and orchestration concerns
- Start with realistic local tooling and environment configuration
- Leave honest TODO markers instead of fake implementations

## Source Domains

- Olist: batch relational commerce data for orders, order items, customers, products, and payments
- Retailrocket: clickstream/event replay data for `view`, `addtocart`, and `transaction` behavior
- DummyJSON: product API JSON for starter catalog enrichment
- Open-Meteo: weather enrichment for daily contextual analytics
- Frankfurter API: FX rates for currency normalization
- MongoDB: raw JSON and event document landing store
- PostgreSQL: local raw/staging/marts schemas for development
- BigQuery: cloud warehouse target for deployed analytics

## Planned Architecture

- Batch ingestion: Olist snapshots plus API-based enrichment pulls
- Streaming replay: Retailrocket events replayed into Kafka/Redpanda topics
- Raw layer: MongoDB documents and PostgreSQL raw tables
- Transform layer: dbt models from raw to staging to marts
- Warehouse targets: PostgreSQL locally and BigQuery in cloud environments
- Orchestration: Kestra-managed workflows
- Data quality: source contracts, SQL expectations, and dbt tests

## Repository Structure

```text
.
├── .github/workflows/              # Lint, pytest, and dbt CI workflows
├── .pre-commit-config.yaml         # Local file hygiene and lint hooks
├── config/                         # Runtime and environment configuration
├── data/
│   ├── contracts/                  # Source and schema contracts
│   └── sample/
│       ├── batch/                  # Small local batch samples
│       └── streaming/              # Small local event samples
├── docs/
│   ├── adr/                        # Architecture decision records
│   ├── diagrams/                   # Architecture and lineage diagrams
│   └── runbooks/                   # Operational notes and run procedures
├── infra/
│   ├── scripts/                    # Setup/bootstrap scripts
│   └── terraform/                  # Future infrastructure-as-code
├── nosql/
│   ├── mongodb/                    # MongoDB schemas, indexes, init assets
│   └── redis/                      # Optional cache-serving assets
├── orchestration/
│   ├── kestra/                     # Kestra flows and namespace assets
│   └── jobs/                       # Shared orchestration helpers
├── kafka/                          # Topic definitions and bootstrap helpers
├── quality/
│   ├── contracts/                  # Data quality contracts
│   ├── expectations/               # Quality rules and tests
│   └── monitors/                   # Freshness/SLA monitoring definitions
├── spark/
│   ├── conf/                       # Spark local/default configs
│   └── jobs/                       # Spark starter jobs
├── sql/
│   ├── postgres/
│   │   ├── init/                   # Source-side setup SQL
│   │   └── queries/                # Source-side analytical or validation SQL
│   └── warehouse/
│       ├── staging/                # Staging SQL patterns
│       ├── intermediate/           # Intermediate transformations
│       └── marts/                  # Analytics-facing models
├── src/
│   └── omnichannel_platform/
│       ├── batch/                  # Batch ingestion starter modules
│       ├── streaming/              # Streaming ingestion starter modules
│       ├── warehouse/              # Warehouse loaders and helpers
│       ├── quality/                # Quality execution layer
│       ├── nosql/                  # Serving-layer sync jobs
│       ├── orchestration/          # Shared orchestration utilities
│       └── common/                 # Shared config, logging, utilities
├── storage/
│   ├── bronze/                     # Raw landed datasets
│   ├── silver/                     # Cleaned datasets
│   ├── gold/                       # Curated analytics outputs
│   └── checkpoints/                # State, offsets, and watermarks
├── tests/
│   ├── fixtures/                   # Small local fixture data for starter tests
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
└── warehouse/
    ├── dbt/
    │   ├── models/
    │   │   ├── staging/            # dbt staging models
    │   │   ├── intermediate/       # dbt intermediate models
    │   │   └── marts/              # dbt mart models
    │   ├── tests/                  # dbt singular test scaffolding
    │   └── profiles.ci.yml         # CI-safe dbt profile
    └── seeds/                      # Small reference seed data
```

## What Exists Now

- Repository structure
- Environment and platform config files for Olist, Retailrocket, DummyJSON, Open-Meteo, and Frankfurter
- Minimal batch and streaming ingestion entry points
- Kestra flow skeletons
- dbt project skeleton with raw-to-staging-to-marts placeholders
- dbt test scaffolding
- Kafka topic scaffolding for Retailrocket replay
- Quality contracts and SQL rule placeholders
- GCP Terraform foundations
- Kafka and Spark starter files
- Pytest fixtures and starter tests
- GitHub Actions workflows for lint, tests, and dbt checks
- Pre-commit hooks for local workflow hygiene
- Local development Make targets and Docker Compose services

## What Is Deliberately Not Implemented Yet

- Full source connectors and secret wiring
- Stateful extraction, CDC, watermarking, and retry logic
- Real warehouse transformations and semantic models
- Production-quality replay guarantees and schema enforcement
- Executable quality orchestration
- Serving-layer sync jobs
- Production cloud credentials and deployment automation

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
make run-batch
make run-streaming
make run-warehouse
make run-quality
```

Optional extras:

```bash
pip install -e ".[warehouse,spark,batch,streaming]"
docker compose up -d
```

## Layer Flow

1. Batch sources land Olist tables and API payloads into `storage/bronze/` and MongoDB raw collections.
2. Retailrocket sample events replay into Kafka topics and are planned for raw event persistence.
3. Local PostgreSQL represents the development warehouse with `raw`, `staging`, and `marts` schemas.
4. dbt models provide placeholder structure for raw-to-staging-to-marts evolution.
5. BigQuery is the intended deployed warehouse target once cloud credentials and infra are ready.

## Current TODOs

- wire real source credentials and environment secrets
- stage Olist and Retailrocket full datasets into local development storage
- replace placeholder dbt SQL with source-backed transformations
- validate Kestra flows in a running instance
- connect Terraform state and GCP project configuration

## Additional Docs

- [Architecture Notes](docs/architecture.md)
