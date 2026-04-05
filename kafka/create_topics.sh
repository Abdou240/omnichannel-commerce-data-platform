#!/usr/bin/env bash
# ============================================================================
# Kafka/Redpanda Topic-Erstellung
# Erstellt die 5 Retailrocket-Topics auf dem angegebenen Broker.
# Wird per `make kafka-topics` oder manuell aufgerufen.
# ============================================================================
set -euo pipefail

BROKER="${1:-localhost:9092}"

echo "Creating starter Kafka topics on ${BROKER}"

# Raw-Topic: Alle Events ungefiltert (3 Partitionen)
rpk topic create retailrocket.events.raw --brokers "${BROKER}" --partitions 3 || true

# Typspezifische Topics (6 Partitionen fuer hoehere Parallelitaet)
rpk topic create retailrocket.events.view --brokers "${BROKER}" --partitions 6 || true
rpk topic create retailrocket.events.addtocart --brokers "${BROKER}" --partitions 6 || true
rpk topic create retailrocket.events.transaction --brokers "${BROKER}" --partitions 6 || true

# Dead Letter Queue: Unbekannte Event-Typen (3 Partitionen)
rpk topic create retailrocket.events.dlq --brokers "${BROKER}" --partitions 3 || true

echo "Topics created successfully on ${BROKER}"
