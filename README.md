# omnichannel-commerce-data-platform

Ein praxisnahes Portfolio-Projekt für Data Engineering rund um eine Omnichannel-Commerce-Plattform.

Dieses Repository modelliert einen realistischen End-to-End-Stack für Batch-, Streaming-,
Warehouse-, Qualitäts- und Orchestrierungs-Workloads. Der Fokus liegt bewusst auf einer sauberen,
erweiterbaren Plattformstruktur, auf ehrlichen Starter-Implementierungen und auf einer
repo-tauglichen Darstellung für Recruiter, Hiring Manager und technische Reviewer.

Das Projekt ist kein künstlich „fertig simulierter“ Showcase. Stattdessen gibt es funktionierende
Starter-Pipelines, echte Ausführungspfade, saubere TODO-Grenzen und eine klare Trennung zwischen
lokalem Entwicklungs-Setup und späterer Cloud-Zielarchitektur.

## Inhaltsverzeichnis

- [Projektziel](#projektziel)
- [Fachlicher Umfang](#fachlicher-umfang)
- [Datenquellen](#datenquellen)
- [Architektur auf einen Blick](#architektur-auf-einen-blick)
- [Datenfluss im Detail](#datenfluss-im-detail)
- [Technologiestack](#technologiestack)
- [Repository-Struktur](#repository-struktur)
- [Lokales Setup](#lokales-setup)
- [Zentrale Make-Targets](#zentrale-make-targets)
- [Was aktuell implementiert ist](#was-aktuell-implementiert-ist)
- [Warehouse- und dbt-Modellierung](#warehouse--und-dbt-modellierung)
- [Datenqualität](#datenqualität)
- [Orchestrierung mit Kestra](#orchestrierung-mit-kestra)
- [Spark-Pfad](#spark-pfad)
- [GCP- und Terraform-Fundament](#gcp--und-terraform-fundament)
- [Validierung und Entwicklung](#validierung-und-entwicklung)
- [Aktuelle Grenzen](#aktuelle-grenzen)
- [Nächste sinnvolle Ausbaustufen](#nächste-sinnvolle-ausbaustufen)

## Projektziel

Die Plattform soll ein realistisches Omnichannel-Commerce-Szenario abbilden:

- relationale Commerce-Daten im Batch-Stil ingestieren
- Clickstream-Ereignisse über Kafka-kompatible Topics replayen
- externe Referenz- und Enrichment-Daten einbinden
- Rohdaten in ein lokales Warehouse überführen
- dbt-Modelle von `raw -> staging -> intermediate -> marts` aufbauen
- Datenqualitätsregeln dokumentieren und ausführbar machen
- eine klare Cloud-Zielarchitektur für BigQuery und GCP vorbereiten

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

Die fachliche Idee ist bewusst breit genug, um Batch, Streaming, Referenzdaten, Modellierung,
Qualität und Cloud-Bausteine sinnvoll in einem gemeinsamen Projekt zu verbinden.

## Datenquellen

### Olist

Batch-orientierte relationale Commerce-Daten auf CSV-Basis:

- Orders
- Order Items
- Customers
- Products
- Payments

Im lokalen Setup werden deterministische Seed-Dateien erzeugt, wenn keine echten CSV-Snapshots
bereitgestellt wurden. Dadurch bleibt der Batch-Pfad lauffähig, ohne einen „Fake-Production“-Eindruck
zu erzeugen.

### Retailrocket

Clickstream-/Event-Daten für Replay-Szenarien:

- `view`
- `addtocart`
- `transaction`

Die Events werden im Starter-Setup aus einer JSONL-Datei gelesen, normalisiert, auf Kafka-Topics
geroutet und zusätzlich in der Raw-Schicht persistiert.

### DummyJSON

Produkt-API als leichtgewichtige Quelle für Enrichment und Dimensionserweiterung.

### Open-Meteo

Wetter-Enrichment auf Tagesebene für ausgewählte brasilianische Städte.

### Frankfurter API

FX-Raten zur späteren Umrechnung von Beträgen und zur Vergleichbarkeit von Commerce-Metriken.

### MongoDB

Raw-Document-Store für JSON-Payloads und Replay-Artefakte.

### PostgreSQL lokal und BigQuery als Zielarchitektur

- PostgreSQL dient lokal als Warehouse- und Raw-Execution-Ziel
- BigQuery ist als Cloud-Warehouse-Ziel in dbt- und Terraform-Struktur vorbereitet

## Architektur auf einen Blick

```text
                          +----------------------+
                          |     Olist CSVs       |
                          |  (oder lokale Seeds) |
                          +----------+-----------+
                                     |
                                     v
                         +-------------------------+
                         |   Batch Ingestion       |
                         |   Python + PostgreSQL   |
                         +------------+------------+
                                      |
             +------------------------+------------------------+
             |                        |                        |
             v                        v                        v
   +------------------+    +------------------+    +------------------+
   | DummyJSON API    |    | Open-Meteo API   |    | Frankfurter API  |
   +------------------+    +------------------+    +------------------+
             \                    |                         /
              \                   |                        /
               +------------------+-----------------------+
                                  |
                                  v
                    storage/bronze + MongoDB raw documents
                                  |
                                  v
                           PostgreSQL raw layer
                                  |
                                  v
                        dbt staging / intermediate
                                  |
                                  v
                               dbt marts
                                  |
                                  v
                       BigQuery als Zielarchitektur


Retailrocket JSONL -> Replay -> Kafka/Redpanda Topics -> PostgreSQL raw + MongoDB raw
```

Eine ergänzende Architekturübersicht liegt in [docs/architecture.md](docs/architecture.md).

## Datenfluss im Detail

### 1. Batch-Ingestion

Die Batch-Pipeline in [commerce_batch_ingestion.py](src/omnichannel_platform/batch/commerce_batch_ingestion.py) übernimmt:

- Bereitstellung oder Erzeugung lokaler Olist-Dateien
- Laden der Olist-Tabellen in `raw.*`
- API-Abrufe für DummyJSON, Open-Meteo und Frankfurter
- Schreiben von Bronze-Artefakten unter `storage/bronze/*/_runs/<batch_id>/`
- optionale Raw-Dokumentablage in MongoDB
- Audit-Einträge in `raw.ingestion_audit`

Die Implementierung ist bewusst minimal, aber nicht nur symbolisch. Sie besitzt echte Ausführungspfade,
arbeitet mit Config-Dateien, erzeugt Artefakte und trennt zwischen strukturierten Tabellendaten und
ungeschnittenen Raw-Dokumenten.

### 2. Streaming-Replay

Die Streaming-Pipeline in [clickstream_consumer.py](src/omnichannel_platform/streaming/clickstream_consumer.py) übernimmt:

- Lesen von Retailrocket-Events aus `data/sample/streaming/retailrocket_events.jsonl`
- Normalisierung der Event-Struktur
- Routing auf fachliche Topics
- Publizieren auf Kafka/Redpanda, sofern ein Broker erreichbar ist
- Persistenz in `raw.retailrocket_events`
- optionales Ablegen der Replay-Dokumente in MongoDB
- Schreiben eines Replay-Checkpoints unter `storage/checkpoints/retailrocket/`

Damit ist ein realistischer Starter für Event-Replay, Routing und Raw-Landing vorhanden, ohne bereits
eine vollständige produktive Streaming-Infrastruktur vorzutäuschen.

### 3. Transformation im Warehouse

Die dbt-Modelle bilden aktuell drei Schichten:

- `staging`: Normalisierung der Rohdaten
- `intermediate`: Zusammenführung, Kontextanreicherung, Sessionisierung
- `marts`: fachlich lesbare Fakt- und Dimensionsmodelle

Besonders wichtig: Die Modelle sind source-aware. Wenn lokale Raw-Tabellen noch nicht vorhanden sind,
kompilieren sie trotzdem sicher mit leeren Fallback-Relationen. So bleiben CI und lokales `dbt build`
stabil, auch wenn nicht immer alle Quellen geladen wurden.

### 4. Datenqualität

Die Datenqualitätslogik kombiniert:

- deklarative Verträge unter `quality/contracts/`
- SQL-Erwartungen unter `quality/expectations/`
- dbt-Tests auf Modell- und Spaltenebene
- einen Python-Runner in [rules_catalog.py](src/omnichannel_platform/quality/rules_catalog.py)

Das Ziel ist eine klare Trennung zwischen:

- dokumentierten Qualitätsanforderungen
- technisch ausführbaren Checks
- Warehouse-naher Validierung

## Technologiestack

### Datenverarbeitung

- Python 3.11+
- pandas
- requests
- SQLAlchemy
- psycopg

### Streaming

- Redpanda als Kafka-kompatibler lokaler Broker
- kafka-python-ng für Producer/Replay-Grundlagen

### Speicher und Warehouse

- PostgreSQL lokal
- MongoDB für Raw-JSON/Event-Dokumente
- BigQuery als Zielarchitektur
- MinIO als lokaler Object-Storage-Baustein

### Transformation und Qualität

- dbt
- pytest
- ruff
- pre-commit

### Orchestrierung und Infrastruktur

- Kestra
- Terraform für GCP
- Docker Compose für den lokalen Plattform-Stack

### Verteilte Verarbeitung

- Spark für den Sessionisierungs-Pfad

## Repository-Struktur

```text
.
├── config/                              # Basis-, Dev- und Prod-Konfiguration
├── data/sample/                         # Kleine lokale Beispiel- und Replay-Daten
├── docs/                                # Architektur, ADRs, Runbooks
├── infra/terraform/gcp/                 # GCP-Grundgerüst für Buckets, Datasets, IAM
├── kafka/                               # Topic-Katalog und Topic-Bootstrap
├── orchestration/kestra/                # Kestra-Flows und Namespace-Artefakte
├── quality/                             # Verträge, SQL-Checks, spätere Monitore
├── spark/                               # Spark-Konfiguration und Jobs
├── sql/postgres/init/                   # Lokale Warehouse- und Raw-Initialisierung
├── src/omnichannel_platform/
│   ├── batch/                           # Batch-Ingestion
│   ├── common/                          # Logging, Config, Clients, I/O
│   ├── quality/                         # Quality-Runner
│   ├── streaming/                       # Replay / Streaming
│   └── warehouse/                       # Warehouse-Layer-Katalog
├── tests/                               # Unit- und Integrationstests
└── warehouse/dbt/                       # dbt-Projekt mit Macros, Modellen und Tests
```

Wichtige Dateien:

- [docker-compose.yml](docker-compose.yml)
- [Makefile](Makefile)
- [config/base.yaml](config/base.yaml)
- [config/dev.yaml](config/dev.yaml)
- [warehouse/dbt/dbt_project.yml](warehouse/dbt/dbt_project.yml)
- [orchestration/kestra/flows/daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml)

## Lokales Setup

### 1. Python-Umgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
make install-local
```

`make install-local` installiert die lokalen Extras für:

- Entwicklung
- Batch
- Streaming
- Warehouse
- MongoDB/NoSQL
- Quality

### 2. Umgebungsvariablen

Die Vorlage liegt in [.env.example](.env.example).

Typische lokale Variablen:

- PostgreSQL-Verbindung
- Kafka/Redpanda-Bootstrap-Server
- MongoDB-URI
- BigQuery-/GCP-Platzhalter
- Kestra- und Spark-Parameter

TODO:

- produktive Secrets niemals direkt im Repo hinterlegen
- für Cloud-Läufe Secret Manager, CI-Secrets oder Orchestrator-Secrets nutzen

### 3. Plattform-Stack starten

```bash
docker compose up -d
```

Der Compose-Stack enthält aktuell:

- PostgreSQL 18
- pgAdmin
- Redpanda v25.3.9
- Redpanda Console
- MongoDB 7
- MinIO
- Kestra v1.1

### 4. Kafka-Topics anlegen

```bash
make kafka-topics
```

Standardtopics:

- `retailrocket.events.raw`
- `retailrocket.events.view`
- `retailrocket.events.addtocart`
- `retailrocket.events.transaction`
- `retailrocket.events.dlq`

### 5. Starter-Workflows ausführen

```bash
make run-batch
make run-streaming
make run-warehouse
make run-quality
```

## Zentrale Make-Targets

| Target | Zweck |
|---|---|
| `make install-local` | lokale Entwicklungs- und Laufzeitabhängigkeiten installieren |
| `make up` | Docker-Compose-Stack starten |
| `make down` | Docker-Compose-Stack stoppen |
| `make run-batch` | Batch-Ingestion für Olist und API-Enrichments ausführen |
| `make run-streaming` | Retailrocket-Replay ausführen |
| `make run-warehouse` | Warehouse-Layer planen und `dbt build` gegen das CI-Profil ausführen |
| `make run-quality` | SQL-basierte Quality-Checks starten |
| `make kafka-topics` | Kafka-/Redpanda-Topics anlegen |
| `make spark-sessionize` | Spark-Sessionisierung für Retailrocket-Beispieldaten ausführen |
| `make test` | pytest-Suite ausführen |
| `make lint` | Ruff-Linting ausführen |

## Was aktuell implementiert ist

### Batch

- Olist-Snapshot-Generierung für lokale Tests
- Laden von Orders, Items, Customers, Products, Payments
- DummyJSON-Produktabruf mit lokalem Fallback
- Open-Meteo-Wetterabruf für konfigurierte Städte
- Frankfurter-FX-Abruf für konfigurierten Zeitraum
- Bronze-Artefakte und Run-Manifeste
- Postgres-Loads in `raw.*`
- optionale Mongo-Persistenz

### Streaming

- Replay aus lokaler JSONL-Datei
- Event-Normalisierung
- Topic-Routing
- Kafka-Publish, wenn Broker verfügbar
- Persistenz nach PostgreSQL
- Replay-Artefakte und Checkpoint-Dateien

### Warehouse

- Raw-Tabellen-Initialisierung in PostgreSQL
- dbt-Macro für relation-aware Fallbacks
- Staging-Modelle für alle aktuellen Quellen
- Intermediate-Modelle für Order-Kontext und Sessions
- Mart-Modelle für Orders, Sessions und Produkte

### Datenqualität

- deklarative Qualitätsverträge
- SQL-Erwartungen
- dbt-Tests
- Python-Runner für Datenqualität mit Report-Ausgabe

### Engineering-Workflow

- pytest-Startertests
- GitHub-Actions-Workflows für Lint, Tests und dbt
- pre-commit-Konfiguration
- klare modulare Repository-Struktur

## Warehouse- und dbt-Modellierung

### Raw-Schicht

Die Rohdatenschicht bildet die operative Landefläche für normalisierte Tabellen:

- `raw.olist_orders`
- `raw.olist_order_items`
- `raw.olist_customers`
- `raw.olist_products`
- `raw.olist_order_payments`
- `raw.retailrocket_events`
- `raw.dummyjson_products`
- `raw.open_meteo_weather`
- `raw.frankfurter_fx_rates`

### Staging-Schicht

Die Staging-Modelle harmonisieren Datentypen, Benennungen und Basisnormalisierung.

Beispiele:

- [stg_olist_orders.sql](warehouse/dbt/models/staging/stg_olist_orders.sql)
- [stg_retailrocket_events.sql](warehouse/dbt/models/staging/stg_retailrocket_events.sql)
- [stg_dummyjson_products.sql](warehouse/dbt/models/staging/stg_dummyjson_products.sql)

### Intermediate-Schicht

Die Intermediate-Modelle bilden technische und fachliche Voraggregation:

- [int_orders_with_context.sql](warehouse/dbt/models/intermediate/int_orders_with_context.sql)
  verbindet Orders mit Kunden, Artikeln, Payments, Wetter und FX
- [int_retailrocket_sessions.sql](warehouse/dbt/models/intermediate/int_retailrocket_sessions.sql)
  sessionisiert Clickstream-Ereignisse mit einer Inaktivitätslücke von 30 Minuten

### Mart-Schicht

Aktuelle Mart-Modelle:

- [fct_commerce_orders.sql](warehouse/dbt/models/marts/fct_commerce_orders.sql)
- [fct_retailrocket_sessions.sql](warehouse/dbt/models/marts/fct_retailrocket_sessions.sql)
- [dim_products.sql](warehouse/dbt/models/marts/dim_products.sql)

Diese Modelle sind bewusst Starter und keine „fake business perfected marts“. Sie zeigen die
Richtung, nicht den endgültigen Fachschnitt.

## Datenqualität

Qualitätsartefakte liegen in:

- [quality/contracts](quality/contracts)
- [quality/expectations](quality/expectations)
- [warehouse/dbt/tests](warehouse/dbt/tests)

Beispiele für Checks:

- `order_id` darf nicht `null` sein
- Retailrocket-Eventtypen müssen in einer bekannten Domain liegen
- FX-Raten müssen positiv sein
- Mart-Order-IDs müssen eindeutig sein

Der Qualitäts-Runner schreibt den letzten Lauf nach:

- `storage/checkpoints/quality/last_run.json`

Wenn PostgreSQL lokal nicht erreichbar ist, werden SQL-Checks sauber übersprungen statt das Repo
unnötig „rot“ erscheinen zu lassen.

## Orchestrierung mit Kestra

Der Flow [daily_platform_ingestion.yml](orchestration/kestra/flows/daily_platform_ingestion.yml) bildet den aktuellen lokalen Ablauf ab:

1. Batch-Ingestion
2. Retailrocket-Replay
3. Warehouse-Layer-Planung
4. Datenqualitätslauf

Der Flow ist absichtlich noch shell-basiert, damit die Einstiegshürde lokal niedrig bleibt. Für eine
nächste Reifestufe wäre ein dediziertes Runtime-Image sinnvoll, in dem Python-Abhängigkeiten und dbt
bereits enthalten sind.

## Spark-Pfad

Unter [spark/jobs/clickstream_sessionization.py](spark/jobs/clickstream_sessionization.py) gibt es einen echten Starter für Sessionisierung:

- liest die Retailrocket-Beispieldatei
- bildet Sessions auf Basis eines 30-Minuten-Gaps
- schreibt Session-Summaries als Parquet nach `storage/gold/retailrocket_sessions`

Das ist bewusst noch kein produktiver Structured-Streaming-Job, aber ein sauberer Einstiegspunkt für
spätere Skalierung.

## GCP- und Terraform-Fundament

Das GCP-Fundament unter [infra/terraform/gcp](infra/terraform/gcp) enthält aktuell:

- Google-Provider `5.6.0`
- Service-Konto
- Raw- und Processed-GCS-Buckets
- BigQuery-Datasets für `commerce_raw`, `commerce_staging`, `commerce_marts`
- IAM-Zuweisungen als Starter-Fundament

Bewusst noch offen:

- Remote State
- Aktivierung benötigter GCP-APIs
- Secret- und Credential-Management
- CI/CD-Deploymentpfade

## Validierung und Entwicklung

### Lokaler Prüfpfad

```bash
ruff check .
pytest
make run-warehouse
make run-quality
```

### Bereits erfolgreich geprüft

Der aktuelle Stand wurde bereits lokal gegen folgende Schritte geprüft:

- `ruff check .`
- `pytest`
- `make run-warehouse` inklusive `dbt build`
- `make run-quality` mit sauberem Skip-Verhalten ohne erreichbares PostgreSQL

### Entwicklerfreundliche Grundlagen

- `pre-commit` ist vorbereitet
- GitHub Actions für Lint, Tests und dbt-Checks sind vorhanden
- Beispiel-Fixtures für Tests liegen im Repo
- die Struktur ist bewusst modular, nicht monolithisch

## Aktuelle Grenzen

- Olist nutzt lokal generierte Seed-Daten, solange keine echten CSV-Snapshots bereitliegen
- Retailrocket ist aktuell Replay-basiert und nicht an einen Live-Collector angebunden
- MongoDB wird als Raw-Store vorbereitet, aber noch nicht mit langfristiger Retention-Strategie betrieben
- BigQuery ist architektonisch vorbereitet, aber nicht komplett durchdeployt
- Kestra startet reale Entry-Points, aber noch ohne dediziertes Runtime-Image
- einige API- und Cloud-Details sind bewusst als TODO markiert, weil dafür echte Secrets und Zielkonten nötig sind

## Nächste sinnvolle Ausbaustufen

- echte Olist-Rohdaten anstelle lokaler Seeds einbinden
- Replay zu einem dauerhaften Consumer-/Streaming-Job weiterentwickeln
- inkrementelle dbt-Strategien ergänzen
- Source Freshness und Exposures in dbt aufbauen
- Datenqualitätsprüfungen in Orchestrierungs-Alerts integrieren
- Streamlit- oder BI-Layer mit Kennzahlen und Session-Analysen ergänzen
- BigQuery-Zielpfad mit echten GCP-Credentials und Remote State produktionsnäher machen

## Kurzfazit

Dieses Projekt zeigt nicht nur einzelne Tools, sondern einen konsistenten Data-Engineering-Ansatz:

- saubere Schichten
- klare technische Grenzen
- ausführbare Starter statt reiner Platzhalter
- dokumentierte Zielarchitektur
- ehrlicher Status zwischen lokal nutzbar und cloud-ready vorbereitet

Genau das soll ein gutes Portfolio-Projekt leisten.
