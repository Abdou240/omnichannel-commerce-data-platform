from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str))
            handle.write("\n")


def write_json(path: Path, payload: Any) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)
