"""Session endpoints for the Omnichannel Commerce REST API."""

from __future__ import annotations

from fastapi import APIRouter, Query

from omnichannel_platform.api.database import query_dataframe, warehouse_schema
from omnichannel_platform.api.models import SessionFunnel, SessionRow

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionRow])
def list_sessions(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    schema = warehouse_schema()
    sql = (
        f"SELECT * FROM {schema}.fct_retailrocket_sessions "
        f"ORDER BY session_start_ts DESC NULLS LAST, session_key LIMIT {limit} OFFSET {offset}"
    )
    df = query_dataframe(sql)
    return df.where(df.notna(), None).to_dict(orient="records")


@router.get("/funnel", response_model=SessionFunnel)
def session_funnel() -> dict:
    schema = warehouse_schema()
    sql = f"""
    SELECT
        count(*) as total_sessions,
        coalesce(sum(view_count), 0)::int as total_views,
        coalesce(sum(addtocart_count), 0)::int as total_addtocart,
        coalesce(sum(transaction_count), 0)::int as total_transactions,
        coalesce(avg(case when transaction_count > 0 then 1.0 else 0.0 end) * 100, 0)
            as conversion_rate_pct
    FROM {schema}.fct_retailrocket_sessions
    """
    df = query_dataframe(sql)
    return df.iloc[0].to_dict()
