from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from omnichannel_platform.common.settings import load_settings


@dataclass(frozen=True)
class BatchSourcePlan:
    source_name: str
    source_kind: str
    landing_path: str
    raw_collection: str | None
    raw_schema: str | None
    details: dict[str, Any]


def build_olist_plan(environment: str) -> BatchSourcePlan:
    settings = load_settings(environment)
    source = settings["sources"]["olist"]
    return BatchSourcePlan(
        source_name="olist",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=None,
        raw_schema=source["raw_schema"],
        details={
            "dataset": source["dataset"],
            "tables": source["tables"],
            "extract_mode": source["extract_mode"],
        },
    )


def build_dummyjson_plan(environment: str) -> BatchSourcePlan:
    settings = load_settings(environment)
    source = settings["sources"]["dummyjson"]
    return BatchSourcePlan(
        source_name="dummyjson",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=source["raw_collection"],
        raw_schema="raw",
        details={
            "base_url": source["base_url"],
            "endpoint": source["endpoint"],
        },
    )


def build_open_meteo_plan(environment: str) -> BatchSourcePlan:
    settings = load_settings(environment)
    source = settings["sources"]["open_meteo"]
    return BatchSourcePlan(
        source_name="open_meteo",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=source["raw_collection"],
        raw_schema="raw",
        details={
            "base_url": source["base_url"],
            "endpoint": source["endpoint"],
            "daily_metrics": source["daily_metrics"],
        },
    )


def build_frankfurter_plan(environment: str) -> BatchSourcePlan:
    settings = load_settings(environment)
    source = settings["sources"]["frankfurter"]
    return BatchSourcePlan(
        source_name="frankfurter",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=source["raw_collection"],
        raw_schema="raw",
        details={
            "base_url": source["base_url"],
            "endpoint": source["endpoint"],
            "base_currency": source["base_currency"],
            "quote_currencies": source["quote_currencies"],
        },
    )


def build_batch_plans(environment: str) -> list[BatchSourcePlan]:
    return [
        build_olist_plan(environment),
        build_dummyjson_plan(environment),
        build_open_meteo_plan(environment),
        build_frankfurter_plan(environment),
    ]

