import pytest

from omnichannel_platform.common.clients import (
    PostgresConnectionSettings,
    ensure_postgres_is_reachable,
    insert_many_documents,
)


class _SuccessfulConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, _statement) -> int:
        return 1


class _SuccessfulEngine:
    def connect(self) -> _SuccessfulConnection:
        return _SuccessfulConnection()


class _FailingConnection:
    def __enter__(self):
        raise ConnectionError("connection refused")

    def __exit__(self, exc_type, exc, traceback):
        return False


class _FailingEngine:
    def connect(self) -> _FailingConnection:
        return _FailingConnection()


class _FailingCollection:
    def insert_many(self, _documents, ordered: bool = False) -> None:
        raise RuntimeError("mongo down")


def test_ensure_postgres_is_reachable_allows_successful_connection() -> None:
    ensure_postgres_is_reachable(_SuccessfulEngine())


def test_ensure_postgres_is_reachable_raises_helpful_message() -> None:
    settings = PostgresConnectionSettings(
        host="localhost",
        port="5432",
        database="commerce_platform",
        user="commerce",
        password="commerce",
    )

    with pytest.raises(SystemExit) as exc_info:
        ensure_postgres_is_reachable(_FailingEngine(), settings)

    message = str(exc_info.value)
    assert "PostgreSQL ist nicht erreichbar." in message
    assert "docker compose up -d postgres" in message
    assert "pg_isready -U commerce -d commerce_platform" in message


def test_insert_many_documents_skips_when_mongo_insert_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "omnichannel_platform.common.clients.optional_mongo_collection",
        lambda database_name, collection_name: _FailingCollection(),
    )

    inserted_count = insert_many_documents(
        "commerce_raw",
        "open_food_facts_products_raw",
        [{"product_code": "123"}],
    )

    assert inserted_count == 0
