# Omnichannel Commerce Architecture

## Scope

This repository models an omnichannel commerce platform with:

- Olist as the batch commerce domain
- Retailrocket as the event/clickstream domain
- DummyJSON as a starter product enrichment API
- Open-Meteo as weather enrichment
- Frankfurter as FX enrichment
- MongoDB for raw JSON and event documents
- PostgreSQL for local warehouse development
- BigQuery as the deployed warehouse target

## Logical Layers

### Raw

- Olist batch tables land into PostgreSQL `raw.*`
- Retailrocket replay events are published to Kafka topics and persisted as raw documents in MongoDB
- DummyJSON, Open-Meteo, and Frankfurter payloads are stored as raw documents and prepared for raw warehouse tables

### Staging

- Normalize Olist order headers and order items
- Normalize Retailrocket event timestamps and event types
- Flatten DummyJSON product payloads into product attributes
- Standardize daily weather and FX reference data

### Marts

- `fct_commerce_orders`
- `fct_retailrocket_sessions`
- `dim_products`

These remain placeholders until the real business rules and source contracts are implemented.

## Local Stack

- Redpanda for Kafka-compatible event replay
- MongoDB for raw document storage
- PostgreSQL for local warehouse development
- Kestra for orchestration scaffolding
- dbt for transformation structure

## Notes

- The repository intentionally avoids pretending that source ingestion is complete.
- Credentials, cloud accounts, and production-grade state handling are left as TODOs.

