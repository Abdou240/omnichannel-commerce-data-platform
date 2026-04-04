from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
from fastapi.testclient import TestClient

from omnichannel_platform.api.main import app


def test_root_endpoint_exposes_docs_links() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
    assert response.json()["health"] == "/api/v1/health"


def test_orders_endpoint_returns_filtered_rows(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_query_dataframe(sql: str, params=None) -> pd.DataFrame:
        captured["sql"] = sql
        captured["params"] = params
        return pd.DataFrame(
            [
                {
                    "order_id": "ord-1",
                    "customer_id": "cust-1",
                    "customer_city": "sao_paulo",
                    "customer_state": "SP",
                    "order_purchase_ts": "2018-01-03T10:00:00Z",
                    "order_status": "delivered",
                    "order_date": "2018-01-03",
                    "item_count": 2,
                    "gross_item_value": 180.0,
                    "freight_value": 15.0,
                    "payment_value_brl": 195.0,
                    "payment_value_usd": 50.0,
                    "payment_type": "credit_card",
                    "product_id": "prod-1",
                    "product_category_name": "electronics",
                    "product_weight_g": 350,
                    "avg_temperature_c": 24.1,
                    "precipitation_mm": 2.4,
                    "brl_to_usd_fx_rate": 0.256,
                }
            ]
        )

    monkeypatch.setattr(
        "omnichannel_platform.api.routes.orders.query_dataframe", fake_query_dataframe
    )
    client = TestClient(app)

    response = client.get(
        "/api/v1/orders",
        params={
            "status": "delivered",
            "category": "electronics",
            "state": "SP",
            "start_date": "2018-01-01",
            "end_date": "2018-01-31",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["order_id"] == "ord-1"
    assert payload[0]["order_purchase_ts"] == "2018-01-03T10:00:00Z"
    assert payload[0]["avg_temperature_c"] == 24.1
    assert "WHERE order_status = :status" in str(captured["sql"])
    assert captured["params"] == {
        "status": "delivered",
        "category": "electronics",
        "state": "SP",
        "start_date": date(2018, 1, 1),
        "end_date": date(2018, 1, 31),
    }


def test_sessions_endpoint_returns_sample_item_id(monkeypatch) -> None:
    def fake_query_dataframe(sql: str, params=None) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "session_key": "visitor-1:1",
                    "visitor_id": "visitor-1",
                    "session_start_ts": "2026-04-03T08:01:00Z",
                    "session_end_ts": "2026-04-03T08:11:00Z",
                    "event_count": 3,
                    "view_count": 1,
                    "addtocart_count": 1,
                    "transaction_count": 1,
                    "sample_item_id": "SKU-1001",
                }
            ]
        )

    monkeypatch.setattr(
        "omnichannel_platform.api.routes.sessions.query_dataframe",
        fake_query_dataframe,
    )
    client = TestClient(app)

    response = client.get("/api/v1/sessions")

    assert response.status_code == 200
    assert response.json()[0]["sample_item_id"] == "SKU-1001"


def test_pipeline_status_endpoint_returns_audit_and_table_stats(monkeypatch) -> None:
    loaded_at = datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc)

    def fake_query_dataframe(sql: str, params=None) -> pd.DataFrame:
        if "raw.ingestion_audit" in sql:
            return pd.DataFrame(
                [
                    {
                        "source_name": "olist",
                        "batch_id": "olist-20260404T090000",
                        "row_count": 2401,
                        "loaded_at": loaded_at,
                    }
                ]
            )
        if "count(*) as cnt" in sql:
            return pd.DataFrame([{"cnt": 12}])
        return pd.DataFrame([{"col_a": 1, "col_b": 2}])

    monkeypatch.setattr(
        "omnichannel_platform.api.routes.pipeline.query_dataframe",
        fake_query_dataframe,
    )
    client = TestClient(app)

    response = client.get("/api/v1/pipeline/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["audit"][0]["source_name"] == "olist"
    assert payload["tables"][0]["row_count"] == 12
    assert payload["tables"][0]["column_count"] == 2


def test_health_endpoint_degrades_when_database_is_unreachable(monkeypatch) -> None:
    def failing_check_database() -> str:
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(
        "omnichannel_platform.api.routes.pipeline.check_database",
        failing_check_database,
    )
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "database": "unreachable"}
