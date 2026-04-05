"""Pydantic Response-Modelle fuer die REST API.

Definiert die Antwortstrukturen fuer alle API-Endpunkte:
  - Orders (OrderRow, OrderKPIs)
  - Sessions (SessionRow, SessionFunnel)
  - Enrichments (ProductRow, WeatherRow, FxRateRow)
  - Pipeline (AuditRow, TableStat, PipelineStatus, HealthResponse)
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str


class OrderRow(BaseModel):
    order_id: str
    customer_id: str
    customer_city: str | None = None
    customer_state: str | None = None
    order_purchase_ts: datetime | None = None
    order_status: str
    order_date: date | None = None
    item_count: int | None = None
    gross_item_value: float | None = None
    freight_value: float | None = None
    payment_value_brl: float | None = None
    payment_value_usd: float | None = None
    payment_type: str | None = None
    product_id: str | None = None
    product_category_name: str | None = None
    product_weight_g: int | None = None
    avg_temperature_c: float | None = None
    precipitation_mm: float | None = None
    brl_to_usd_fx_rate: float | None = None


class OrderKPIs(BaseModel):
    total_orders: int
    total_revenue_brl: float
    total_revenue_usd: float
    avg_order_value_brl: float
    total_items: int
    unique_customers: int
    avg_freight: float
    delivery_rate_pct: float


class SessionRow(BaseModel):
    session_key: str
    visitor_id: str
    session_start_ts: datetime | None = None
    session_end_ts: datetime | None = None
    event_count: int
    view_count: int
    addtocart_count: int
    transaction_count: int
    sample_item_id: str | None = None


class SessionFunnel(BaseModel):
    total_sessions: int
    total_views: int
    total_addtocart: int
    total_transactions: int
    conversion_rate_pct: float


class ProductRow(BaseModel):
    product_key: str
    product_id: str
    product_name: str | None = None
    brand: str | None = None
    category: str | None = None
    price_usd: float | None = None
    image_front_url: str | None = None
    source_system: str
    ecoscore_grade: str | None = None


class WeatherRow(BaseModel):
    weather_date: date
    city: str
    avg_temperature_c: float | None = None
    precipitation_mm: float | None = None


class FxRateRow(BaseModel):
    rate_date: date
    base_currency: str
    quote_currency: str
    fx_rate: float


class AuditRow(BaseModel):
    source_name: str
    batch_id: str
    row_count: int
    loaded_at: datetime


class TableStat(BaseModel):
    table_name: str
    row_count: int
    column_count: int


class PipelineStatus(BaseModel):
    audit: list[AuditRow]
    tables: list[TableStat]
