"""Batch ingestion for the Omnichannel Commerce platform.

Implemented starter flows:
  - Olist relational seed generation and PostgreSQL raw loads
  - DummyJSON product pulls with bronze landing and optional Mongo raw docs
  - Open-Meteo weather enrichment pulls for configured Brazilian cities
  - Frankfurter FX rate pulls with bronze landing and optional Mongo raw docs

This module keeps the foundations realistic without pretending to be
production-complete. Secrets, stateful watermarks, and retries remain TODOs.
"""

from __future__ import annotations

import argparse
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yaml
from requests import Response
from sqlalchemy import text
from sqlalchemy.engine import Engine

from omnichannel_platform.batch.source_plans import BatchSourcePlan, build_batch_plans
from omnichannel_platform.common.clients import create_postgres_engine, insert_many_documents
from omnichannel_platform.common.io import ensure_directory, write_json, write_jsonl
from omnichannel_platform.common.logging import get_logger

LOGGER = get_logger(__name__)

OLIST_FILE_TABLE_MAP = {
    "olist_orders_dataset.csv": "olist_orders",
    "olist_order_items_dataset.csv": "olist_order_items",
    "olist_customers_dataset.csv": "olist_customers",
    "olist_products_dataset.csv": "olist_products",
    "olist_order_payments_dataset.csv": "olist_order_payments",
}

OLIST_DATE_COLUMNS = {
    "olist_orders_dataset.csv": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_estimated_delivery_date",
    ]
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_batch_id(prefix: str) -> str:
    return f"{prefix}-{utc_now().strftime('%Y%m%dT%H%M%S')}"


def mongo_database_name() -> str:
    return os.getenv("MONGO_DATABASE", "commerce_raw")


def audit_batch(engine: Engine, source_name: str, batch_id: str, row_count: int) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into raw.ingestion_audit (source_name, batch_id, loaded_at, row_count) "
                "values (:source_name, :batch_id, now(), :row_count) "
                "on conflict (source_name, batch_id) do update "
                "set loaded_at = now(), row_count = excluded.row_count"
            ),
            {
                "source_name": source_name,
                "batch_id": batch_id,
                "row_count": row_count,
            },
        )


def truncate_raw_table(engine: Engine, table_name: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(f"truncate table raw.{table_name}"))


def load_dataframe(engine: Engine, table_name: str, dataframe: pd.DataFrame) -> int:
    truncate_raw_table(engine, table_name)
    if dataframe.empty:
        return 0

    dataframe.to_sql(
        table_name,
        engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
    )
    return len(dataframe)


def landing_subdir(base_path: str, *parts: str) -> Path:
    return ensure_directory(Path(base_path).joinpath(*parts))


def run_artifact_dir(base_path: str, batch_id: str) -> Path:
    return landing_subdir(base_path, "_runs", batch_id)


def request_json(url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    LOGGER.info("Requesting %s", url)
    response: Response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def write_run_manifest(
    output_dir: Path,
    *,
    source_name: str,
    batch_id: str,
    row_count: int,
    metadata: dict[str, Any] | None = None,
) -> None:
    payload = {
        "source_name": source_name,
        "batch_id": batch_id,
        "row_count": row_count,
        "generated_at": utc_now().isoformat(),
        "metadata": metadata or {},
    }
    write_json(output_dir / "run_manifest.json", payload)


def _seed_olist_frames() -> dict[str, pd.DataFrame]:
    rng = random.Random(42)
    base_purchase_ts = datetime(2018, 1, 1, 8, 0, tzinfo=timezone.utc)

    city_state_pairs = [
        ("sao_paulo", "SP"),
        ("rio_de_janeiro", "RJ"),
        ("belo_horizonte", "MG"),
    ]
    order_statuses = [
        "delivered",
        "shipped",
        "processing",
        "invoiced",
        "approved",
    ]
    payment_types = ["credit_card", "boleto", "voucher", "debit_card"]
    categories = ["bed_bath_table", "electronics", "fashion_bags_accessories", "watches_gifts"]

    customers: list[dict[str, Any]] = []
    for index in range(1, 251):
        city, state = city_state_pairs[index % len(city_state_pairs)]
        customers.append(
            {
                "customer_id": f"cust-{index:04d}",
                "customer_city": city,
                "customer_state": state,
            }
        )

    products: list[dict[str, Any]] = []
    for index in range(1, 151):
        products.append(
            {
                "product_id": f"prod-{index:04d}",
                "product_category_name": categories[index % len(categories)],
                "product_name_length": 20 + (index % 40),
                "product_description_length": 80 + (index % 300),
                "product_photos_qty": 1 + (index % 5),
                "product_weight_g": 150 + (index % 2000),
            }
        )

    orders: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    payments: list[dict[str, Any]] = []

    for index in range(1, 501):
        order_id = f"ord-{index:05d}"
        customer_id = f"cust-{rng.randint(1, 250):04d}"
        purchase_ts = base_purchase_ts + timedelta(hours=index * 4)
        approved_ts = purchase_ts + timedelta(hours=rng.randint(1, 12))
        estimated_delivery = purchase_ts + timedelta(days=rng.randint(4, 14))
        status = order_statuses[index % len(order_statuses)]

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_status": status,
                "order_purchase_timestamp": purchase_ts,
                "order_approved_at": approved_ts,
                "order_estimated_delivery_date": estimated_delivery,
            }
        )

        item_count = 1 + (index % 3)
        order_total = 0.0
        for item_number in range(1, item_count + 1):
            price = round(rng.uniform(15, 450), 2)
            freight = round(rng.uniform(5, 50), 2)
            items.append(
                {
                    "order_id": order_id,
                    "order_item_id": item_number,
                    "product_id": f"prod-{rng.randint(1, 150):04d}",
                    "seller_id": f"seller-{rng.randint(1, 40):03d}",
                    "price": price,
                    "freight_value": freight,
                }
            )
            order_total += price + freight

        payments.append(
            {
                "order_id": order_id,
                "payment_sequential": 1,
                "payment_type": payment_types[index % len(payment_types)],
                "payment_installments": 1 + (index % 6),
                "payment_value": round(order_total, 2),
            }
        )

    return {
        "olist_orders_dataset.csv": pd.DataFrame(orders),
        "olist_order_items_dataset.csv": pd.DataFrame(items),
        "olist_customers_dataset.csv": pd.DataFrame(customers),
        "olist_products_dataset.csv": pd.DataFrame(products),
        "olist_order_payments_dataset.csv": pd.DataFrame(payments),
    }


def ensure_olist_seed_files(plan: BatchSourcePlan) -> dict[str, Path]:
    landing_path = ensure_directory(Path(plan.landing_path))
    manifest_path = Path(plan.details.get("local_manifest", ""))
    expected_files = list(OLIST_FILE_TABLE_MAP)

    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = yaml.safe_load(handle) or {}
        expected_files = [
            entry["file_name"]
            for entry in manifest.get("tables", [])
            if entry.get("file_name") in OLIST_FILE_TABLE_MAP
        ] or expected_files

    expected_paths = {file_name: landing_path / file_name for file_name in expected_files}
    if all(path.exists() for path in expected_paths.values()):
        return expected_paths

    LOGGER.info("Generating local Olist seed files under %s", landing_path)
    seed_frames = _seed_olist_frames()
    for file_name, output_path in expected_paths.items():
        seed_frames[file_name].to_csv(output_path, index=False)

    return expected_paths


def read_olist_dataframe(file_name: str, csv_path: Path) -> pd.DataFrame:
    parse_dates = OLIST_DATE_COLUMNS.get(file_name, [])
    return pd.read_csv(csv_path, parse_dates=parse_dates)


def ingest_olist(plan: BatchSourcePlan, engine: Engine) -> int:
    batch_id = build_batch_id("olist")
    csv_paths = ensure_olist_seed_files(plan)
    output_dir = run_artifact_dir(plan.landing_path, batch_id)
    total_rows = 0
    table_counts: dict[str, int] = {}

    for file_name in sorted(csv_paths):
        table_name = OLIST_FILE_TABLE_MAP[file_name]
        dataframe = read_olist_dataframe(file_name, csv_paths[file_name])
        loaded_rows = load_dataframe(engine, table_name, dataframe)
        table_counts[table_name] = loaded_rows
        total_rows += loaded_rows
        LOGGER.info("Loaded %s rows from %s into raw.%s", loaded_rows, file_name, table_name)

    write_run_manifest(
        output_dir,
        source_name="olist",
        batch_id=batch_id,
        row_count=total_rows,
        metadata={"tables": table_counts},
    )
    audit_batch(engine, "olist", batch_id, total_rows)
    return total_rows


def load_dummyjson_fallback() -> dict[str, Any]:
    fallback_path = Path("data/sample/batch/dummyjson_products_sample.json")
    with fallback_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def ingest_dummyjson(plan: BatchSourcePlan, engine: Engine) -> int:
    batch_id = build_batch_id("dummyjson")
    ingested_at = utc_now()
    output_dir = run_artifact_dir(plan.landing_path, batch_id)
    base_url = plan.details["base_url"]
    endpoint = plan.details["endpoint"]
    page_size = int(plan.details.get("page_size", 30))

    flattened_rows: list[dict[str, Any]] = []
    raw_documents: list[dict[str, Any]] = []
    skip = 0
    used_fallback = False

    while True:
        try:
            payload = request_json(
                f"{base_url}{endpoint}",
                params={"limit": page_size, "skip": skip},
            )
        except requests.RequestException:
            LOGGER.warning("DummyJSON request failed, using local sample payload instead", exc_info=True)
            payload = load_dummyjson_fallback()
            used_fallback = True

        products = payload.get("products", [])
        if not products:
            break

        raw_documents.extend(
            [
                {
                    **product,
                    "batch_id": batch_id,
                    "ingested_at": ingested_at.isoformat(),
                    "source_system": "dummyjson",
                    "fallback": used_fallback,
                }
                for product in products
            ]
        )
        flattened_rows.extend(
            [
                {
                    "product_id": str(product["id"]),
                    "title": product["title"],
                    "brand": product.get("brand", "unknown"),
                    "category": product.get("category", "unknown"),
                    "price_usd": float(product["price"]),
                    "ingested_at": ingested_at,
                }
                for product in products
            ]
        )

        skip += page_size
        if used_fallback or skip >= payload.get("total", len(products)):
            break

    write_jsonl(output_dir / "products_raw.jsonl", raw_documents)
    write_run_manifest(
        output_dir,
        source_name="dummyjson",
        batch_id=batch_id,
        row_count=len(flattened_rows),
        metadata={"page_size": page_size, "fallback": used_fallback},
    )
    insert_many_documents(mongo_database_name(), plan.raw_collection or "dummyjson_products_raw", raw_documents)

    dataframe = pd.DataFrame(
        flattened_rows,
        columns=["product_id", "title", "brand", "category", "price_usd", "ingested_at"],
    )
    loaded_rows = load_dataframe(engine, "dummyjson_products", dataframe)
    audit_batch(engine, "dummyjson", batch_id, loaded_rows)
    return loaded_rows


def generate_weather_fallback_rows(plan: BatchSourcePlan, ingested_at: datetime) -> list[dict[str, Any]]:
    geographies = plan.details.get("geographies", [{"city": "sao_paulo"}])
    dates = pd.date_range(plan.details["start_date"], plan.details["end_date"], freq="D")
    rows: list[dict[str, Any]] = []

    for geography in geographies:
        for date_value in dates[:14]:
            rows.append(
                {
                    "weather_date": date_value.date().isoformat(),
                    "city": geography["city"],
                    "avg_temperature_c": 18.0 + (date_value.day % 10),
                    "precipitation_mm": float(date_value.day % 6),
                    "ingested_at": ingested_at,
                }
            )

    return rows


def ingest_open_meteo(plan: BatchSourcePlan, engine: Engine) -> int:
    batch_id = build_batch_id("open-meteo")
    ingested_at = utc_now()
    output_dir = run_artifact_dir(plan.landing_path, batch_id)
    raw_documents: list[dict[str, Any]] = []
    flattened_rows: list[dict[str, Any]] = []
    used_fallback = False

    geographies = plan.details.get("geographies", [])
    for geography in geographies:
        params = {
            "latitude": geography["latitude"],
            "longitude": geography["longitude"],
            "start_date": plan.details["start_date"],
            "end_date": plan.details["end_date"],
            "daily": ",".join(plan.details["daily_metrics"]),
            "timezone": "UTC",
        }
        try:
            payload = request_json(f"{plan.details['base_url']}{plan.details['endpoint']}", params=params)
            raw_documents.append(
                {
                    "city": geography["city"],
                    "batch_id": batch_id,
                    "ingested_at": ingested_at.isoformat(),
                    "payload": payload,
                }
            )
            daily = payload.get("daily", {})
            dates = daily.get("time", [])
            temperatures = daily.get("temperature_2m_mean", [])
            precipitation = daily.get("precipitation_sum", [])
            flattened_rows.extend(
                [
                    {
                        "weather_date": date_value,
                        "city": geography["city"],
                        "avg_temperature_c": temperatures[index] if index < len(temperatures) else None,
                        "precipitation_mm": precipitation[index] if index < len(precipitation) else None,
                        "ingested_at": ingested_at,
                    }
                    for index, date_value in enumerate(dates)
                ]
            )
        except requests.RequestException:
            LOGGER.warning("Open-Meteo request failed, using local fallback rows", exc_info=True)
            flattened_rows = generate_weather_fallback_rows(plan, ingested_at)
            raw_documents = [
                {
                    "city": row["city"],
                    "batch_id": batch_id,
                    "ingested_at": ingested_at.isoformat(),
                    "payload": row,
                    "fallback": True,
                }
                for row in flattened_rows
            ]
            used_fallback = True
            break

    write_jsonl(output_dir / "weather_raw.jsonl", raw_documents)
    write_run_manifest(
        output_dir,
        source_name="open_meteo",
        batch_id=batch_id,
        row_count=len(flattened_rows),
        metadata={"geographies": [geo["city"] for geo in geographies], "fallback": used_fallback},
    )
    insert_many_documents(mongo_database_name(), plan.raw_collection or "open_meteo_weather_raw", raw_documents)

    dataframe = pd.DataFrame(
        flattened_rows,
        columns=["weather_date", "city", "avg_temperature_c", "precipitation_mm", "ingested_at"],
    )
    loaded_rows = load_dataframe(engine, "open_meteo_weather", dataframe)
    audit_batch(engine, "open_meteo", batch_id, loaded_rows)
    return loaded_rows


def generate_fx_fallback_rows(plan: BatchSourcePlan, ingested_at: datetime) -> list[dict[str, Any]]:
    dates = pd.date_range(plan.details["start_date"], plan.details["end_date"], freq="D")
    rows: list[dict[str, Any]] = []

    for date_value in dates[:14]:
        rows.append(
            {
                "rate_date": date_value.date().isoformat(),
                "base_currency": plan.details["base_currency"],
                "quote_currency": "USD",
                "fx_rate": 1.1 + (date_value.day % 5) / 100,
                "ingested_at": ingested_at,
            }
        )
        rows.append(
            {
                "rate_date": date_value.date().isoformat(),
                "base_currency": plan.details["base_currency"],
                "quote_currency": "BRL",
                "fx_rate": 4.2 + (date_value.day % 7) / 10,
                "ingested_at": ingested_at,
            }
        )

    return rows


def ingest_frankfurter(plan: BatchSourcePlan, engine: Engine) -> int:
    batch_id = build_batch_id("frankfurter")
    ingested_at = utc_now()
    output_dir = run_artifact_dir(plan.landing_path, batch_id)

    request_url = (
        f"{plan.details['base_url']}{plan.details['endpoint']}/"
        f"{plan.details['start_date']}..{plan.details['end_date']}"
    )
    request_params = {
        "from": plan.details["base_currency"],
        "to": ",".join(plan.details["quote_currencies"]),
    }

    raw_documents: list[dict[str, Any]]
    flattened_rows: list[dict[str, Any]]
    used_fallback = False

    try:
        payload = request_json(request_url, params=request_params)
        raw_documents = [
            {
                "batch_id": batch_id,
                "ingested_at": ingested_at.isoformat(),
                "payload": payload,
            }
        ]
        flattened_rows = []
        for rate_date, rates in sorted(payload.get("rates", {}).items()):
            for quote_currency, fx_rate in rates.items():
                flattened_rows.append(
                    {
                        "rate_date": rate_date,
                        "base_currency": plan.details["base_currency"],
                        "quote_currency": quote_currency,
                        "fx_rate": fx_rate,
                        "ingested_at": ingested_at,
                    }
                )
    except requests.RequestException:
        LOGGER.warning("Frankfurter request failed, using local fallback rows", exc_info=True)
        flattened_rows = generate_fx_fallback_rows(plan, ingested_at)
        raw_documents = [
            {
                "batch_id": batch_id,
                "ingested_at": ingested_at.isoformat(),
                "payload": row,
                "fallback": True,
            }
            for row in flattened_rows
        ]
        used_fallback = True

    write_jsonl(output_dir / "fx_rates_raw.jsonl", raw_documents)
    write_run_manifest(
        output_dir,
        source_name="frankfurter",
        batch_id=batch_id,
        row_count=len(flattened_rows),
        metadata={
            "base_currency": plan.details["base_currency"],
            "quote_currencies": plan.details["quote_currencies"],
            "fallback": used_fallback,
        },
    )
    insert_many_documents(mongo_database_name(), plan.raw_collection or "frankfurter_fx_raw", raw_documents)

    dataframe = pd.DataFrame(
        flattened_rows,
        columns=["rate_date", "base_currency", "quote_currency", "fx_rate", "ingested_at"],
    )
    loaded_rows = load_dataframe(engine, "frankfurter_fx_rates", dataframe)
    audit_batch(engine, "frankfurter", batch_id, loaded_rows)
    return loaded_rows


INGESTORS = {
    "olist": ingest_olist,
    "dummyjson": ingest_dummyjson,
    "open_meteo": ingest_open_meteo,
    "frankfurter": ingest_frankfurter,
}


def run(environment: str, source_name: str) -> None:
    engine = create_postgres_engine()
    plans = build_batch_plans(environment)

    LOGGER.info("Starting omnichannel batch ingestion for environment=%s", environment)
    for plan in plans:
        if source_name != "all" and plan.source_name != source_name:
            continue

        try:
            loaded_rows = INGESTORS[plan.source_name](plan, engine)
            LOGGER.info("Source %s ingested %s rows", plan.source_name, loaded_rows)
        except Exception:
            LOGGER.exception("Batch ingestion failed for source=%s", plan.source_name)
            raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch ingestion for omnichannel commerce sources.")
    parser.add_argument("--env", default="dev", help="Configuration environment to load.")
    parser.add_argument(
        "--source",
        default="all",
        choices=["all", "olist", "dummyjson", "open_meteo", "frankfurter"],
        help="Limit ingestion to a single source.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.env, args.source)


if __name__ == "__main__":
    main()
