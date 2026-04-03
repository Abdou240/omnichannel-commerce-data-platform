# Omnichannel Commerce Architecture

## Scope

Dieses Repository modelliert eine lokal lauffähige Omnichannel-Commerce-Plattform mit realen oder
realitätsnah eingebundenen Quellen:

- Olist für relationale Commerce-Batchdaten
- Retailrocket für Clickstream-Replay
- Open Food Facts für echte Produkt-JSON-Dokumente
- Open-Meteo für Wetter-Enrichment
- Frankfurter für FX-Normalisierung
- MongoDB als Raw-Document-Store
- PostgreSQL als lokales Raw- und Warehouse-Ziel
- BigQuery als Cloud-Ziel inklusive öffentlicher Referenzdatensätze

## End-to-End Flow

```text
Olist CSVs / Seeds -----------------------------+
Open Food Facts Product API --------------------+--> bronze files + Mongo raw --> PostgreSQL raw
Open-Meteo API ---------------------------------+
Frankfurter API --------------------------------+

Retailrocket replay file --> Kafka topics ------+--> PostgreSQL raw + Mongo raw

PostgreSQL raw --> dbt staging --> dbt intermediate --> dbt marts --> BigQuery target
                                                            |
                                                            +--> spätere BigQuery-Referenzpfade:
                                                                 - bigquery-public-data.ga4_obfuscated_sample_ecommerce
                                                                 - bigquery-public-data.thelook_ecommerce
```

## Raw Layer

### PostgreSQL raw tables

- `raw.olist_orders`
- `raw.olist_order_items`
- `raw.olist_customers`
- `raw.olist_products`
- `raw.olist_order_payments`
- `raw.retailrocket_events`
- `raw.open_food_facts_products`
- `raw.open_meteo_weather`
- `raw.frankfurter_fx_rates`
- `raw.ingestion_audit`

### MongoDB raw collections

- `retailrocket_events_raw`
- `open_food_facts_products_raw`
- `open_meteo_weather_raw`
- `frankfurter_fx_raw`

MongoDB dient hier als Raw-Document-Store für JSON-Payload-Inspektion, Replay-Spuren und flexible
Fehleranalyse.

## Staging Layer

Die dbt-Staging-Schicht normalisiert quellspezifische Strukturen:

- Olist orders, items, customers, products, payments
- Retailrocket events
- Open Food Facts products
- Open-Meteo weather
- Frankfurter FX rates

Jedes Staging-Modell ist source-aware und kompiliert sauber weiter, auch wenn lokal noch nicht alle
Raw-Tabellen vorhanden sind.

## Intermediate Layer

### `int_orders_with_context`

Starter-Order-Modell auf Grain `order_id` mit:

- Olist order headers
- Olist item aggregates
- Olist customer geography
- Wetterkontext auf Kaufdatum und Stadt
- FX-Kontext auf Kaufdatum

### `int_retailrocket_sessions`

Starter-Sessionisierung für Clickstream-Ereignisse mit `visitor_id` und 30 Minuten
Inaktivitätslücke.

## Mart Layer

### `fct_commerce_orders`

Starter-Faktmodell für Commerce-Bestellungen mit:

- Bestellstatus und Kaufzeitpunkten
- Kundengeografie
- Artikel- und Payment-Kennzahlen
- Wetter- und FX-Kontext

### `fct_retailrocket_sessions`

Starter-Faktmodell für Sessions mit:

- Session-Grenzen
- Event-Anzahlen nach Typ
- Beispiel-Item-Bezug

### `dim_products`

Starter-Produktdimension mit zwei klar getrennten Quellen:

- Olist-Produktattribute
- Open-Food-Facts-Produktstammdaten

Die beiden Systeme bleiben über `product_key` und `source_system` logisch getrennt. Ein echtes
SKU-Matching zwischen Olist und Open Food Facts ist bewusst noch nicht implementiert.

## BigQuery Public References

Für die Cloud-Zielarchitektur sind zwei echte öffentliche BigQuery-Referenzen vorgesehen:

- `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
- `bigquery-public-data.thelook_ecommerce`

Wichtig: Diese Public Datasets liegen in der Regel in der `US` Multi-Region. Eigene BigQuery-Targets
für direkte Joins oder Ableitungen sollten deshalb ebenfalls in `US` geplant werden.

## Orchestration

Kestra orchestriert aktuell den lokalen Starter-Ablauf:

1. Batch-Ingestion
2. Retailrocket-Replay
3. Warehouse-Layer-Planung
4. Quality-Ausführung

Der Flow bleibt bewusst shell-basiert, bis ein dediziertes Runtime-Image mit Python- und dbt-Stack
eingeführt wird.

## Quality

Die Quality-Basis kombiniert:

- YAML-Verträge unter `quality/contracts/`
- SQL-Erwartungen unter `quality/expectations/`
- dbt-Modelltests und Singular Tests

Der Python-Runner führt SQL-Erwartungen gegen PostgreSQL aus und schreibt Reports nach:

- `storage/checkpoints/quality/last_run.json`

## Cloud Foundation

Terraform provisioniert aktuell Starter-Ressourcen in GCP für:

- Raw- und Processed-GCS-Buckets
- BigQuery-Datasets für raw, staging und marts
- ein Plattform-Service-Konto inklusive IAM-Bindings

Secrets, API-Aktivierung, Remote State und Umgebungs-Promotion bleiben weiterhin TODOs.
