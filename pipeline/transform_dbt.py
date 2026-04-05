"""/* @bruin
name: staging.fct_commerce_orders
type: python
depends:
  - raw.olist_orders
  - raw.retailrocket_events
  - raw.enrichments
description: Run dbt build to transform raw data into staging views and mart tables
@bruin */"""

# Actual execution handled by:
#   dbt build --project-dir warehouse/dbt --profiles-dir .dbt
