from datetime import date

import pandas as pd

from omnichannel_platform.dashboard.logic import apply_order_filters, build_table_stats


def test_apply_order_filters_respects_multiple_dimensions() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "order_id": "ord-1",
                "order_date": pd.Timestamp("2018-01-02"),
                "order_status": "delivered",
                "product_category_name": "electronics",
                "customer_state": "SP",
                "payment_type": "credit_card",
            },
            {
                "order_id": "ord-2",
                "order_date": pd.Timestamp("2018-01-05"),
                "order_status": "processing",
                "product_category_name": "watches_gifts",
                "customer_state": "RJ",
                "payment_type": "boleto",
            },
        ]
    )

    filtered = apply_order_filters(
        dataframe,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 3),
        statuses=["delivered"],
        categories=["electronics"],
        states=["SP"],
        payment_types=["credit_card"],
    )

    assert filtered["order_id"].tolist() == ["ord-1"]


def test_build_table_stats_returns_row_and_column_counts() -> None:
    stats = build_table_stats(
        {
            "orders": pd.DataFrame([{"order_id": "1"}]),
            "sessions": pd.DataFrame([{"session_key": "a", "event_count": 3}]),
        }
    )

    assert stats.to_dict(orient="records") == [
        {"Tabelle": "orders", "Zeilen": 1, "Spalten": 1},
        {"Tabelle": "sessions", "Zeilen": 1, "Spalten": 2},
    ]
