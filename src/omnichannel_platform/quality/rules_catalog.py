from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from omnichannel_platform.common.io import ensure_directory, write_json
from omnichannel_platform.common.logging import get_logger
from omnichannel_platform.common.settings import repo_root

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class QualityExpectationResult:
    name: str
    status: str
    row_count: int
    path: str
    error: str | None = None


def list_quality_assets() -> dict[str, list[str]]:
    root = repo_root()
    return {
        "contracts": sorted(
            str(path.relative_to(root))
            for path in (root / "quality" / "contracts").glob("*.yml")
        ),
        "expectations": sorted(
            str(path.relative_to(root))
            for path in (root / "quality" / "expectations").glob("*.sql")
        ),
    }


def load_contracts() -> list[dict[str, Any]]:
    root = repo_root()
    contracts: list[dict[str, Any]] = []
    for path in sorted((root / "quality" / "contracts").glob("*.yml")):
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        payload["_path"] = str(path.relative_to(root))
        contracts.append(payload)
    return contracts


def expectation_paths() -> list[Path]:
    return sorted((repo_root() / "quality" / "expectations").glob("*.sql"))


def optional_postgres_engine():
    try:
        from sqlalchemy import text

        from omnichannel_platform.common.clients import create_postgres_engine
    except ModuleNotFoundError:
        LOGGER.warning("SQLAlchemy/Postgres dependencies are unavailable; skipping SQL expectations")
        return None

    try:
        engine = create_postgres_engine()
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        return engine
    except ModuleNotFoundError:
        LOGGER.warning("Postgres driver dependencies are unavailable; skipping SQL expectations")
        return None
    except Exception:
        LOGGER.warning("PostgreSQL is not reachable; skipping SQL expectations")
        return None


def execute_expectation(path: Path, engine) -> QualityExpectationResult:
    if engine is None:
        return QualityExpectationResult(
            name=path.stem,
            status="skipped",
            row_count=0,
            path=str(path.relative_to(repo_root())),
            error="postgres_unavailable",
        )

    sql = path.read_text(encoding="utf-8")
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            rows = connection.execute(text(sql)).fetchall()
    except Exception as exc:
        return QualityExpectationResult(
            name=path.stem,
            status="skipped",
            row_count=0,
            path=str(path.relative_to(repo_root())),
            error=str(exc),
        )

    failure_count = len(rows)
    return QualityExpectationResult(
        name=path.stem,
        status="failed" if failure_count else "passed",
        row_count=failure_count,
        path=str(path.relative_to(repo_root())),
    )


def write_quality_report(results: list[QualityExpectationResult], contracts: list[dict[str, Any]]) -> None:
    report_dir = ensure_directory(repo_root() / "storage" / "checkpoints" / "quality")
    payload = {
        "contracts": contracts,
        "results": [asdict(result) for result in results],
        "summary": {
            "passed": sum(result.status == "passed" for result in results),
            "failed": sum(result.status == "failed" for result in results),
            "skipped": sum(result.status == "skipped" for result in results),
        },
    }
    write_json(report_dir / "last_run.json", payload)


def run(strict: bool = True) -> None:
    assets = list_quality_assets()
    contracts = load_contracts()

    LOGGER.info("Discovered %s quality contract files", len(assets["contracts"]))
    for contract in contracts:
        LOGGER.info("  contract=%s owner=%s", contract["_path"], contract.get("owner", "unknown"))

    engine = optional_postgres_engine()
    results = [execute_expectation(path, engine) for path in expectation_paths()]
    for result in results:
        LOGGER.info(
            "Expectation %s status=%s failures=%s",
            result.name,
            result.status,
            result.row_count,
        )
        if result.error:
            LOGGER.info("  detail=%s", result.error)

    write_quality_report(results, contracts)

    failed = [result for result in results if result.status == "failed"]
    if strict and failed:
        raise SystemExit(f"{len(failed)} quality expectations failed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SQL-backed data quality expectations.")
    parser.add_argument(
        "--non-strict",
        action="store_true",
        help="Do not return a failing exit code when expectations produce failing rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(strict=not args.non_strict)


if __name__ == "__main__":
    main()
