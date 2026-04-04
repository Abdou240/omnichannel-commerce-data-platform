from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text

from omnichannel_platform.common.logging import get_logger

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class PostgresConnectionSettings:
    host: str
    port: str
    database: str
    user: str
    password: str


def postgres_connection_settings_from_env() -> PostgresConnectionSettings:
    return PostgresConnectionSettings(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "commerce_platform"),
        user=os.getenv("POSTGRES_USER", "commerce"),
        password=os.getenv("POSTGRES_PASSWORD", "commerce"),
    )


def create_postgres_engine():
    settings = postgres_connection_settings_from_env()
    return create_engine(
        "postgresql+psycopg://"
        f"{settings.user}:{settings.password}@{settings.host}:{settings.port}/{settings.database}",
        connect_args={"connect_timeout": 5},
        pool_pre_ping=True,
    )


def ensure_postgres_is_reachable(
    engine, settings: PostgresConnectionSettings | None = None
) -> None:
    active_settings = settings or postgres_connection_settings_from_env()

    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:
        raise SystemExit(
            "PostgreSQL ist nicht erreichbar.\n"
            f"Verbindung: host={active_settings.host} port={active_settings.port} "
            f"db={active_settings.database} user={active_settings.user}\n\n"
            "Starte zuerst die lokale Datenbank, zum Beispiel mit:\n"
            "  docker compose up -d postgres\n"
            "  docker compose ps postgres\n"
            "  docker compose exec postgres pg_isready "
            f"-U {active_settings.user} -d {active_settings.database}\n\n"
            "Wenn du kein Docker-PostgreSQL nutzt, pruefe bitte deine "
            "POSTGRES_* Werte in .env oder in deiner Shell."
        ) from exc


def optional_mongo_collection(database_name: str, collection_name: str):
    try:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
    except ModuleNotFoundError:
        return None

    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(uri, serverSelectionTimeoutMS=2000)

    try:
        client.admin.command("ping")
    except PyMongoError as exc:
        LOGGER.warning(
            "MongoDB ist nicht erreichbar; Mongo-Persist wird uebersprungen (%s)",
            exc,
        )
        return None

    return client[database_name][collection_name]


def insert_many_documents(
    database_name: str, collection_name: str, documents: list[dict[str, Any]]
) -> int:
    if not documents:
        return 0

    collection = optional_mongo_collection(database_name, collection_name)
    if collection is None:
        return 0

    try:
        collection.insert_many(documents, ordered=False)
    except Exception as exc:
        LOGGER.warning(
            "MongoDB-Insert in %s.%s fehlgeschlagen; Persist wird uebersprungen (%s)",
            database_name,
            collection_name,
            exc,
        )
        return 0

    return len(documents)
