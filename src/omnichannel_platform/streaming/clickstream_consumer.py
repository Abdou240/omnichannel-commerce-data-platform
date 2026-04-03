from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

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


def build_plan(environment: str) -> StreamingIngestionPlan:
    settings = load_settings(environment)
    stream_config = settings["sources"]["retailrocket"]
    return StreamingIngestionPlan(
        replay_source=stream_config["replay_source"],
        raw_topic=stream_config["raw_topic"],
        event_topics=stream_config["event_topics"],
        consumer_group=stream_config["consumer_group"],
        checkpoint_path=stream_config["checkpoint_path"],
        bootstrap_servers=stream_config.get("bootstrap_servers"),
    )


def route_event_topic(event_type: str, event_topics: dict[str, str]) -> str:
    return event_topics.get(event_type.lower(), event_topics["default"])


def normalize_retailrocket_event(raw_event: dict[str, Any], event_topics: dict[str, str]) -> dict[str, Any]:
    event_type = str(raw_event["event_type"]).lower()
    return {
        "event_id": raw_event["event_id"],
        "visitor_id": raw_event["visitor_id"],
        "event_type": event_type,
        "item_id": raw_event.get("item_id"),
        "transaction_id": raw_event.get("transaction_id"),
        "event_ts": raw_event["event_ts"],
        "kafka_topic": route_event_topic(event_type, event_topics),
    }


def run(environment: str, mode: str) -> None:
    plan = build_plan(environment)
    LOGGER.info("Starting Retailrocket replay scaffold for environment=%s mode=%s", environment, mode)
    LOGGER.info(
        "Would replay source=%s raw_topic=%s group=%s checkpoint=%s bootstrap=%s",
        plan.replay_source,
        plan.raw_topic,
        plan.consumer_group,
        plan.checkpoint_path,
        plan.bootstrap_servers or "TODO_BOOTSTRAP_SERVERS",
    )
    for event_type, topic in plan.event_topics.items():
        LOGGER.info("  topic[%s]=%s", event_type, topic)

    LOGGER.info(
        "TODO: implement Kafka producer wiring, Mongo raw persistence, "
        "checkpoint handling, and DLQ publishing"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starter Retailrocket replay entry point.")
    parser.add_argument("--env", default="dev", help="Configuration environment to load.")
    parser.add_argument("--mode", choices=["replay", "continuous"], default="replay")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.env, args.mode)


if __name__ == "__main__":
    main()
