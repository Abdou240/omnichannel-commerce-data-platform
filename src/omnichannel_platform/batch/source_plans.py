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


def _source_config(environment: str, source_name: str) -> dict[str, Any]:
    settings = load_settings(environment)
    return dict(settings["sources"][source_name])


def build_olist_plan(environment: str) -> BatchSourcePlan:
    source = _source_config(environment, "olist")
    return BatchSourcePlan(
        source_name="olist",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=None,
        raw_schema=source["raw_schema"],
        details=source,
    )


def build_open_food_facts_plan(environment: str) -> BatchSourcePlan:
    source = _source_config(environment, "open_food_facts")
    return BatchSourcePlan(
        source_name="open_food_facts",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=source["raw_collection"],
        raw_schema="raw",
        details=source,
    )


def build_open_meteo_plan(environment: str) -> BatchSourcePlan:
    source = _source_config(environment, "open_meteo")
    return BatchSourcePlan(
        source_name="open_meteo",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=source["raw_collection"],
        raw_schema="raw",
        details=source,
    )


def build_frankfurter_plan(environment: str) -> BatchSourcePlan:
    source = _source_config(environment, "frankfurter")
    return BatchSourcePlan(
        source_name="frankfurter",
        source_kind=source["source_kind"],
        landing_path=source["landing_path"],
        raw_collection=source["raw_collection"],
        raw_schema="raw",
        details=source,
    )


def build_batch_plans(environment: str) -> list[BatchSourcePlan]:
    return [
        build_olist_plan(environment),
        build_open_food_facts_plan(environment),
        build_open_meteo_plan(environment),
        build_frankfurter_plan(environment),
    ]
