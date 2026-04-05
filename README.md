# Omnichannel Commerce Data Platform

Ein End-to-End Data-Engineering-Projekt fuer das DataTalks Zoomcamp.

Batch-, Streaming-, Warehouse-, Quality- und Visualisierungs-Schichten
auf Basis realer Datenquellen mit lokaler Docker-Infrastruktur und
Cloud-Deployment-Pfad (GCP Cloud Run).

---

## Inhaltsverzeichnis

- [Architektur](#architektur)
- [Technologiestack](#technologiestack)
- [Schnellstart](#schnellstart)
- [Datenquellen](#datenquellen)
- [Pipeline-Schichten](#pipeline-schichten)
- [API und Dashboard](#api-und-dashboard)
- [Datenqualitaet](#datenqualitaet)
- [Orchestrierung](#orchestrierung)
- [CI/CD](#cicd)
- [Cloud-Deployment](#cloud-deployment)
- [Repository-Struktur](#repository-struktur)
- [Make-Targets](#make-targets)

---

## Architektur

```text
┌─────────────────────────────────────────────────────────────────────┐
│                          DATENQUELLEN                              │
│  Olist (CSV Seeds)  ·  Open Food Facts (API)  ·  Open-Meteo (API) │
│  Frankfurter FX (API)  ·  Retailrocket (JSONL Replay)             │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     RAW LAYER (PostgreSQL)                         │
│  9 Tabellen + ingestion_audit  ·  Optional: MongoDB (JSON-Docs)   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ dbt
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   TRANSFORMATION (dbt)                             │
│  9 Staging Views  →  2 Intermediate Views  →  3 Mart Tables       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
          ┌─────────────────┐     ┌─────────────────┐
          │  FastAPI REST   │     │  Streamlit       │
          │  API (:8000)    │────▶│  Dashboard       │
          │  /api/v1/*      │     │  (:8501)         │
          └─────────────────┘     └─────────────────┘
```

**Querschnittsfunktionen:**
Kestra (Orchestrierung) · Redpanda (Kafka-kompatibler Broker) · PySpark (Sessionisierung) ·
Great Expectations + SQL-Checks (Qualitaet) · DVC (Datenversionierung) · Bruin (Pipeline-Definitionen) ·
Terraform (GCP IaC) · GitHub Actions (5 CI/CD Workflows)

---

## Technologiestack

| Kategorie | Technologie | Version |
|---|---|---|
| Datenbank | PostgreSQL | 18 |
| Streaming | Redpanda (Kafka-kompatibel) | v25.3.9 |
| Document Store | MongoDB | 7 |
| Object Storage | MinIO | latest |
| Orchestrierung | Kestra | v1.1 |
| Transformation | dbt (postgres, duckdb, bigquery) | >=1.9 |
| Batch Processing | PySpark | >=3.5 |
| Data Quality | Great Expectations + SQL-Expectations | >=1.15 |
| Pipeline Definitions | Bruin | latest |
| REST API | FastAPI + Uvicorn | >=0.115 |
| Frontend | Streamlit + Plotly (Dark Theme) | >=1.38 |
| IaC | Terraform (Google Provider) | 5.6.0 |
| Cloud Runtime | Cloud Run (2 Services: API + Dashboard) | — |
| CI/CD | GitHub Actions (5 Workflows) | — |
| Python | Python | 3.11 (CI/Docker) |
| Linting | ruff | >=0.6 |
| Testing | pytest (32 Tests) | >=8.0 |

---

## Schnellstart

### Voraussetzungen

- Python 3.11+ (3.11 empfohlen; dbt und GX sind inkompatibel mit 3.14)
- Docker und Docker Compose

### Setup

```bash
# 1. Python-Umgebung einrichten
python3 -m venv .venv && source .venv/bin/activate
make install-local

# 2. Environment-Datei anlegen
cp .env.example .env

# 3. Infrastruktur starten
docker compose up -d postgres    # Minimum fuer Pipeline
docker compose up -d             # Kompletter Stack (10 Services)

# 4. PostgreSQL pruefen
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

### Kompletter Pipeline-Durchlauf

```bash
make kafka-topics                # Kafka-Topics anlegen
make run-batch                   # Batch: 4 Quellen -> raw.*
make run-streaming               # Streaming: Retailrocket -> raw.retailrocket_events
make run-warehouse               # dbt: raw -> staging -> marts
make run-quality-all             # Quality: SQL-Checks + Great Expectations
make run-api                     # API starten (Port 8000)
make run-dashboard               # Dashboard starten (Port 8501)
```

### Tests und Lint

```bash
ruff check . && ruff format --check . && pytest
```

---

## Datenquellen

| Quelle | Typ | Ziel-Tabelle(n) | Fallback |
|---|---|---|---|
| **Olist** | Batch (CSV Seeds) | `raw.olist_orders`, `raw.olist_order_items`, `raw.olist_customers`, `raw.olist_products`, `raw.olist_order_payments` | Deterministische Seed-Generierung (500 Orders, Seed=42) |
| **Open Food Facts** | Batch (REST API) | `raw.open_food_facts_products` | Lokales Sample-JSON |
| **Open-Meteo** | Batch (REST API) | `raw.open_meteo_weather` | 14 Fallback-Tage pro Stadt |
| **Frankfurter** | Batch (REST API v2) | `raw.frankfurter_fx_rates` | 14 Fallback-Tage |
| **Retailrocket** | Streaming (JSONL Replay) | `raw.retailrocket_events` | — |

Alle Batch-Quellen werden mit `python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev` ausgefuehrt.
Einzelne Quelle: `--source olist|open_food_facts|open_meteo|frankfurter`.

---

## Pipeline-Schichten

### Batch-Ingestion

Verarbeitet 4 Quellen sequenziell, schreibt Bronze-Artefakte und protokolliert in `raw.ingestion_audit`.
Optional: MongoDB-Persist fuer JSON-Payloads (graceful skip wenn nicht erreichbar).

```bash
make run-batch                                    # Alle Quellen
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source olist  # Einzeln
```

### Streaming-Replay

Liest Retailrocket-Events aus JSONL, normalisiert sie, routet auf Kafka-Topics
(`view`, `addtocart`, `transaction`, `dlq`) und persistiert in PostgreSQL.

```bash
make run-streaming
```

### dbt Warehouse (raw → staging → marts)

| Schicht | Modelle | Materialisierung |
|---|---|---|
| **Staging** | 9 Views (stg_olist_*, stg_retailrocket_*, stg_open_food_facts_*, stg_open_meteo_*, stg_frankfurter_*) | View |
| **Intermediate** | `int_orders_with_context` (Orders+Customers+Items+Payments+Weather+FX), `int_retailrocket_sessions` (30-Min-Gap Sessionisierung) | View |
| **Marts** | `fct_commerce_orders` (Order-Grain mit BRL/USD), `fct_retailrocket_sessions` (Session-Grain), `dim_products` (Olist + Open Food Facts) | Table |

```bash
make run-warehouse      # dbt build gegen DuckDB (CI-Profil)
dbt build --project-dir warehouse/dbt --target dev  # Gegen lokales PostgreSQL
```

### Spark

PySpark-Sessionisierung: Berechnet Sessions aus Clickstream-Events mit konfigurierbarer
Inaktivitaetsluecke und schreibt Parquet nach `storage/gold/`.

```bash
make spark-sessionize
```

---

## API und Dashboard

### FastAPI REST API

Data-Access-Layer zwischen PostgreSQL und Frontend. Swagger-Docs unter `/docs`.

| Endpunkt | Beschreibung |
|---|---|
| `GET /api/v1/health` | Healthcheck |
| `GET /api/v1/orders` | Commerce-Orders (Filter: status, category, state, date) |
| `GET /api/v1/orders/kpis` | Aggregierte KPIs |
| `GET /api/v1/sessions` | Retailrocket-Sessions |
| `GET /api/v1/sessions/funnel` | Conversion-Funnel |
| `GET /api/v1/products` | Produktdimension |
| `GET /api/v1/weather` | Wetterdaten |
| `GET /api/v1/fx-rates` | Wechselkurse |
| `GET /api/v1/pipeline/status` | Audit-Log + Tabellenstatistiken |

```bash
make run-api   # http://localhost:8000
```

### Streamlit Dashboard

8 Seiten mit Dark Theme, interaktiven Filtern und automatischen Insights:

| Seite | Inhalt |
|---|---|
| Commerce KPIs | 8 Metriken, Status-Pie, Zahlungsarten-Bar |
| Zeitliche Trends | Tages-/Wochen-/Monats-Aggregation, Kategorien-Umsatz |
| Kategorien & Regionen | Top-10 Kategorien/Bundesstaaten, Heatmap |
| Produkt-Analyse | Olist vs. Open Food Facts, Ecoscore-Verteilung |
| Session-Analyse | KPIs, Conversion-Funnel, Event-Histogramm |
| Wetter & FX | Temperatur, Niederschlag, EUR/USD + EUR/BRL Kurse |
| Datenquellen | Quellen-Uebersicht, letzte Ingestion, Datenfluss |
| Pipeline-Status | Audit-Tabelle, Tabellenstatistiken |

**Dual-Mode:** `API_BASE_URL` gesetzt → API-Modus, ungesetzt → Direkt-DB-Modus.

```bash
make run-dashboard                              # DB-Modus (Port 8501)
API_BASE_URL=http://localhost:8000 make run-dashboard  # API-Modus
```

---

## Datenqualitaet

### SQL-Expectations

4 YAML-Vertraege (`quality/contracts/`) + 5 SQL-Checks (`quality/expectations/`).
Jede SQL-Datei gibt fehlerhafte Zeilen zurueck — 0 Zeilen = bestanden.

```bash
make run-quality
```

### Great Expectations

Programmatische Validierung fuer 5 Tabellen (not_null, unique, accepted_values, row_count).
Erfordert Python <3.14 — wird bei ImportError uebersprungen.

```bash
make run-gx
make run-quality-all   # Beide Runner nacheinander
```

Reports: `storage/checkpoints/quality/last_run.json` und `storage/checkpoints/great_expectations/last_run.json`

### Bruin Pipeline

5 deklarative Asset-Definitionen in `pipeline/` mit DAG-Abhaengigkeiten und Column-Level-Checks:

```
ingest_olist ──┐
ingest_streaming ──┼── transform_dbt ── quality_checks
ingest_enrichments ─┘
```

---

## Orchestrierung

**Kestra** orchestriert den taeglichen Pipeline-Durchlauf (Flow: `daily_platform_ingestion.yml`):

1. Batch-Ingestion (alle 4 Quellen)
2. Streaming-Replay
3. Warehouse-Layer-Planung
4. dbt Build
5. Quality-Checks

**Schedule:** Taeglich um 06:00 UTC · **UI:** http://localhost:8080

---

## CI/CD

| Workflow | Trigger | Inhalt |
|---|---|---|
| `lint.yml` | Push/PR | pre-commit (ruff check + format) |
| `tests.yml` | Push/PR | pytest (32 Tests, kein DB noetig) |
| `dbt-checks.yml` | Push/PR | dbt parse + build (DuckDB CI-Profil) |
| `integration.yml` | Push/PR | PostgreSQL-Service → Schemas → Lint → Tests → Batch → Streaming → Quality → dbt → Marts-Verify → Docker-Builds |
| `deploy-gcp.yml` | Manuell | API + Dashboard → Artifact Registry → 2 Cloud Run Services |

Alle Workflows nutzen Python 3.11 auf `ubuntu-latest`.

---

## Cloud-Deployment

### Terraform (GCP)

Provisioniert in `infra/terraform/gcp/`:
- 2 GCS-Buckets (Raw + Processed)
- 3 BigQuery-Datasets (`commerce_raw`, `commerce_staging`, `commerce_marts`)
- 1 Artifact Registry Repository
- 2 Cloud Run Services (API + Dashboard)
- Service Account mit IAM-Bindings

```bash
make terraform-init-gcp
make terraform-plan-gcp
make terraform-apply-gcp
```

### Cloud Run Deployment

`deploy-gcp.yml` baut beide Images, deployt API zuerst und verbindet das Dashboard
ueber `API_BASE_URL` mit der API-Service-URL.

Benoetigte GitHub Secrets: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_SA_KEY`, `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

### Docker

Multi-Stage Dockerfile mit 3 Targets:

| Target | Zweck | Port |
|---|---|---|
| `pipeline` | Batch/Streaming/Quality CLI | — |
| `api` | FastAPI REST API | 8000 |
| `dashboard` | Streamlit Frontend | 8080 |

10 Docker-Compose-Services: PostgreSQL, pgAdmin, Redpanda, Redpanda Console, MongoDB, MinIO, Kestra, Platform-Runner, API, Dashboard.

---

## Repository-Struktur

```
.
├── config/                          # base.yaml, dev.yaml, prod.yaml
├── dashboard/app.py                 # Streamlit-Frontend (8 Seiten, Dark Theme)
├── data/sample/                     # DVC-tracked Sample-Daten (Batch + Streaming)
├── infra/terraform/gcp/             # Terraform: GCS, BigQuery, Cloud Run
├── kafka/                           # Topic-Katalog + create_topics.sh
├── nosql/mongodb/init.js            # MongoDB Collections + Indexes
├── orchestration/kestra/flows/      # Kestra-Flow (daily_platform_ingestion)
├── pipeline/                        # Bruin Asset-Definitionen (5 Stufen)
├── quality/
│   ├── contracts/                   # 4 YAML-Vertraege
│   └── expectations/                # 5 SQL-Checks
├── spark/jobs/                      # PySpark Clickstream-Sessionisierung
├── sql/postgres/init/               # Schema-Init + Raw-Tabellen-DDL
├── src/omnichannel_platform/
│   ├── api/                         # FastAPI (4 Router, Models, DB-Zugriff)
│   ├── batch/                       # Batch-Ingestion (4 Quellen)
│   ├── common/                      # Logging, Settings, Clients, IO
│   ├── dashboard/                   # Testbare Dashboard-Logik
│   ├── quality/                     # rules_catalog + gx_validation
│   ├── streaming/                   # Clickstream-Consumer (Replay + Kafka)
│   └── warehouse/                   # Layer-Katalog
├── tests/
│   ├── fixtures/                    # Test-Daten (JSON, JSONL)
│   ├── unit/                        # 12 Unit-Test-Dateien
│   └── integration/                 # 2 Integrations-Tests
├── warehouse/dbt/
│   ├── models/staging/              # 9 Staging Views
│   ├── models/intermediate/         # 2 Intermediate Views
│   ├── models/marts/                # 3 Mart Tables
│   └── tests/                       # 3 Singular-Tests
├── docker-compose.yml               # 10 Services
├── Dockerfile                       # Multi-Stage (pipeline, api, dashboard)
├── Makefile                         # Alle Targets
└── pyproject.toml                   # Dependencies + Extras
```

---

## Make-Targets

### Setup

| Target | Beschreibung |
|---|---|
| `make install-local` | Vollinstallation (alle Extras ausser Spark) |
| `make install-dev` | Nur dev-Tools (pytest, ruff, pre-commit) |
| `make lint` / `make test` | Linting / Tests |

### Pipeline

| Target | Beschreibung |
|---|---|
| `make run-batch` | Batch-Ingestion (4 Quellen) |
| `make run-streaming` | Streaming-Replay |
| `make run-warehouse` | Layer-Planung + dbt build |
| `make run-quality` / `make run-gx` | SQL-Checks / Great Expectations |
| `make run-quality-all` | Beide Quality-Runner |
| `make run-api` | FastAPI auf Port 8000 |
| `make run-dashboard` | Streamlit auf Port 8501 |
| `make spark-sessionize` | PySpark-Sessionisierung |

### Docker und Cloud

| Target | Beschreibung |
|---|---|
| `make up` / `make down` | Docker Stack starten/stoppen |
| `make kafka-topics` | Kafka-Topics anlegen |
| `make docker-build-pipeline` | Pipeline-Image bauen |
| `make docker-build-api` | API-Image bauen |
| `make docker-build-dashboard` | Dashboard-Image bauen |
| `make terraform-init-gcp` | Terraform initialisieren |
| `make terraform-plan-gcp` | Terraform Plan anzeigen |
| `make terraform-apply-gcp` | Terraform Apply |

---

## Bekannte Einschraenkungen

- dbt und Great Expectations sind inkompatibel mit Python 3.14 — CI und Docker nutzen Python 3.11
- Olist nutzt deterministische Seed-Daten (echte Kaggle-CSVs sind per Credential-Config vorbereitet)
- BigQuery ist architektonisch vorbereitet (Terraform), aber nicht mit Live-Credentials deployed
- Kestra-Tasks laufen shellbasiert (dediziertes Runtime-Image fuer Produktion noetig)

---

## Default-Credentials (nur Docker-Compose)

| Service | User | Password |
|---|---|---|
| PostgreSQL | commerce | commerce |
| pgAdmin | admin@admin.com | root |
| MinIO | minio | minio123 |
