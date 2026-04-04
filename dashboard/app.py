"""Streamlit dashboard for the Omnichannel Commerce Data Platform.

Supports two data-loading modes:
  1. API mode (API_BASE_URL is set): fetches data from the FastAPI REST API
  2. Direct DB mode (default): reads from PostgreSQL via SQLAlchemy
"""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from omnichannel_platform.dashboard.logic import (
    apply_order_filters,
    build_table_stats,
    dashboard_database_url,
    derive_commerce_insights,
    derive_session_insights,
    raw_schema,
    warehouse_schema,
)

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(
    page_title="Omnichannel Commerce Data Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(241, 196, 15, 0.08), transparent 32%),
            linear-gradient(180deg, #f6f4ef 0%, #ffffff 30%, #f9fafb 100%);
    }
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
    .dashboard-hero {
        padding: 1.2rem 1.4rem;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.82);
        backdrop-filter: blur(8px);
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

WAREHOUSE_SCHEMA = warehouse_schema()
RAW_SCHEMA = raw_schema()


@st.cache_resource
def get_engine():
    from sqlalchemy import create_engine

    return create_engine(dashboard_database_url())


@st.cache_data(ttl=300)
def _load_from_db(query: str) -> pd.DataFrame:
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def _load_from_api(endpoint: str) -> pd.DataFrame:
    import requests

    resp = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return pd.DataFrame(data) if data else pd.DataFrame()
    return pd.DataFrame()


@st.cache_data(ttl=300)
def _load_api_json(endpoint: str) -> dict:
    import requests

    resp = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else {}


def load_dataframe(query: str, api_endpoint: str | None = None) -> pd.DataFrame:
    if API_BASE_URL and api_endpoint:
        return _load_from_api(api_endpoint)
    return _load_from_db(query)


def load_datasets() -> dict[str, pd.DataFrame]:
    pipeline_payload = _load_api_json("/api/v1/pipeline/status") if API_BASE_URL else {}

    return {
        "orders": load_dataframe(
            f"select * from {WAREHOUSE_SCHEMA}.fct_commerce_orders",
            "/api/v1/orders?limit=5000",
        ),
        "sessions": load_dataframe(
            f"select * from {WAREHOUSE_SCHEMA}.fct_retailrocket_sessions",
            "/api/v1/sessions?limit=5000",
        ),
        "products": load_dataframe(
            f"select * from {WAREHOUSE_SCHEMA}.dim_products",
            "/api/v1/products?limit=5000",
        ),
        "weather": load_dataframe(
            f"select * from {RAW_SCHEMA}.open_meteo_weather",
            "/api/v1/weather?limit=5000",
        ),
        "fx": load_dataframe(
            f"select * from {RAW_SCHEMA}.frankfurter_fx_rates",
            "/api/v1/fx-rates?limit=5000",
        ),
        "audit": (
            pd.DataFrame(pipeline_payload.get("audit", []))
            if API_BASE_URL
            else load_dataframe(
                f"select * from {RAW_SCHEMA}.ingestion_audit order by loaded_at desc"
            )
        ),
        "table_stats": (
            pd.DataFrame(pipeline_payload.get("tables", [])) if API_BASE_URL else pd.DataFrame()
        ),
    }


def parse_dates(dataframes: dict[str, pd.DataFrame]) -> None:
    orders = dataframes["orders"]
    if not orders.empty:
        orders["order_date"] = pd.to_datetime(orders["order_date"])
        orders["order_purchase_ts"] = pd.to_datetime(orders["order_purchase_ts"])

    sessions = dataframes["sessions"]
    if not sessions.empty:
        sessions["session_start_ts"] = pd.to_datetime(sessions["session_start_ts"])
        sessions["session_end_ts"] = pd.to_datetime(sessions["session_end_ts"])
        if "sample_item_id" not in sessions.columns:
            sessions["sample_item_id"] = None

    weather = dataframes["weather"]
    if not weather.empty:
        weather["weather_date"] = pd.to_datetime(weather["weather_date"])

    fx = dataframes["fx"]
    if not fx.empty:
        fx["rate_date"] = pd.to_datetime(fx["rate_date"])

    products = dataframes["products"]
    if (
        not products.empty
        and "product_category_name" not in products.columns
        and "category" in products.columns
    ):
        products["product_category_name"] = products["category"]

    audit = dataframes["audit"]
    if not audit.empty and "loaded_at" in audit.columns:
        audit["loaded_at"] = pd.to_datetime(audit["loaded_at"])

    table_stats = dataframes["table_stats"]
    if not table_stats.empty and {"table_name", "row_count", "column_count"}.issubset(
        table_stats.columns
    ):
        dataframes["table_stats"] = table_stats.rename(
            columns={
                "table_name": "Tabelle",
                "row_count": "Zeilen",
                "column_count": "Spalten",
            }
        )


def selected_date_window(min_date: date, max_date: date) -> tuple[date | None, date | None]:
    value = st.sidebar.date_input(
        "Zeitraum",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(value, tuple) and len(value) == 2:
        return value[0], value[1]
    if isinstance(value, list) and len(value) == 2:
        return value[0], value[1]
    if isinstance(value, date):
        return value, value
    return None, None


def render_kpi_metrics(filtered_orders: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bestellungen", f"{len(filtered_orders):,}")
    col2.metric("Umsatz (BRL)", f"R$ {filtered_orders['payment_value_brl'].sum():,.2f}")
    col3.metric(
        "Durchschn. Bestellwert",
        f"R$ {filtered_orders['payment_value_brl'].mean() if not filtered_orders.empty else 0:,.2f}",
    )
    col4.metric("Artikel gesamt", f"{int(filtered_orders['item_count'].sum()):,}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Kunden (unique)", f"{filtered_orders['customer_id'].nunique():,}")
    col6.metric("Umsatz (USD)", f"$ {filtered_orders['payment_value_usd'].fillna(0).sum():,.2f}")
    col7.metric(
        "Durchschn. Fracht",
        f"R$ {filtered_orders['freight_value'].mean() if not filtered_orders.empty else 0:,.2f}",
    )
    delivered_share = (
        (filtered_orders["order_status"] == "delivered").mean() * 100
        if not filtered_orders.empty
        else 0
    )
    col8.metric("Lieferquote", f"{delivered_share:.1f}%")


def main() -> None:
    st.markdown(
        """
        <div class="dashboard-hero">
            <h1>Omnichannel Commerce Data Platform</h1>
            <p>
                End-to-end Uebersicht ueber Batch, Streaming, Warehouse, Data Quality und
                Commerce-Insights auf Basis realer Quellen und lokaler Starter-Pipelines.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode_label = "API-Modus" if API_BASE_URL else "Direkter DB-Modus"
    st.caption(
        f"Datenzugriff: {mode_label}"
        + (f" via `{API_BASE_URL}`" if API_BASE_URL else " via SQLAlchemy/PostgreSQL")
    )

    try:
        dataframes = load_datasets()
    except Exception as exc:
        st.error(f"Datenbankverbindung fehlgeschlagen: {exc}")
        st.info(
            "Bitte zuerst den Plattform-Stack und die Pipeline starten:\n\n"
            "```bash\n"
            "docker compose up -d\n"
            "docker compose up -d api\n"
            "make run-batch\n"
            "make run-streaming\n"
            "make run-warehouse\n"
            "make run-quality\n"
            "```"
        )
        return

    parse_dates(dataframes)
    orders = dataframes["orders"]

    st.sidebar.title("Navigation")
    pages = [
        "Commerce KPIs",
        "Zeitliche Trends",
        "Kategorien & Regionen",
        "Produkt-Analyse",
        "Session-Analyse",
        "Wetter & FX",
        "Datenquellen",
        "Pipeline-Status",
    ]
    page = st.sidebar.radio("Seite", pages)

    if orders.empty:
        st.warning("Noch keine Bestelldaten im Warehouse. Bitte Batch und dbt zuerst ausfuehren.")
        return

    st.sidebar.markdown("---")
    st.sidebar.subheader("Order-Filter")

    min_date = orders["order_date"].min().date()
    max_date = orders["order_date"].max().date()
    start_date, end_date = selected_date_window(min_date, max_date)

    selected_statuses = st.sidebar.multiselect(
        "Bestellstatus",
        options=sorted(orders["order_status"].dropna().unique()),
        default=sorted(orders["order_status"].dropna().unique()),
    )
    selected_categories = st.sidebar.multiselect(
        "Produktkategorie",
        options=sorted(orders["product_category_name"].dropna().unique()),
        default=sorted(orders["product_category_name"].dropna().unique()),
    )
    selected_states = st.sidebar.multiselect(
        "Bundesstaat",
        options=sorted(orders["customer_state"].dropna().unique()),
        default=sorted(orders["customer_state"].dropna().unique()),
    )
    selected_payment_types = st.sidebar.multiselect(
        "Zahlungsart",
        options=sorted(orders["payment_type"].dropna().unique()),
        default=sorted(orders["payment_type"].dropna().unique()),
    )

    filtered_orders = apply_order_filters(
        orders,
        start_date=start_date,
        end_date=end_date,
        statuses=selected_statuses,
        categories=selected_categories,
        states=selected_states,
        payment_types=selected_payment_types,
    )

    st.sidebar.caption(f"Gefilterte Bestellungen: {len(filtered_orders):,} / {len(orders):,}")

    if page == "Commerce KPIs":
        st.subheader("Commerce KPIs")
        render_kpi_metrics(filtered_orders)

        insight_columns = st.columns(len(derive_commerce_insights(filtered_orders)))
        for column, insight in zip(
            insight_columns, derive_commerce_insights(filtered_orders), strict=False
        ):
            column.info(insight)

        status_counts = filtered_orders["order_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Anzahl"]
        payment_counts = filtered_orders["payment_type"].value_counts().reset_index()
        payment_counts.columns = ["Zahlungsart", "Anzahl"]

        col1, col2 = st.columns(2)
        col1.plotly_chart(
            px.pie(
                status_counts,
                names="Status",
                values="Anzahl",
                color_discrete_sequence=px.colors.qualitative.Set2,
            ),
            use_container_width=True,
        )
        col2.plotly_chart(
            px.bar(
                payment_counts,
                x="Zahlungsart",
                y="Anzahl",
                color="Zahlungsart",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            ),
            use_container_width=True,
        )

    elif page == "Zeitliche Trends":
        st.subheader("Zeitliche Trends")
        frequency = st.radio("Aggregation", ["Tag", "Woche", "Monat"], horizontal=True)
        freq_map = {"Tag": "D", "Woche": "W", "Monat": "ME"}

        time_frame = filtered_orders.copy()
        time_frame["period"] = (
            time_frame["order_date"].dt.to_period(freq_map[frequency]).dt.to_timestamp()
        )
        grouped = (
            time_frame.groupby("period")
            .agg(
                order_count=("order_id", "count"),
                revenue_brl=("payment_value_brl", "sum"),
                avg_items=("item_count", "mean"),
            )
            .reset_index()
        )

        st.plotly_chart(
            px.bar(grouped, x="period", y="order_count", title="Bestellungen pro Zeitraum"),
            use_container_width=True,
        )
        st.plotly_chart(
            px.area(grouped, x="period", y="revenue_brl", title="Umsatzentwicklung (BRL)"),
            use_container_width=True,
        )

        category_time = (
            time_frame.groupby(["period", "product_category_name"])["payment_value_brl"]
            .sum()
            .reset_index()
        )
        st.plotly_chart(
            px.area(
                category_time,
                x="period",
                y="payment_value_brl",
                color="product_category_name",
                title="Umsatz nach Kategorie",
            ),
            use_container_width=True,
        )

    elif page == "Kategorien & Regionen":
        st.subheader("Kategorien & Regionen")

        top_categories = (
            filtered_orders.groupby("product_category_name")["payment_value_brl"]
            .sum()
            .sort_values(ascending=True)
            .tail(10)
            .reset_index()
        )
        top_states = (
            filtered_orders.groupby("customer_state")["order_id"]
            .count()
            .sort_values(ascending=True)
            .tail(10)
            .reset_index()
        )

        col1, col2 = st.columns(2)
        col1.plotly_chart(
            px.bar(
                top_categories,
                x="payment_value_brl",
                y="product_category_name",
                orientation="h",
                title="Top Kategorien nach Umsatz",
                color_discrete_sequence=["#b5554f"],
            ),
            use_container_width=True,
        )
        col2.plotly_chart(
            px.bar(
                top_states,
                x="order_id",
                y="customer_state",
                orientation="h",
                title="Top Bundesstaaten nach Bestellungen",
                color_discrete_sequence=["#26547c"],
            ),
            use_container_width=True,
        )

        heatmap = filtered_orders.pivot_table(
            values="payment_value_brl",
            index="product_category_name",
            columns="customer_state",
            aggfunc="sum",
            fill_value=0,
        )
        st.plotly_chart(
            px.imshow(
                heatmap,
                aspect="auto",
                color_continuous_scale="Viridis",
                title="Umsatz-Heatmap: Kategorie x Bundesstaat",
            ),
            use_container_width=True,
        )

    elif page == "Produkt-Analyse":
        st.subheader("Produkt-Analyse")
        products = dataframes["products"]

        if products.empty:
            st.warning("Keine Produktdaten vorhanden. Bitte `dbt build` ausfuehren.")
        else:
            source_counts = products["source_system"].value_counts().reset_index()
            source_counts.columns = ["Quelle", "Anzahl"]

            col1, col2 = st.columns(2)
            col1.metric("Produkte gesamt", f"{len(products):,}")
            col2.metric("Quellen", f"{products['source_system'].nunique()}")

            st.plotly_chart(
                px.pie(
                    source_counts,
                    names="Quelle",
                    values="Anzahl",
                    title="Produkte nach Quelle",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                ),
                use_container_width=True,
            )

            if "product_category_name" in products.columns:
                cat_counts = (
                    products["product_category_name"]
                    .dropna()
                    .value_counts()
                    .head(15)
                    .sort_values()
                    .reset_index()
                )
                cat_counts.columns = ["Kategorie", "Anzahl"]
                st.plotly_chart(
                    px.bar(
                        cat_counts,
                        x="Anzahl",
                        y="Kategorie",
                        orientation="h",
                        title="Top 15 Produktkategorien",
                        color_discrete_sequence=["#2a9d8f"],
                    ),
                    use_container_width=True,
                )

            if "ecoscore_grade" in products.columns:
                eco = products["ecoscore_grade"].dropna()
                if not eco.empty:
                    eco_counts = eco.value_counts().sort_index().reset_index()
                    eco_counts.columns = ["Ecoscore", "Anzahl"]
                    st.plotly_chart(
                        px.bar(
                            eco_counts,
                            x="Ecoscore",
                            y="Anzahl",
                            title="Open Food Facts Ecoscore-Verteilung",
                            color="Ecoscore",
                            color_discrete_sequence=px.colors.qualitative.Safe,
                        ),
                        use_container_width=True,
                    )

    elif page == "Session-Analyse":
        sessions = dataframes["sessions"]
        st.subheader("Session-Analyse")

        if sessions.empty:
            st.warning("Keine Session-Daten vorhanden. Bitte `make run-streaming` ausfuehren.")
            return

        session_columns = st.columns(4)
        session_columns[0].metric("Sessions", f"{len(sessions):,}")
        session_columns[1].metric("Unique Visitors", f"{sessions['visitor_id'].nunique():,}")
        session_columns[2].metric("Events/Session", f"{sessions['event_count'].mean():.1f}")
        conversion_rate = (sessions["transaction_count"] > 0).mean() * 100
        session_columns[3].metric("Conversion Rate", f"{conversion_rate:.1f}%")

        for insight in derive_session_insights(sessions):
            st.info(insight)

        event_totals = pd.DataFrame(
            {
                "Event-Typ": ["Views", "Add to Cart", "Transactions"],
                "Anzahl": [
                    sessions["view_count"].sum(),
                    sessions["addtocart_count"].sum(),
                    sessions["transaction_count"].sum(),
                ],
            }
        )
        col1, col2 = st.columns(2)
        col1.plotly_chart(
            px.bar(
                event_totals,
                x="Event-Typ",
                y="Anzahl",
                color="Event-Typ",
                color_discrete_sequence=["#26547c", "#f4a259", "#2a9d8f"],
            ),
            use_container_width=True,
        )
        col2.plotly_chart(
            go.Figure(
                go.Funnel(
                    y=event_totals["Event-Typ"],
                    x=event_totals["Anzahl"],
                    textinfo="value+percent initial",
                )
            ),
            use_container_width=True,
        )

        st.plotly_chart(
            px.histogram(
                sessions,
                x="event_count",
                nbins=20,
                title="Verteilung der Events pro Session",
                color_discrete_sequence=["#7b2cbf"],
            ),
            use_container_width=True,
        )

    elif page == "Wetter & FX":
        st.subheader("Wetter & FX")
        weather = dataframes["weather"]
        fx = dataframes["fx"]

        if not weather.empty:
            st.plotly_chart(
                px.line(
                    weather,
                    x="weather_date",
                    y="avg_temperature_c",
                    color="city",
                    title="Temperaturverlauf",
                ),
                use_container_width=True,
            )
            st.plotly_chart(
                px.bar(
                    weather,
                    x="weather_date",
                    y="precipitation_mm",
                    color="city",
                    title="Niederschlag",
                ),
                use_container_width=True,
            )

        if not fx.empty:
            st.plotly_chart(
                px.line(
                    fx,
                    x="rate_date",
                    y="fx_rate",
                    color="quote_currency",
                    title="EUR/USD und EUR/BRL Wechselkurse",
                ),
                use_container_width=True,
            )

        correlation_frame = filtered_orders.dropna(
            subset=["avg_temperature_c", "payment_value_brl"]
        )
        if not correlation_frame.empty:
            st.plotly_chart(
                px.scatter(
                    correlation_frame,
                    x="avg_temperature_c",
                    y="payment_value_brl",
                    color="customer_state",
                    opacity=0.55,
                    title="Temperatur vs. Bestellwert",
                ),
                use_container_width=True,
            )

    elif page == "Datenquellen":
        st.subheader("Datenquellen-Uebersicht")

        source_info = [
            {
                "Quelle": "Olist (CSV Seeds)",
                "Typ": "Batch",
                "Tabellen": "5 (orders, items, customers, products, payments)",
                "Erwartete Zeilen": "~2.401",
            },
            {
                "Quelle": "Open Food Facts API",
                "Typ": "Batch (API)",
                "Tabellen": "1 (open_food_facts_products)",
                "Erwartete Zeilen": "3-4",
            },
            {
                "Quelle": "Open-Meteo API",
                "Typ": "Batch (API)",
                "Tabellen": "1 (open_meteo_weather)",
                "Erwartete Zeilen": "~1.095",
            },
            {
                "Quelle": "Frankfurter API v2",
                "Typ": "Batch (API)",
                "Tabellen": "1 (frankfurter_fx_rates)",
                "Erwartete Zeilen": "~730",
            },
            {
                "Quelle": "Retailrocket (JSONL Replay)",
                "Typ": "Streaming",
                "Tabellen": "1 (retailrocket_events)",
                "Erwartete Zeilen": "3 (Sample)",
            },
        ]
        st.dataframe(pd.DataFrame(source_info), use_container_width=True, hide_index=True)

        audit = dataframes["audit"]
        if not audit.empty:
            st.markdown("#### Letzte Ingestion pro Quelle")
            latest = audit.sort_values("loaded_at", ascending=False).drop_duplicates("source_name")
            for _, row in latest.iterrows():
                st.markdown(
                    f"**{row['source_name']}**: {row['row_count']:,} Zeilen "
                    f"(Batch `{row['batch_id']}`, {row['loaded_at']})"
                )

        st.markdown("#### Datenfluss")
        st.markdown(
            """
            ```
            Olist CSVs ──┐
            Food Facts ──┤                    ┌─ staging (9 Views)
            Open-Meteo ──┼── raw.* (9 Tab.) ──┼─ intermediate (2 Views)
            Frankfurter ─┤                    └─ marts (3 Tables)
            Retailrocket ┘
            ```
            """
        )

    elif page == "Pipeline-Status":
        st.subheader("Pipeline-Status")

        audit = dataframes["audit"]
        if not audit.empty:
            st.dataframe(
                audit[["source_name", "batch_id", "row_count", "loaded_at"]],
                use_container_width=True,
            )

        stats = dataframes["table_stats"]
        if stats.empty:
            stats = build_table_stats(
                {
                    "fct_commerce_orders": dataframes["orders"],
                    "fct_retailrocket_sessions": dataframes["sessions"],
                    "dim_products": dataframes["products"],
                    "open_meteo_weather": dataframes["weather"],
                    "frankfurter_fx_rates": dataframes["fx"],
                }
            )
        st.dataframe(stats, use_container_width=True)

        st.markdown(
            """
            | Komponente | Technologie |
            |---|---|
            | Warehouse | PostgreSQL 18 |
            | Streaming | Redpanda v25.3.9 |
            | Document Store | MongoDB 7 |
            | Transformation | dbt |
            | Orchestrierung | Kestra v1.1 |
            | Dashboard | Streamlit + Plotly |
            | Cloud Ziel | Cloud Run + BigQuery |
            """
        )


if __name__ == "__main__":
    main()
