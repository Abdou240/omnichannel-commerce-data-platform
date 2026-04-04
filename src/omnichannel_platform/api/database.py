"""Shared database engine for the FastAPI application."""

from __future__ import annotations

import os
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


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
    return os.getenv("DASHBOARD_WAREHOUSE_SCHEMA", "staging")


def raw_schema() -> str:
    return os.getenv("DASHBOARD_RAW_SCHEMA", "raw")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(
        _database_url(),
        connect_args={"connect_timeout": 5},
        pool_pre_ping=True,
    )


def check_database() -> str:
    """Return 'ok' if database is reachable, otherwise raise."""
    with get_engine().connect() as conn:
        conn.execute(text("select 1"))
    return "ok"


def query_dataframe(sql: str, params: Mapping[str, Any] | None = None) -> pd.DataFrame:
    return pd.read_sql(text(sql), get_engine(), params=dict(params or {}))
