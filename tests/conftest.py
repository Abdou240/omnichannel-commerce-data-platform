from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_orders(fixtures_dir: Path) -> list[dict]:
    with (fixtures_dir / "sample_orders.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def sample_clickstream_events(fixtures_dir: Path) -> list[dict]:
    events: list[dict] = []
    with (fixtures_dir / "sample_clickstream_events.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events
