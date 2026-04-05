"""/* @bruin
name: quality.validation
type: python
depends:
  - staging.fct_commerce_orders
description: Run data quality checks (custom SQL expectations + Great Expectations)
@bruin */"""

# Actual execution handled by:
#   python -m omnichannel_platform.quality.rules_catalog --non-strict
#   python -m omnichannel_platform.quality.gx_validation --non-strict
