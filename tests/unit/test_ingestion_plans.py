from omnichannel_platform.batch.source_plans import (
    build_batch_plans,
    build_olist_plan,
)
from omnichannel_platform.streaming.clickstream_consumer import (
    build_plan as build_stream_plan,
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


def test_route_event_topic_maps_known_retailrocket_events() -> None:
    plan = build_stream_plan("dev")

    assert route_event_topic("view", plan.event_topics) == "retailrocket.events.view"
    assert route_event_topic("transaction", plan.event_topics) == "retailrocket.events.transaction"
    assert route_event_topic("unknown", plan.event_topics) == "retailrocket.events.dlq"
