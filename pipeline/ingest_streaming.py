"""/* @bruin
name: raw.retailrocket_events
type: python
depends:
  - raw.schema_init
description: Replay Retailrocket clickstream events into PostgreSQL via Kafka or direct insert
columns:
  - name: event_id
    type: varchar
    checks:
      - name: not_null
  - name: visitor_id
    type: varchar
    checks:
      - name: not_null
  - name: event_type
    type: varchar
    checks:
      - name: not_null
      - name: accepted_values
        value: ["view", "addtocart", "transaction"]
@bruin */"""

# Actual execution handled by:
#   python -m omnichannel_platform.streaming.clickstream_consumer --env dev --mode replay
