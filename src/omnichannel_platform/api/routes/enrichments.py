"""Enrichment-Endpunkte: Products, Weather und FX-Rates.

GET /api/v1/products   -> dim_products (mit Filter nach source_system)
GET /api/v1/weather    -> raw.open_meteo_weather (mit Filter nach Stadt/Datum)
GET /api/v1/fx-rates   -> raw.frankfurter_fx_rates (mit Filter nach Waehrung/Datum)
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from omnichannel_platform.api.database import query_dataframe, raw_schema, warehouse_schema
from omnichannel_platform.api.models import FxRateRow, ProductRow, WeatherRow

router = APIRouter(prefix="/api/v1", tags=["enrichments"])


@router.get("/products", response_model=list[ProductRow])
def list_products(
    source: str | None = Query(
        None, description="Filter by source_system (olist, open_food_facts)"
    ),
    limit: int = Query(200, ge=1, le=5000),
) -> list[dict]:
    schema = warehouse_schema()
    params: dict[str, object] = {}
    where = ""
    if source is not None:
        where = " WHERE source_system = :source"
        params["source"] = source

    sql = f"SELECT * FROM {schema}.dim_products{where} ORDER BY product_key LIMIT {limit}"
    df = query_dataframe(sql, params)
    return df.where(df.notna(), None).to_dict(orient="records")


@router.get("/weather", response_model=list[WeatherRow])
def list_weather(
    city: str | None = Query(None, description="Filter by city"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
) -> list[dict]:
    schema = raw_schema()
    conditions: list[str] = []
    params: dict[str, object] = {}
    if city is not None:
        conditions.append("city = :city")
        params["city"] = city
    if start_date is not None:
        conditions.append("weather_date >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("weather_date <= :end_date")
        params["end_date"] = end_date
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM {schema}.open_meteo_weather{where} ORDER BY weather_date LIMIT {limit}"
    df = query_dataframe(sql, params)
    return df.where(df.notna(), None).to_dict(orient="records")


@router.get("/fx-rates", response_model=list[FxRateRow])
def list_fx_rates(
    quote_currency: str | None = Query(None, description="Filter by quote currency (USD, BRL)"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
) -> list[dict]:
    schema = raw_schema()
    conditions: list[str] = []
    params: dict[str, object] = {}
    if quote_currency is not None:
        conditions.append("quote_currency = :quote_currency")
        params["quote_currency"] = quote_currency
    if start_date is not None:
        conditions.append("rate_date >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("rate_date <= :end_date")
        params["end_date"] = end_date
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM {schema}.frankfurter_fx_rates{where} ORDER BY rate_date LIMIT {limit}"
    df = query_dataframe(sql, params)
    return df.where(df.notna(), None).to_dict(orient="records")
