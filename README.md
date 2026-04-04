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

**Ueberblick:**
- [Projektziel](#projektziel)
- [Fachlicher Umfang](#fachlicher-umfang)
- [Datenquellen](#datenquellen)
- [Architektur auf einen Blick](#architektur-auf-einen-blick)
- [Technologiestack](#technologiestack)
- [Repository-Struktur](#repository-struktur)

**Teil 1 -- Setup:**
- [Lokales Setup](#lokales-setup) (Python, .env, Docker Stack)
- [Setup-Referenz](#setup-referenz) (Details zu Extras, Umgebungsvariablen, Compose-Stack)
- [Zentrale Make-Targets](#zentrale-make-targets)

**Teil 2 -- Python-Skripte, Tests und Pipeline-Ausfuehrung:**
- [Datenfluss im Detail](#datenfluss-im-detail) (Batch, Streaming, dbt, Quality, kompletter Durchlauf)
- [Schritt-fuer-Schritt Testanleitung](#schritt-fuer-schritt-testanleitung)
- [Warehouse- und dbt-Modellierung](#warehouse--und-dbt-modellierung)
- [Datenqualitaet](#datenqualitaet)
- [Orchestrierung mit Kestra](#orchestrierung-mit-kestra)
- [Spark-Pfad](#spark-pfad)
- [Dashboard und Frontend](#dashboard-und-frontend)

**Teil 3 -- Deployment und Cloud:**
- [Containerisierung mit Docker](#containerisierung-mit-docker)
- [GCP- und Terraform-Fundament](#gcp--und-terraform-fundament)
- [CI/CD-Pipeline](#cicd-pipeline)

**Abschluss:**
- [Was aktuell implementiert ist](#was-aktuell-implementiert-ist)
- [Aktuelle Grenzen](#aktuelle-grenzen)
- [Naechste sinnvolle Ausbaustufen](#naechste-sinnvolle-ausbaustufen)

---

## Projektziel

Die Plattform soll ein realistisches Omnichannel-Commerce-Szenario abbilden:

- relationale Commerce-Daten im Batch-Stil ingestieren (Olist-Bestellungen, 4 externe APIs)
- Clickstream-Ereignisse ueber Kafka-kompatible Topics replayen (Retailrocket)
- externe Referenz- und Enrichment-Daten einbinden (Wetter, FX-Raten, Produktstammdaten)
- Rohdaten in ein lokales Warehouse ueberfuehren (PostgreSQL `raw.*`)
- dbt-Modelle von `raw -> staging -> intermediate -> marts` aufbauen (14 Modelle, 3 Schichten)
- Datenqualitaetsregeln dokumentieren und ausfuehrbar machen (4 Vertraege, 4 SQL-Expectations)
- Ergebnisse in einem interaktiven Dashboard visualisieren (Streamlit mit 8 Seiten und Filtern)
- alles containerisieren (Multi-Stage Dockerfile, 9 Docker-Compose-Services)
- eine klare Cloud-Zielarchitektur fuer BigQuery und GCP vorbereiten (Terraform, Cloud Run)

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

### Frankfurter API (v2)

FX-Raten (EUR -> USD, EUR -> BRL) zur spaeten Umrechnung von Betraegen und zur Vergleichbarkeit
von Commerce-Metriken. Nutzt die Frankfurter API v2 (`/v2/rates`) mit flacher Liste als
Antwortformat (ein Eintrag pro Datum+Waehrungspaar).

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
| CI/CD | GitHub Actions | 5 Workflows |

---

## Repository-Struktur

```text
.
├── .dockerignore                    # Schlanker Docker-Build-Context
├── .github/workflows/              # CI/CD: lint, pytest, dbt-checks, integration, deploy-gcp
├── Dockerfile                       # Multi-Stage Build (pipeline + dashboard)
├── docker-compose.yml               # 9 Services (Postgres, Redpanda, Kestra, ...)
├── Makefile                         # Alle Make-Targets
├── pyproject.toml                   # Python-Abhaengigkeiten und Extras
├── dashboard/                       # Streamlit-Frontend (app.py)
├── config/                          # Basis-, Dev- und Prod-Konfiguration
│   ├── base.yaml                    # Alle Quellen, Warehouse, Orchestrierung
│   ├── dev.yaml                     # Lokale Overrides (Kafka, Geo, etc.)
│   └── prod.yaml                    # Cloud-Platzhalter
├── data/sample/                     # Kleine lokale Beispiel- und Replay-Daten
│   ├── batch/                       # Olist-Manifest, Open Food Facts Sample
│   └── streaming/                   # Retailrocket JSONL (3 Events)
├── docs/                            # Architektur, ADRs, Runbooks
├── infra/terraform/gcp/             # GCP-Grundgeruest (Buckets, Datasets, IAM, Cloud Run)
├── kafka/                           # Topic-Katalog und create_topics.sh
├── nosql/mongodb/                   # init.js fuer Collections und Indexes
├── orchestration/kestra/flows/      # Kestra-Flow (daily_platform_ingestion)
├── quality/
│   ├── contracts/                   # 4 YAML-Vertraege
│   └── expectations/                # 4 SQL-Checks (fx_rates, order_statuses, etc.)
├── spark/jobs/                      # clickstream_sessionization.py
├── sql/postgres/init/               # Schema-Init + Raw-Tabellen-DDL
├── src/omnichannel_platform/
│   ├── batch/                       # commerce_batch_ingestion, source_plans, orders_ingestion
│   ├── common/                      # logging, settings, clients (Postgres/Mongo), io
│   ├── dashboard/                   # testbare Dashboard-Logik (logic.py)
│   ├── quality/                     # rules_catalog (SQL-Runner + Report)
│   ├── streaming/                   # clickstream_consumer (Replay + Kafka + Persist)
│   └── warehouse/                   # layer_catalog
├── tests/
│   ├── fixtures/                    # sample_orders.json, sample_clickstream_events.jsonl
│   ├── unit/                        # 11 Testdateien, 27 Tests
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
    └── seeds/                       # (bereit fuer Referenzdaten)
```

Wichtige Einstiegspunkte:

- [Dockerfile](Dockerfile) -- Multi-Stage Docker Build
- [docker-compose.yml](docker-compose.yml) -- 9-Service Plattform-Stack
- [dashboard/app.py](dashboard/app.py) -- Streamlit-Frontend
- [src/omnichannel_platform/batch/commerce_batch_ingestion.py](src/omnichannel_platform/batch/commerce_batch_ingestion.py) -- Batch-Pipeline
- [src/omnichannel_platform/streaming/clickstream_consumer.py](src/omnichannel_platform/streaming/clickstream_consumer.py) -- Streaming-Pipeline
- [src/omnichannel_platform/quality/rules_catalog.py](src/omnichannel_platform/quality/rules_catalog.py) -- Quality-Runner
- [orchestration/kestra/flows/daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml) -- Kestra-Orchestrierung
- [infra/terraform/gcp/main.tf](infra/terraform/gcp/main.tf) -- GCP-Infrastruktur

---

## Lokales Setup

> **Hinweis zu Python-Versionen:** Das Projekt unterstuetzt Python >=3.11. Alle Abhaengigkeiten
> sind mit Python 3.11-3.14 getestet. Die Docker-Images und CI-Workflows nutzen Python 3.11.

### Schnellstart fuer die Python-Skripte

```bash
# 1. Python-Umgebung
python3 -m venv .venv
source .venv/bin/activate
make install-local

# 2. Environment-Datei anlegen
cp .env.example .env

# 3. Mindest-Services fuer lokale Skript-Tests starten
docker compose up -d postgres

# Optional, aber empfohlen fuer den vollen E2E-Pfad:
docker compose up -d mongo redpanda

# 4. PostgreSQL pruefen
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

**Wichtig:** Fuehre alle `python -m omnichannel_platform...` Befehle aus dem Repository-Root aus.

### Welche Docker-Services braucht welches Skript?

| Skript | Pflicht | Optional | Hinweis |
|---|---|---|---|
| `commerce_batch_ingestion.py` | `postgres` | `mongo` | Batch laedt immer nach PostgreSQL. Mongo-Persist wird bei Nicht-Erreichbarkeit uebersprungen. |
| `clickstream_consumer.py` | `postgres` | `redpanda`, `mongo` | Replay persistiert immer nach PostgreSQL. Kafka- und Mongo-Schritte sind optional. |
| `rules_catalog.py` | `postgres` | — | SQL-Checks brauchen die Raw-/Mart-Tabellen in PostgreSQL. |
| `dashboard/app.py` | `postgres` | — | Dashboard liest aus Raw/Staging/Marts. |

### Typische lokale Stolpersteine

- `connection refused` auf `localhost:5432`: PostgreSQL laeuft nicht. Starte `docker compose up -d postgres`.
- `localhost:27017 connection refused`: MongoDB laeuft nicht. Das ist fuer Batch und Streaming **kein** Blocker; Mongo-Persist wird uebersprungen.
- Open Food Facts liefert `429 Too Many Requests`: Die Batch-Pipeline faellt automatisch auf das lokale Sample unter `data/sample/batch/open_food_facts_products_sample.json` zurueck.
- `postgres` startet und beendet sich sofort mit einem Hinweis auf PostgreSQL 18: Dann ist meist ein altes lokales Docker-Volume inkompatibel.

Wenn dir die alte lokale Entwicklungsdatenbank nicht wichtig ist, starte sauber neu:

```bash
docker compose down
docker volume rm omnichannel-commerce-data-platform_postgres_data
docker compose up -d postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

Wenn du die alten Daten behalten musst, solltest du das Volume nicht loeschen, sondern
entweder auf die fruehere PostgreSQL-Version zurueckgehen oder das Volume per `pg_upgrade`
migrieren.

---

## Datenfluss im Detail

### 1. Batch-Ingestion (`commerce_batch_ingestion.py`)

**Skript:** [commerce_batch_ingestion.py](src/omnichannel_platform/batch/commerce_batch_ingestion.py)

**Was macht `commerce_batch_ingestion.py` kurz?**

Das Skript ist der Batch-Einstiegspunkt fuer die lokale Raw-Layer-Befuellung.
Es verarbeitet nacheinander vier Quellen:

- `olist`: erzeugt oder liest lokale CSV-Snapshots und laedt sie in `raw.olist_*`
- `open_food_facts`: ruft Produktdaten per API ab und laedt sie in `raw.open_food_facts_products`
- `open_meteo`: holt Wetterdaten und laedt sie in `raw.open_meteo_weather`
- `frankfurter`: holt FX-Raten und laedt sie in `raw.frankfurter_fx_rates`

Zusaetzlich schreibt das Skript Bronze-Artefakte unter `storage/bronze/...` und protokolliert jeden Lauf
in `raw.ingestion_audit`.

**Pflicht vor dem Start: PostgreSQL vorbereiten**

```bash
docker compose up -d postgres
docker compose ps postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

**Was machen diese drei Docker-Kommandos?**

| Kommando | Bedeutung | Was wird gestartet / ausgefuehrt? |
|---|---|---|
| `docker compose up -d postgres` | Startet nur den PostgreSQL-Service aus `docker-compose.yml` im Hintergrund | Docker-Compose-Service: `postgres`, Container: `omnichannel-postgres` |
| `docker compose ps postgres` | Zeigt den Status genau dieses Services | Kein neuer Container, nur Statusanzeige fuer `postgres` |
| `docker compose exec postgres pg_isready -U commerce -d commerce_platform` | Fuehrt im laufenden PostgreSQL-Container das Healthcheck-Tool `pg_isready` aus | Befehl laeuft **im** Container `omnichannel-postgres` |

**Wichtig:** `docker compose up -d postgres` startet **nicht** den ganzen Stack, sondern nur den Service
`postgres`. Services wie `mongo`, `redpanda`, `dashboard` oder `kestra` bleiben dabei aus.

**Dann den Batch starten:**

```bash
# Alle 4 Quellen auf einmal (Standardverhalten)
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev

# Einzelne Quelle gezielt ausfuehren
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source olist
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source open_food_facts
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source open_meteo
python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source frankfurter

# Oder per Makefile (fuehrt alle Quellen aus)
make run-batch
```

**CLI-Argumente:**

| Flag | Werte | Default | Bedeutung |
|---|---|---|---|
| `--env` | `dev`, `prod` | `dev` | Laedt `config/base.yaml` + `config/<env>.yaml` |
| `--source` | `all`, `olist`, `open_food_facts`, `open_meteo`, `frankfurter` | `all` | Beschraenkt den Lauf auf eine einzelne Quelle |

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
| **olist** | 1. Prueft ob Seed-CSVs unter `storage/bronze/olist/` existieren. 2. Falls nicht: generiert deterministische Daten mit `random.Random(42)` (500 Orders, 250 Customers, 150 Products, 1001 Items, 500 Payments). 3. Liest alle 5 CSVs, TRUNCATE + APPEND in `raw.olist_*`. 4. Schreibt Audit-Eintrag und Run-Manifest. | 2401 total | `storage/bronze/olist/_runs/<batch_id>/run_manifest.json` |
| **open_food_facts** | 1. Ruft 4 konfigurierte Barcodes per API ab (z.B. Nutella, Coca-Cola). 2. Normalisiert Produktdaten (code, name, brands, categories, ecoscore). 3. Bei API-Fehler: Fallback auf `data/sample/batch/open_food_facts_products_sample.json`. 4. Speichert in `raw.open_food_facts_products` + optional MongoDB. | 3-4 Produkte | `storage/bronze/open_food_facts/products/_runs/<batch_id>/products_raw.jsonl` |
| **open_meteo** | 1. Holt Tageswerte (Temperatur, Niederschlag) fuer 3 Staedte (Sao Paulo, Rio, Belo Horizonte) ueber 365 Tage (2018). 2. Bei API-Fehler: generiert 14 Fallback-Tage pro Stadt. 3. Speichert in `raw.open_meteo_weather` + optional MongoDB. | ~1095 (365 x 3) | `storage/bronze/open_meteo/weather/_runs/<batch_id>/weather_raw.jsonl` |
| **frankfurter** | 1. Holt EUR->USD und EUR->BRL Wechselkurse fuer 2018. 2. Bei API-Fehler: generiert 14 Fallback-Tage mit 2 Waehrungen. 3. Speichert in `raw.frankfurter_fx_rates` + optional MongoDB. | ~730 (365 Tage x 2) | `storage/bronze/frankfurter/fx/_runs/<batch_id>/fx_rates_raw.jsonl` |

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
# Audit-Tabelle pruefen
docker compose exec postgres psql -U commerce -d commerce_platform -c \
  "SELECT source_name, batch_id, row_count, loaded_at FROM raw.ingestion_audit ORDER BY loaded_at DESC;"

# Einzelne Tabellen pruefen
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT count(*) FROM raw.olist_orders;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT count(*) FROM raw.open_meteo_weather;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT * FROM raw.open_food_facts_products LIMIT 3;"
docker compose exec postgres psql -U commerce -d commerce_platform -c "SELECT * FROM raw.frankfurter_fx_rates LIMIT 5;"
```

**Was pruefen diese `psql`-Kommandos genau?**

| Kommando | Zweck |
|---|---|
| `SELECT ... FROM raw.ingestion_audit ...` | Zeigt, welche Quellen im letzten Lauf geladen wurden, mit `batch_id`, `row_count` und Zeitstempel |
| `SELECT count(*) FROM raw.olist_orders;` | Prueft, ob die Olist-Orders wirklich im Raw-Schema gelandet sind |
| `SELECT count(*) FROM raw.open_meteo_weather;` | Prueft, ob die Wetterdaten geladen wurden |
| `SELECT * FROM raw.open_food_facts_products LIMIT 3;` | Zeigt ein paar echte Beispielzeilen der Produkt-Enrichment-Daten |
| `SELECT * FROM raw.frankfurter_fx_rates LIMIT 5;` | Zeigt ein paar geladene FX-Raten |

**Schrittweise in den Container und in `psql` gehen**

Wenn du nicht nur Einmal-Kommandos ausfuehren, sondern PostgreSQL interaktiv erkunden willst:

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
| Frankfurter API down | Generiert 14 Fallback-Tage mit 2 Waehrungen, Log-Warnung |
| MongoDB nicht erreichbar | Mongo-Persist wird mit Warnung uebersprungen, Pipeline laeuft weiter |

### 2. Streaming-Replay (`clickstream_consumer.py`)

**Skript:** [clickstream_consumer.py](src/omnichannel_platform/streaming/clickstream_consumer.py)

**Starten:**

```bash
# Replay-Modus (Standard)
python -m omnichannel_platform.streaming.clickstream_consumer --env dev --mode replay

# Continuous-Modus (aktuell identisch mit Replay, spaeter Kafka-Consumer-Loop)
python -m omnichannel_platform.streaming.clickstream_consumer --env dev --mode continuous

# Oder per Makefile
make run-streaming
```

**CLI-Argumente:**

| Flag | Werte | Default | Bedeutung |
|---|---|---|---|
| `--env` | `dev`, `prod` | `dev` | Konfigurationsumgebung |
| `--mode` | `replay`, `continuous` | `replay` | `replay` = einmaliger Durchlauf, `continuous` = aktuell identisch, spaeter dauerhafter Consumer |

**Voraussetzungen:**
- PostgreSQL muss laufen (Pflicht fuer `raw.retailrocket_events`)
- Redpanda/Kafka ist optional (Events werden trotzdem persistiert)
- MongoDB ist optional

**Wenn PostgreSQL lokal noch nicht laeuft, starte es vor dem Replay explizit:**

```bash
docker compose up -d postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform
```

**Interner Ablauf (Schritt fuer Schritt):**

1. **Plan laden:** Liest `config/base.yaml` + `config/dev.yaml`, baut einen `StreamingIngestionPlan` mit Replay-Source, Topic-Mapping, Consumer-Group und Bootstrap-Servers.
2. **Events lesen:** Oeffnet `data/sample/streaming/retailrocket_events.jsonl` und liest alle Events (aktuell 3 Beispiel-Events: je 1x view, addtocart, transaction).
3. **Normalisierung:** Jedes Event wird normalisiert -- Event-Type in Lowercase, IDs als Strings, Zuweisung des Ziel-Topics ueber ein konfigurierbares Mapping:
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
# PostgreSQL: Event-Verteilung pruefen
docker compose exec postgres psql -U commerce -d commerce_platform -c \
  "SELECT event_type, count(*) FROM raw.retailrocket_events GROUP BY event_type;"
# Erwartet: view=1, addtocart=1, transaction=1

# Checkpoint pruefen
cat storage/checkpoints/retailrocket/last_replay.json
# Erwartet: {"mode": "replay", "record_count": 3, "last_event_ts": "...", ...}

# Archivierte Replay-Dateien pruefen
ls storage/checkpoints/retailrocket/replays/

# Kafka-Topics pruefen (wenn Redpanda laeuft)
docker compose exec redpanda rpk topic list
docker compose exec redpanda rpk topic consume retailrocket.events.raw --num 3
```

**Fehlerszenarien:**

| Situation | Verhalten |
|---|---|
| PostgreSQL nicht erreichbar | `ensure_postgres_is_reachable()` bricht ab mit deutschsprachiger Hilfemeldung |
| Redpanda/Kafka nicht erreichbar | Kafka-Publish wird uebersprungen, Rest laeuft weiter |
| MongoDB nicht erreichbar | Mongo-Persist wird mit Warnung uebersprungen, Rest laeuft weiter |
| JSONL-Datei leer | Replay beendet sich sauber mit `records=0` |

### 3. Transformation im Warehouse (`dbt build`)

**Starten:**

```bash
# Option A: dbt gegen DuckDB (kein PostgreSQL noetig, gut fuer CI)
make run-warehouse
# Oder nur dbt:
make dbt-build-ci

# Option B: dbt gegen lokales PostgreSQL (nach Batch-Ingestion)
mkdir -p ~/.dbt && cp warehouse/dbt/profiles.yml.example ~/.dbt/profiles.yml
dbt build --project-dir warehouse/dbt --target dev
```

Die dbt-Modelle bilden aktuell drei Schichten:

- **staging** (9 Views): Normalisierung der Rohdaten mit source-aware Fallbacks. Das Macro `raw_relation_exists()` sorgt dafuer, dass Modelle auch kompilieren, wenn einzelne Raw-Tabellen noch nicht existieren (z.B. im DuckDB-CI-Profil).
- **intermediate** (2 Views):
  - `int_orders_with_context`: Verbindet Orders mit Customers (Stadt, Bundesstaat), Items (Artikelanzahl, Warenwert), Payments (BRL-Betrag, Zahlungsart), Weather (Temperatur, Niederschlag am Kauftag+Stadt) und FX (BRL->USD Cross-Rate ueber EUR).
  - `int_retailrocket_sessions`: 30-Min-Gap-Sessionisierung mit Window-Functions (LAG, SUM), Event-Type-Counts pro Session.
- **marts** (3 Tables):
  - `fct_commerce_orders`: Order-Grain Fact mit BRL- und USD-Betraegen, Kundengeografie, Produktkategorie, Wetterkontext
  - `fct_retailrocket_sessions`: Session-Grain Fact mit view/addtocart/transaction-Counts
  - `dim_products`: Olist + Open Food Facts kombiniert ueber `product_key` und `source_system`

Zusaetzlich laufen bei jedem `dbt build`:
- 3 Singular-Tests (`assert_valid_olist_order_statuses`, `assert_valid_retailrocket_event_types`, `assert_positive_fx_rates`)
- Spalten-Tests (not_null, unique) auf allen Schluesselfeldern

### 4. Datenqualitaet (`rules_catalog.py`)

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

1. **Contract-Discovery:** Laedt alle YAML-Dateien aus `quality/contracts/` -- das sind deklarative Vertraege, die beschreiben welche Spalten welche Bedingungen erfuellen muessen (z.B. not null, domain values).
2. **Expectation-Discovery:** Findet alle `.sql`-Dateien unter `quality/expectations/`.
3. **PostgreSQL-Verbindung pruefen:** Versucht eine Verbindung aufzubauen. Wenn PostgreSQL nicht erreichbar ist, werden alle SQL-Expectations als `skipped` markiert (kein Fehler).
4. **SQL-Execution:** Fuehrt jede SQL-Datei gegen PostgreSQL aus. Die SQL-Queries sind so geschrieben, dass sie Zeilen zurueckgeben die NICHT der Erwartung entsprechen. 0 Ergebniszeilen = passed, >0 Zeilen = failed.
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
#   "contracts": [...],      # Liste der geladenen YAML-Vertraege
#   "results": [             # Ergebnis pro SQL-Expectation
#     {"name": "assert_positive_fx_rates", "status": "passed", "row_count": 0, ...},
#     ...
#   ],
#   "summary": {"passed": 4, "failed": 0, "skipped": 0}
# }
```

### 5. Kompletter Pipeline-Durchlauf (Reihenfolge)

Die Skripte bauen aufeinander auf. Fuer einen vollstaendigen Durchlauf ist folgende Reihenfolge noetig:

```bash
docker compose up -d                     # 1. Infrastruktur starten
make kafka-topics                        # 2. Kafka-Topics anlegen
make run-batch                           # 3. Batch: fuellt raw.* (Olist + APIs)
make run-streaming                       # 4. Streaming: fuellt raw.retailrocket_events
dbt build --project-dir warehouse/dbt \
  --target dev                           # 5. dbt: baut staging -> intermediate -> marts
make run-quality                         # 6. Quality: prueft alle Tabellen
make run-dashboard                       # 7. Dashboard: zeigt alles im Browser an
```

Schritt 3 und 4 koennen parallel laufen (unabhaengige Quellen). Schritt 5 setzt voraus, dass
die Raw-Tabellen gefuellt sind. Schritt 6 setzt voraus, dass dbt gelaufen ist (fuer Mart-Checks).
Das Dashboard (Schritt 7) zeigt nur Daten an, wenn mindestens Schritt 3-5 abgeschlossen sind.

---

## Setup-Referenz

### 1. Python-Umgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
make install-local
```

#### Was macht `make install-local`?

Der Befehl fuehrt `pip install -e ".[dev,batch,streaming,warehouse,nosql,quality,dashboard]"` aus.
Das installiert das Projekt im editierbaren Modus (`-e`) zusammen mit allen optionalen Abhaengigkeitsgruppen:

| Extra-Gruppe | Installierte Pakete | Wofuer benoetigt |
|---|---|---|
| **dev** | pytest, ruff, pre-commit | Unit-Tests, Linting, Git-Hooks |
| **batch** | pandas, requests, sqlalchemy, psycopg, pyarrow, click, tqdm | Batch-Ingestion (Olist Seeds, API-Abrufe, PostgreSQL-Loads) |
| **streaming** | kafka-python-ng, sqlalchemy, psycopg | Retailrocket-Replay, Kafka-Publish, PostgreSQL-Persist |
| **warehouse** | dbt-postgres, dbt-duckdb, dbt-bigquery | dbt-Transformation gegen alle drei Targets |
| **nosql** | pymongo | MongoDB-Raw-Document-Store |
| **quality** | sqlalchemy, psycopg | SQL-Expectations gegen PostgreSQL ausfuehren |
| **dashboard** | streamlit, plotly, pandas, sqlalchemy, psycopg | Streamlit-Frontend mit Plotly-Charts |

Zusaetzlich werden die Basispakete `pydantic`, `python-dotenv` und `PyYAML` installiert, die fuer
Konfigurationsloading und Settings benoetigt werden.

**Alternative Installationsvarianten:**

```bash
make install          # Nur Basispakete (pydantic, dotenv, PyYAML)
make install-dev      # Basispakete + dev (pytest, ruff, pre-commit)
make install-local    # Alles ausser Spark (empfohlen fuer lokale Entwicklung)
```

Spark (`pyspark`) wird bewusst nicht ueber `install-local` installiert, da es eine eigene
JVM-Runtime benoetigt. Fuer die Spark-Sessionisierung: `pip install -e ".[spark]"`.

### 2. Umgebungsvariablen

```bash
cp .env.example .env
```

#### Was macht `cp .env.example .env`?

Die Datei `.env.example` enthaelt alle konfigurierbaren Umgebungsvariablen mit sinnvollen
Standardwerten fuer die lokale Entwicklung. Durch das Kopieren wird eine `.env`-Datei erzeugt,
die von `python-dotenv` beim Start jeder Pipeline automatisch geladen wird.

Die wichtigsten Variablengruppen in `.env`:

| Gruppe | Variablen | Standardwert | Bedeutung |
|---|---|---|---|
| **PostgreSQL** | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `localhost`, `5432`, `commerce_platform`, `commerce`, `commerce` | Verbindung zum lokalen Warehouse und Raw-Landing |
| **Kafka/Redpanda** | `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_TOPIC_*` | `localhost:9092` | Broker-Adresse und Topic-Namen fuer Streaming |
| **MongoDB** | `MONGO_URI`, `MONGO_DATABASE`, `MONGO_COLLECTION_*` | `mongodb://localhost:27017`, `commerce_raw` | Raw-Document-Store fuer JSON-Payloads |
| **APIs** | `OPEN_FOOD_FACTS_BASE_URL`, `OPEN_METEO_BASE_URL`, `FRANKFURTER_BASE_URL` | Oeffentliche Endpunkte | Externe Datenquellen fuer Enrichment |
| **MinIO** | `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | `localhost:9000`, `minio`, `minio123` | Lokales Object Storage |
| **Warehouse** | `WAREHOUSE_LOCAL_ENGINE`, `DBT_TARGET` | `postgres`, `dev` | Steuerung des lokalen Warehouse-Backends |
| **Kestra** | `KESTRA_NAMESPACE`, `KESTRA_HOST` | `omnichannel.platform.dev`, `http://localhost:8080` | Orchestrierungs-Endpunkte |
| **Dashboard** | `DASHBOARD_PORT`, `DASHBOARD_WAREHOUSE_SCHEMA`, `DASHBOARD_RAW_SCHEMA` | `8501`, `staging`, `raw` | Frontend-Konfiguration |
| **GCP** | `GCP_PROJECT_ID`, `GCP_REGION`, `GOOGLE_APPLICATION_CREDENTIALS` | `TODO_*` (muss angepasst werden) | Cloud-Deployment |

**Fuer den lokalen Betrieb muessen in der Regel keine Werte geaendert werden.** Die Standardwerte
passen zum Docker-Compose-Stack. Erst fuer Cloud-Deployments oder abweichende Hosts muessen die
`TODO_*`-Platzhalter durch echte Werte ersetzt werden.

Die `.env`-Datei ist in `.gitignore` eingetragen und wird nicht eingecheckt.

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
# tests/integration/test_module_resolution.py         1 passed
# tests/integration/test_repository_foundations.py    1 passed
# tests/unit/test_batch_helpers.py                    1 passed
# tests/unit/test_clients.py                          3 passed
# tests/unit/test_dashboard_insights.py               4 passed
# tests/unit/test_dashboard_logic.py                  2 passed
# tests/unit/test_frankfurter_edge_cases.py           2 passed
# tests/unit/test_frankfurter_payload.py              1 passed
# tests/unit/test_ingestion_plans.py                  5 passed
# tests/unit/test_olist_seed_determinism.py           2 passed
# tests/unit/test_quality_assets.py                   1 passed
# tests/unit/test_sample_fixtures.py                  2 passed
# tests/unit/test_settings.py                         2 passed
# ============================== 27 passed ==============================
```

**Was wird getestet:**
- `test_settings.py`: YAML-Config-Loading, Deep-Merge, Environment-Override
- `test_ingestion_plans.py`: Batch-Source-Plans (Olist, Open Food Facts, Open-Meteo, Frankfurter), Streaming-Plan, Event-Routing, Event-Normalisierung
- `test_sample_fixtures.py`: Fixture-Struktur (Orders, Clickstream)
- `test_dashboard_logic.py`: Filterlogik und Tabellenstatistiken fuer das Frontend
- `test_quality_assets.py`: Quality-Asset-Discovery (Contracts + Expectations)
- `test_clients.py`: PostgreSQL-Erreichbarkeitspruefung (`ensure_postgres_is_reachable`), MongoDB-Fehlerbehandlung
- `test_batch_helpers.py`: Datumsnormalisierung (`normalize_date_series`)
- `test_frankfurter_payload.py`: Frankfurter API v2 Payload-Normalisierung
- `test_frankfurter_edge_cases.py`: Edge Cases (unvollstaendige Eintraege, leere Listen)
- `test_dashboard_insights.py`: Commerce- und Session-Insight-Ableitung, leere DataFrames
- `test_olist_seed_determinism.py`: Deterministische Seed-Generierung, erwartete Zeilenzahlen
- `test_repository_foundations.py`: Prueft ob alle Schluesssel-Dateien existieren
- `test_module_resolution.py`: Prueft ob das Paket ohne PYTHONPATH importierbar ist

### Test 2: Batch-Ingestion (Olist Seed + API-Enrichments)

```bash
# Zuerst PostgreSQL vorbereiten
docker compose up -d postgres
docker compose ps postgres
docker compose exec postgres pg_isready -U commerce -d commerce_platform

# Dann den Batch starten
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
# olist          | olist-20260403T...          | 2401   (500 orders + 1001 items + 250 customers + 150 products + 500 payments)
# open_food_facts| open-food-facts-20260403T...| 3-4
# open_meteo     | weather-20260403T...        | ~1095  (365 Tage x 3 Staedte)
# frankfurter    | fx-20260403T...             | ~730   (365 Tage x 2 Waehrungen)

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
- MongoDB nicht erreichbar: Replay laeuft trotzdem (Mongo-Persist wird mit Warnung uebersprungen)
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
#   - Produkt-Analyse (Quellen-Split + Kategorien + Ecoscore)
#   - Session-Analyse (Funnel + Histogramm)
#   - Wetter & FX (Zeitreihen + Scatter)
#   - Datenquellen (Quellen-Uebersicht + Freshness + Datenfluss)
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

### Setup und Entwicklung

| Target | Zweck | Voraussetzung |
|---|---|---|
| `make install` | Nur Basispakete (pydantic, dotenv, PyYAML) | Python-venv |
| `make install-dev` | Basispakete + dev (pytest, ruff, pre-commit) | Python-venv |
| `make install-local` | Alles ausser Spark (empfohlen) | Python-venv |
| `make lint` | Ruff-Linting ausfuehren | `make install-dev` |
| `make test` | pytest-Suite ausfuehren (27 Tests) | `make install-dev` |
| `make pre-commit` | Pre-commit Hooks ausfuehren | `make install-dev` |

### Docker und Infrastruktur

| Target | Zweck | Voraussetzung |
|---|---|---|
| `make up` | Docker-Compose-Stack starten (9 Services) | Docker installiert |
| `make down` | Docker-Compose-Stack stoppen | Docker |
| `make logs` | Docker-Compose-Logs live anzeigen | Docker |
| `make kafka-topics` | 5 Kafka-/Redpanda-Topics anlegen | Redpanda laeuft |
| `make docker-build-pipeline` | Pipeline-Image lokal bauen (`Dockerfile` target `pipeline`) | Docker |
| `make docker-build-dashboard` | Dashboard-Image bauen (kann mit `GCP_PROJECT_ID` und `GCP_REGION` getaggt werden) | Docker |

### Pipeline-Ausfuehrung

| Target | Zweck | Voraussetzung |
|---|---|---|
| `make run-batch` | Batch-Ingestion: Olist Seeds + Open Food Facts + Open-Meteo + Frankfurter | PostgreSQL laeuft |
| `make run-streaming` | Retailrocket-Replay: JSONL lesen, normalisieren, Kafka + PG persistieren | PostgreSQL laeuft |
| `make run-warehouse` | Layer-Planung + `dbt build` gegen DuckDB-CI-Profil | `make install-local` |
| `make dbt-build-ci` | Nur `dbt build` gegen DuckDB (ohne Layer-Planung) | dbt installiert |
| `make run-quality` | SQL-Expectations gegen PostgreSQL ausfuehren, JSON-Report schreiben | Optional: PostgreSQL |
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

- 27 pytest-Tests (Unit + Integration)
- 5 GitHub-Actions-Workflows (lint, tests, dbt-checks, integration, deploy-gcp)
- pre-commit-Konfiguration
- Docker-Build-Smoke-Test in der Integrationspipeline
- Modulare Repository-Struktur

### Frontend und Deployment

- Streamlit-Dashboard mit 8 Seiten: Commerce KPIs, Zeitliche Trends, Kategorien & Regionen, Produkt-Analyse, Session-Analyse, Wetter & FX, Datenquellen, Pipeline-Status
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

Der Kestra-Flow [daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml) orchestriert
den kompletten taeglichen Pipeline-Durchlauf als eine Abfolge von Shell-Tasks:

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
| `streaming_mode` | STRING | `replay` | Replay oder Continuous-Modus fuer den Streaming-Schritt |

**Schedule:** Daily um 06:00 UTC (`0 6 * * *`)

**Zugang:** `http://localhost:8080` nach `docker compose up -d`. Die Kestra-UI zeigt den Flow unter
dem Namespace `omnichannel.platform.dev`. Von dort kann der Flow manuell getriggert, die Inputs
ueberschrieben und die Ausfuehrungshistorie eingesehen werden.

**Hinweis:** Die Tasks laufen aktuell noch shellbasiert. Fuer Produktionsbetrieb muessten sie in einem
dedizierten Runtime-Image mit allen Python- und dbt-Abhaengigkeiten laufen.

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
(Java 11+) muss verfuegbar sein.

**CLI-Argumente:**

| Flag | Default | Bedeutung |
|---|---|---|
| `--input-path` | (Pflicht) | Pfad zur JSONL-Datei mit Retailrocket-Events |
| `--output-path` | (Pflicht) | Zielverzeichnis fuer Parquet-Output |
| `--gap-minutes` | `30` | Inaktivitaetsluecke in Minuten fuer die Sessionisierung |

**Interner Ablauf:**

1. Liest Events aus der JSONL-Datei und validiert das Schema (event_id, visitor_id, event_type, item_id, event_ts).
2. Normalisiert Timestamps in UTC und Event-Types in Lowercase.
3. Partitioniert nach `visitor_id` und sortiert nach `event_ts`.
4. Berechnet die Zeitdifferenz zum vorherigen Event per `LAG`-Window-Function.
5. Setzt eine neue Session-Grenze, wenn die Luecke > `gap-minutes` betraegt.
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

## Dashboard und Frontend

**Skript:** [dashboard/app.py](dashboard/app.py) (Streamlit-Einstiegspunkt)
**Logik:** [src/omnichannel_platform/dashboard/logic.py](src/omnichannel_platform/dashboard/logic.py) (testbare Filterung, Insights, DB-URL)
**Tests:** [tests/unit/test_dashboard_logic.py](tests/unit/test_dashboard_logic.py) (2 Unit-Tests fuer Filterlogik und Tabellenstatistiken)

**Starten:**

```bash
# Option A: direkt lokal (schnellste Variante fuer Entwicklung)
make run-dashboard
# Entspricht: streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

# Option B: als Docker-Container (mit dem Rest des Stacks)
docker compose up -d dashboard

# Option C: nur Dashboard-Container isoliert starten
docker build --target dashboard -t omnichannel-dashboard:local .
docker run -p 8501:8080 \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=commerce_platform \
  -e POSTGRES_USER=commerce \
  -e POSTGRES_PASSWORD=commerce \
  omnichannel-dashboard:local
```

**Voraussetzungen:**
- PostgreSQL muss laufen und die Warehouse-Tabellen muessen existieren (d.h. mindestens `make run-batch` + `dbt build` muessen vorher gelaufen sein)
- Wenn noch keine Daten vorhanden sind, zeigt das Dashboard eine Warnung mit den notwendigen Schritten

**Architektur des Dashboards:**

Die Streamlit-App (`dashboard/app.py`) laedt beim Start alle relevanten DataFrames aus PostgreSQL
und cached sie fuer 5 Minuten (`@st.cache_data(ttl=300)`). Die Geschaeftslogik (Filterung,
Insight-Ableitung, Tabellenstatistiken) liegt in `src/omnichannel_platform/dashboard/logic.py` --
dadurch ist sie unabhaengig von Streamlit testbar.

Die Datenbankverbindung wird ueber Umgebungsvariablen konfiguriert und als SQLAlchemy-Engine
per `@st.cache_resource` einmalig initialisiert.

Das Frontend unter [dashboard/app.py](dashboard/app.py) visualisiert die Pipeline sowohl fachlich
als auch technisch.

**Filter (Sidebar):**

Alle Filter wirken gleichzeitig und seitenuebergreifend. Die aktuelle Trefferanzahl wird in
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
| Lokal (Python) | `make run-dashboard` | `http://localhost:8501` |
| Docker Compose | `docker compose up -d dashboard` | `http://localhost:8501` |
| GCP Cloud Run | `make deploy-dashboard-gcp` | Cloud-Run-URL (Terraform-Output) |

Dashboard-Seiten im Detail:

| Seite | Inhalt |
|---|---|
| Commerce KPIs | 8 Metriken (Bestellungen, Umsatz BRL/USD, Durchschnittsbestellwert, Artikel, Kunden, Fracht, Lieferquote), Insight-Kacheln, Pie-Chart (Status), Bar-Chart (Zahlungsart) |
| Zeitliche Trends | Bestellvolumen und Umsatzentwicklung nach Tag/Woche/Monat, gestapelter Kategorien-Umsatz |
| Kategorien & Regionen | Top-10 Kategorien nach Umsatz, Top-10 Bundesstaaten, Heatmap (Kategorie x Bundesstaat) |
| Produkt-Analyse | Produkte nach Quelle (Olist vs. Open Food Facts), Top-15 Kategorien, Ecoscore-Verteilung |
| Session-Analyse | Session-KPIs (Visitors, Events/Session, Conversion Rate), Event-Funnel, Histogramm der Event-Verteilung |
| Wetter & FX | Temperaturverlauf, Niederschlag, EUR/USD- und EUR/BRL-Kurse, Scatter (Temperatur vs. Bestellwert) |
| Datenquellen | Quellen-Uebersicht (5 Quellen mit Typ/Tabellen/Zeilen), letzte Ingestion pro Quelle, Datenfluss-Diagramm |
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
| [tests.yml](.github/workflows/tests.yml) | push main + PRs | `pytest` (27 Tests) |
| [dbt-checks.yml](.github/workflows/dbt-checks.yml) | push main + PRs | `dbt parse` + `dbt build` (DuckDB CI-Profil) |
| [integration.yml](.github/workflows/integration.yml) | push main + PRs | PostgreSQL-Service, Batch/Streaming/Quality/dbt-End-to-End und Docker-Builds |
| [deploy-gcp.yml](.github/workflows/deploy-gcp.yml) | workflow_dispatch (manuell) | Dashboard-Image bauen, nach Artifact Registry pushen und auf Cloud Run deployen |

Alle Workflows nutzen Python 3.11 und laufen auf `ubuntu-latest`.

#### lint.yml

Fuehrt `pre-commit run --all-files` aus. Das umfasst alle konfigurierten Hooks wie
`ruff check`, Trailing-Whitespace-Bereinigung und YAML-Syntax-Pruefung. Dieser Workflow
schlaegt fehl, wenn Codeformatierungs- oder Linting-Regeln verletzt werden.

#### tests.yml

Installiert die `dev`-, `batch`- und `dashboard`-Extras und fuehrt `pytest` aus. Testet alle 27 Tests
(11 Unit-Testdateien + 2 Integrations-Testdateien). Kein PostgreSQL noetig -- alle Tests
laufen rein lokal gegen Fixtures und YAML-Konfiguration.

#### dbt-checks.yml

Baut das dbt-Projekt gegen ein temporaeres DuckDB-Backend. Fuehrt zuerst `dbt parse` aus
(prueft ob alle Modelle syntaktisch korrekt sind), dann `dbt build` (kompiliert, materialisiert
und testet alle Modelle). Nutzt das CI-Profil aus `warehouse/dbt/profiles.ci.yml`.

#### integration.yml

Der umfangreichste Workflow. Startet einen PostgreSQL-18-Service-Container und durchlaeuft
den kompletten Pipeline-Pfad:

1. Schema-Initialisierung (SQL-DDL aus `sql/postgres/init/`)
2. Lint (`ruff check .`)
3. pytest (alle 27 Tests)
4. Batch-Ingestion (`--source olist` -- nur Olist Seeds, keine API-Aufrufe in CI)
5. Verifizierung: `raw.ingestion_audit` enthaelt Olist-Eintrag
6. Streaming-Replay (`--mode replay`)
7. Verifizierung: `raw.retailrocket_events` hat Daten
8. Quality-Checks (`--non-strict`)
9. dbt-Build gegen echtes PostgreSQL (mit temporaerem Profil)
10. Verifizierung: `staging.fct_commerce_orders` hat Daten
11. Docker-Image-Builds (Pipeline + Dashboard) als Smoke-Test

#### deploy-gcp.yml

Manuell ausloesbar ueber `workflow_dispatch` mit Umgebungswahl (`dev` / `prod`). Baut das Dashboard-
Image, pusht es in die Artifact Registry und deployed es auf Cloud Run. Benoetigt folgende
GitHub-Secrets: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_SA_KEY`, `POSTGRES_HOST`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`. Das Image wird mit dem Commit-SHA und `latest` getaggt.

### Lokale CI-Simulation

```bash
# Lint (entspricht lint.yml)
make lint

# Tests (entspricht tests.yml)
make test

# dbt CI-Build (entspricht dbt-checks.yml)
make dbt-build-ci

# Fuer eine volle Integration wie integration.yml:
# -> Docker-Stack + make run-batch + make run-streaming + dbt build + make run-quality
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
- `pytest` -- 27/27 gruen
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

- **Echte Daten:** 4 reale Datenquellen (Olist, Open Food Facts API, Open-Meteo API, Frankfurter API) + Clickstream-Replay
- **Saubere Schichten:** Raw -> Staging (9 Views) -> Intermediate (2 Views) -> Marts (3 Tables)
- **Ausfuehrbare Pipelines:** Jedes Skript ist per CLI aufrufbar, jede Ausgabe verifizierbar
- **Containerisiert:** Multi-Stage Dockerfile, 9 Docker-Compose-Services, Cloud-Run-ready
- **Getestet:** 27 pytest-Tests, 5 CI/CD-Workflows, 4 SQL-Quality-Expectations
- **Visualisiert:** Streamlit-Dashboard mit 8 Seiten, interaktiven Filtern und automatischen Insights
- **Cloud-ready:** Terraform fuer GCS, BigQuery, Artifact Registry und Cloud Run
- **Dokumentiert:** Ausfuehrliche README mit CLI-Referenzen, erwarteten Ausgaben und Fehlerszenarien

Genau das soll ein gutes Portfolio-Projekt leisten.
