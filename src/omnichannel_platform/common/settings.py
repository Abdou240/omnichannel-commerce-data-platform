"""Konfigurationsmanagement fuer die Omnichannel Commerce Data Platform.

Laedt die zentrale Konfiguration aus config/base.yaml und merged optional
environment-spezifische Overrides (config/dev.yaml, config/prod.yaml).
Wird von allen Layern (Batch, Streaming, Warehouse, Quality) verwendet.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    """Gibt den absoluten Pfad zum Repository-Root zurueck (3 Ebenen ueber dieser Datei)."""
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict[str, Any]:
    """Liest eine YAML-Datei und gibt den Inhalt als Dictionary zurueck."""
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merged zwei Dicts rekursiv: Override-Werte ueberschreiben Base-Werte.

    Verschachtelte Dicts werden Ebene fuer Ebene gemerged, einfache Werte
    werden direkt ueberschrieben. Wird genutzt, um dev.yaml/prod.yaml
    auf base.yaml zu legen.
    """
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def current_environment() -> str:
    """Liest die aktive Umgebung aus der Umgebungsvariable ENVIRONMENT (Default: 'dev')."""
    return os.getenv("ENVIRONMENT", "dev")


def load_settings(environment: str | None = None) -> dict[str, Any]:
    """Laedt die vollstaendige Konfiguration fuer die angegebene Umgebung.

    1. Liest config/base.yaml als Basis
    2. Merged optional config/<environment>.yaml darueber
    3. Setzt runtime.environment auf den aktiven Umgebungsnamen
    """
    env_name = environment or current_environment()
    root = repo_root()

    # Basiskonfiguration laden (alle Quellen, Warehouse, Orchestrierung)
    base = load_yaml(root / "config" / "base.yaml")
    override_path = root / "config" / f"{env_name}.yaml"

    # Environment-spezifische Overrides mergen (z.B. dev.yaml -> lokale Kafka-Broker)
    if override_path.exists():
        base = deep_merge(base, load_yaml(override_path))

    # Runtime-Block mit aktiver Umgebung anreichern
    runtime = dict(base.get("runtime", {}))
    runtime["environment"] = env_name
    base["runtime"] = runtime
    return base
