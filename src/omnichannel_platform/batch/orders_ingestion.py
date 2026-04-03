from __future__ import annotations

import argparse

from omnichannel_platform.batch.source_plans import BatchSourcePlan, build_olist_plan
from omnichannel_platform.common.logging import get_logger

LOGGER = get_logger(__name__)

def build_plan(environment: str) -> BatchSourcePlan:
    return build_olist_plan(environment)


def run(environment: str) -> None:
    plan = build_plan(environment)
    LOGGER.info("Starting Olist batch ingestion scaffold for environment=%s", environment)
    LOGGER.info(
        "Would extract source=%s tables=%s mode=%s into %s",
        plan.source_name,
        plan.details["tables"],
        plan.details["extract_mode"],
        plan.landing_path,
    )
    LOGGER.info("TODO: implement CSV discovery, batch manifests, watermarking, and idempotent writes")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starter batch ingestion entry point.")
    parser.add_argument("--env", default="dev", help="Configuration environment to load.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.env)


if __name__ == "__main__":
    main()
