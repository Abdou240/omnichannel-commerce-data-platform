"""Testbare Dashboard-Logik (getrennt von Streamlit-UI).

Enthaelt reine Python-Funktionen fuer:
  - DB-Verbindungsaufbau (dashboard_database_url)
  - Schema-Aufloesung (warehouse_schema, raw_schema)
  - Bestellungs-Filterung (apply_order_filters)
  - Tabellenstatistiken (build_table_stats)
  - Commerce- und Session-Insights (derive_commerce_insights, derive_session_insights)

Diese Funktionen werden von dashboard/app.py aufgerufen und in
tests/unit/test_dashboard_logic.py und test_dashboard_insights.py getestet.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from datetime import date

import pandas as pd


def dashboard_database_url() -> str:
    """Baut die PostgreSQL-Connection-URL aus Umgebungsvariablen."""
    return (
        f"postgresql+psycopg://"
        f"{os.getenv('POSTGRES_USER', 'commerce')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'commerce')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'commerce_platform')}"
    )


def warehouse_schema() -> str:
    return os.getenv("DASHBOARD_WAREHOUSE_SCHEMA", os.getenv("POSTGRES_STAGING_SCHEMA", "staging"))


def raw_schema() -> str:
    return os.getenv("DASHBOARD_RAW_SCHEMA", os.getenv("POSTGRES_RAW_SCHEMA", "raw"))


def apply_order_filters(
    dataframe: pd.DataFrame,
    *,
    start_date: date | None,
    end_date: date | None,
    statuses: Sequence[str],
    categories: Sequence[str],
    states: Sequence[str],
    payment_types: Sequence[str],
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    filtered = dataframe.copy()
    mask = pd.Series(True, index=filtered.index)

    if start_date is not None:
        mask &= filtered["order_date"] >= pd.Timestamp(start_date)
    if end_date is not None:
        mask &= filtered["order_date"] <= pd.Timestamp(end_date)
    if statuses:
        mask &= filtered["order_status"].isin(statuses)
    if categories:
        mask &= filtered["product_category_name"].isin(categories)
    if states:
        mask &= filtered["customer_state"].isin(states)
    if payment_types:
        mask &= filtered["payment_type"].isin(payment_types)

    return filtered.loc[mask].copy()


def build_table_stats(named_frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    rows = [
        {
            "Tabelle": table_name,
            "Zeilen": len(frame),
            "Spalten": len(frame.columns),
        }
        for table_name, frame in named_frames.items()
    ]
    return pd.DataFrame(rows)


def derive_commerce_insights(dataframe: pd.DataFrame) -> list[str]:
    """Leitet Commerce-Insights ab: Top-Kategorie, Top-Bundesstaat, Lieferquote."""
    if dataframe.empty:
        return ["Keine Commerce-Daten nach Anwendung der aktuellen Filter."]

    insights: list[str] = []

    top_category = (
        dataframe.groupby("product_category_name")["payment_value_brl"]
        .sum()
        .sort_values(ascending=False)
    )
    if not top_category.empty:
        insights.append(
            f"Top-Kategorie nach Umsatz: {top_category.index[0]} "
            f"mit R$ {top_category.iloc[0]:,.2f}."
        )

    top_state = dataframe["customer_state"].value_counts()
    if not top_state.empty:
        insights.append(
            f"Bundesstaat mit den meisten Bestellungen: {top_state.index[0]} "
            f"mit {int(top_state.iloc[0])} Orders."
        )

    delivered_share = (dataframe["order_status"] == "delivered").mean() * 100
    insights.append(f"Lieferquote im Filterausschnitt: {delivered_share:.1f}%.")
    return insights


def derive_session_insights(dataframe: pd.DataFrame) -> list[str]:
    """Leitet Session-Insights ab: Conversion-Rate, Avg Events, haeufigstes Item."""
    if dataframe.empty:
        return ["Keine Session-Daten vorhanden."]

    insights: list[str] = []
    conversion_share = (dataframe["transaction_count"] > 0).mean() * 100
    insights.append(f"Session-Conversion-Rate: {conversion_share:.1f}%.")

    avg_events = dataframe["event_count"].mean()
    insights.append(f"Durchschnittlich {avg_events:.1f} Events pro Session.")

    top_item = dataframe["sample_item_id"].dropna().astype(str).value_counts()
    if not top_item.empty:
        insights.append(f"Haeufigstes Session-Item: {top_item.index[0]}.")

    return insights
