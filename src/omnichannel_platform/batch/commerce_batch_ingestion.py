from __future__ import annotations

import argparse

from omnichannel_platform.batch.source_plans import BatchSourcePlan, build_batch_plans
from omnichannel_platform.common.logging import get_logger

LOGGER = get_logger(__name__)


def log_plan(plan: BatchSourcePlan) -> None:
    LOGGER.info(
        "Batch source=%s kind=%s landing=%s raw_schema=%s raw_collection=%s",
        plan.source_name,
        plan.source_kind,
        plan.landing_path,
        plan.raw_schema or "n/a",
        plan.raw_collection or "n/a",
    )
    for key, value in plan.details.items():
        LOGGER.info("  %s=%s", key, value)


def run(environment: str, source_name: str) -> None:
    plans = build_batch_plans(environment)

    LOGGER.info("Planning omnichannel batch ingestion for environment=%s", environment)
    for plan in plans:
        if source_name != "all" and plan.source_name != source_name:
            continue
        log_plan(plan)

    LOGGER.info(
        "TODO: implement Olist snapshot loading, DummyJSON API pulls, "
        "Open-Meteo enrichment fetches, and Frankfurter FX extraction"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starter batch planner for omnichannel commerce sources.")
    parser.add_argument("--env", default="dev", help="Configuration environment to load.")
    parser.add_argument(
        "--source",
        default="all",
        choices=["all", "olist", "dummyjson", "open_meteo", "frankfurter"],
        help="Limit planning output to a single batch source.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.env, args.source)


if __name__ == "__main__":
    main()

