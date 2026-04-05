# omnichannel-commerce-data-platform

Ein praxisnahes Portfolio-Projekt für Data Engineering rund um eine Omnichannel-Commerce-Plattform.

Dieses Repository modelliert einen realistischen End-to-End-Stack für Batch-, Streaming-,
Warehouse-, Qualitäts- und Orchestrierungs-Workloads. Der Fokus liegt bewusst auf einer sauberen,
erweiterbaren Plattformstruktur, auf ehrlichen Starter-Implementierungen und auf einer
repo-tauglichen Darstellung für Recruiter, Hiring Manager und technische Reviewer.

Das Projekt ist kein künstlich "fertig simulierter" Showcase. Stattdessen gibt es funktionierende
Starter-Pipelines, echte Ausführungspfade, saubere TODO-Grenzen und eine klare Trennung zwischen
lokalem Entwicklungs-Setup und späterer Cloud-Zielarchitektur.

---

## Inhaltsverzeichnis

**Überblick:**
- [Projektziel](#projektziel)
- [Fachlicher Umfang](#fachlicher-umfang)
- [Datenquellen](#datenquellen)
- [Architektur auf einen Blick](#architektur-auf-einen-blick)
- [Technologiestack](#technologiestack)
- [Repository-Struktur](#repository-struktur)

**Teil 1 -- Setup:**
- [Lokales Setup](#lokales-setup) (Python, .env, Docker Stack)
- [Zentrale Make-Targets](#zentrale-make-targets)

**Teil 2 -- Python-Skripte, Tests und Pipeline-Ausführung:**
- [Datenfluss im Detail](#datenfluss-im-detail) (Batch, Streaming, dbt, Quality, kompletter Durchlauf)
- [Warehouse- und dbt-Modellierung](#warehouse--und-dbt-modellierung)
- [Datenqualität](#datenqualität)
- [Orchestrierung mit Kestra](#orchestrierung-mit-kestra)
- [Spark-Pfad](#spark-pfad)
- [API-Schicht (FastAPI)](#api-schicht-fastapi)
- [Dashboard und Frontend](#dashboard-und-frontend)

**Teil 3 -- Deployment und Cloud:**
- [Containerisierung mit Docker](#containerisierung-mit-docker)
- [GCP- und Terraform-Fundament](#gcp--und-terraform-fundament)
- [CI/CD-Pipeline](#cicd-pipeline)

**Abschluss:**
- [Was aktuell implementiert ist](#was-aktuell-implementiert-ist)
- [Aktuelle Grenzen](#aktuelle-grenzen)
- [Nächste sinnvolle Ausbaustufen](#nächste-sinnvolle-ausbaustufen)

---

## Projektziel

Die Plattform soll ein realistisches Omnichannel-Commerce-Szenario abbilden:

- relationale Commerce-Daten im Batch-Stil ingestieren (Olist-Bestellungen, 4 externe APIs)
- Clickstream-Ereignisse über Kafka-kompatible Topics replayen (Retailrocket)
- externe Referenz- und Enrichment-Daten einbinden (Wetter, FX-Raten, Produktstammdaten)
- Rohdaten in ein lokales Warehouse überführen (PostgreSQL `raw.*`)
- dbt-Modelle von `raw -> staging -> intermediate -> marts` aufbauen (14 Modelle, 3 Schichten)
- Datenqualitätsregeln dokumentieren und ausführbar machen (4 Verträge, 4 SQL-Expectations)
- Ergebnisse in einem interaktiven Dashboard visualisieren (Streamlit mit 8 Seiten und Filtern)
- alles containerisieren (Multi-Stage Dockerfile, 9 Docker-Compose-Services)
- eine klare Cloud-Zielarchitektur für BigQuery und GCP vorbereiten (Terraform, Cloud Run)

Das Repository soll zeigen, dass nicht nur SQL oder Python beherrscht wird, sondern dass ein
Data-Engineering-Projekt als Plattform gedacht, strukturiert, dokumentiert und weiterentwickelt
werden kann.

## Fachlicher Umfang

Im Mittelpunkt steht eine Omnichannel-Commerce-Domäne mit mehreren fachlichen Perspektiven:

- Bestellungen und Bestellpositionen
- Produkte und Produktattribute
- Kunden- und Standortkontext
- Klick- und Session-Verhalten
- Wetterkontext für Nachfrage- oder Aktivitätsmuster
- Währungsumrechnung für vergleichbare Kennzahlen

## Datenquellen

### Olist

Batch-orientierte relationale Commerce-Daten auf CSV-Basis:

- Orders, Order Items, Customers, Products, Payments

Im lokalen Setup werden deterministische Seed-Dateien erzeugt, wenn keine echten CSV-Snapshots
bereitgestellt wurden. Dadurch bleibt der Batch-Pfad lauffähig, ohne einen "Fake-Production"-Eindruck
zu erzeugen.

Die Zielquelle ist das reale Kaggle-Dataset `olistbr/brazilian-ecommerce`. Für einen echten Download-
Pfad sind Kaggle-Credentials nötig; bis dahin bleibt die Seed-Strategie der lauffähige Fallback.

### Retailrocket

Clickstream-/Event-Daten für Replay-Szenarien:

- `view`, `addtocart`, `transaction`

Die Events werden im Starter-Setup aus einer JSONL-Datei gelesen, normalisiert, auf Kafka-Topics
geroutet und zusätzlich in der Raw-Schicht persistiert.

### Open Food Facts

Echte Produkt-API für JSON-basierte Produktstammdaten. Im aktuellen Starter ruft die Batch-Pipeline
konkrete Produkt-Barcodes über die Open Food Facts API ab. Das ist robuster als ein freier
Such-Endpoint und bildet trotzdem echte Live-Daten ab. Bei temporärer API-Störung fällt die
Pipeline auf ein lokales Sample zurück.

### Open-Meteo

Wetter-Enrichment auf Tagesebene für ausgewählte brasilianische Städte (Sao Paulo, Rio de Janeiro,
Belo Horizonte).

### Frankfurter API (v2)

FX-Raten (EUR -> USD, EUR -> BRL) zur späten Umrechnung von Beträgen und zur Vergleichbarkeit
von Commerce-Metriken. Nutzt die Frankfurter API v2 (`/v2/rates`) mit flacher Liste als
Antwortformat (ein Eintrag pro Datum+Währungspaar).

### MongoDB

Raw-Document-Store für JSON-Payloads und Replay-Artefakte.

### PostgreSQL lokal und BigQuery als Zielarchitektur

- PostgreSQL dient lokal als Warehouse- und Raw-Execution-Ziel
- BigQuery ist als Cloud-Warehouse-Ziel in dbt- und Terraform-Struktur vorbereitet
- als reale Public-Reference-Sets sind `ga4_obfuscated_sample_ecommerce` und `thelook_ecommerce`
  vorgesehen
- wichtig: diese Public Datasets liegen in der `US` Multi-Region

---

## Architektur auf einen Blick

```text
+---------------------------------------------------------------------+
|                        DATENQUELLEN                                 |
+---------------------------------------------------------------------+
|                                                                     |
|  Olist CSVs/Seeds    Open Food Facts    Open-Meteo    Frankfurter   |
|  (Batch relational)  (Product API)      (Weather)     (FX Rates)    |
|         |                  |                |              |         |
|         +------------------+----------------+--------------+         |
|                            |                                        |
|  Retailrocket JSONL -----> | Kafka/Redpanda Topics                  |
|  (Clickstream Replay)      |                                        |
+----------------------------+----------------------------------------+
                             |
                             v
+---------------------------------------------------------------------+
|                      RAW / BRONZE LAYER                             |
+---------------------------------------------------------------------+
|                                                                     |
|  storage/bronze/*          PostgreSQL raw.*       MongoDB            |
|  (Dateiartefakte)          (9 Tabellen)           (4 Collections)   |
|  - Olist CSVs              - olist_orders         - retailrocket    |
|  - API JSON responses      - olist_order_items      _events_raw     |
|  - Run-Manifeste           - olist_customers      - open_food_facts |
|                            - olist_products         _products_raw   |
|                            - olist_order_payments - open_meteo      |
|                            - retailrocket_events    _weather_raw    |
|                            - open_food_facts      - frankfurter     |
|                              _products              _fx_raw         |
|                            - open_meteo_weather                     |
|                            - frankfurter_fx_rates                   |
|                            - ingestion_audit                        |
+---------------------------------------------------------------------+
                             |
                             v
+---------------------------------------------------------------------+
|                   dbt TRANSFORMATION LAYER                          |
+---------------------------------------------------------------------+
|                                                                     |
|  STAGING (Views)            INTERMEDIATE (Views)    MARTS (Tables)  |
|  - stg_olist_orders         - int_orders_with       - fct_commerce  |
|  - stg_olist_order_items      _context                _orders       |
|  - stg_olist_customers      - int_retailrocket      - fct_retail    |
|  - stg_olist_products         _sessions               rocket       |
|  - stg_olist_order_payments                           _sessions     |
|  - stg_retailrocket_events                          - dim_products  |
|  - stg_open_food_facts                                              |
|    _products                                                        |
|  - stg_open_meteo_weather                                           |
|  - stg_frankfurter_fx_rates                                         |
+---------------------------------------------------------------------+
                             |
                             v
+---------------------------------------------------------------------+
|                    ZIELARCHITEKTUR                                   |
+---------------------------------------------------------------------+
|                                                                     |
|  BigQuery (commerce_raw / commerce_staging / commerce_marts)        |
|  GCS Buckets (Raw + Processed)                                      |
|  Terraform-provisioniert                                            |
|                                                                     |
|  Public BigQuery Referenzen:                                        |
|  - bigquery-public-data.ga4_obfuscated_sample_ecommerce             |
|  - bigquery-public-data.thelook_ecommerce                           |
+---------------------------------------------------------------------+

+---------------------------------------------------------------------+
|                    QUERSCHNITTSFUNKTIONEN                           |
+---------------------------------------------------------------------+
|                                                                     |
|  Orchestrierung: Kestra v1.1 (daily_platform_ingestion)             |
|  Streaming:      Redpanda v25.3.9 (Kafka-kompatibel)               |
|  Spark:          Clickstream Sessionisierung (PySpark)              |
|  Qualität:      SQL-Expectations + Great Expectations + dbt-Tests   |
|  Sample-Daten:    Direkt versionierte YAML-/JSON-/JSONL-Fixtures    |
|  Pipeline Def:   Bruin (Asset-basierte Pipeline-Definitionen)       |
|  CI/CD:          GitHub Actions (lint, pytest, dbt build)           |
|  IaC:            Terraform (Google Provider 5.6.0)                  |
|  Frontend:       Streamlit + Plotly (Dark Theme)                    |
|  REST API:       FastAPI                                            |
|  Deployment:     Docker Compose + Cloud Run                         |
+---------------------------------------------------------------------+
```

Eine ergänzende Architekturübersicht liegt in [docs/architecture.md](docs/architecture.md).

---

## Technologiestack

| Kategorie | Technologie | Version |
|---|---|---|
| Datenbank (lokal) | PostgreSQL | 18 |
| Streaming Broker | Redpanda | v25.3.9 |
| Document Store | MongoDB | 7 |
| Object Storage (lokal) | MinIO | latest |
| Orchestrierung | Kestra | v1.1 |
| Transformation | dbt | >=1.9 |
| Batch Processing | Spark / PySpark | >=3.5 |
| IaC | Terraform (Google Provider) | 5.6.0 |
| Cloud Warehouse | BigQuery | (Zielarchitektur) |
| Cloud Storage | GCS | (Zielarchitektur) |
| Data Quality | Great Expectations | >=1.15 |
| Sample-Daten | Direkt im Git-Repo versioniert | kleine Fixtures |
| Pipeline Definitions | Bruin | latest |
| REST API | FastAPI + Uvicorn | >=0.115 / >=0.34 |
| Frontend | Streamlit + Plotly | >=1.38 / >=5.24 |
| Container | Docker / Docker Compose | latest |
| Cloud App Runtime | Cloud Run | 2 Services (API + Dashboard) |
| Python | Python | >=3.11 |
| Build Tool | uv / pip | latest |
| Linting | ruff | >=0.6 |
| Testing | pytest | >=8.0 |
| CI/CD | GitHub Actions | 5 Workflows |

---

## Repository-Struktur

```text
.
├── .dockerignore                    # Schlanker Docker-Build-Context
├── .github/workflows/              # CI/CD: lint, pytest, dbt-checks, integration, deploy-gcp
├── Dockerfile                       # Multi-Stage Build (pipeline + api + dashboard)
├── docker-compose.yml               # 10 Services (Postgres, API, Dashboard, Redpanda, Kestra, ...)
├── Makefile                         # Alle Make-Targets
├── pyproject.toml                   # Python-Abhängigkeiten und Extras
├── dashboard/                       # Streamlit-Frontend (app.py)
├── config/                          # Basis-, Dev- und Prod-Konfiguration
│   ├── base.yaml                    # Alle Quellen, Warehouse, Orchestrierung
│   ├── dev.yaml                     # Lokale Overrides (Kafka, Geo, etc.)
│   └── prod.yaml                    # Cloud-Platzhalter
├── .bruin.yml                       # Bruin Pipeline-Konfiguration
├── .dvc/                            # Optionale DVC-Konfiguration für spätere größere Artefakte
├── data/sample/                     # Direkt versionierte Beispiel- und Replay-Daten
│   ├── batch/                       # Olist-Manifest, Open Food Facts Sample
│   └── streaming/                   # Retailrocket JSONL
├── docs/                            # Architektur, ADRs, Runbooks
├── infra/terraform/gcp/             # GCP-Grundgerüst (Buckets, Datasets, IAM, Cloud Run)
├── kafka/                           # Topic-Katalog und create_topics.sh
├── nosql/mongodb/                   # init.js für Collections und Indexes
├── orchestration/kestra/flows/      # Kestra-Flow (daily_platform_ingestion)
├── pipeline/                        # Bruin Asset-Definitionen (5 Pipeline-Schritte)
├── quality/
│   ├── contracts/                   # 4 YAML-Verträge
│   └── expectations/                # 5 SQL-Checks (fx_rates, order_statuses, etc.)
├── spark/jobs/                      # clickstream_sessionization.py
├── sql/postgres/init/               # Schema-Init + Raw-Tabellen-DDL
├── src/omnichannel_platform/
│   ├── api/                         # FastAPI-App, Router, Models, DB-Zugriff
│   ├── batch/                       # commerce_batch_ingestion, source_plans, orders_ingestion
│   ├── common/                      # logging, settings, clients (Postgres/Mongo), io
│   ├── dashboard/                   # testbare Dashboard-Logik (logic.py)
│   ├── quality/                     # rules_catalog + gx_validation (Great Expectations)
│   ├── streaming/                   # clickstream_consumer (Replay + Kafka + Persist)
│   └── warehouse/                   # layer_catalog
├── tests/
│   ├── fixtures/                    # sample_orders.json, sample_clickstream_events.jsonl
│   ├── unit/                        # 12+ Testdateien, API- und Dashboard-Tests
│   └── integration/                 # 2 Integrations-Checks
└── warehouse/
    ├── dbt/
    │   ├── macros/                  # raw_relations.sql (source-aware Fallback)
    │   ├── models/
    │   │   ├── staging/             # 9 Staging Views
    │   │   ├── intermediate/        # 2 Intermediate Views
    │   │   └── marts/               # 3 Mart Tables
    │   ├── tests/                   # 3 Singular Tests
    │   ├── dbt_project.yml
    │   ├── profiles.ci.yml          # DuckDB CI-Profil
    │   └── profiles.yml.example     # Postgres/DuckDB/BigQuery Multi-Target
    └── seeds/                       # (bereit für Referenzdaten)
```

Wichtige Einstiegspunkte:

- [Dockerfile](Dockerfile) -- Multi-Stage Docker Build
- [docker-compose.yml](docker-compose.yml) -- 10-Service Plattform-Stack
- [dashboard/app.py](dashboard/app.py) -- Streamlit-Frontend
- [src/omnichannel_platform/api/main.py](src/omnichannel_platform/api/main.py) -- FastAPI-REST-API
- [src/omnichannel_platform/batch/commerce_batch_ingestion.py](src/omnichannel_platform/batch/commerce_batch_ingestion.py) -- Batch-Pipeline
- [src/omnichannel_platform/streaming/clickstream_consumer.py](src/omnichannel_platform/streaming/clickstream_consumer.py) -- Streaming-Pipeline
- [src/omnichannel_platform/quality/rules_catalog.py](src/omnichannel_platform/quality/rules_catalog.py) -- Quality-Runner
- [orchestration/kestra/flows/daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml) -- Kestra-Orchestrierung
- [infra/terraform/gcp/main.tf](infra/terraform/gcp/main.tf) -- GCP-Infrastruktur

---

## Lokales Setup

> **Hinweis zu Python-Versionen:** Das Projekt unterstützt Python >=3.11 und ist grundlegend mit Python 3.11-3.14 getestet.
> **Wichtig für Python 3.14:** Das Paket `dbt-core` (bzw. dessen Abhängigkeit `mashumaro`) ist aktuell inkompatibel mit Python 3.14. Wenn du lokal Python 3.14 nutzt, führe `dbt build` wie unter [Warehouse und dbt-Modellierung](#3-transformation-im-warehouse-dbt-build) (Option C) beschrieben im Docker-Container aus.
> Die Docker-Images und CI-Workflows nutzen stabil Python 3.11.

### Schnellstart für die Python-Skripte

```bash
# 1. Python-Umgebung
python3 -m venv .venv
source .venv/bin/activate
make install-local

# 2. Environment-Datei anlegen
cp .env.example .env

# 3. Mindest-Services für lokale Skript-Tests starten
docker compose up -d postgres

# Optional, aber empfohlen für den vollen E2E-Pfad:
docker compose up -d mongo redpanda

# Optional für Dashboard-im-API-Modus:
docker compose up -d api

# 4. PostgreSQL prüfen
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

**Wichtig:** Führe alle `python -m omnichannel_platform...` Befehle aus dem Repository-Root aus.

**Was richtet der Schnellstart ein?**

- `make install-local` installiert das Projekt editierbar mit `dev`, `batch`, `streaming`, `warehouse`, `nosql`, `quality`, `dashboard` und `api`
- `cp .env.example .env` erzeugt die lokale Laufzeitkonfiguration auf Basis der mitgelieferten Defaults
- für die meisten lokalen Läufe müssen die Werte in `.env` nicht angepasst werden

**Alternative Installationsvarianten:**

```bash
make install          # nur Basispakete
make install-dev      # Basispakete + pytest, ruff, pre-commit
make install-local    # lokales Vollsetup ohne Spark
```

**Hinweise zu Extras und Laufzeit:**

- Spark ist bewusst nicht Teil von `make install-local`; dafür separat `pip install -e ".[spark]"`
- das Dashboard nutzt `API_BASE_URL`, wenn es über FastAPI statt direkt über SQLAlchemy lesen soll
- die Standardwerte in `.env` passen zum Docker-Compose-Stack

### Grundlegende Repo-Checks

Direkt nach dem Setup kannst du die wichtigsten lokalen Validierungen ausführen:

```bash
make lint
make test
```

**Was decken die Tests ab?**

- `test_settings.py`: Config-Loading, Deep-Merge, Environment-Override
- `test_module_resolution.py`: Paket ist direkt aus dem Repo-Root importierbar
- `test_repository_foundations.py`: Schlüsseldateien und Repo-Grundstruktur existieren
- `test_ingestion_plans.py`: Source-Plans für Batch und Streaming, Event-Routing, Normalisierung
- `test_clients.py`: PostgreSQL-Preflight und Mongo-Fallback-Verhalten
- `test_api_routes.py`: FastAPI-Endpunkte für Orders, Sessions, Pipeline-Status und Health
- `test_dashboard_logic.py` und `test_dashboard_insights.py`: Filterlogik, KPI-Helfer und Insight-Ableitung
- `test_quality_assets.py`: Discovery von Contracts und SQL-Expectations

### Welche Docker-Services braucht welches Skript?

| Skript | Pflicht | Optional | Hinweis |
|---|---|---|---|
| `commerce_batch_ingestion.py` | `postgres` | `mongo` | Batch lädt immer nach PostgreSQL. Mongo-Persist wird bei Nicht-Erreichbarkeit übersprungen. |
| `clickstream_consumer.py` | `postgres` | `redpanda`, `mongo` | Replay persistiert immer nach PostgreSQL. Kafka- und Mongo-Schritte sind optional. |
| `omnichannel_platform.api.main` | `postgres` | — | FastAPI stellt Orders, Sessions, Enrichments, Health und Pipeline-Status als REST-API bereit. |
| `rules_catalog.py` | `postgres` | — | SQL-Checks brauchen die Raw-/Mart-Tabellen in PostgreSQL. |
| `dashboard/app.py` | `postgres` | `api` | Dashboard kann direkt aus PostgreSQL lesen oder über die FastAPI-Schicht arbeiten. |

### Typische lokale Stolpersteine

- `connection refused` auf `localhost:5432`: PostgreSQL läuft nicht. Starte `docker compose up -d postgres`.
- `localhost:27017 connection refused`: MongoDB läuft nicht. Das ist für Batch und Streaming **kein** Blocker; Mongo-Persist wird übersprungen.
- Open Food Facts liefert `429 Too Many Requests`: Die Batch-Pipeline fällt automatisch auf das lokale Sample unter `data/sample/batch/open_food_facts_products_sample.json` zurück.
- `postgres` startet und beendet sich sofort mit einem Hinweis auf PostgreSQL 18: Dann ist meist ein altes lokales Docker-Volume inkompatibel.

Wenn dir die alte lokale Entwicklungsdatenbank nicht wichtig ist, starte sauber neu:

```bash
docker compose down
docker volume rm omnichannel-commerce-data-platform_postgres_data
docker compose up -d postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

Wenn du die alten Daten behalten musst, solltest du das Volume nicht löschen, sondern
entweder auf die frühere PostgreSQL-Version zurückgehen oder das Volume per `pg_upgrade`
migrieren.

---

## Datenfluss im Detail

### 1. Batch-Ingestion (`commerce_batch_ingestion.py`)

**Skript:** [commerce_batch_ingestion.py](src/omnichannel_platform/batch/commerce_batch_ingestion.py)

**Was macht `commerce_batch_ingestion.py` kurz?**

Das Skript ist der Batch-Einstiegspunkt für die lokale Raw-Layer-Befüllung.
Es verarbeitet nacheinander vier Quellen:

- `olist`: erzeugt oder liest lokale CSV-Snapshots und lädt sie in `raw.olist_*`
- `open_food_facts`: ruft Produktdaten per API ab und lädt sie in `raw.open_food_facts_products`
- `open_meteo`: holt Wetterdaten und lädt sie in `raw.open_meteo_weather`
- `frankfurter`: holt FX-Raten und lädt sie in `raw.frankfurter_fx_rates`

Zusätzlich schreibt das Skript Bronze-Artefakte unter `storage/bronze/...` und protokolliert jeden Lauf
in `raw.ingestion_audit`.

**Pflicht vor dem Start: PostgreSQL vorbereiten**

```bash
docker compose up -d postgres
docker compose ps postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

**Was machen diese drei Docker-Kommandos?**

| Kommando | Bedeutung | Was wird gestartet / ausgeführt? |
|---|---|---|
| `docker compose up -d postgres` | Startet nur den PostgreSQL-Service aus `docker-compose.yml` im Hintergrund | Docker-Compose-Service: `postgres`, Container: `omnichannel-postgres` |
| `docker compose ps postgres` | Zeigt den Status genau dieses Services | Kein neuer Container, nur Statusanzeige für `postgres` |
| `docker compose exec postgres pg_isready -U commerce -d commerce_platform` | Führt im laufenden PostgreSQL-Container das Healthcheck-Tool `pg_isready` aus | Befehl läuft **im** Container `omnichannel-postgres` |

**Wichtig:** `docker compose up -d postgres` startet **nicht** den ganzen Stack, sondern nur den Service
`postgres`. Services wie `mongo`, `redpanda`, `dashboard` oder `kestra` bleiben dabei aus.

**Dann den Batch starten:**

```bash
# Alle 4 Quellen auf einmal (Standardverhalten)
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev

# Einzelne Quelle gezielt ausführen
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source olist
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source open_food_facts
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source open_meteo
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source frankfurter

# Oder per Makefile (führt alle Quellen aus)
make run-batch
```

**CLI-Argumente:**

| Flag | Werte | Default | Bedeutung |
|---|---|---|---|
| `--env` | `dev`, `prod` | `dev` | Lädt `config/base.yaml` + `config/<env>.yaml` |
| `--source` | `all`, `olist`, `open_food_facts`, `open_meteo`, `frankfurter` | `all` | Beschränkt den Lauf auf eine einzelne Quelle |

**Voraussetzungen:**
- PostgreSQL muss laufen (`docker compose up -d postgres`)
- MongoDB und Redpanda sind optional (graceful Skip wenn nicht erreichbar)

**Wenn direkt `connection refused` auf `localhost:5432` erscheint, fehlt fast immer genau dieser Schritt.**

```bash
docker compose up -d postgres
docker compose ps postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

**Interner Ablauf pro Quelle:**

| Quelle | Was passiert | Erwartete Zeilen | Artefakte |
|---|---|---|---|
| **olist** | 1. Prüft ob Seed-CSVs unter `storage/bronze/olist/` existieren. 2. Falls nicht: generiert deterministische Daten mit `random.Random(42)` (500 Orders, 250 Customers, 150 Products, 1001 Items, 500 Payments). 3. Liest alle 5 CSVs, TRUNCATE + APPEND in `raw.olist_*`. 4. Schreibt Audit-Eintrag und Run-Manifest. | 2401 total | `storage/bronze/olist/_runs/<batch_id>/run_manifest.json` |
| **open_food_facts** | 1. Ruft 4 konfigurierte Barcodes per API ab (z.B. Nutella, Coca-Cola). 2. Normalisiert Produktdaten (code, name, brands, categories, ecoscore). 3. Bei API-Fehler: Fallback auf `data/sample/batch/open_food_facts_products_sample.json`. 4. Speichert in `raw.open_food_facts_products` + optional MongoDB. | 3-4 Produkte | `storage/bronze/open_food_facts/products/_runs/<batch_id>/products_raw.jsonl` |
| **open_meteo** | 1. Holt Tageswerte (Temperatur, Niederschlag) für 3 Städte (Sao Paulo, Rio, Belo Horizonte) über 365 Tage (2018). 2. Bei API-Fehler: generiert 14 Fallback-Tage pro Stadt. 3. Speichert in `raw.open_meteo_weather` + optional MongoDB. | ~1095 (365 x 3) | `storage/bronze/open_meteo/weather/_runs/<batch_id>/weather_raw.jsonl` |
| **frankfurter** | 1. Holt EUR->USD und EUR->BRL Wechselkurse für 2018. 2. Bei API-Fehler: generiert 14 Fallback-Tage mit 2 Währungen. 3. Speichert in `raw.frankfurter_fx_rates` + optional MongoDB. | ~730 (365 Tage x 2) | `storage/bronze/frankfurter/fx/_runs/<batch_id>/fx_rates_raw.jsonl` |

**Erwartete Log-Ausgabe (Beispiel):**

```
INFO  Starting omnichannel batch ingestion for environment=dev
INFO  Generating local Olist seed files under storage/bronze/olist
INFO  Loaded 250 rows from olist_customers_dataset.csv into raw.olist_customers
INFO  Loaded 1200 rows from olist_order_items_dataset.csv into raw.olist_order_items
INFO  Loaded 500 rows from olist_order_payments_dataset.csv into raw.olist_order_payments
INFO  Loaded 500 rows from olist_orders_dataset.csv into raw.olist_orders
INFO  Loaded 150 rows from olist_products_dataset.csv into raw.olist_products
INFO  Source olist ingested 2401 rows
INFO  Requesting https://world.openfoodfacts.org/api/v2/product/3017620422003.json
INFO  Requesting https://world.openfoodfacts.org/api/v2/product/5449000000996.json
INFO  Requesting https://world.openfoodfacts.org/api/v2/product/7622210449283.json
INFO  Requesting https://world.openfoodfacts.org/api/v2/product/3274080005003.json
INFO  Source open_food_facts ingested 4 rows
INFO  Requesting https://archive-api.open-meteo.com/v1/archive?latitude=...
INFO  Source open_meteo ingested 1095 rows
INFO  Requesting https://api.frankfurter.dev/v2/rates?from=2018-01-01&to=2018-12-31&base=EUR&quotes=USD,BRL
INFO  Source frankfurter ingested 730 rows
```

**Verifizierung nach dem Lauf:**

```bash
# Audit-Tabelle prüfen
docker compose exec postgres psql -U commerce -d commerce_platform -c \
  "SELECT source_name, batch_id, row_count, loaded_at FROM raw.ingestion_audit ORDER BY loaded_at DESC;"

# Einzelne Tabellen prüfen
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT count(*) FROM raw.olist_orders;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT count(*) FROM raw.open_meteo_weather;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT * FROM raw.open_food_facts_products LIMIT 3;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT * FROM raw.frankfurter_fx_rates LIMIT 5;"
```

**Was prüfen diese `psql`-Kommandos genau?**

| Kommando | Zweck |
|---|---|
| `SELECT ... FROM raw.ingestion_audit ...` | Zeigt, welche Quellen im letzten Lauf geladen wurden, mit `batch_id`, `row_count` und Zeitstempel |
| `SELECT count(*) FROM raw.olist_orders;` | Prüft, ob die Olist-Orders wirklich im Raw-Schema gelandet sind |
| `SELECT count(*) FROM raw.open_meteo_weather;` | Prüft, ob die Wetterdaten geladen wurden |
| `SELECT * FROM raw.open_food_facts_products LIMIT 3;` | Zeigt ein paar echte Beispielzeilen der Produkt-Enrichment-Daten |
| `SELECT * FROM raw.frankfurter_fx_rates LIMIT 5;` | Zeigt ein paar geladene FX-Raten |

**Schrittweise in den Container und in `psql` gehen**

Wenn du nicht nur Einmal-Kommandos ausführen, sondern PostgreSQL interaktiv erkunden willst:

```bash
# 1. Interaktive Shell im laufenden PostgreSQL-Container
docker compose exec postgres bash

# 2. Im Container psql starten
psql -U commerce -d commerce_platform
```

Dann in `psql` zum Erkunden:

```sql
\conninfo
\l
\dn
\dt
\dt raw.*
\d raw.ingestion_audit
\d raw.olist_orders
SELECT * FROM raw.ingestion_audit ORDER BY loaded_at DESC LIMIT 10;
SELECT count(*) FROM raw.olist_orders;
SELECT count(*) FROM raw.open_meteo_weather;
SELECT * FROM raw.open_food_facts_products LIMIT 3;
SELECT * FROM raw.frankfurter_fx_rates LIMIT 5;
```

**Bedeutung der wichtigsten `psql`-Befehle**

| Befehl | Bedeutung |
|---|---|
| `\conninfo` | Zeigt, mit welcher DB und welchem User du verbunden bist |
| `\l` | Listet alle Datenbanken |
| `\dn` | Listet alle Schemas |
| `\dt` | Listet Tabellen im aktuellen Suchpfad |
| `\dt raw.*` | Listet gezielt alle Tabellen im Schema `raw` |
| `\d raw.ingestion_audit` | Zeigt Struktur einer einzelnen Tabelle |
| `\q` | Beendet `psql` |

Zum Verlassen:

```bash
# psql verlassen
\q

# Container-Shell verlassen
exit
```

**Fehlerszenarien:**

| Situation | Verhalten |
|---|---|
| PostgreSQL nicht erreichbar | `ensure_postgres_is_reachable()` bricht ab mit deutschsprachiger Hilfemeldung |
| Open Food Facts API down | Automatischer Fallback auf lokales Sample-JSON, Log-Warnung |
| Open-Meteo API down | Generiert 14 Fallback-Tage pro Stadt, Log-Warnung |
| Frankfurter API down | Generiert 14 Fallback-Tage mit 2 Währungen, Log-Warnung |
| MongoDB nicht erreichbar | Mongo-Persist wird mit Warnung übersprungen, Pipeline läuft weiter |

**Relevante Tests für diesen Abschnitt:**

- `tests/unit/test_ingestion_plans.py`
- `tests/unit/test_olist_seed_determinism.py`
- `tests/unit/test_batch_helpers.py`
- `tests/unit/test_clients.py`

### 2. Streaming-Replay (`clickstream_consumer.py`)

**Skript:** [clickstream_consumer.py](src/omnichannel_platform/streaming/clickstream_consumer.py)

**Starten:**

```bash
# Replay-Modus (Standard)
python -m omnichannel_platform.streaming.clickstream_consumer --env dev --mode replay

# Continuous-Modus (aktuell identisch mit Replay, später Kafka-Consumer-Loop)
python -m omnichannel_platform.streaming.clickstream_consumer --env dev --mode continuous

# Oder per Makefile
make run-streaming
```

**CLI-Argumente:**

| Flag | Werte | Default | Bedeutung |
|---|---|---|---|
| `--env` | `dev`, `prod` | `dev` | Konfigurationsumgebung |
| `--mode` | `replay`, `continuous` | `replay` | `replay` = einmaliger Durchlauf, `continuous` = aktuell identisch, später dauerhafter Consumer |

**Voraussetzungen:**
- PostgreSQL muss laufen (Pflicht für `raw.retailrocket_events`)
- Redpanda/Kafka ist optional (Events werden trotzdem persistiert)
- MongoDB ist optional

**Wenn PostgreSQL lokal noch nicht läuft, starte es vor dem Replay explizit:**

```bash
docker compose up -d postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

**Interner Ablauf (Schritt für Schritt):**

1. **Plan laden:** Liest `config/base.yaml` + `config/dev.yaml`, baut einen `StreamingIngestionPlan` mit Replay-Source, Topic-Mapping, Consumer-Group und Bootstrap-Servers.
2. **Events lesen:** Öffnet `data/sample/streaming/retailrocket_events.jsonl` und liest alle Events (aktuell 3 Beispiel-Events: je 1x view, addtocart, transaction).
3. **Normalisierung:** Jedes Event wird normalisiert -- Event-Type in Lowercase, IDs als Strings, Zuweisung des Ziel-Topics über ein konfigurierbares Mapping:
   - `view` -> `retailrocket.events.view`
   - `addtocart` -> `retailrocket.events.addtocart`
   - `transaction` -> `retailrocket.events.transaction`
   - unbekannte Typen -> `retailrocket.events.dlq` (Dead Letter Queue)
4. **Kafka-Publish:** Wenn ein Broker erreichbar ist, wird jedes Event auf den Raw-Topic und den typspezifischen Topic gesendet. Bei Verbindungsfehler: graceful Skip mit Log-Warnung.
5. **PostgreSQL-Persist:** TRUNCATE auf `raw.retailrocket_events`, dann INSERT aller normalisierten Rows.
6. **MongoDB-Persist:** Ablage der Roh-Events inkl. `replayed_at`-Timestamp in der konfigurierten Collection.
7. **Checkpoint schreiben:** Speichert `last_replay.json` unter `storage/checkpoints/retailrocket/` und archiviert Roh- und normalisierte Events unter `replays/`.

**Erwartete Log-Ausgabe:**

```
INFO  Starting Retailrocket streaming ingestion for environment=dev mode=replay
INFO  Replay source=data/sample/streaming/retailrocket_events.jsonl raw_topic=retailrocket.events.raw
      group=retailrocket-replay-dev checkpoint=storage/checkpoints/retailrocket/
      bootstrap=localhost:9092
INFO  Retailrocket replay finished: records=3 postgres=3 mongo=3
INFO    routed_topic=retailrocket.events.addtocart count=1
INFO    routed_topic=retailrocket.events.transaction count=1
INFO    routed_topic=retailrocket.events.view count=1
```

**Verifizierung nach dem Lauf:**

```bash
# PostgreSQL: Event-Verteilung prüfen
docker compose exec postgres psql -U commerce -d commerce_platform -c \
  "SELECT event_type, count(*) FROM raw.retailrocket_events GROUP BY event_type;"
# Erwartet: view=1, addtocart=1, transaction=1

# Checkpoint prüfen
cat storage/checkpoints/retailrocket/last_replay.json
# Erwartet: {"mode": "replay", "record_count": 3, "last_event_ts": "...", ...}

# Archivierte Replay-Dateien prüfen
ls storage/checkpoints/retailrocket/replays/

# Kafka-Topics prüfen (wenn Redpanda läuft)
docker compose exec redpanda rpk topic list
docker compose exec redpanda rpk topic consume retailrocket.events.raw --num 3
```

**Fehlerszenarien:**

| Situation | Verhalten |
|---|---|
| PostgreSQL nicht erreichbar | `ensure_postgres_is_reachable()` bricht ab mit deutschsprachiger Hilfemeldung |
| Redpanda/Kafka nicht erreichbar | Kafka-Publish wird übersprungen, Rest läuft weiter |
| MongoDB nicht erreichbar | Mongo-Persist wird mit Warnung übersprungen, Rest läuft weiter |
| JSONL-Datei leer | Replay beendet sich sauber mit `records=0` |

**Relevante Tests für diesen Abschnitt:**

- `tests/unit/test_ingestion_plans.py`
- `tests/unit/test_clients.py`

### 3. Transformation im Warehouse (`dbt build`)

**Starten:**

```bash
# Option A: dbt gegen DuckDB (kein PostgreSQL nötig, gut für CI)
make run-warehouse
# (Bei lokalem Python 3.14 stattdessen im Container ausführen:)
# docker compose exec platform-runner make run-warehouse

# Oder nur dbt:
make dbt-build-ci

# Option B: dbt gegen lokales PostgreSQL (nach Batch-Ingestion)
mkdir -p ~/.dbt && cp warehouse/dbt/profiles.yml.example ~/.dbt/profiles.yml
dbt build --project-dir warehouse/dbt --target dev

# Option C: dbt im Docker-Container (empfohlen bei lokalem Python 3.14)
# Der platform-runner Container nutzt Python 3.11 und vermeidet dbt-Inkompatibilitäten
docker compose up -d platform-runner
docker compose exec platform-runner bash -c '
mkdir -p /tmp/dbt-profiles
cat > /tmp/dbt-profiles/profiles.yml << PROFILES
omnichannel_platform:
  target: local-pg
  outputs:
    local-pg:
      type: postgres
      host: postgres
      user: commerce
      password: commerce
      port: 5432
      dbname: commerce_platform
      schema: staging
      threads: 4
PROFILES
dbt build --project-dir warehouse/dbt --profiles-dir /tmp/dbt-profiles --target local-pg
'
```

Die dbt-Modelle bilden aktuell drei Schichten:

- **staging** (9 Views): Normalisierung der Rohdaten mit source-aware Fallbacks. Das Macro `raw_relation_exists()` sorgt dafür, dass Modelle auch kompilieren, wenn einzelne Raw-Tabellen noch nicht existieren (z.B. im DuckDB-CI-Profil).
- **intermediate** (2 Views):
  - `int_orders_with_context`: Verbindet Orders mit Customers (Stadt, Bundesstaat), Items (Artikelanzahl, Warenwert), Payments (BRL-Betrag, Zahlungsart), Weather (Temperatur, Niederschlag am Kauftag+Stadt) und FX (BRL->USD Cross-Rate über EUR).
  - `int_retailrocket_sessions`: 30-Min-Gap-Sessionisierung mit Window-Functions (LAG, SUM), Event-Type-Counts pro Session.
- **marts** (3 Tables):
  - `fct_commerce_orders`: Order-Grain Fact mit BRL- und USD-Beträgen, Kundengeografie, Produktkategorie, Wetterkontext
  - `fct_retailrocket_sessions`: Session-Grain Fact mit view/addtocart/transaction-Counts
  - `dim_products`: Olist + Open Food Facts kombiniert über `product_key` und `source_system`

Zusätzlich laufen bei jedem `dbt build`:
- 3 Singular-Tests (`assert_valid_olist_order_statuses`, `assert_valid_retailrocket_event_types`, `assert_positive_fx_rates`)
- Spalten-Tests (not_null, unique) auf allen Schlüsselfeldern

**PostgreSQL-Ergebnis nach einem echten Build prüfen:**

```bash
docker compose exec postgres psql -U commerce -d commerce_platform -c "
  SELECT count(*) as orders, avg(payment_value_brl) as avg_payment
  FROM marts.fct_commerce_orders;
"
docker compose exec postgres psql -U commerce -d commerce_platform -c "
  SELECT * FROM marts.dim_products LIMIT 5;
"
```

**Relevante Tests für diesen Abschnitt:**

- dbt-Singular- und Schema-Tests im Projekt selbst
- `tests/integration/test_repository_foundations.py`

### 4. Datenqualität (`rules_catalog.py`)

**Skript:** [rules_catalog.py](src/omnichannel_platform/quality/rules_catalog.py)

**Starten:**

```bash
# Strict-Modus (Exit-Code 1 bei fehlgeschlagenen Expectations)
python -m omnichannel_platform.quality.rules_catalog

# Non-Strict-Modus (immer Exit-Code 0, auch bei Fehlern)
python -m omnichannel_platform.quality.rules_catalog --non-strict

# Per Makefile
make run-quality
```

**CLI-Argumente:**

| Flag | Default | Bedeutung |
|---|---|---|
| `--non-strict` | nicht gesetzt (= strict) | Im Strict-Modus bricht das Skript mit Exit-Code 1 ab, wenn Expectations fehlschlagen. Mit `--non-strict` wird nur geloggt. |

**Interner Ablauf:**

1. **Contract-Discovery:** Lädt alle YAML-Dateien aus `quality/contracts/` -- das sind deklarative Verträge, die beschreiben welche Spalten welche Bedingungen erfüllen müssen (z.B. not null, domain values).
2. **Expectation-Discovery:** Findet alle `.sql`-Dateien unter `quality/expectations/`.
3. **PostgreSQL-Verbindung prüfen:** Versucht eine Verbindung aufzubauen. Wenn PostgreSQL nicht erreichbar ist, werden alle SQL-Expectations als `skipped` markiert (kein Fehler).
4. **SQL-Execution:** Führt jede SQL-Datei gegen PostgreSQL aus. Die SQL-Queries sind so geschrieben, dass sie Zeilen zurückgeben die NICHT der Erwartung entsprechen. 0 Ergebniszeilen = passed, >0 Zeilen = failed.
5. **Report schreiben:** Speichert einen JSON-Report nach `storage/checkpoints/quality/last_run.json`.

**Erwartete Log-Ausgabe (mit PostgreSQL und Daten):**

```
INFO  Discovered 4 quality contract files
INFO    contract=quality/contracts/raw_olist_orders.yml owner=platform-team
INFO    contract=quality/contracts/raw_retailrocket_events.yml owner=platform-team
INFO    contract=quality/contracts/marts_commerce.yml owner=platform-team
INFO    contract=quality/contracts/reference_enrichments.yml owner=platform-team
INFO  Expectation assert_positive_fx_rates status=passed failures=0
INFO  Expectation assert_valid_olist_order_statuses status=passed failures=0
INFO  Expectation assert_valid_retailrocket_event_types status=passed failures=0
INFO  Expectation reference_open_food_facts_products_not_null status=passed failures=0
```

**Erwartete Log-Ausgabe (ohne PostgreSQL):**

```
INFO  Discovered 4 quality contract files
WARNING  PostgreSQL is not reachable; skipping SQL expectations
INFO  Expectation assert_positive_fx_rates status=skipped failures=0
INFO  Expectation assert_valid_olist_order_statuses status=skipped failures=0
INFO  Expectation assert_valid_retailrocket_event_types status=skipped failures=0
INFO  Expectation reference_open_food_facts_products_not_null status=skipped failures=0
```

**Verifizierung:**

```bash
cat storage/checkpoints/quality/last_run.json | python -m json.tool
# Erwartete Struktur:
# {
#   "contracts": [...],      # Liste der geladenen YAML-Verträge
#   "results": [             # Ergebnis pro SQL-Expectation
#     {"name": "assert_positive_fx_rates", "status": "passed", "row_count": 0, ...},
#     ...
#   ],
#   "summary": {"passed": 4, "failed": 0, "skipped": 0}
# }
```

**Relevante Tests für diesen Abschnitt:**

- `tests/unit/test_quality_assets.py`
- `tests/unit/test_clients.py`

### 5. Kompletter Pipeline-Durchlauf (Reihenfolge)

Die Skripte bauen aufeinander auf. Für einen vollständigen Durchlauf ist folgende Reihenfolge nötig:

```bash
docker compose up -d                     # 1. Infrastruktur starten
make kafka-topics                        # 2. Kafka-Topics anlegen
make run-batch                           # 3. Batch: füllt raw.* (Olist + APIs)
make run-streaming                       # 4. Streaming: füllt raw.retailrocket_events
dbt build --project-dir warehouse/dbt \
  --target dev                           # 5. dbt: baut staging -> intermediate -> marts
make run-quality                         # 6. Quality: prüft alle Tabellen
make run-dashboard                       # 7. Dashboard: zeigt alles im Browser an
```

Schritt 3 und 4 können parallel laufen (unabhängige Quellen). Schritt 5 setzt voraus, dass
die Raw-Tabellen gefüllt sind. Schritt 6 setzt voraus, dass dbt gelaufen ist (für Mart-Checks).
Das Dashboard (Schritt 7) zeigt nur Daten an, wenn mindestens Schritt 3-5 abgeschlossen sind.

---

## Gesamtvalidierung

Wenn du den gesamten Stand einmal sauber durchtesten willst, reicht diese Reihenfolge:

```bash
make lint
make test
docker compose up -d postgres mongo redpanda api dashboard
docker compose exec postgres pg_isready -U commerce -d commerce_platform
make kafka-topics
make run-batch
make run-streaming
mkdir -p ~/.dbt && cp warehouse/dbt/profiles.yml.example ~/.dbt/profiles.yml
dbt build --project-dir warehouse/dbt --target dev
make run-quality
curl http://localhost:8000/api/v1/health
curl -f http://localhost:8501/_stcore/health
```

Die Detailprüfungen stehen jetzt direkt in den jeweiligen Fachabschnitten:

- Setup und Repo-Checks: [Lokales Setup](#lokales-setup)
- Batch und Raw-Layer: [1. Batch-Ingestion](#1-batch-ingestion-commerce_batch_ingestionpy)
- Streaming und Kafka: [2. Streaming-Replay](#2-streaming-replay-clickstream_consumerpy)
- Warehouse und dbt: [3. Transformation im Warehouse](#3-transformation-im-warehouse-dbt-build)
- Datenqualität: [4. Datenqualität](#4-datenqualität-rules_catalogpy)
- Spark: [Spark-Pfad](#spark-pfad)
- API: [API-Schicht (FastAPI)](#api-schicht-fastapi)
- Dashboard: [Dashboard und Frontend](#dashboard-und-frontend)
- Terraform und Cloud: [GCP- und Terraform-Fundament](#gcp--und-terraform-fundament)

---

## Zentrale Make-Targets

### Setup und Entwicklung

| Target | Zweck | Voraussetzung |
|---|---|---|
| `make install` | Nur Basispakete (pydantic, dotenv, PyYAML) | Python-venv |
| `make install-dev` | Basispakete + dev (pytest, ruff, pre-commit) | Python-venv |
| `make install-local` | Alles außer Spark, inklusive API (empfohlen) | Python-venv |
| `make lint` | Ruff-Linting ausführen | `make install-dev` |
| `make test` | pytest-Suite ausführen (inkl. API-Tests) | `make install-dev` |
| `make pre-commit` | Pre-commit Hooks ausführen | `make install-dev` |

### Docker und Infrastruktur

| Target | Zweck | Voraussetzung |
|---|---|---|
| `make up` | Docker-Compose-Stack starten (10 Services) | Docker installiert |
| `make down` | Docker-Compose-Stack stoppen | Docker |
| `make logs` | Docker-Compose-Logs live anzeigen | Docker |
| `make kafka-topics` | 5 Kafka-/Redpanda-Topics anlegen | Redpanda läuft |
| `make docker-build-pipeline` | Pipeline-Image lokal bauen (`Dockerfile` target `pipeline`) | Docker |
| `make docker-build-api` | API-Image lokal bauen (`Dockerfile` target `api`) | Docker |
| `make docker-build-dashboard` | Dashboard-Image bauen (kann mit `GCP_PROJECT_ID` und `GCP_REGION` getaggt werden) | Docker |

### Pipeline-Ausführung

| Target | Zweck | Voraussetzung |
|---|---|---|
| `make run-batch` | Batch-Ingestion: Olist Seeds + Open Food Facts + Open-Meteo + Frankfurter | PostgreSQL läuft |
| `make run-streaming` | Retailrocket-Replay: JSONL lesen, normalisieren, Kafka + PG persistieren | PostgreSQL läuft |
| `make run-api` | FastAPI REST API lokal auf Port 8000 starten | PostgreSQL läuft |
| `make run-warehouse` | Layer-Planung + `dbt build` gegen DuckDB-CI-Profil | `make install-local` |
| `make dbt-build-ci` | Nur `dbt build` gegen DuckDB (ohne Layer-Planung) | dbt installiert |
| `make run-quality` | SQL-Expectations gegen PostgreSQL ausführen, JSON-Report schreiben | Optional: PostgreSQL |
| `make run-gx` | Great Expectations Validierung (5 Tabellen, programmatisch) | PostgreSQL + Python <3.14 |
| `make run-quality-all` | Beide Quality-Runner nacheinander (SQL + GX) | PostgreSQL |
| `make run-dashboard` | Streamlit-Dashboard lokal starten auf Port 8501 | `make install-local` |
| `make spark-sessionize` | PySpark-Sessionisierung: JSONL -> Parquet | PySpark + JVM |

### GCP Cloud-Deployment

| Target | Zweck | Voraussetzung |
|---|---|---|
| `make terraform-init-gcp` | Terraform in `infra/terraform/gcp` initialisieren | Terraform + `terraform.tfvars` |
| `make terraform-plan-gcp` | Terraform-Plan inkl. Cloud-Run-Image-Variable anzeigen | `terraform init` |
| `make terraform-apply-gcp` | Terraform-Apply: GCS, BigQuery, Artifact Registry, Cloud Run | `terraform init` |
| `make deploy-dashboard-gcp` | All-in-One: Dashboard-Image bauen, pushen, Cloud Run deployen | Docker + gcloud auth |

---

## Was aktuell implementiert ist

### Batch

- Olist-Seed-Generierung (deterministisch, 500 Orders, 250 Customers, 150 Products, 1200 Items, 500 Payments)
- Laden aller 5 Olist-Tabellen in `raw.*` mit TRUNCATE+APPEND
- Open-Food-Facts-Produktabruf per Barcode (4 konfigurierte Barcodes) mit lokalem Fallback
- Open-Meteo-Wetterabruf für 3 brasilianische Städte (365 Tage)
- Frankfurter-FX-Abruf für EUR->USD/BRL (1 Jahr Handelstage)
- Bronze-Artefakte und Run-Manifeste pro Batch-Lauf
- PostgreSQL-Loads in `raw.*` mit Ingestion-Audit
- Optionale Mongo-Persistenz für alle API-Payloads

### Streaming

- Replay aus lokaler JSONL-Datei (3 Beispiel-Events)
- Event-Normalisierung (Lowercasing, String-Casting)
- Topic-Routing (`view` -> `retailrocket.events.view`, `addtocart` -> `retailrocket.events.addtocart`, `transaction` -> `retailrocket.events.transaction`, unbekannt -> DLQ)
- Kafka-Publish wenn Broker verfügbar (graceful Skip wenn nicht)
- Persistenz nach PostgreSQL `raw.retailrocket_events`
- Optionale MongoDB-Persist
- Replay-Artefakte und Checkpoint-Dateien

### Warehouse (dbt)

- `raw_relation_exists` Macro für source-aware Fallbacks
- 9 Staging-Views (alle Quellen normalisiert)
- `int_orders_with_context`: Orders + Customers + Items + Payments + Wetter + FX-Cross-Rate (BRL->USD)
- `int_retailrocket_sessions`: 30-Min-Gap-Sessionisierung mit Window-Functions
- `fct_commerce_orders`: Order-Grain Fact mit `payment_value_usd`
- `fct_retailrocket_sessions`: Session-Grain Fact mit Event-Type-Counts
- `dim_products`: Olist + Open Food Facts kombiniert über `product_key` und `source_system`
- 3 Singular-Tests + Spalten-Tests (not_null, unique)

### Datenqualität

- 4 deklarative Qualitätsverträge (Olist, Retailrocket, Marts, Enrichments)
- SQL-Expectations (FX-Raten positiv, Order-Statuses gültig, Event-Types gültig, Produkt-Codes nicht null)
- **Great Expectations** Integration mit programmatischen Expectations für 5 Tabellen (not_null, unique, accepted_values, row_count)
- Python-Runner mit PostgreSQL-Execution und JSON-Report
- Graceful Skip wenn PostgreSQL nicht erreichbar oder Python >=3.14 (GX-Einschränkung)

### Sample-Daten

- 3 kleine Beispiel-Dateien sind direkt im Repo versioniert: `olist_manifest.yaml`, `open_food_facts_products_sample.json`, `retailrocket_events.jsonl`
- kein zusätzlicher `dvc pull` ist für lokale Entwicklung oder CI notwendig
- die Dateien sind bewusst klein gehalten, damit Fallbacks und Replay-Pfade nach einem frischen Clone sofort funktionieren

### Bruin Pipeline

- **Bruin** Asset-Definitionen in `pipeline/` mit deklarativen Column-Checks
- 5 Pipeline-Assets: `ingest_olist`, `ingest_streaming`, `ingest_enrichments`, `transform_dbt`, `quality_checks`
- DAG-Abhängigkeiten zwischen Assets (z.B. `transform_dbt` hängt von allen Ingestion-Assets ab)
- `.bruin.yml` Projektkonfiguration mit PostgreSQL-Verbindung

### Spark

- Clickstream-Sessionisierung mit PySpark
- Schema-Validation, 30-Min-Gap, Window-Functions
- Parquet-Output nach `storage/gold/retailrocket_sessions`

### Engineering-Workflow

- 32 pytest-Tests (Unit + Integration)
- 5 GitHub-Actions-Workflows (lint, tests, dbt-checks, integration, deploy-gcp)
- pre-commit-Konfiguration
- Docker-Build-Smoke-Test in der Integrationspipeline
- Modulare Repository-Struktur

### Frontend und Deployment

- Streamlit-Dashboard mit 8 Seiten: Commerce KPIs, Zeitliche Trends, Kategorien & Regionen, Produkt-Analyse, Session-Analyse, Wetter & FX, Datenquellen, Pipeline-Status
- Sidebar-Filter (Zeitraum, Status, Kategorie, Bundesstaat, Zahlungsart) wirken seitenübergreifend
- Testbare Dashboard-Logik unter `src/omnichannel_platform/dashboard/logic.py` mit eigenen Unit-Tests
- Multi-Stage-Dockerfile (Python 3.11-slim) für Pipeline- und Dashboard-Image
- Docker-Compose mit 10 Services inkl. `platform-runner` (Idle-Container für Pipeline-Ausführung), API und Dashboard
- `.dockerignore` für schlanken Build-Context

### Cloud und IaC

- Terraform provisioniert automatisch benötigte GCP APIs (Artifact Registry, BigQuery, Cloud Build, Cloud Run, Storage)
- Artifact Registry Repository für Container-Images
- 2 Cloud Run Services (API + Dashboard) mit konfigurierbaren Env-Vars, Scaling und IAM
- `deploy-gcp.yml` Workflow: API zuerst, dann Dashboard mit `API_BASE_URL` auf API-Service-URL
- `.env.example` mit allen konfigurierbaren Umgebungsvariablen (Datenbanken, APIs, Cloud, Dashboard)
- `terraform.tfvars.example` als Vorlage für GCP-Konfiguration

---

## Warehouse- und dbt-Modellierung

### Raw-Schicht

Die Rohdatenschicht bildet die operative Landefläche für normalisierte Tabellen:

| Tabelle | Quelle | Erwartete Zeilen (Seed) |
|---|---|---|
| `raw.olist_orders` | Olist Seed | ~500 |
| `raw.olist_order_items` | Olist Seed | ~1200 |
| `raw.olist_customers` | Olist Seed | ~250 |
| `raw.olist_products` | Olist Seed | ~150 |
| `raw.olist_order_payments` | Olist Seed | ~500 |
| `raw.retailrocket_events` | Replay | 3 (Sample) |
| `raw.open_food_facts_products` | API | 3-4 |
| `raw.open_meteo_weather` | API | ~1095 |
| `raw.frankfurter_fx_rates` | API | ~520 |

### Staging-Schicht

Die Staging-Modelle harmonisieren Datentypen, Benennungen und Basisnormalisierung.
Jedes Modell nutzt `raw_relation_exists()` für source-aware Fallbacks.

### Intermediate-Schicht

- [int_orders_with_context.sql](warehouse/dbt/models/intermediate/int_orders_with_context.sql):
  Verbindet Orders mit Customers (Stadt, Bundesstaat), Items (Artikelanzahl, Warenwert),
  Payments (BRL-Betrag, Zahlungsart), Weather (Temperatur, Niederschlag am Kauftag+Stadt),
  FX (BRL->USD Cross-Rate über EUR)

- [int_retailrocket_sessions.sql](warehouse/dbt/models/intermediate/int_retailrocket_sessions.sql):
  Sessionisierung mit 30-Min-Inaktivitätslücke, Window-Functions (LAG, SUM), Event-Type-Counts

### Mart-Schicht

- [fct_commerce_orders.sql](warehouse/dbt/models/marts/fct_commerce_orders.sql):
  Order-Grain mit BRL und USD-Beträgen, Kundengeografie, Produktkategorie, Wetterkontext
- [fct_retailrocket_sessions.sql](warehouse/dbt/models/marts/fct_retailrocket_sessions.sql):
  Session-Grain mit view/addtocart/transaction-Counts
- [dim_products.sql](warehouse/dbt/models/marts/dim_products.sql):
  Olist-Produkte + Open-Food-Facts-Produkte über `product_key` + `source_system` getrennt

---

## Datenqualität

### Verträge

| Datei | Scope |
|---|---|
| [raw_olist_orders.yml](quality/contracts/raw_olist_orders.yml) | order_id not null, status domain, timestamp present |
| [raw_retailrocket_events.yml](quality/contracts/raw_retailrocket_events.yml) | event_id not null, visitor_id not null, event_type domain |
| [marts_commerce.yml](quality/contracts/marts_commerce.yml) | order_id unique, customer_id present |
| [reference_enrichments.yml](quality/contracts/reference_enrichments.yml) | product_code not null, fx_rate positive, weather_date present |

### SQL-Expectations

| Datei | Prüft |
|---|---|
| `assert_positive_fx_rates.sql` | Alle FX-Raten > 0 |
| `assert_valid_olist_order_statuses.sql` | Nur bekannte Order-Statuses |
| `assert_valid_retailrocket_event_types.sql` | Nur view/addtocart/transaction |
| `reference_open_food_facts_products_not_null.sql` | product_code und product_name nicht leer |

### Great Expectations (GX)

Zusätzlich zu den SQL-Expectations validiert Great Expectations 5 Tabellen programmatisch:

| Tabelle | Expectations |
|---|---|
| `raw.olist_orders` | not_null(order_id), unique(order_id), not_null(timestamp), accepted_values(status) |
| `raw.retailrocket_events` | not_null(event_id), not_null(visitor_id), accepted_values(event_type), row_count > 0 |
| `raw.frankfurter_fx_rates` | not_null(rate_date), not_null(fx_rate), row_count > 0 |
| `raw.open_meteo_weather` | not_null(weather_date), not_null(city), row_count > 0 |
| `marts.fct_commerce_orders` | not_null(order_id), unique(order_id), not_null(customer_id), not_null(payment_value_brl), row_count > 0 |

```bash
make run-gx                   # GX-Validierung ausführen
make run-quality-all          # Beide Runner (SQL + GX)
```

**Hinweis:** Great Expectations erfordert Python <3.14. In CI (Python 3.11) und Docker funktioniert es.
Bei lokaler Python 3.14 wird GX automatisch übersprungen.

### Report-Ausgabe

```bash
# Custom SQL-Expectations:
cat storage/checkpoints/quality/last_run.json

# Great Expectations:
cat storage/checkpoints/great_expectations/last_run.json
```

---

## Orchestrierung mit Kestra

Der Kestra-Flow [daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml) orchestriert
den kompletten täglichen Pipeline-Durchlauf als eine Abfolge von Shell-Tasks:

| Schritt | Task-ID | Befehl | Beschreibung |
|---|---|---|---|
| 1 | `start_log` | (Log) | Startnachricht mit Flow-ID und Environment |
| 2 | `batch_ingestion` | `python -m omnichannel_platform.batch.commerce_batch_ingestion --env <env>` | Alle 4 Batch-Quellen (Olist + APIs) |
| 3 | `retailrocket_replay` | `python -m omnichannel_platform.streaming.clickstream_consumer --env <env> --mode <mode>` | Streaming-Replay |
| 4 | `warehouse_layers` | `python -m omnichannel_platform.warehouse.layer_catalog --env <env>` | Layer-Planung |
| 5 | `dbt_build` | `dbt build --project-dir warehouse/dbt --profiles-dir .dbt` | dbt-Build gegen DuckDB-CI-Profil |
| 6 | `run_quality` | `python -m omnichannel_platform.quality.rules_catalog --non-strict` | Quality-Checks (non-strict) |
| 7 | `finish_log` | (Log) | Abschlussnachricht |

**Parametrisierte Inputs:**

| Input | Typ | Default | Beschreibung |
|---|---|---|---|
| `environment` | STRING | `dev` | Konfigurationsumgebung (steuert welche YAML-Config geladen wird) |
| `streaming_mode` | STRING | `replay` | Replay oder Continuous-Modus für den Streaming-Schritt |

**Schedule:** Daily um 06:00 UTC (`0 6 * * *`)

**Zugang:** `http://localhost:8080` nach `docker compose up -d`. Die Kestra-UI zeigt den Flow unter
dem Namespace `omnichannel.platform.dev`. Von dort kann der Flow manuell getriggert, die Inputs
überschrieben und die Ausführungshistorie eingesehen werden.

**Hinweis:** Die Tasks laufen aktuell noch shellbasiert. Für Produktionsbetrieb müssten sie in einem
dedizierten Runtime-Image mit allen Python- und dbt-Abhängigkeiten laufen.

---

## Spark-Pfad

**Skript:** [clickstream_sessionization.py](spark/jobs/clickstream_sessionization.py)

**Starten:**

```bash
# Per Makefile
make spark-sessionize

# Oder direkt per spark-submit mit benutzerdefinierten Parametern
spark-submit spark/jobs/clickstream_sessionization.py \
  --input-path data/sample/streaming/retailrocket_events.jsonl \
  --output-path storage/gold/retailrocket_sessions \
  --gap-minutes 30
```

**Voraussetzung:** PySpark muss installiert sein (`pip install -e ".[spark]"`) und eine JVM-Runtime
(Java 11+) muss verfügbar sein.

**CLI-Argumente:**

| Flag | Default | Bedeutung |
|---|---|---|
| `--input-path` | (Pflicht) | Pfad zur JSONL-Datei mit Retailrocket-Events |
| `--output-path` | (Pflicht) | Zielverzeichnis für Parquet-Output |
| `--gap-minutes` | `30` | Inaktivitätslücke in Minuten für die Sessionisierung |

**Interner Ablauf:**

1. Liest Events aus der JSONL-Datei und validiert das Schema (event_id, visitor_id, event_type, item_id, event_ts).
2. Normalisiert Timestamps in UTC und Event-Types in Lowercase.
3. Partitioniert nach `visitor_id` und sortiert nach `event_ts`.
4. Berechnet die Zeitdifferenz zum vorherigen Event per `LAG`-Window-Function.
5. Setzt eine neue Session-Grenze, wenn die Lücke > `gap-minutes` beträgt.
6. Bildet Session-IDs als kumulative Summe der Grenzen per `SUM`-Window-Function.
7. Aggregiert pro Session: `event_count`, `view_count`, `addtocart_count`, `transaction_count`, `sample_item_id`.
8. Schreibt das Ergebnis als Parquet nach `output-path`.

**Erwartete Spalten im Parquet-Output:**

```
session_key, visitor_id, session_start_ts, session_end_ts,
event_count, view_count, addtocart_count, transaction_count, sample_item_id
```

**Verifizierung:**

```bash
ls storage/gold/retailrocket_sessions/
python -c "
import pandas as pd
df = pd.read_parquet('storage/gold/retailrocket_sessions')
print(df)
print(f'Sessions: {len(df)}')
"
```

---

## API-Schicht (FastAPI)

**Einstiegspunkt:** [src/omnichannel_platform/api/main.py](src/omnichannel_platform/api/main.py)
**Router:** [src/omnichannel_platform/api/routes/](src/omnichannel_platform/api/routes/)
**Tests:** [tests/unit/test_api_routes.py](tests/unit/test_api_routes.py)

Die API entkoppelt Datenzugriff und Frontend. Statt dass das Dashboard SQL direkt gegen PostgreSQL
ausführt, kann es über REST-Endpunkte auf dieselben Daten zugreifen. Dadurch werden Swagger-Doku,
weitere Clients und später Cloud-Deployments deutlich einfacher.

**Starten:**

```bash
# Lokal direkt
make run-api

# Oder als Compose-Service
docker compose up -d api
```

Danach ist die API unter `http://localhost:8000` erreichbar.

**Wichtige Endpunkte:**

| Endpoint | Zweck |
|---|---|
| `/` | Root-Metadaten und Links |
| `/docs` | Swagger / OpenAPI UI |
| `/api/v1/health` | Healthcheck inkl. DB-Erreichbarkeit |
| `/api/v1/orders` | Gefilterte Commerce-Orders |
| `/api/v1/orders/kpis` | Aggregierte KPI-Antwort |
| `/api/v1/sessions` | Session-Daten aus dem Mart |
| `/api/v1/sessions/funnel` | Views -> Cart -> Transaction Funnel |
| `/api/v1/products` | Produktdimension |
| `/api/v1/weather` | Wetterdaten |
| `/api/v1/fx-rates` | FX-Raten |
| `/api/v1/pipeline/status` | Audit + Tabellenstatistiken |

**Verifizierung:**

```bash
curl http://localhost:8000/
curl http://localhost:8000/api/v1/health
curl "http://localhost:8000/api/v1/orders?limit=5"
curl "http://localhost:8000/api/v1/orders/kpis"
curl "http://localhost:8000/api/v1/sessions?limit=5"
curl "http://localhost:8000/api/v1/sessions/funnel"
curl "http://localhost:8000/api/v1/pipeline/status"
```

**Relevante Tests für diesen Abschnitt:**

- `tests/unit/test_api_routes.py`
- `tests/unit/test_clients.py`

---

## Dashboard und Frontend

**Skript:** [dashboard/app.py](dashboard/app.py) (Streamlit-Einstiegspunkt)
**Logik:** [src/omnichannel_platform/dashboard/logic.py](src/omnichannel_platform/dashboard/logic.py) (testbare Filterung, Insights, DB-URL)
**Tests:** [tests/unit/test_dashboard_logic.py](tests/unit/test_dashboard_logic.py) (2 Unit-Tests für Filterlogik und Tabellenstatistiken)

**Starten:**

```bash
# Option A: direkt lokal im API-Modus
API_BASE_URL=http://localhost:8000 make run-dashboard

# Option B: direkt lokal im DB-Modus
make run-dashboard
# Entspricht: streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

# Option C: als Docker-Container (mit dem Rest des Stacks)
docker compose up -d dashboard

# Option D: nur Dashboard-Container isoliert starten
docker build --target dashboard -t omnichannel-dashboard:local .
docker run -p 8501:8080 \
  -e API_BASE_URL=http://host.docker.internal:8000 \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=commerce_platform \
  -e POSTGRES_USER=commerce \
  -e POSTGRES_PASSWORD=commerce \
  omnichannel-dashboard:local
```

**Voraussetzungen:**
- PostgreSQL muss laufen und die Warehouse-Tabellen müssen existieren (d.h. mindestens `make run-batch` + `dbt build` müssen vorher gelaufen sein)
- Wenn noch keine Daten vorhanden sind, zeigt das Dashboard eine Warnung mit den notwendigen Schritten

**Architektur des Dashboards:**

Die Streamlit-App (`dashboard/app.py`) unterstützt zwei Datenmodi:

- **API-Modus:** Wenn `API_BASE_URL` gesetzt ist, lädt das Dashboard Daten über die FastAPI-Schicht
- **DB-Modus:** Ohne `API_BASE_URL` liest das Dashboard direkt per SQLAlchemy aus PostgreSQL

Im Docker-Compose-Setup arbeitet das Dashboard standardmäßig im API-Modus gegen `http://api:8000`.

Die Daten werden für 5 Minuten gecached (`@st.cache_data(ttl=300)`). Die Geschäftslogik (Filterung,
Insight-Ableitung, Tabellenstatistiken) liegt in `src/omnichannel_platform/dashboard/logic.py` --
dadurch ist sie unabhängig von Streamlit testbar.

Die Datenbankverbindung wird über Umgebungsvariablen konfiguriert und als SQLAlchemy-Engine
per `@st.cache_resource` einmalig initialisiert.

Das Frontend unter [dashboard/app.py](dashboard/app.py) visualisiert die Pipeline sowohl fachlich
als auch technisch.

**Filter (Sidebar):**

Alle Filter wirken gleichzeitig und seitenübergreifend. Die aktuelle Trefferanzahl wird in
Echtzeit in der Sidebar angezeigt.

| Filter | Typ | Beschreibung |
|---|---|---|
| Zeitraum | Datumsbereich | Start- und Enddatum (min/max aus Bestelldaten) |
| Bestellstatus | Multiselect | z.B. delivered, shipped, processing, invoiced, approved |
| Produktkategorie | Multiselect | z.B. electronics, bed_bath_table, watches_gifts |
| Bundesstaat | Multiselect | z.B. SP, RJ, MG (brasilianische Bundesstaaten) |
| Zahlungsart | Multiselect | credit_card, boleto, voucher, debit_card |

**Deployment-Pfade:**

| Pfad | Befehl | URL |
|---|---|---|
| Lokal (Python, API-Modus) | `API_BASE_URL=http://localhost:8000 make run-dashboard` | `http://localhost:8501` |
| Lokal (Python, DB-Modus) | `make run-dashboard` | `http://localhost:8501` |
| Docker Compose | `docker compose up -d dashboard` | `http://localhost:8501` |
| GCP Cloud Run | `deploy-gcp.yml` Workflow (API + Dashboard) | Cloud-Run-URL (Workflow-Output) |

Dashboard-Seiten im Detail:

| Seite | Inhalt |
|---|---|
| Commerce KPIs | 8 Metriken (Bestellungen, Umsatz BRL/USD, Durchschnittsbestellwert, Artikel, Kunden, Fracht, Lieferquote), Insight-Kacheln, Pie-Chart (Status), Bar-Chart (Zahlungsart) |
| Zeitliche Trends | Bestellvolumen und Umsatzentwicklung nach Tag/Woche/Monat, gestapelter Kategorien-Umsatz |
| Kategorien & Regionen | Top-10 Kategorien nach Umsatz, Top-10 Bundesstaaten, Heatmap (Kategorie x Bundesstaat) |
| Produkt-Analyse | Produkte nach Quelle (Olist vs. Open Food Facts), Top-15 Kategorien, Ecoscore-Verteilung |
| Session-Analyse | Session-KPIs (Visitors, Events/Session, Conversion Rate), Event-Funnel, Histogramm der Event-Verteilung |
| Wetter & FX | Temperaturverlauf, Niederschlag, EUR/USD- und EUR/BRL-Kurse, Scatter (Temperatur vs. Bestellwert) |
| Datenquellen | Quellen-Übersicht (5 Quellen mit Typ/Tabellen/Zeilen), letzte Ingestion pro Quelle, Datenfluss-Diagramm |
| Pipeline-Status | Ingestion-Audit-Tabelle, Zeilen-/Spalten-Statistiken pro Warehouse-Tabelle, Technologie-Stack |

Die Sidebar erlaubt kombinierte Filterung nach Zeitraum, Bestellstatus, Produktkategorie, Bundesstaat und Zahlungsart.
Alle Filter wirken gleichzeitig -- die gefilterte Trefferanzahl wird in Echtzeit angezeigt.

**Verifizierung:**

```bash
curl -f http://localhost:8501/_stcore/health
```

Manuell im Browser prüfen:

- `Commerce KPIs`: KPI-Kacheln, Status-Pie, Zahlungsarten-Bar-Chart
- `Zeitliche Trends`: Tages-/Wochen-/Monatsaggregation
- `Session-Analyse`: Funnel und Histogramm
- `Pipeline-Status`: Audit-Tabelle und Tabellenstatistiken

**Relevante Tests für diesen Abschnitt:**

- `tests/unit/test_dashboard_logic.py`
- `tests/unit/test_dashboard_insights.py`

---

## GCP- und Terraform-Fundament

[infra/terraform/gcp](infra/terraform/gcp):

- Google-Provider `5.6.0` mit Credentials-File
- Automatische API-Aktivierung (Artifact Registry, BigQuery, Cloud Build, Cloud Run, Storage)
- Service-Konto mit BigQuery-Admin, Storage-Admin und Artifact-Registry-Reader
- 2 GCS-Buckets (Raw, Processed) mit Versioning und 30-Tage-Lifecycle
- 3 BigQuery-Datasets: `commerce_raw`, `commerce_staging`, `commerce_marts`
- 1 Artifact Registry Repository für Container-Images
- 2 Cloud Run Services: API (FastAPI) + Dashboard (Streamlit), deployed via `deploy-gcp.yml` Workflow
- Location: `US` (kompatibel mit Public Datasets)

### GCP Cloud-Deployment Schritt für Schritt

```bash
# 1. Voraussetzungen: gcloud CLI installiert, GCP-Projekt erstellt, Service Account JSON vorhanden

# 2. terraform.tfvars anlegen
cd infra/terraform/gcp
cp terraform.tfvars.example terraform.tfvars
# In terraform.tfvars anpassen:
#   credentials           = "~/.gcp/my-creds.json"
#   project_id            = "your-gcp-project-id"
#   region                = "us-central1"
#   raw_bucket_name       = "your-project-raw-data"
#   processed_bucket_name = "your-project-processed-data"
cd ../../..

# 3. Terraform initialisieren und Infrastruktur provisionieren (ohne Dashboard-Image)
make terraform-init-gcp
make terraform-plan-gcp
make terraform-apply-gcp

# 4. Docker für Artifact Registry authentifizieren
gcloud auth configure-docker us-central1-docker.pkg.dev

# 5. Dashboard-Image bauen und pushen + Cloud Run deployen
make deploy-dashboard-gcp \
  GCP_PROJECT_ID=your-gcp-project-id \
  GCP_REGION=us-central1

# 6. Cloud-Run-URL abrufen
terraform -chdir=infra/terraform/gcp output dashboard_service_url
```

Das Cloud-Run-Dashboard benötigt eine erreichbare PostgreSQL-Instanz (z.B. Cloud SQL).
Die Verbindungsparameter werden über `dashboard_env_vars` in `terraform.tfvars` konfiguriert.

### Terraform-Dry-Run lokal prüfen

```bash
cd infra/terraform/gcp
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform validate
terraform plan
cd ../../..
```

**Erwartete Ressourcen im Plan:**

- 1 Service Account
- 2 GCS Buckets (Raw + Processed)
- 3 BigQuery Datasets (`commerce_raw`, `commerce_staging`, `commerce_marts`)
- 1 Artifact Registry Repository
- 2 Cloud Run Services (API + Dashboard)

---

## CI/CD-Pipeline

### Workflows

| Workflow | Trigger | Prüft |
|---|---|---|
| [lint.yml](.github/workflows/lint.yml) | push main + PRs | `pre-commit run --all-files` |
| [tests.yml](.github/workflows/tests.yml) | push main + PRs | `pytest` (inkl. API-Tests) |
| [dbt-checks.yml](.github/workflows/dbt-checks.yml) | push main + PRs | `dbt parse` + `dbt build` (DuckDB CI-Profil) |
| [integration.yml](.github/workflows/integration.yml) | push main + PRs | PostgreSQL-Service, Batch/Streaming/Quality/dbt-End-to-End und Docker-Builds |
| [deploy-gcp.yml](.github/workflows/deploy-gcp.yml) | workflow_dispatch (manuell) | API + Dashboard Images bauen, nach Artifact Registry pushen und auf Cloud Run deployen |

Alle Workflows nutzen Python 3.11 und laufen auf `ubuntu-latest`.

#### lint.yml

Führt `pre-commit run --all-files` aus. Das umfasst alle konfigurierten Hooks wie
`ruff check`, Trailing-Whitespace-Bereinigung und YAML-Syntax-Prüfung. Dieser Workflow
schlägt fehl, wenn Codeformatierungs- oder Linting-Regeln verletzt werden.

#### tests.yml

Installiert die `dev`-, `batch`-, `dashboard`- und `api`-Extras und führt `pytest` aus.
(12 Unit-Testdateien + 2 Integrations-Testdateien). Kein PostgreSQL nötig -- alle Tests
laufen rein lokal gegen Fixtures und YAML-Konfiguration.

#### dbt-checks.yml

Baut das dbt-Projekt gegen ein temporäres DuckDB-Backend. Führt zuerst `dbt parse` aus
(prüft ob alle Modelle syntaktisch korrekt sind), dann `dbt build` (kompiliert, materialisiert
und testet alle Modelle). Nutzt das CI-Profil aus `warehouse/dbt/profiles.ci.yml`.

#### integration.yml

Der umfangreichste Workflow. Startet einen PostgreSQL-18-Service-Container und durchläuft
den kompletten Pipeline-Pfad:

1. Schema-Initialisierung (SQL-DDL aus `sql/postgres/init/`)
2. Lint (`ruff check .`)
3. pytest (inkl. API-Tests)
4. Batch-Ingestion (`--source olist` -- nur Olist Seeds, keine API-Aufrufe in CI)
5. Verifizierung: `raw.ingestion_audit` enthält Olist-Eintrag
6. Streaming-Replay (`--mode replay`)
7. Verifizierung: `raw.retailrocket_events` hat Daten
8. Quality-Checks (`--non-strict`)
9. dbt-Build gegen echtes PostgreSQL (mit temporärem Profil)
10. Verifizierung: `marts.fct_commerce_orders` hat Daten
11. Docker-Image-Builds (Pipeline + API + Dashboard) als Smoke-Test

#### deploy-gcp.yml

Manuell auslösbar über `workflow_dispatch` mit Umgebungswahl (`dev` / `prod`). Baut sowohl das
API-Image als auch das Dashboard-Image, pusht beide in die Artifact Registry und deployed sie
auf zwei separate Cloud Run Services. Die API wird zuerst deployed, danach das Dashboard mit
`API_BASE_URL` auf die API-Service-URL gesetzt (API-Modus). Benötigt folgende GitHub-Secrets:
`GCP_PROJECT_ID`, `GCP_REGION`, `GCP_SA_KEY`, `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
Beide Images werden mit dem Commit-SHA und `latest` getaggt.

### Lokale CI-Simulation

```bash
# Lint (entspricht lint.yml)
make lint

# Tests (entspricht tests.yml)
make test

# dbt CI-Build (entspricht dbt-checks.yml)
make dbt-build-ci

# Für eine volle Integration wie integration.yml:
# -> Docker-Stack + make run-batch + make run-streaming + dbt build + make run-quality
```

---

## Validierung und Entwicklung

### Lokaler Prüfpfad

```bash
ruff check .
pytest
make run-warehouse
make run-quality
```

### Bereits erfolgreich geprüft

- `ruff check .` -- sauber
- `pytest` -- 32/32 grün
- `make run-warehouse` inklusive `dbt build` -- sauber
- `make run-quality` mit sauberem Skip-Verhalten ohne erreichbares PostgreSQL
- kleine Sample-Dateien direkt im Repo versioniert und in CI verfügbar

---

## Kleine Sample-Daten im Repo

Die lokalen Seed- und Replay-Samples sind bewusst direkt im Git-Repo versioniert. Dadurch funktionieren
CI, lokale Fallbacks und Demo-Läufe ohne zusätzliche Daten-Downloads.

**Direkt versionierte Dateien:**

| Datei | Zweck |
|---|---|
| `data/sample/batch/olist_manifest.yaml` | Olist-Tabellenzuordnung für Seed-Generierung |
| `data/sample/batch/open_food_facts_products_sample.json` | Fallback-Produktdaten bei API-Störung |
| `data/sample/streaming/retailrocket_events.jsonl` | 3 Sample-Events für Streaming-Replay |

Die vorhandene `.dvc/`-Konfiguration kann später für größere Artefakte oder Landing-Zonen erweitert werden,
ist für die aktuellen Beispiel-Files aber nicht erforderlich.

---

## Bruin Pipeline-Definitionen

[Bruin](https://bruin-data.github.io/bruin/) definiert Pipeline-Assets deklarativ mit DAG-Abhängigkeiten
und Column-Level-Checks in `pipeline/`:

| Asset | Abhängigkeiten | Beschreibung |
|---|---|---|
| `ingest_olist.py` | `raw.schema_init` | Olist Seed-Daten laden (order_id unique, status domain) |
| `ingest_streaming.py` | `raw.schema_init` | Retailrocket Replay (event_id, visitor_id, event_type checks) |
| `ingest_enrichments.py` | `raw.schema_init` | API-Enrichments (FX positive, weather_date not_null) |
| `transform_dbt.py` | Alle Ingestion-Assets | dbt-Build: raw -> staging -> marts |
| `quality_checks.py` | `marts.fct_commerce_orders` | SQL-Expectations + Great Expectations |

**Konfiguration:** `.bruin.yml` im Projektroot mit PostgreSQL-Verbindung.

---

## Aktuelle Grenzen

- Olist nutzt lokal generierte Seed-Daten, solange keine echten CSV-Snapshots bereitliegen
- Retailrocket ist aktuell Replay-basiert und nicht an einen Live-Collector angebunden
- Open Food Facts nutzt bei temporären API-Störungen einen lokalen Fallback
- MongoDB wird als Raw-Store vorbereitet, aber noch nicht mit langfristiger Retention-Strategie
- BigQuery ist architektonisch vorbereitet, aber nicht komplett durchdeployt
- Kestra startet reale Entry-Points, aber noch ohne dediziertes Runtime-Image
- Cloud Run deployed API + Dashboard via GitHub Actions, aber noch ohne produktive Secret-Injektion (GCP Secret Manager)

---

## Nächste sinnvolle Ausbaustufen

- echte Olist-Rohdaten per Kaggle-Downloadpfad anstelle lokaler Seeds einbinden
- vollständige Retailrocket-Dateien automatisiert laden und replayen
- Replay zu einem dauerhaften Consumer-/Streaming-Job weiterentwickeln
- inkrementelle dbt-Strategien ergänzen
- Source Freshness und Exposures in dbt aufbauen
- Datenqualitätsprüfungen in Orchestrierungs-Alerts integrieren
- Dashboard für Cloud mit BigQuery oder Cloud-SQL-Verbindung finalisieren
- BigQuery-Zielpfad mit echten GCP-Credentials und Remote State produktionsnäher machen
- BigQuery-spezifische Starter-Modelle für `ga4_obfuscated_sample_ecommerce` und `thelook_ecommerce` ergänzen

---

## Kurzfazit

Dieses Projekt zeigt nicht nur einzelne Tools, sondern einen konsistenten Data-Engineering-Ansatz:

- **Echte Daten:** 4 reale Datenquellen (Olist, Open Food Facts API, Open-Meteo API, Frankfurter API) + Clickstream-Replay
- **Saubere Schichten:** Raw -> Staging (9 Views) -> Intermediate (2 Views) -> Marts (3 Tables)
- **Ausführbare Pipelines:** Jedes Skript ist per CLI aufrufbar, jede Ausgabe verifizierbar
- **Containerisiert:** Multi-Stage Dockerfile, 9 Docker-Compose-Services, Cloud-Run-ready
- **Getestet:** 27 pytest-Tests, 5 CI/CD-Workflows, 4 SQL-Quality-Expectations
- **Visualisiert:** Streamlit-Dashboard mit 8 Seiten, interaktiven Filtern und automatischen Insights
- **Cloud-ready:** Terraform für GCS, BigQuery, Artifact Registry und Cloud Run
- **Dokumentiert:** Ausführliche README mit CLI-Referenzen, erwarteten Ausgaben und Fehlerszenarien

Genau das soll ein gutes Portfolio-Projekt leisten.
