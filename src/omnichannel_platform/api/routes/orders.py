"""Order-Endpunkte: GET /api/v1/orders (mit Filtern) und GET /api/v1/orders/kpis.

Liest aus der Mart-Tabelle fct_commerce_orders (staging/marts Schema).
Unterstuetzt Filter nach Status, Kategorie, Bundesstaat, Datumsbereich und Pagination.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from omnichannel_platform.api.database import query_dataframe, warehouse_schema
from omnichannel_platform.api.models import OrderKPIs, OrderRow

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.get("", response_model=list[OrderRow])
def list_orders(
    status: str | None = Query(None, description="Filter by order status"),
    category: str | None = Query(None, description="Filter by product category"),
    state: str | None = Query(None, description="Filter by customer state"),
    start_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=5000, description="Max rows"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> list[dict]:
    schema = warehouse_schema()
    conditions: list[str] = []
    params: dict[str, object] = {}
    if status is not None:
        conditions.append("order_status = :status")
        params["status"] = status
    if category is not None:
        conditions.append("product_category_name = :category")
        params["category"] = category
    if state is not None:
        conditions.append("customer_state = :state")
        params["state"] = state
    if start_date is not None:
        conditions.append("order_date >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("order_date <= :end_date")
        params["end_date"] = end_date

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = (
        f"SELECT * FROM {schema}.fct_commerce_orders"
        f"{where} ORDER BY order_date DESC NULLS LAST, order_id LIMIT {limit} OFFSET {offset}"
    )
    df = query_dataframe(sql, params)
    return df.where(df.notna(), None).to_dict(orient="records")


@router.get("/kpis", response_model=OrderKPIs)
def order_kpis(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
) -> dict:
    schema = warehouse_schema()
    conditions: list[str] = []
    params: dict[str, object] = {}
    if start_date is not None:
        conditions.append("order_date >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("order_date <= :end_date")
        params["end_date"] = end_date
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
    SELECT
        count(*) as total_orders,
        coalesce(sum(payment_value_brl), 0) as total_revenue_brl,
        coalesce(sum(payment_value_usd), 0) as total_revenue_usd,
        coalesce(avg(payment_value_brl), 0) as avg_order_value_brl,
        coalesce(sum(item_count), 0)::int as total_items,
        count(distinct customer_id) as unique_customers,
        coalesce(avg(freight_value), 0) as avg_freight,
        coalesce(avg(case when order_status = 'delivered' then 1.0 else 0.0 end) * 100, 0) as delivery_rate_pct
    FROM {schema}.fct_commerce_orders{where}
    """
    df = query_dataframe(sql, params)
    return df.iloc[0].to_dict()
