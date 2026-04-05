"""Datenbank-Zugriff fuer die FastAPI-API.

Stellt eine gecachte SQLAlchemy-Engine bereit und bietet Hilfsfunktionen
fuer SQL-Abfragen (query_dataframe) und Health-Checks (check_database).
Schema-Namen werden per Umgebungsvariable konfiguriert.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _validate_identifier(name: str) -> str:
    """Ensure *name* is a safe SQL identifier (schema/table) to prevent injection."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def _database_url() -> str:
    return (
        f"postgresql+psycopg://"
        f"{os.getenv('POSTGRES_USER', 'commerce')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'commerce')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'commerce_platform')}"
    )


def warehouse_schema() -> str:
    return _validate_identifier(os.getenv("DASHBOARD_WAREHOUSE_SCHEMA", "staging"))


def raw_schema() -> str:
    return _validate_identifier(os.getenv("DASHBOARD_RAW_SCHEMA", "raw"))


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(
        _database_url(),
        connect_args={"connect_timeout": 5},
        pool_pre_ping=True,
    )


def _reset_engine() -> None:
    """Clear the cached engine — useful for test teardown."""
    get_engine.cache_clear()


def check_database() -> str:
    """Return 'ok' if database is reachable, otherwise raise."""
    with get_engine().connect() as conn:
        conn.execute(text("select 1"))
    return "ok"


def query_dataframe(sql: str, params: Mapping[str, Any] | None = None) -> pd.DataFrame:
    return pd.read_sql(text(sql), get_engine(), params=dict(params or {}))
