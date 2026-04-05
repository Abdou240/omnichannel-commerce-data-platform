"""/* @bruin
name: raw.olist_orders
type: python
depends:
  - raw.schema_init
description: Ingest Olist e-commerce seed data into PostgreSQL raw schema
columns:
  - name: order_id
    type: varchar
    checks:
      - name: not_null
      - name: unique
  - name: order_status
    type: varchar
    checks:
      - name: not_null
      - name: accepted_values
        value: ["delivered", "shipped", "processing", "invoiced", "approved", "created", "canceled", "unavailable"]
  - name: order_purchase_timestamp
    type: timestamp
    checks:
      - name: not_null
@bruin */"""

# ── Bruin Asset-Definition: Olist Batch-Ingestion ──────────────────────────
# Dieses Asset definiert die Olist-Datenquelle im Bruin-DAG.
# Die eigentliche Ausfuehrung erfolgt ueber das Python-Modul:
#   python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source olist
# Bruin nutzt die obigen Metadaten fuer DAG-Abhaengigkeiten und Column-Checks.
