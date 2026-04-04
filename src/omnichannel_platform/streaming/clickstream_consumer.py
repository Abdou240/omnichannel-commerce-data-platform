from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from omnichannel_platform.common.clients import create_postgres_engine, ensure_postgres_is_reachable
from omnichannel_platform.common.io import ensure_directory, read_jsonl, write_json, write_jsonl
from omnichannel_platform.common.logging import get_logger
from omnichannel_platform.common.settings import load_settings

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class StreamingIngestionPlan:
    replay_source: str
    raw_topic: str
    event_topics: dict[str, str]
    consumer_group: str
    checkpoint_path: str
    bootstrap_servers: str | None
    raw_collection: str
    session_gap_minutes: int


def build_plan(environment: str) -> StreamingIngestionPlan:
    settings = load_settings(environment)
    stream_config = settings["sources"]["retailrocket"]
    raw_collection = settings["raw_document_store"]["collections"]["retailrocket_events"]
    return StreamingIngestionPlan(
        replay_source=stream_config["replay_source"],
        raw_topic=stream_config["raw_topic"],
        event_topics=stream_config["event_topics"],
        consumer_group=stream_config["consumer_group"],
        checkpoint_path=stream_config["checkpoint_path"],
        bootstrap_servers=stream_config.get("bootstrap_servers"),
        raw_collection=raw_collection,
        session_gap_minutes=int(stream_config.get("session_gap_minutes", 30)),
    )


def route_event_topic(event_type: str, event_topics: dict[str, str]) -> str:
    return event_topics.get(event_type.lower(), event_topics["default"])


def normalize_retailrocket_event(
    raw_event: dict[str, Any], event_topics: dict[str, str]
) -> dict[str, Any]:
    event_type = str(raw_event["event_type"]).lower()
    return {
        "event_id": str(raw_event["event_id"]),
        "visitor_id": str(raw_event["visitor_id"]),
        "event_type": event_type,
        "item_id": None if raw_event.get("item_id") is None else str(raw_event["item_id"]),
        "transaction_id": (
            None if raw_event.get("transaction_id") is None else str(raw_event["transaction_id"])
        ),
        "event_ts": raw_event["event_ts"],
        "kafka_topic": route_event_topic(event_type, event_topics),
    }


def optional_kafka_producer(bootstrap_servers: str | None):
    if not bootstrap_servers:
        return None

    try:
        from kafka import KafkaProducer
    except ModuleNotFoundError:
        LOGGER.warning("kafka-python-ng is not installed; skipping Kafka publish")
        return None

    try:
        return KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda payload: json.dumps(payload).encode("utf-8"),
            key_serializer=lambda key: key.encode("utf-8") if key else None,
        )
    except Exception:
        LOGGER.warning(
            "Unable to initialize Kafka producer; replay will continue without publish",
            exc_info=True,
        )
        return None


def mongo_database_name() -> str:
    return os.getenv("MONGO_DATABASE", "commerce_raw")


def persist_to_postgres(engine, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    from sqlalchemy import text

    with engine.begin() as connection:
        connection.execute(text("truncate table raw.retailrocket_events"))
        connection.execute(
            text(
                "insert into raw.retailrocket_events ("
                "event_id, visitor_id, event_type, item_id, transaction_id, event_ts, kafka_topic"
                ") values ("
                ":event_id, :visitor_id, :event_type, :item_id, :transaction_id, :event_ts, :kafka_topic"
                ")"
            ),
            rows,
        )

    return len(rows)


def persist_to_mongo(collection_name: str, raw_documents: list[dict[str, Any]]) -> int:
    from omnichannel_platform.common.clients import insert_many_documents

    return insert_many_documents(mongo_database_name(), collection_name, raw_documents)


def publish_to_kafka(
    plan: StreamingIngestionPlan, producer, normalized_rows: list[dict[str, Any]]
) -> None:
    if producer is None:
        return

    try:
        for row in normalized_rows:
            producer.send(plan.raw_topic, key=row["event_id"], value=row)
            producer.send(row["kafka_topic"], key=row["event_id"], value=row)

        producer.flush()
    except Exception:
        LOGGER.warning(
            "Kafka publish failed; replay will continue with raw persistence only", exc_info=True
        )


def write_replay_artifacts(
    plan: StreamingIngestionPlan,
    raw_documents: list[dict[str, Any]],
    normalized_rows: list[dict[str, Any]],
    mode: str,
) -> None:
    checkpoint_dir = ensure_directory(Path(plan.checkpoint_path))
    archive_dir = ensure_directory(checkpoint_dir / "replays")
    replay_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    write_jsonl(archive_dir / f"{replay_id}_raw.jsonl", raw_documents)
    write_jsonl(archive_dir / f"{replay_id}_normalized.jsonl", normalized_rows)
    write_json(
        checkpoint_dir / "last_replay.json",
        {
            "mode": mode,
            "replay_source": plan.replay_source,
            "record_count": len(normalized_rows),
            "last_event_ts": normalized_rows[-1]["event_ts"] if normalized_rows else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def run_replay(plan: StreamingIngestionPlan, mode: str, engine) -> dict[str, Any]:
    replay_source = Path(plan.replay_source)
    raw_events = read_jsonl(replay_source)
    normalized_rows = [
        normalize_retailrocket_event(event, plan.event_topics) for event in raw_events
    ]
    raw_documents = [
        {
            **event,
            "normalized_topic": normalized["kafka_topic"],
            "replayed_at": datetime.now(timezone.utc).isoformat(),
        }
        for event, normalized in zip(raw_events, normalized_rows, strict=True)
    ]

    producer = optional_kafka_producer(plan.bootstrap_servers)
    try:
        publish_to_kafka(plan, producer, normalized_rows)
    finally:
        if producer is not None:
            producer.close()

    inserted_rows = persist_to_postgres(engine, normalized_rows)
    mongo_rows = persist_to_mongo(plan.raw_collection, raw_documents)
    write_replay_artifacts(plan, raw_documents, normalized_rows, mode)

    topic_counts: dict[str, int] = {}
    for row in normalized_rows:
        topic_counts[row["kafka_topic"]] = topic_counts.get(row["kafka_topic"], 0) + 1

    return {
        "record_count": len(normalized_rows),
        "postgres_rows": inserted_rows,
        "mongo_rows": mongo_rows,
        "topic_counts": topic_counts,
    }


def run(environment: str, mode: str) -> None:
    plan = build_plan(environment)
    LOGGER.info(
        "Starting Retailrocket streaming ingestion for environment=%s mode=%s", environment, mode
    )
    LOGGER.info(
        "Replay source=%s raw_topic=%s group=%s checkpoint=%s bootstrap=%s",
        plan.replay_source,
        plan.raw_topic,
        plan.consumer_group,
        plan.checkpoint_path,
        plan.bootstrap_servers or "NOT_CONFIGURED",
    )

    if mode == "continuous":
        LOGGER.info(
            "Continuous mode currently performs a single bounded replay pass. "
            "TODO: replace with a long-running Kafka consumer loop."
        )

    engine = create_postgres_engine()
    ensure_postgres_is_reachable(engine)
    summary = run_replay(plan, mode, engine)
    LOGGER.info(
        "Retailrocket replay finished: records=%s postgres=%s mongo=%s",
        summary["record_count"],
        summary["postgres_rows"],
        summary["mongo_rows"],
    )
    for topic, count in sorted(summary["topic_counts"].items()):
        LOGGER.info("  routed_topic=%s count=%s", topic, count)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retailrocket replay entry point.")
    parser.add_argument("--env", default="dev", help="Configuration environment to load.")
    parser.add_argument("--mode", choices=["replay", "continuous"], default="replay")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.env, args.mode)


if __name__ == "__main__":
    main()
