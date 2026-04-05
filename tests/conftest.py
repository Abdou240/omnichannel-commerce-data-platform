"""Pytest-Konfigurations- und Fixture-Datei.

Stellt gemeinsame Test-Fixtures bereit:
  - fixtures_dir: Pfad zum tests/fixtures/-Verzeichnis
  - sample_orders: Beispiel-Bestellungen aus sample_orders.json
  - sample_clickstream_events: Beispiel-Events aus sample_clickstream_events.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Gibt den Pfad zum tests/fixtures/-Verzeichnis zurueck."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_orders(fixtures_dir: Path) -> list[dict]:
    """Laedt Beispiel-Bestellungen aus tests/fixtures/sample_orders.json."""
    with (fixtures_dir / "sample_orders.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def sample_clickstream_events(fixtures_dir: Path) -> list[dict]:
    """Laedt Beispiel-Events aus tests/fixtures/sample_clickstream_events.jsonl."""
    events: list[dict] = []
    with (fixtures_dir / "sample_clickstream_events.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events
