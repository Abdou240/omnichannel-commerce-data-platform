"""Dateisystem-Hilfsfunktionen fuer JSON/JSONL-Dateien.

Wird von Batch-Ingestion, Streaming-Replay und Quality-Reports verwendet,
um Bronze-Artefakte, Run-Manifeste und Checkpoint-Dateien zu schreiben/lesen.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def ensure_directory(path: Path) -> Path:
    """Erstellt das Verzeichnis (inkl. Eltern) falls noetig und gibt den Pfad zurueck."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Liest eine JSONL-Datei (ein JSON-Objekt pro Zeile) und gibt eine Liste zurueck."""
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Schreibt eine Liste von Dicts als JSONL-Datei (ein JSON-Objekt pro Zeile)."""
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str))
            handle.write("\n")


def write_json(path: Path, payload: Any) -> None:
    """Schreibt ein JSON-Objekt formatiert (indent=2) in eine Datei."""
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)
