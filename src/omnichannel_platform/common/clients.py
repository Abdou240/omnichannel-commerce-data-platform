from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine


def create_postgres_engine():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "commerce_platform")
    user = os.getenv("POSTGRES_USER", "commerce")
    password = os.getenv("POSTGRES_PASSWORD", "commerce")
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}")


def optional_mongo_collection(database_name: str, collection_name: str):
    try:
        from pymongo import MongoClient
    except ModuleNotFoundError:
        return None

    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
    return client[database_name][collection_name]


def insert_many_documents(database_name: str, collection_name: str, documents: list[dict[str, Any]]) -> int:
    if not documents:
        return 0

    collection = optional_mongo_collection(database_name, collection_name)
    if collection is None:
        return 0

    collection.insert_many(documents, ordered=False)
    return len(documents)
