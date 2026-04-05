"""/* @bruin
name: quality.validation
type: python
depends:
  - marts.fct_commerce_orders
description: Run data quality checks (custom SQL expectations + Great Expectations)
@bruin */"""

# ── Bruin Asset-Definition: Datenqualitaet ─────────────────────────────────
# Letzter Schritt im DAG: Laeuft nach der dbt-Transformation.
# Fuehrt beide Quality-Engines aus:
#   1. SQL-Expectations: python -m omnichannel_platform.quality.rules_catalog --non-strict
#   2. Great Expectations: python -m omnichannel_platform.quality.gx_validation --non-strict
