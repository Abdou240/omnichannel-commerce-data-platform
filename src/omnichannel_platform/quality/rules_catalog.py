from __future__ import annotations

from omnichannel_platform.common.logging import get_logger
from omnichannel_platform.common.settings import repo_root

LOGGER = get_logger(__name__)


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


def run() -> None:
    assets = list_quality_assets()
    LOGGER.info("Discovered %s quality contract files", len(assets["contracts"]))
    for path in assets["contracts"]:
        LOGGER.info("  contract=%s", path)

    LOGGER.info("Discovered %s quality expectation files", len(assets["expectations"]))
    for path in assets["expectations"]:
        LOGGER.info("  expectation=%s", path)

    LOGGER.info(
        "TODO: wire these contracts and SQL checks into dbt tests, Kestra validation, "
        "or a dedicated quality runner"
    )


def main() -> None:
    run()


if __name__ == "__main__":
    main()
