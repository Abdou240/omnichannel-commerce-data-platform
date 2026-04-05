"""Pipeline-Status und Health-Endpunkte.

GET /api/v1/health          -> Datenbank-Erreichbarkeit pruefen
GET /api/v1/pipeline/status -> Audit-Log + Tabellenstatistiken (Zeilen, Spalten)
"""

from __future__ import annotations

from fastapi import APIRouter

from omnichannel_platform.api.database import (
    check_database,
    query_dataframe,
    raw_schema,
    warehouse_schema,
)
from omnichannel_platform.api.models import HealthResponse, PipelineStatus

router = APIRouter(prefix="/api/v1", tags=["pipeline"])


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    try:
        check_database()
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "unreachable"}


@router.get("/pipeline/status", response_model=PipelineStatus)
def pipeline_status() -> dict:
    raw = raw_schema()
    wh = warehouse_schema()

    audit_df = query_dataframe(
        f"SELECT source_name, batch_id, row_count, loaded_at "
        f"FROM {raw}.ingestion_audit ORDER BY loaded_at DESC LIMIT 50"
    )

    table_queries = {
        "fct_commerce_orders": f"{wh}.fct_commerce_orders",
        "fct_retailrocket_sessions": f"{wh}.fct_retailrocket_sessions",
        "dim_products": f"{wh}.dim_products",
        "open_meteo_weather": f"{raw}.open_meteo_weather",
        "frankfurter_fx_rates": f"{raw}.frankfurter_fx_rates",
    }

    tables = []
    for name, fqn in table_queries.items():
        try:
            df = query_dataframe(f"SELECT * FROM {fqn} LIMIT 1")
            count_df = query_dataframe(f"SELECT count(*) as cnt FROM {fqn}")
            tables.append(
                {
                    "table_name": name,
                    "row_count": int(count_df.iloc[0]["cnt"]),
                    "column_count": len(df.columns),
                }
            )
        except Exception:
            tables.append({"table_name": name, "row_count": 0, "column_count": 0})

    return {
        "audit": audit_df.to_dict(orient="records"),
        "tables": tables,
    }
