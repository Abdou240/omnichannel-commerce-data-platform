def test_sample_orders_fixture_has_required_keys(sample_orders: list[dict]) -> None:
    required_keys = {
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_estimated_delivery_date",
    }

    assert sample_orders
    assert required_keys.issubset(sample_orders[0].keys())


def test_sample_clickstream_fixture_has_required_keys(
    sample_clickstream_events: list[dict],
) -> None:
    required_keys = {
        "event_id",
        "visitor_id",
        "event_ts",
        "event_type",
        "item_id",
        "transaction_id",
    }

    assert sample_clickstream_events
    assert required_keys.issubset(sample_clickstream_events[0].keys())
