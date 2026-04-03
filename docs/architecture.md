# Omnichannel Commerce Architecture

## Scope

This repository models a local-first Omnichannel Commerce platform with:

- Olist batch commerce data
- Retailrocket clickstream replay
- DummyJSON product enrichment
- Open-Meteo weather enrichment
- Frankfurter FX normalization
- MongoDB raw document storage
- PostgreSQL local raw warehouse
- BigQuery as the cloud warehouse target

## End-to-End Flow

```text
Olist CSVs / seeds -----------------------------+
DummyJSON API ----------------------------------+--> bronze files + Mongo raw --> PostgreSQL raw
Open-Meteo API ---------------------------------+
Frankfurter API --------------------------------+

Retailrocket replay file --> Kafka topics ------+--> PostgreSQL raw + Mongo raw

PostgreSQL raw --> dbt staging --> dbt intermediate --> dbt marts --> BigQuery target
```

## Raw Layer

### PostgreSQL raw tables

- `raw.olist_orders`
- `raw.olist_order_items`
- `raw.olist_customers`
- `raw.olist_products`
- `raw.olist_order_payments`
- `raw.retailrocket_events`
- `raw.dummyjson_products`
- `raw.open_meteo_weather`
- `raw.frankfurter_fx_rates`
- `raw.ingestion_audit`

### MongoDB raw collections

- `retailrocket_events_raw`
- `dummyjson_products_raw`
- `open_meteo_weather_raw`
- `frankfurter_fx_raw`

MongoDB is used as a raw document store for JSON payload inspection and flexible replay traces.

## Staging Layer

The dbt staging layer normalizes source-specific structures:

- Olist orders, items, customers, products, payments
- Retailrocket events
- DummyJSON products
- Open-Meteo weather
- Frankfurter FX rates

Each staging model is source-aware and compiles safely even when local raw tables are not present yet.

## Intermediate Layer

### `int_orders_with_context`

Starter order-grain enrichment that joins:

- Olist order headers
- Olist item aggregates
- Olist customer geography
- Olist product attributes
- weather by order date and customer city
- FX by order date

### `int_retailrocket_sessions`

Starter clickstream sessionization that groups events by `visitor_id` and a 30-minute inactivity gap.

## Mart Layer

### `fct_commerce_orders`

Starter order-grain fact model with:

- order timing and status
- customer geography
- item and payment metrics
- weather context
- FX normalization helper

### `fct_retailrocket_sessions`

Starter session-grain fact model with:

- session boundaries
- event counts by type
- sample item identifier

### `dim_products`

Starter product dimension combining:

- Olist product attributes
- DummyJSON API products

The two source systems remain logically distinct through `product_key` and `source_system`.

## Orchestration

Kestra orchestrates the local starter flow:

1. batch ingestion
2. Retailrocket replay
3. warehouse layer planning
4. quality execution

The flow is intentionally shell-based until a dedicated runtime image is introduced.

## Quality

Quality foundations combine:

- YAML contracts under `quality/contracts/`
- SQL expectations under `quality/expectations/`
- dbt model tests and singular tests

The Python quality runner executes SQL expectations against PostgreSQL and writes reports to:

- `storage/checkpoints/quality/last_run.json`

## Cloud Foundation

Terraform currently provisions starter GCP resources for:

- raw and processed GCS buckets
- BigQuery datasets for raw, staging, and marts
- a platform service account and IAM bindings

Secrets, API enablement, remote state, and environment promotion remain TODOs.
