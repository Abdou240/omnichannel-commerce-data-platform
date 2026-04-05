"""/* @bruin
name: raw.enrichments
type: python
depends:
  - raw.schema_init
description: Ingest enrichment data from Open Food Facts, Open-Meteo, and Frankfurter APIs
columns:
  - name: fx_rate
    type: float
    checks:
      - name: positive
  - name: weather_date
    type: date
    checks:
      - name: not_null
@bruin */"""

# Actual execution handled by:
#   python -m omnichannel_platform.batch.commerce_batch_ingestion --env dev --source enrichments
