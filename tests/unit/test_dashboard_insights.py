from datetime import date

import pandas as pd

from omnichannel_platform.dashboard.logic import (
    apply_order_filters,
    derive_commerce_insights,
    derive_session_insights,
)


def test_derive_commerce_insights_reports_top_category_and_state() -> None:
    orders = pd.DataFrame(
        [
            {
                "order_id": "o1",
                "product_category_name": "electronics",
                "payment_value_brl": 200.0,
                "customer_state": "SP",
                "order_status": "delivered",
            },
            {
                "order_id": "o2",
                "product_category_name": "electronics",
                "payment_value_brl": 150.0,
                "customer_state": "SP",
                "order_status": "delivered",
            },
            {
                "order_id": "o3",
                "product_category_name": "fashion_bags_accessories",
                "payment_value_brl": 50.0,
                "customer_state": "RJ",
                "order_status": "shipped",
            },
        ]
    )

    insights = derive_commerce_insights(orders)

    assert len(insights) == 3
    assert "electronics" in insights[0]
    assert "SP" in insights[1]
    assert "66.7%" in insights[2]


def test_derive_commerce_insights_handles_empty_dataframe() -> None:
    empty = pd.DataFrame(
        columns=[
            "order_id",
            "product_category_name",
            "payment_value_brl",
            "customer_state",
            "order_status",
        ]
    )

    insights = derive_commerce_insights(empty)

    assert len(insights) == 1
    assert "Keine" in insights[0]


def test_derive_session_insights_reports_conversion_rate() -> None:
    sessions = pd.DataFrame(
        [
            {
                "session_key": "s1",
                "visitor_id": "v1",
                "event_count": 5,
                "view_count": 3,
                "addtocart_count": 1,
                "transaction_count": 1,
                "sample_item_id": "item-10",
            },
            {
                "session_key": "s2",
                "visitor_id": "v2",
                "event_count": 2,
                "view_count": 2,
                "addtocart_count": 0,
                "transaction_count": 0,
                "sample_item_id": "item-20",
            },
        ]
    )

    insights = derive_session_insights(sessions)

    assert len(insights) == 3
    assert "50.0%" in insights[0]
    assert "3.5" in insights[1]


def test_apply_order_filters_returns_copy_for_empty_dataframe() -> None:
    empty = pd.DataFrame(
        columns=[
            "order_id",
            "order_date",
            "order_status",
            "product_category_name",
            "customer_state",
            "payment_type",
        ]
    )

    filtered = apply_order_filters(
        empty,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 12, 31),
        statuses=["delivered"],
        categories=["electronics"],
        states=["SP"],
        payment_types=["credit_card"],
    )

    assert filtered.empty
    assert filtered is not empty
