from __future__ import annotations

import argparse
from dataclasses import dataclass

from omnichannel_platform.common.logging import get_logger
from omnichannel_platform.common.settings import load_settings

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class WarehouseLayerPlan:
    layer_name: str
    assets: list[str]
    warehouse_engine: str


def build_layer_plans(environment: str) -> list[WarehouseLayerPlan]:
    settings = load_settings(environment)
    local_engine = settings["warehouse"]["local"]["engine"]

    return [
        WarehouseLayerPlan(
            layer_name="raw",
            warehouse_engine=local_engine,
            assets=[
                "raw.olist_orders",
                "raw.olist_order_items",
                "raw.olist_customers",
                "raw.olist_products",
                "raw.olist_order_payments",
                "raw.retailrocket_events",
                "raw.open_food_facts_products",
                "raw.open_meteo_weather",
                "raw.frankfurter_fx_rates",
            ],
        ),
        WarehouseLayerPlan(
            layer_name="staging",
            warehouse_engine=local_engine,
            assets=[
                "stg_olist_orders",
                "stg_olist_order_items",
                "stg_olist_customers",
                "stg_olist_products",
                "stg_olist_order_payments",
                "stg_retailrocket_events",
                "stg_open_food_facts_products",
                "stg_open_meteo_weather",
                "stg_frankfurter_fx_rates",
            ],
        ),
        WarehouseLayerPlan(
            layer_name="marts",
            warehouse_engine=local_engine,
            assets=[
                "int_orders_with_context",
                "int_retailrocket_sessions",
                "fct_commerce_orders",
                "fct_retailrocket_sessions",
                "dim_products",
            ],
        ),
    ]


def run(environment: str) -> None:
    LOGGER.info("Planning raw-to-staging-to-marts warehouse layers for environment=%s", environment)
    for plan in build_layer_plans(environment):
        LOGGER.info("Layer=%s engine=%s", plan.layer_name, plan.warehouse_engine)
        for asset in plan.assets:
            LOGGER.info("  asset=%s", asset)

    LOGGER.info(
        "Warehouse foundations are now wired to raw source tables and starter dbt transforms. "
        "TODO: extend marts with production business semantics and incremental models."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starter warehouse layer planner.")
    parser.add_argument("--env", default="dev", help="Configuration environment to load.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.env)


if __name__ == "__main__":
    main()
