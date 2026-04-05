"""Convenience-Wrapper fuer Olist-only Batch-Ingestion.

Alternativer Einstiegspunkt, der nur die Olist-Quelle verarbeitet.
Aequivalent zu: python -m omnichannel_platform.batch.commerce_batch_ingestion --source olist
"""

from __future__ import annotations

import argparse

from omnichannel_platform.batch.commerce_batch_ingestion import run as run_batch_ingestion
from omnichannel_platform.common.logging import get_logger

LOGGER = get_logger(__name__)


def run(environment: str) -> None:
    """Fuehrt nur die Olist-Batch-Ingestion aus (delegiert an commerce_batch_ingestion)."""
    LOGGER.info("Running Olist-only batch ingestion wrapper for environment=%s", environment)
    run_batch_ingestion(environment, "olist")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Olist-only batch ingestion.")
    parser.add_argument("--env", default="dev", help="Configuration environment to load.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.env)


if __name__ == "__main__":
    main()
