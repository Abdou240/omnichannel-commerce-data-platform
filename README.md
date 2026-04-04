# omnichannel-commerce-data-platform

Ein praxisnahes Portfolio-Projekt fuer Data Engineering rund um eine Omnichannel-Commerce-Plattform.

Dieses Repository modelliert einen realistischen End-to-End-Stack fuer Batch-, Streaming-,
Warehouse-, Qualitaets- und Orchestrierungs-Workloads. Der Fokus liegt bewusst auf einer sauberen,
erweiterbaren Plattformstruktur, auf ehrlichen Starter-Implementierungen und auf einer
repo-tauglichen Darstellung fuer Recruiter, Hiring Manager und technische Reviewer.

Das Projekt ist kein kuenstlich "fertig simulierter" Showcase. Stattdessen gibt es funktionierende
Starter-Pipelines, echte Ausfuehrungspfade, saubere TODO-Grenzen und eine klare Trennung zwischen
lokalem Entwicklungs-Setup und spaeterer Cloud-Zielarchitektur.

---

## Inhaltsverzeichnis

- [Projektziel](#projektziel)
- [Fachlicher Umfang](#fachlicher-umfang)
- [Datenquellen](#datenquellen)
- [Architektur auf einen Blick](#architektur-auf-einen-blick)
- [Datenfluss im Detail](#datenfluss-im-detail)
- [Technologiestack](#technologiestack)
- [Repository-Struktur](#repository-struktur)
- [Lokales Setup](#lokales-setup)
- [Schritt-fuer-Schritt Testanleitung](#schritt-fuer-schritt-testanleitung)
- [Zentrale Make-Targets](#zentrale-make-targets)
- [Was aktuell implementiert ist](#was-aktuell-implementiert-ist)
- [Warehouse- und dbt-Modellierung](#warehouse--und-dbt-modellierung)
- [Datenqualitaet](#datenqualitaet)
- [Orchestrierung mit Kestra](#orchestrierung-mit-kestra)
- [Spark-Pfad](#spark-pfad)
- [Dashboard und Frontend](#dashboard-und-frontend)
- [GCP- und Terraform-Fundament](#gcp--und-terraform-fundament)
- [CI/CD-Pipeline](#cicd-pipeline)
- [Validierung und Entwicklung](#validierung-und-entwicklung)
- [Aktuelle Grenzen](#aktuelle-grenzen)
- [Naechste sinnvolle Ausbaustufen](#naechste-sinnvolle-ausbaustufen)

---

## Projektziel

Die Plattform soll ein realistisches Omnichannel-Commerce-Szenario abbilden:

- relationale Commerce-Daten im Batch-Stil ingestieren
- Clickstream-Ereignisse ueber Kafka-kompatible Topics replayen
- externe Referenz- und Enrichment-Daten einbinden
- Rohdaten in ein lokales Warehouse ueberfuehren
- dbt-Modelle von `raw -> staging -> intermediate -> marts` aufbauen
- Datenqualitaetsregeln dokumentieren und ausfuehrbar machen
- eine klare Cloud-Zielarchitektur fuer BigQuery und GCP vorbereiten

Das Repository soll zeigen, dass nicht nur SQL oder Python beherrscht wird, sondern dass ein
Data-Engineering-Projekt als Plattform gedacht, strukturiert, dokumentiert und weiterentwickelt
werden kann.

## Fachlicher Umfang

Im Mittelpunkt steht eine Omnichannel-Commerce-Domaene mit mehreren fachlichen Perspektiven:

- Bestellungen und Bestellpositionen
- Produkte und Produktattribute
- Kunden- und Standortkontext
- Klick- und Session-Verhalten
- Wetterkontext fuer Nachfrage- oder Aktivitaetsmuster
- Waehrungsumrechnung fuer vergleichbare Kennzahlen

## Datenquellen

### Olist

Batch-orientierte relationale Commerce-Daten auf CSV-Basis:

- Orders, Order Items, Customers, Products, Payments

Im lokalen Setup werden deterministische Seed-Dateien erzeugt, wenn keine echten CSV-Snapshots
bereitgestellt wurden. Dadurch bleibt der Batch-Pfad lauffaehig, ohne einen "Fake-Production"-Eindruck
zu erzeugen.

Die Zielquelle ist das reale Kaggle-Dataset `olistbr/brazilian-ecommerce`. Fuer einen echten Download-
Pfad sind Kaggle-Credentials noetig; bis dahin bleibt die Seed-Strategie der lauffaehige Fallback.

### Retailrocket

Clickstream-/Event-Daten fuer Replay-Szenarien:

- `view`, `addtocart`, `transaction`

Die Events werden im Starter-Setup aus einer JSONL-Datei gelesen, normalisiert, auf Kafka-Topics
geroutet und zusaetzlich in der Raw-Schicht persistiert.

### Open Food Facts

Echte Produkt-API fuer JSON-basierte Produktstammdaten. Im aktuellen Starter ruft die Batch-Pipeline
konkrete Produkt-Barcodes ueber die Open Food Facts API ab. Das ist robuster als ein freier
Such-Endpoint und bildet trotzdem echte Live-Daten ab. Bei temporaerer API-Stoerung faellt die
Pipeline auf ein lokales Sample zurueck.

### Open-Meteo

Wetter-Enrichment auf Tagesebene fuer ausgewaehlte brasilianische Staedte (Sao Paulo, Rio de Janeiro,
Belo Horizonte).

### Frankfurter API

FX-Raten (EUR -> USD, EUR -> BRL) zur spaeten Umrechnung von Betraegen und zur Vergleichbarkeit
von Commerce-Metriken.

### MongoDB

Raw-Document-Store fuer JSON-Payloads und Replay-Artefakte.

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
|  Qualitaet:      SQL-Expectations + dbt-Tests + Quality-Runner      |
|  CI/CD:          GitHub Actions (lint, pytest, dbt build)           |
|  IaC:            Terraform (Google Provider 5.6.0)                  |
|  Frontend:       Streamlit + Plotly                                 |
|  Deployment:     Docker Compose + Cloud Run                         |
+---------------------------------------------------------------------+
```

Eine ergaenzende Architekturuebersicht liegt in [docs/architecture.md](docs/architecture.md).

---

## Datenfluss im Detail

### 1. Batch-Ingestion

Die Batch-Pipeline in [commerce_batch_ingestion.py](src/omnichannel_platform/batch/commerce_batch_ingestion.py) uebernimmt:

- Bereitstellung oder Erzeugung lokaler Olist-Seed-Dateien (500 Orders, 250 Customers, 150 Products)
- Laden aller 5 Olist-Tabellen in `raw.*`
- API-Abrufe fuer Open Food Facts (per Barcode), Open-Meteo (365 Tage, 3 Staedte) und Frankfurter (FX-Jahresraten)
- Schreiben von Bronze-Artefakten unter `storage/bronze/*/_runs/<batch_id>/`
- optionale Raw-Dokumentablage in MongoDB
- Audit-Eintraege in `raw.ingestion_audit`

### 2. Streaming-Replay

Die Streaming-Pipeline in [clickstream_consumer.py](src/omnichannel_platform/streaming/clickstream_consumer.py) uebernimmt:

- Lesen von Retailrocket-Events aus `data/sample/streaming/retailrocket_events.jsonl`
- Normalisierung der Event-Struktur (Lowercasing, String-Casting, Topic-Routing)
- Publizieren auf Kafka/Redpanda, sofern ein Broker erreichbar ist
- Persistenz in `raw.retailrocket_events` (PostgreSQL)
- optionales Ablegen der Replay-Dokumente in MongoDB
- Schreiben eines Replay-Checkpoints unter `storage/checkpoints/retailrocket/`

### 3. Transformation im Warehouse

Die dbt-Modelle bilden aktuell drei Schichten:

- **staging**: Normalisierung der Rohdaten mit source-aware Fallbacks (leere Relationen wenn Raw-Tabellen fehlen)
- **intermediate**: `int_orders_with_context` (Orders + Kunden + Items + Payments + Wetter + FX), `int_retailrocket_sessions` (30-Min-Gap-Sessionisierung)
- **marts**: `fct_commerce_orders`, `fct_retailrocket_sessions`, `dim_products` (Olist + Open Food Facts kombiniert)

### 4. Datenqualitaet

Die Datenqualitaetslogik kombiniert:

- deklarative Vertraege unter `quality/contracts/`
- SQL-Erwartungen unter `quality/expectations/`
- dbt-Tests auf Modell- und Spaltenebene
- einen Python-Runner in [rules_catalog.py](src/omnichannel_platform/quality/rules_catalog.py) mit Report-Ausgabe

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
| Frontend | Streamlit + Plotly | >=1.38 / >=5.24 |
| Container | Docker / Docker Compose | latest |
| Cloud App Runtime | Cloud Run | (Zielarchitektur) |
| Python | Python | >=3.11 |
| Build Tool | uv / pip | latest |
| Linting | ruff | >=0.6 |
| Testing | pytest | >=8.0 |
| CI/CD | GitHub Actions | 4 Workflows |

---

## Repository-Struktur

```text
.
├── .dockerignore                    # Schlanker Docker-Build-Context
├── .github/workflows/              # CI: lint, pytest, dbt-checks
├── dashboard/                       # Streamlit-Frontend
├── config/                          # Basis-, Dev- und Prod-Konfiguration
│   ├── base.yaml                    # Alle Quellen, Warehouse, Orchestrierung
│   ├── dev.yaml                     # Lokale Overrides (Kafka, Geo, etc.)
│   └── prod.yaml                    # Cloud-Platzhalter
├── data/sample/                     # Kleine lokale Beispiel- und Replay-Daten
│   ├── batch/                       # Olist-Manifest, Open Food Facts Sample
│   └── streaming/                   # Retailrocket JSONL (3 Events)
├── docs/                            # Architektur, ADRs, Runbooks
├── infra/terraform/gcp/             # GCP-Grundgeruest (Buckets, Datasets, IAM)
├── kafka/                           # Topic-Katalog und create_topics.sh
├── nosql/mongodb/                   # init.js fuer Collections und Indexes
├── orchestration/kestra/flows/      # Kestra-Flow (daily_platform_ingestion)
├── quality/
│   ├── contracts/                   # 4 YAML-Vertraege
│   └── expectations/                # SQL-Checks (fx_rates, order_statuses, etc.)
├── spark/jobs/                      # clickstream_sessionization.py
├── sql/postgres/init/               # Schema-Init + Raw-Tabellen-DDL
├── src/omnichannel_platform/
│   ├── batch/                       # commerce_batch_ingestion, source_plans, orders_ingestion
│   ├── common/                      # logging, settings, clients (Postgres/Mongo), io
│   ├── dashboard/                   # testbare Dashboard-Logik
│   ├── quality/                     # rules_catalog (SQL-Runner + Report)
│   ├── streaming/                   # clickstream_consumer (Replay + Kafka + Persist)
│   └── warehouse/                   # layer_catalog
├── tests/
│   ├── fixtures/                    # sample_orders.json, sample_clickstream_events.jsonl
│   ├── unit/                        # 5 Testdateien, 13 Tests
│   └── integration/                 # Repository-Foundation-Check
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
    └── seeds/                       # (bereit fuer Referenzdaten)
```

Wichtige Einstiegspunkte:

- [Dockerfile](Dockerfile)
- [docker-compose.yml](docker-compose.yml)
- [dashboard/app.py](dashboard/app.py)
- [orchestration/kestra/flows/daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml)
- [infra/terraform/gcp/main.tf](infra/terraform/gcp/main.tf)

---

## Lokales Setup

### 1. Python-Umgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
make install-local
```

`make install-local` installiert alle lokalen Extras: dev, batch, streaming, warehouse, nosql, quality, dashboard.

### 2. Umgebungsvariablen

```bash
cp .env.example .env
# Anpassen: POSTGRES_HOST, KAFKA_BOOTSTRAP_SERVERS, MONGO_URI, etc.
```

### 3. Plattform-Stack starten

```bash
docker compose up -d
```

Der Compose-Stack enthaelt: PostgreSQL 18, pgAdmin, Redpanda v25.3.9 + Console, MongoDB 7, MinIO, Kestra v1.1, einen `platform-runner`-Container und das Streamlit-Dashboard.

| Service | Port | Zweck |
|---|---|---|
| postgres | 5432 | Lokales Warehouse + Raw Landing |
| pgadmin | 8085 | Web-UI fuer PostgreSQL |
| redpanda | 9092 / 29092 | Kafka-kompatibler Broker |
| redpanda-console | 8484 | Web-UI fuer Topics und Consumer |
| mongo | 27017 | Raw-Document-Store |
| minio | 9000 / 9001 | Lokales Object Storage |
| kestra | 8080 | Orchestrierungs-UI |
| platform-runner | — | Idle-Container zum Ausfuehren von Pipeline-Befehlen per `docker compose exec` |
| dashboard | 8501 | Streamlit-Frontend |

Der `platform-runner` ist ein schlafender Container mit allen Pipeline-Abhaengigkeiten. Er erlaubt es, Pipeline-Schritte im Container-Kontext auszufuehren:

```bash
docker compose exec platform-runner python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev
docker compose exec platform-runner python -m omnichannel_platform.streaming.clickstream_consumer --env dev --mode replay
```

### 4. Kafka-Topics anlegen

```bash
make kafka-topics
```

### 5. Starter-Workflows ausfuehren

```bash
make run-batch          # Batch-Ingestion (Olist + APIs)
make run-streaming      # Retailrocket Replay
make run-warehouse      # dbt build (CI-Profil mit DuckDB)
make run-quality        # Quality-Checks
make run-dashboard      # Streamlit-Frontend lokal
```

---

## Schritt-fuer-Schritt Testanleitung

Dieser Abschnitt beschreibt, wie jede implementierte Komponente einzeln getestet werden kann.

### Voraussetzungen

```bash
# Python-Umgebung aufsetzen
python3 -m venv .venv
source .venv/bin/activate
make install-local

# Docker-Stack starten (PostgreSQL, Redpanda, MongoDB, MinIO, Kestra)
docker compose up -d

# Warten bis PostgreSQL bereit ist
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

### Test 1: Unit-Tests und Lint

```bash
# Lint-Pruefung -- muss ohne Fehler durchlaufen
make lint

# Unit-Tests -- alle Tests muessen gruen sein
make test

# Erwartete Ausgabe:
# tests/integration/test_repository_foundations.py    1 passed
# tests/unit/test_dashboard_logic.py                  2 passed
# tests/unit/test_ingestion_plans.py                 5 passed
# tests/unit/test_quality_assets.py                  1 passed
# tests/unit/test_sample_fixtures.py                 2 passed
# tests/unit/test_settings.py                        2 passed
# ============================== 13 passed ==============================
```

**Was wird getestet:**
- `test_settings.py`: YAML-Config-Loading, Deep-Merge, Environment-Override
- `test_ingestion_plans.py`: Batch-Source-Plans (Olist, Open Food Facts, Open-Meteo, Frankfurter), Streaming-Plan, Event-Routing, Event-Normalisierung
- `test_sample_fixtures.py`: Fixture-Struktur (Orders, Clickstream)
- `test_dashboard_logic.py`: Filterlogik und Tabellenstatistiken fuer das Frontend
- `test_quality_assets.py`: Quality-Asset-Discovery (Contracts + Expectations)
- `test_repository_foundations.py`: Prueft ob alle Schluesssel-Dateien existieren

### Test 2: Batch-Ingestion (Olist Seed + API-Enrichments)

```bash
# Nur Olist
make run-batch ENVIRONMENT=dev

# Oder einzelne Quelle
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source olist
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source open_food_facts
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source open_meteo
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source frankfurter
```

**Pruefung nach dem Lauf:**

```bash
# PostgreSQL: Pruefen ob Daten geladen wurden
docker compose exec postgres psql -U commerce -d commerce_platform -c "
  SELECT source_name, batch_id, row_count, loaded_at
  FROM raw.ingestion_audit
  ORDER BY loaded_at DESC;
"

# Erwartetes Ergebnis:
# source_name    | batch_id                    | row_count
# olist          | olist-20260403T...          | ~2400  (500 orders + 1200 items + 250 customers + 150 products + 500 payments)
# open_food_facts| open-food-facts-20260403T...| 3-4
# open_meteo     | weather-20260403T...        | ~1095  (365 Tage x 3 Staedte)
# frankfurter    | fx-20260403T...             | ~500   (260 Handelstage x 2 Waehrungen)

# Einzelne Raw-Tabellen pruefen
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT count(*) FROM raw.olist_orders;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT count(*) FROM raw.open_meteo_weather;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT * FROM raw.open_food_facts_products LIMIT 3;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT * FROM raw.frankfurter_fx_rates LIMIT 5;"

# Bronze-Artefakte pruefen
ls -la storage/bronze/olist/_runs/
ls -la storage/bronze/open_food_facts/products/_runs/
ls -la storage/bronze/open_meteo/weather/_runs/
ls -la storage/bronze/frankfurter/fx/_runs/
```

**Fehlerszenarien:**
- PostgreSQL nicht erreichbar: Pipeline scheitert (Postgres ist Pflicht)
- Open Food Facts API nicht erreichbar: Fallback auf `data/sample/batch/open_food_facts_products_sample.json`
- Open-Meteo / Frankfurter API nicht erreichbar: Pipeline loggt Warnung und ueberspringt

### Test 3: Streaming-Replay (Retailrocket)

```bash
make run-streaming
```

**Pruefung nach dem Lauf:**

```bash
# PostgreSQL: Retailrocket-Events pruefen
docker compose exec postgres psql -U commerce -d commerce_platform -c "
  SELECT event_type, count(*) FROM raw.retailrocket_events GROUP BY event_type;
"
# Erwartetes Ergebnis: view=1, addtocart=1, transaction=1

# Replay-Checkpoint pruefen
cat storage/checkpoints/retailrocket/last_replay.json

# Replay-Archiv pruefen
ls storage/checkpoints/retailrocket/replays/

# Kafka-Topics pruefen (wenn Redpanda laeuft)
docker compose exec redpanda rpk topic list
docker compose exec redpanda rpk topic consume retailrocket.events.raw --num 3
```

**Fehlerszenarien:**
- Redpanda nicht erreichbar: Replay laeuft trotzdem (Kafka-Publish wird uebersprungen)
- MongoDB nicht erreichbar: Replay laeuft trotzdem (Mongo-Persist wird uebersprungen)
- PostgreSQL nicht erreichbar: Pipeline-Schritt scheitert

### Test 4: dbt Transformation (DuckDB CI-Profil)

```bash
# Vollstaendiger dbt-Build mit DuckDB (kein PostgreSQL noetig)
make run-warehouse

# Oder einzeln
make dbt-build-ci
```

**Pruefung nach dem Lauf:**

```bash
# dbt-Target-Artefakte pruefen
ls warehouse/dbt/target/
cat warehouse/dbt/target/manifest.json | python -m json.tool | head -20

# DuckDB-Datei pruefen (falls vorhanden)
ls -la storage/warehouse/local.duckdb
```

**Was dbt baut:**
- 9 Staging-Views: `stg_olist_orders`, `stg_olist_order_items`, `stg_olist_customers`, `stg_olist_products`, `stg_olist_order_payments`, `stg_retailrocket_events`, `stg_open_food_facts_products`, `stg_open_meteo_weather`, `stg_frankfurter_fx_rates`
- 2 Intermediate-Views: `int_orders_with_context`, `int_retailrocket_sessions`
- 3 Mart-Tables: `fct_commerce_orders`, `fct_retailrocket_sessions`, `dim_products`
- 3 Singular-Tests: `assert_valid_olist_order_statuses`, `assert_valid_retailrocket_event_types`, `assert_positive_fx_rates`
- Spalten-Tests: not_null, unique auf Schluesselfeldern

**dbt mit PostgreSQL-Target (nach Batch-Ingestion):**

```bash
# dbt-Profil fuer lokales PostgreSQL kopieren
mkdir -p ~/.dbt
cp warehouse/dbt/profiles.yml.example ~/.dbt/profiles.yml

# dbt gegen echte Daten bauen
dbt build --project-dir warehouse/dbt --target dev

# Mart-Ergebnisse pruefen
docker compose exec postgres psql -U commerce -d commerce_platform -c "
  SELECT count(*) as orders, avg(payment_value_brl) as avg_payment
  FROM staging.fct_commerce_orders;
"
docker compose exec postgres psql -U commerce -d commerce_platform -c "
  SELECT * FROM staging.dim_products LIMIT 5;
"
```

### Test 5: Datenqualitaet

```bash
# Quality-Checks ausfuehren (mit PostgreSQL)
make run-quality

# Oder im Non-Strict-Modus (kein Exit-Code bei Fehlern)
python -m omnichannel_platform.quality.rules_catalog --non-strict
```

**Pruefung nach dem Lauf:**

```bash
# Quality-Report pruefen
cat storage/checkpoints/quality/last_run.json | python -m json.tool

# Erwartete Struktur:
# {
#   "contracts": [...],      # Liste der geladenen Vertraege
#   "results": [...],        # passed / failed / skipped pro Expectation
#   "summary": {
#     "passed": N,
#     "failed": 0,
#     "skipped": M
#   }
# }
```

**Wenn PostgreSQL nicht laeuft:** Alle SQL-Expectations werden sauber als `skipped` markiert.

### Test 6: Spark Sessionisierung

```bash
# Spark-Submit (PySpark muss installiert sein)
make spark-sessionize

# Oder direkt
spark-submit spark/jobs/clickstream_sessionization.py \
  --input-path data/sample/streaming/retailrocket_events.jsonl \
  --output-path storage/gold/retailrocket_sessions \
  --gap-minutes 30
```

**Pruefung nach dem Lauf:**

```bash
# Parquet-Output pruefen
ls storage/gold/retailrocket_sessions/

# Mit Python lesen
python -c "
import pandas as pd
df = pd.read_parquet('storage/gold/retailrocket_sessions')
print(df)
print(f'Sessions: {len(df)}')
print(f'Spalten: {list(df.columns)}')
"
# Erwartete Spalten: session_key, visitor_id, session_start_ts, session_end_ts,
#                    event_count, view_count, addtocart_count, transaction_count, sample_item_id
```

### Test 7: Kafka-Topics (Redpanda)

```bash
# Topics anlegen
make kafka-topics

# Topics pruefen
docker compose exec redpanda rpk topic list

# Erwartete Topics:
# retailrocket.events.raw          (3 Partitions)
# retailrocket.events.view         (6 Partitions)
# retailrocket.events.addtocart    (6 Partitions)
# retailrocket.events.transaction  (6 Partitions)
# retailrocket.events.dlq          (3 Partitions)
```

### Test 8: Terraform (Dry-Run)

```bash
cd infra/terraform/gcp

# Terraform-Konfiguration validieren (ohne echten Cloud-Zugang)
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform validate
terraform plan

# Zurueck ins Projektroot
cd ../../..
```

**Erwartete Ressourcen im Plan:**
- 1 Service Account
- 2 GCS Buckets (Raw + Processed) mit Lifecycle-Rules
- 3 BigQuery Datasets (raw, staging, marts)
- 1 Artifact Registry Repository
- 1 optionaler Cloud Run Service (wenn `dashboard_container_image` gesetzt ist)
- IAM Bindings fuer BigQuery, Storage und Artifact Registry

### Test 9: Dashboard lokal

```bash
# Voraussetzung: Daten muessen im Warehouse vorhanden sein (Batch + dbt vorher ausfuehren)

# Option A: direkt lokal (Python-Umgebung mit dashboard-Extras)
make run-dashboard

# Option B: als Docker-Container
docker compose up -d dashboard
```

Danach ist das Frontend unter `http://localhost:8501` erreichbar.

**Pruefung:**

```bash
# Healthcheck
curl -f http://localhost:8501/_stcore/health

# Im Browser oeffnen: http://localhost:8501
# Erwartete Seiten im Sidebar:
#   - Commerce KPIs (8 Metriken + Pie/Bar-Charts)
#   - Zeitliche Trends (Aggregation Tag/Woche/Monat)
#   - Kategorien & Regionen (Top-10 + Heatmap)
#   - Session-Analyse (Funnel + Histogramm)
#   - Wetter & FX (Zeitreihen + Scatter)
#   - Pipeline-Status (Audit-Tabelle + Tabellenstatistiken)
```

**Wenn keine Daten vorhanden sind:** Das Dashboard zeigt eine Warnung mit den notwendigen Schritten (`make run-batch`, `make run-streaming`, `make run-warehouse`).

### Test 10: Docker-Builds

```bash
# Pipeline-Image (lokal)
make docker-build-pipeline

# Dashboard-Image (mit Cloud-Tag)
make docker-build-dashboard GCP_PROJECT_ID=your-project-id GCP_REGION=us-central1

# Beide Images pruefen
docker images | grep omnichannel
```

### Test 11: Vollstaendiger End-to-End-Lauf

```bash
# 1. Stack starten
docker compose up -d

# 2. Warten bis alles bereit ist
docker compose exec postgres pg_isready -U commerce -d commerce_platform

# 3. Topics anlegen
make kafka-topics

# 4. Batch-Ingestion
make run-batch

# 5. Streaming-Replay
make run-streaming

# 6. dbt gegen PostgreSQL bauen
mkdir -p ~/.dbt && cp warehouse/dbt/profiles.yml.example ~/.dbt/profiles.yml
dbt build --project-dir warehouse/dbt --target dev

# 7. Quality-Checks
make run-quality

# 8. Ergebnisse pruefen
docker compose exec postgres psql -U commerce -d commerce_platform -c "
  SELECT 'raw.olist_orders' as table_name, count(*) FROM raw.olist_orders
  UNION ALL SELECT 'raw.olist_order_items', count(*) FROM raw.olist_order_items
  UNION ALL SELECT 'raw.olist_customers', count(*) FROM raw.olist_customers
  UNION ALL SELECT 'raw.olist_products', count(*) FROM raw.olist_products
  UNION ALL SELECT 'raw.olist_order_payments', count(*) FROM raw.olist_order_payments
  UNION ALL SELECT 'raw.retailrocket_events', count(*) FROM raw.retailrocket_events
  UNION ALL SELECT 'raw.open_food_facts_products', count(*) FROM raw.open_food_facts_products
  UNION ALL SELECT 'raw.open_meteo_weather', count(*) FROM raw.open_meteo_weather
  UNION ALL SELECT 'raw.frankfurter_fx_rates', count(*) FROM raw.frankfurter_fx_rates
  UNION ALL SELECT 'staging.fct_commerce_orders', count(*) FROM staging.fct_commerce_orders
  UNION ALL SELECT 'staging.fct_retailrocket_sessions', count(*) FROM staging.fct_retailrocket_sessions
  UNION ALL SELECT 'staging.dim_products', count(*) FROM staging.dim_products;
"

# 9. Dashboard pruefen
curl -I http://localhost:8501

# 10. Stack beenden
docker compose down
```

---

## Zentrale Make-Targets

| Target | Zweck |
|---|---|
| `make install-local` | Lokale Entwicklungs- und Laufzeitabhaengigkeiten installieren |
| `make up` | Docker-Compose-Stack starten |
| `make down` | Docker-Compose-Stack stoppen |
| `make logs` | Docker-Compose-Logs anzeigen |
| `make run-batch` | Batch-Ingestion fuer Olist und API-Enrichments ausfuehren |
| `make run-streaming` | Retailrocket-Replay ausfuehren |
| `make run-warehouse` | Warehouse-Layer planen + `dbt build` (DuckDB CI-Profil) |
| `make dbt-build-ci` | Nur `dbt build` gegen DuckDB-CI-Profil |
| `make run-quality` | SQL-basierte Quality-Checks starten |
| `make run-dashboard` | Streamlit-Dashboard lokal starten |
| `make kafka-topics` | Kafka-/Redpanda-Topics anlegen |
| `make spark-sessionize` | Spark-Sessionisierung fuer Retailrocket-Beispieldaten |
| `make docker-build-pipeline` | Pipeline-Container lokal bauen |
| `make docker-build-dashboard` | Dashboard-Container fuer lokalen oder Cloud-Tag bauen |
| `make terraform-init-gcp` | Terraform in `infra/terraform/gcp` initialisieren |
| `make terraform-plan-gcp` | Terraform-Plan inkl. Cloud-Run-Image-Variable ausfuehren |
| `make terraform-apply-gcp` | Terraform-Apply fuer GCP und Cloud Run ausfuehren |
| `make deploy-dashboard-gcp` | Dashboard-Image pushen und Cloud-Run-Deploy ueber Terraform anstossen |
| `make test` | pytest-Suite ausfuehren (13 Tests) |
| `make lint` | Ruff-Linting ausfuehren |
| `make pre-commit` | Pre-commit Hooks ausfuehren |

---

## Was aktuell implementiert ist

### Batch

- Olist-Seed-Generierung (deterministisch, 500 Orders, 250 Customers, 150 Products, 1200 Items, 500 Payments)
- Laden aller 5 Olist-Tabellen in `raw.*` mit TRUNCATE+APPEND
- Open-Food-Facts-Produktabruf per Barcode (4 konfigurierte Barcodes) mit lokalem Fallback
- Open-Meteo-Wetterabruf fuer 3 brasilianische Staedte (365 Tage)
- Frankfurter-FX-Abruf fuer EUR->USD/BRL (1 Jahr Handelstage)
- Bronze-Artefakte und Run-Manifeste pro Batch-Lauf
- PostgreSQL-Loads in `raw.*` mit Ingestion-Audit
- Optionale Mongo-Persistenz fuer alle API-Payloads

### Streaming

- Replay aus lokaler JSONL-Datei (3 Beispiel-Events)
- Event-Normalisierung (Lowercasing, String-Casting)
- Topic-Routing (`view` -> `retailrocket.events.view`, `addtocart` -> `retailrocket.events.addtocart`, `transaction` -> `retailrocket.events.transaction`, unbekannt -> DLQ)
- Kafka-Publish wenn Broker verfuegbar (graceful Skip wenn nicht)
- Persistenz nach PostgreSQL `raw.retailrocket_events`
- Optionale MongoDB-Persist
- Replay-Artefakte und Checkpoint-Dateien

### Warehouse (dbt)

- `raw_relation_exists` Macro fuer source-aware Fallbacks
- 9 Staging-Views (alle Quellen normalisiert)
- `int_orders_with_context`: Orders + Customers + Items + Payments + Wetter + FX-Cross-Rate (BRL->USD)
- `int_retailrocket_sessions`: 30-Min-Gap-Sessionisierung mit Window-Functions
- `fct_commerce_orders`: Order-Grain Fact mit `payment_value_usd`
- `fct_retailrocket_sessions`: Session-Grain Fact mit Event-Type-Counts
- `dim_products`: Olist + Open Food Facts kombiniert ueber `product_key` und `source_system`
- 3 Singular-Tests + Spalten-Tests (not_null, unique)

### Datenqualitaet

- 4 deklarative Qualitaetsvertraege (Olist, Retailrocket, Marts, Enrichments)
- SQL-Expectations (FX-Raten positiv, Order-Statuses gueltig, Event-Types gueltig, Produkt-Codes nicht null)
- Python-Runner mit PostgreSQL-Execution und JSON-Report
- Graceful Skip wenn PostgreSQL nicht erreichbar

### Spark

- Clickstream-Sessionisierung mit PySpark
- Schema-Validation, 30-Min-Gap, Window-Functions
- Parquet-Output nach `storage/gold/retailrocket_sessions`

### Engineering-Workflow

- 13 pytest-Tests (Unit + Integration)
- 4 GitHub-Actions-Workflows (lint, tests, dbt-checks, integration)
- pre-commit-Konfiguration
- Docker-Build-Smoke-Test in der Integrationspipeline
- Modulare Repository-Struktur

### Frontend und Deployment

- Streamlit-Dashboard mit 6 Seiten: Commerce KPIs, Zeitliche Trends, Kategorien & Regionen, Session-Analyse, Wetter & FX, Pipeline-Status
- Sidebar-Filter (Zeitraum, Status, Kategorie, Bundesstaat, Zahlungsart) wirken seitenuebergreifend
- Testbare Dashboard-Logik unter `src/omnichannel_platform/dashboard/logic.py` mit eigenen Unit-Tests
- Multi-Stage-Dockerfile (Python 3.11-slim) fuer Pipeline- und Dashboard-Image
- Docker-Compose mit 9 Services inkl. `platform-runner` (Idle-Container fuer Pipeline-Ausfuehrung) und Dashboard
- `.dockerignore` fuer schlanken Build-Context

### Cloud und IaC

- Terraform provisioniert automatisch benoetigte GCP APIs (Artifact Registry, BigQuery, Cloud Build, Cloud Run, Storage)
- Artifact Registry Repository fuer Container-Images
- Optionaler Cloud Run Service mit konfigurierbaren Env-Vars, Scaling und IAM (public/private)
- `make deploy-dashboard-gcp` als One-Command-Deploy: Image bauen, pushen, Terraform-Apply
- `.env.example` mit allen konfigurierbaren Umgebungsvariablen (Datenbanken, APIs, Cloud, Dashboard)
- `terraform.tfvars.example` als Vorlage fuer GCP-Konfiguration

---

## Warehouse- und dbt-Modellierung

### Raw-Schicht

Die Rohdatenschicht bildet die operative Landeflaeche fuer normalisierte Tabellen:

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
Jedes Modell nutzt `raw_relation_exists()` fuer source-aware Fallbacks.

### Intermediate-Schicht

- [int_orders_with_context.sql](warehouse/dbt/models/intermediate/int_orders_with_context.sql):
  Verbindet Orders mit Customers (Stadt, Bundesstaat), Items (Artikelanzahl, Warenwert),
  Payments (BRL-Betrag, Zahlungsart), Weather (Temperatur, Niederschlag am Kauftag+Stadt),
  FX (BRL->USD Cross-Rate ueber EUR)

- [int_retailrocket_sessions.sql](warehouse/dbt/models/intermediate/int_retailrocket_sessions.sql):
  Sessionisierung mit 30-Min-Inaktivitaetsluecke, Window-Functions (LAG, SUM), Event-Type-Counts

### Mart-Schicht

- [fct_commerce_orders.sql](warehouse/dbt/models/marts/fct_commerce_orders.sql):
  Order-Grain mit BRL und USD-Betraegen, Kundengeografie, Produktkategorie, Wetterkontext
- [fct_retailrocket_sessions.sql](warehouse/dbt/models/marts/fct_retailrocket_sessions.sql):
  Session-Grain mit view/addtocart/transaction-Counts
- [dim_products.sql](warehouse/dbt/models/marts/dim_products.sql):
  Olist-Produkte + Open-Food-Facts-Produkte ueber `product_key` + `source_system` getrennt

---

## Datenqualitaet

### Vertraege

| Datei | Scope |
|---|---|
| [raw_olist_orders.yml](quality/contracts/raw_olist_orders.yml) | order_id not null, status domain, timestamp present |
| [raw_retailrocket_events.yml](quality/contracts/raw_retailrocket_events.yml) | event_id not null, visitor_id not null, event_type domain |
| [marts_commerce.yml](quality/contracts/marts_commerce.yml) | order_id unique, customer_id present |
| [reference_enrichments.yml](quality/contracts/reference_enrichments.yml) | product_code not null, fx_rate positive, weather_date present |

### SQL-Expectations

| Datei | Prueft |
|---|---|
| `assert_positive_fx_rates.sql` | Alle FX-Raten > 0 |
| `assert_valid_olist_order_statuses.sql` | Nur bekannte Order-Statuses |
| `assert_valid_retailrocket_event_types.sql` | Nur view/addtocart/transaction |
| `reference_open_food_facts_products_not_null.sql` | product_code und product_name nicht leer |

### Report-Ausgabe

```bash
# Nach make run-quality:
cat storage/checkpoints/quality/last_run.json
```

---

## Orchestrierung mit Kestra

Der Flow [daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml):

1. `batch_ingestion` -- Olist + Open Food Facts + Open-Meteo + Frankfurter
2. `retailrocket_replay` -- Streaming-Replay
3. `warehouse_layers` -- Layer-Planung
4. `dbt_build` -- `dbt build` gegen das CI-sichere Profil
5. `run_quality` -- Quality-Checks (non-strict)
6. Parametrisierte Inputs: `environment` (default: dev), `streaming_mode` (default: replay)
7. Trigger: Daily um 06:00 UTC

Zugang: `http://localhost:8080` nach `docker compose up -d`

---

## Spark-Pfad

[clickstream_sessionization.py](spark/jobs/clickstream_sessionization.py):

- Liest Retailrocket-Events aus JSONL
- Normalisiert Timestamps und Event-Types
- Bildet Sessions ueber `visitor_id` mit 30-Min-Gap
- Aggregiert: event_count, view_count, addtocart_count, transaction_count
- Schreibt Parquet nach `storage/gold/retailrocket_sessions`

---

## Dashboard und Frontend

Das Frontend unter [dashboard/app.py](dashboard/app.py) visualisiert die Pipeline sowohl fachlich
als auch technisch.

Aktuell enthalten:

- Commerce-KPI-Seite mit Order-Volumen, Umsatz, Lieferquote und Payment-Split
- Zeitliche Trends fuer Bestellungen und Umsatz
- Kategorien- und Regionenanalysen inklusive Heatmap
- Retailrocket-Sessionanalyse mit Event-Funnel
- Wetter- und FX-Kontext
- Pipeline-Status mit Ingestion-Audit und Tabellenuebersicht

Filter:

- Zeitraum
- Bestellstatus
- Produktkategorie
- Bundesstaat
- Zahlungsart

Deployment-Pfade:

- lokal per `make run-dashboard`
- im Compose-Stack per `docker compose up -d dashboard`
- in GCP als Cloud-Run-Zielarchitektur

Dashboard-Seiten im Detail:

| Seite | Inhalt |
|---|---|
| Commerce KPIs | 8 Metriken (Bestellungen, Umsatz BRL/USD, Durchschnittsbestellwert, Artikel, Kunden, Fracht, Lieferquote), Insight-Kacheln, Pie-Chart (Status), Bar-Chart (Zahlungsart) |
| Zeitliche Trends | Bestellvolumen und Umsatzentwicklung nach Tag/Woche/Monat, gestapelter Kategorien-Umsatz |
| Kategorien & Regionen | Top-10 Kategorien nach Umsatz, Top-10 Bundesstaaten, Heatmap (Kategorie x Bundesstaat) |
| Session-Analyse | Session-KPIs (Visitors, Events/Session, Conversion Rate), Event-Funnel, Histogramm der Event-Verteilung |
| Wetter & FX | Temperaturverlauf, Niederschlag, EUR/USD- und EUR/BRL-Kurse, Scatter (Temperatur vs. Bestellwert) |
| Pipeline-Status | Ingestion-Audit-Tabelle, Zeilen-/Spalten-Statistiken pro Warehouse-Tabelle, Technologie-Stack |

Die Sidebar erlaubt kombinierte Filterung nach Zeitraum, Bestellstatus, Produktkategorie, Bundesstaat und Zahlungsart.
Alle Filter wirken gleichzeitig -- die gefilterte Trefferanzahl wird in Echtzeit angezeigt.

---

## GCP- und Terraform-Fundament

[infra/terraform/gcp](infra/terraform/gcp):

- Google-Provider `5.6.0` mit Credentials-File
- Automatische API-Aktivierung (Artifact Registry, BigQuery, Cloud Build, Cloud Run, Storage)
- Service-Konto mit BigQuery-Admin, Storage-Admin und Artifact-Registry-Reader
- 2 GCS-Buckets (Raw, Processed) mit Versioning und 30-Tage-Lifecycle
- 3 BigQuery-Datasets: `commerce_raw`, `commerce_staging`, `commerce_marts`
- 1 Artifact Registry Repository fuer Container-Images
- 1 optionaler Cloud Run Service fuer das Streamlit-Dashboard (wird nur erstellt wenn `dashboard_container_image` gesetzt ist)
- Location: `US` (kompatibel mit Public Datasets)

### GCP Cloud-Deployment Schritt fuer Schritt

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

# 4. Docker fuer Artifact Registry authentifizieren
gcloud auth configure-docker us-central1-docker.pkg.dev

# 5. Dashboard-Image bauen und pushen + Cloud Run deployen
make deploy-dashboard-gcp \
  GCP_PROJECT_ID=your-gcp-project-id \
  GCP_REGION=us-central1

# 6. Cloud-Run-URL abrufen
terraform -chdir=infra/terraform/gcp output dashboard_service_url
```

Das Cloud-Run-Dashboard benoetigt eine erreichbare PostgreSQL-Instanz (z.B. Cloud SQL).
Die Verbindungsparameter werden ueber `dashboard_env_vars` in `terraform.tfvars` konfiguriert.

---

## CI/CD-Pipeline

### Workflows

| Workflow | Trigger | Prueft |
|---|---|---|
| [lint.yml](.github/workflows/lint.yml) | push main + PRs | `pre-commit run --all-files` |
| [tests.yml](.github/workflows/tests.yml) | push main + PRs | `pytest` (13 Tests) |
| [dbt-checks.yml](.github/workflows/dbt-checks.yml) | push main + PRs | `dbt parse` + `dbt build` (DuckDB CI-Profil) |
| [integration.yml](.github/workflows/integration.yml) | push main + PRs | PostgreSQL-Service, Batch/Streaming/Quality/dbt-End-to-End und Docker-Builds |

Alle Workflows nutzen Python 3.11 und laufen auf `ubuntu-latest`.

### Lokale CI-Simulation

```bash
# Lint
make lint

# Tests
make test

# dbt CI-Build
make dbt-build-ci
```

---

## Validierung und Entwicklung

### Lokaler Pruefpfad

```bash
ruff check .
pytest
make run-warehouse
make run-quality
```

### Bereits erfolgreich geprueft

- `ruff check .` -- sauber
- `pytest` -- 13/13 gruen
- `make run-warehouse` inklusive `dbt build` -- sauber
- `make run-quality` mit sauberem Skip-Verhalten ohne erreichbares PostgreSQL

---

## Aktuelle Grenzen

- Olist nutzt lokal generierte Seed-Daten, solange keine echten CSV-Snapshots bereitliegen
- Retailrocket ist aktuell Replay-basiert und nicht an einen Live-Collector angebunden
- Open Food Facts nutzt bei temporaeren API-Stoerungen einen lokalen Fallback
- MongoDB wird als Raw-Store vorbereitet, aber noch nicht mit langfristiger Retention-Strategie
- BigQuery ist architektonisch vorbereitet, aber nicht komplett durchdeployt
- Kestra startet reale Entry-Points, aber noch ohne dediziertes Runtime-Image
- Cloud Run ist vorbereitet, aber noch ohne produktive Secret-Injektion und ohne finalen Datenbank-Zielpfad

---

## Naechste sinnvolle Ausbaustufen

- echte Olist-Rohdaten per Kaggle-Downloadpfad anstelle lokaler Seeds einbinden
- vollstaendige Retailrocket-Dateien automatisiert laden und replayen
- Replay zu einem dauerhaften Consumer-/Streaming-Job weiterentwickeln
- inkrementelle dbt-Strategien ergaenzen
- Source Freshness und Exposures in dbt aufbauen
- Datenqualitaetspruefungen in Orchestrierungs-Alerts integrieren
- Dashboard fuer Cloud mit BigQuery oder Cloud-SQL-Verbindung finalisieren
- BigQuery-Zielpfad mit echten GCP-Credentials und Remote State produktionsnaeher machen
- BigQuery-spezifische Starter-Modelle fuer `ga4_obfuscated_sample_ecommerce` und `thelook_ecommerce` ergaenzen

---

## Kurzfazit

Dieses Projekt zeigt nicht nur einzelne Tools, sondern einen konsistenten Data-Engineering-Ansatz:

- saubere Schichten (Raw -> Staging -> Intermediate -> Marts)
- klare technische Grenzen
- ausfuehrbare Starter statt reiner Platzhalter
- dokumentierte Zielarchitektur
- ehrlicher Status zwischen lokal nutzbar und cloud-ready vorbereitet

Genau das soll ein gutes Portfolio-Projekt leisten.
