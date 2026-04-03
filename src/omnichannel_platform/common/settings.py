from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def current_environment() -> str:
    return os.getenv("ENVIRONMENT", "dev")


def load_settings(environment: str | None = None) -> dict[str, Any]:
    env_name = environment or current_environment()
    root = repo_root()

    base = load_yaml(root / "config" / "base.yaml")
    override_path = root / "config" / f"{env_name}.yaml"

    if override_path.exists():
        base = deep_merge(base, load_yaml(override_path))

    runtime = dict(base.get("runtime", {}))
    runtime["environment"] = env_name
    base["runtime"] = runtime
    return base

