"""/* @bruin
name: marts.fct_commerce_orders
type: python
depends:
  - raw.olist_orders
  - raw.retailrocket_events
  - raw.enrichments
description: Run dbt build to transform raw data into staging views and mart tables
@bruin */"""

# ── Bruin Asset-Definition: dbt Transformation ─────────────────────────────
# Abhaengig von allen 3 Raw-Ingestoren. Fuehrt dbt build aus, das
# 9 Staging Views + 2 Intermediate Views + 3 Mart Tables erstellt.
# Ausfuehrung:
#   dbt build --project-dir warehouse/dbt --profiles-dir .dbt
