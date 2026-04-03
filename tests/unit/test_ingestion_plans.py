from omnichannel_platform.batch.source_plans import (
    build_batch_plans,
    build_olist_plan,
)
from omnichannel_platform.streaming.clickstream_consumer import (
    build_plan as build_stream_plan,
    normalize_retailrocket_event,
    route_event_topic,
)


def test_olist_batch_plan_uses_configured_dataset() -> None:
    plan = build_olist_plan("dev")

    assert plan.source_name == "olist"
    assert plan.details["dataset"] == "olistbr/brazilian-ecommerce"
    assert "olist_orders" in plan.details["tables"]


def test_batch_catalog_contains_external_enrichments() -> None:
    plans = build_batch_plans("dev")
    source_names = {plan.source_name for plan in plans}

    assert source_names == {"olist", "dummyjson", "open_meteo", "frankfurter"}


def test_streaming_plan_uses_retailrocket_topics() -> None:
    plan = build_stream_plan("dev")

    assert plan.raw_topic == "retailrocket.events.raw"
    assert plan.consumer_group == "retailrocket-replay-dev"
    assert plan.session_gap_minutes == 30


def test_route_event_topic_maps_known_retailrocket_events() -> None:
    plan = build_stream_plan("dev")

    assert route_event_topic("view", plan.event_topics) == "retailrocket.events.view"
    assert route_event_topic("transaction", plan.event_topics) == "retailrocket.events.transaction"
    assert route_event_topic("unknown", plan.event_topics) == "retailrocket.events.dlq"


def test_normalize_retailrocket_event_lowercases_and_routes() -> None:
    plan = build_stream_plan("dev")
    event = {
        "event_id": "evt-1",
        "visitor_id": "visitor-1",
        "event_type": "View",
        "item_id": 42,
        "transaction_id": None,
        "event_ts": "2026-04-03T08:01:00Z",
    }

    normalized = normalize_retailrocket_event(event, plan.event_topics)

    assert normalized["event_type"] == "view"
    assert normalized["item_id"] == "42"
    assert normalized["kafka_topic"] == "retailrocket.events.view"
