# Kafka Starter Assets

This directory contains the topic and bootstrap assets for Retailrocket replay.

Current scope:

- topic catalog for raw, typed, and DLQ Retailrocket events
- local topic creation script aligned to the Redpanda Compose stack
- routing-compatible topic names shared by config and Python replay code

Topic pattern:

- `retailrocket.events.raw`
- `retailrocket.events.view`
- `retailrocket.events.addtocart`
- `retailrocket.events.transaction`
- `retailrocket.events.dlq`

Local usage:

```bash
make kafka-topics
```

TODO:

- add ACLs and auth configuration for managed Kafka
- add schema registry subjects and compatibility policy
- add producer and consumer smoke tests for managed environments
