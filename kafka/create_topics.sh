#!/usr/bin/env bash
set -euo pipefail

BROKER="${1:-localhost:9092}"

echo "Creating starter Kafka topics on ${BROKER}"

rpk topic create retailrocket.events.raw --brokers "${BROKER}" --partitions 3 || true
rpk topic create retailrocket.events.view --brokers "${BROKER}" --partitions 6 || true
rpk topic create retailrocket.events.addtocart --brokers "${BROKER}" --partitions 6 || true
rpk topic create retailrocket.events.transaction --brokers "${BROKER}" --partitions 6 || true
rpk topic create retailrocket.events.dlq --brokers "${BROKER}" --partitions 3 || true

echo "TODO: add replication, ACLs, and environment-specific topic settings for managed Kafka."
