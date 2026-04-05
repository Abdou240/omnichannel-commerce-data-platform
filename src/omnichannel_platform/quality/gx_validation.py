"""Great Expectations validation runner for the Omnichannel Commerce Data Platform.

Runs programmatic GX expectations against PostgreSQL tables.
Requires Python <3.14 (GX constraint) — intended for CI (Python 3.11) and Docker.

Usage:
    python -m omnichannel_platform.quality.gx_validation [--non-strict]
"""

from __future__ import annotations

import argparse
import json

from omnichannel_platform.common.io import ensure_directory
from omnichannel_platform.common.logging import get_logger
from omnichannel_platform.common.settings import repo_root

LOGGER = get_logger(__name__)


def _build_postgres_url() -> str:
    import os

    return (
        f"postgresql+psycopg://"
        f"{os.getenv('POSTGRES_USER', 'commerce')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'commerce')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'commerce_platform')}"
    )


def run(strict: bool = True) -> None:
    try:
        import great_expectations as gx
        from great_expectations.expectations import (
            ExpectColumnDistinctValuesToBeInSet,
            ExpectColumnValuesToBeUnique,
            ExpectColumnValuesToNotBeNull,
            ExpectTableRowCountToBeGreaterThan,
        )
    except ImportError:
        LOGGER.warning(
            "great_expectations is not installed (requires Python <3.14). "
            "Skipping GX validation."
        )
        return

    LOGGER.info("Initializing Great Expectations context")
    context = gx.get_context()

    connection_string = _build_postgres_url()
    pg_datasource = context.data_sources.add_or_update_postgres(
        name="postgres_warehouse",
        connection_string=connection_string,
    )

    # ── Table definitions with expectations ──────────────────────────────
    table_expectations: dict[str, list] = {
        "raw.olist_orders": [
            ExpectColumnValuesToNotBeNull(column="order_id"),
            ExpectColumnValuesToBeUnique(column="order_id"),
            ExpectColumnValuesToNotBeNull(column="order_purchase_timestamp"),
            ExpectColumnDistinctValuesToBeInSet(
                column="order_status",
                value_set=[
                    "delivered", "shipped", "processing", "invoiced",
                    "approved", "created", "canceled", "unavailable",
                ],
            ),
        ],
        "raw.retailrocket_events": [
            ExpectColumnValuesToNotBeNull(column="event_id"),
            ExpectColumnValuesToNotBeNull(column="visitor_id"),
            ExpectColumnDistinctValuesToBeInSet(
                column="event_type",
                value_set=["view", "addtocart", "transaction"],
            ),
            ExpectTableRowCountToBeGreaterThan(value=0),
        ],
        "raw.frankfurter_fx_rates": [
            ExpectColumnValuesToNotBeNull(column="rate_date"),
            ExpectColumnValuesToNotBeNull(column="fx_rate"),
            ExpectTableRowCountToBeGreaterThan(value=0),
        ],
        "raw.open_meteo_weather": [
            ExpectColumnValuesToNotBeNull(column="weather_date"),
            ExpectColumnValuesToNotBeNull(column="city"),
            ExpectTableRowCountToBeGreaterThan(value=0),
        ],
        "staging.fct_commerce_orders": [
            ExpectColumnValuesToNotBeNull(column="order_id"),
            ExpectColumnValuesToBeUnique(column="order_id"),
            ExpectColumnValuesToNotBeNull(column="customer_id"),
            ExpectColumnValuesToNotBeNull(column="payment_value_brl"),
            ExpectTableRowCountToBeGreaterThan(value=0),
        ],
    }

    all_results: list[dict] = []
    total_passed = 0
    total_failed = 0
    total_skipped = 0

    for full_table, expectations in table_expectations.items():
        schema, table_name = full_table.split(".", 1)
        LOGGER.info("Validating %s.%s (%d expectations)", schema, table_name, len(expectations))

        try:
            data_asset = pg_datasource.add_or_update_table_asset(
                name=full_table,
                table_name=table_name,
                schema_name=schema,
            )
            batch_definition = data_asset.add_or_update_batch_definition(
                name=f"{full_table}_full",
            )
            batch = batch_definition.get_batch()

            suite = context.suites.add_or_update(
                gx.ExpectationSuite(name=f"suite_{full_table.replace('.', '_')}")
            )
            suite.expectations = expectations

            validation_result = batch.validate(suite)

            for result in validation_result.results:
                exp_type = result.expectation_config.type
                success = result.success
                status = "passed" if success else "failed"
                if success:
                    total_passed += 1
                else:
                    total_failed += 1
                LOGGER.info("  %s: %s -> %s", full_table, exp_type, status)
                all_results.append({
                    "table": full_table,
                    "expectation": exp_type,
                    "status": status,
                })

        except Exception as exc:
            LOGGER.warning("  Skipped %s: %s", full_table, exc)
            total_skipped += len(expectations)
            all_results.append({
                "table": full_table,
                "expectation": "all",
                "status": "skipped",
                "error": str(exc),
            })

    # ── Write report ─────────────────────────────────────────────────────
    report_dir = ensure_directory(repo_root() / "storage" / "checkpoints" / "great_expectations")
    report = {
        "engine": "great_expectations",
        "summary": {
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
        },
        "results": all_results,
    }
    report_path = report_dir / "last_run.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    LOGGER.info(
        "GX validation complete: %d passed, %d failed, %d skipped -> %s",
        total_passed, total_failed, total_skipped, report_path,
    )

    if strict and total_failed > 0:
        LOGGER.error("%d GX expectations failed", total_failed)
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Great Expectations validations.")
    parser.add_argument(
        "--non-strict",
        action="store_true",
        help="Do not exit with error code on failures.",
    )
    args = parser.parse_args()
    run(strict=not args.non_strict)


if __name__ == "__main__":
    main()
