# Kafka Starter Assets

This directory contains small platform-level Kafka assets for local development and future managed deployments.

Current scope:

- topic catalog for Retailrocket clickstream replay
- topic bootstrap script for local Redpanda/Kafka

Current topic pattern:

- `retailrocket.events.raw`
- `retailrocket.events.view`
- `retailrocket.events.addtocart`
- `retailrocket.events.transaction`
- `retailrocket.events.dlq`

TODO:

- add ACLs and auth configuration for managed Kafka
- add schema registry subjects and compatibility policy
- add producer and consumer smoke tests once message contracts exist
