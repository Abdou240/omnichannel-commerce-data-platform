"""FastAPI application for the Omnichannel Commerce Data Platform.

Provides a REST API layer between the PostgreSQL warehouse and any client
(Streamlit dashboard, Jupyter notebooks, BI tools, mobile apps).

Run locally:
    uvicorn omnichannel_platform.api.main:app --reload --port 8000

Run via module:
    python -m omnichannel_platform.api.main
"""

from __future__ import annotations

from fastapi import FastAPI

from omnichannel_platform.api.routes import enrichments, orders, pipeline, sessions

app = FastAPI(
    title="Omnichannel Commerce Data Platform API",
    description=(
        "REST API fuer Commerce-Orders, Clickstream-Sessions, "
        "Wetter-/FX-Enrichments und Pipeline-Status. "
        "Datenquelle: PostgreSQL Warehouse (raw/staging/marts)."
    ),
    version="0.1.0",
)

app.include_router(orders.router)
app.include_router(sessions.router)
app.include_router(enrichments.router)
app.include_router(pipeline.router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "service": "omnichannel-commerce-data-platform-api",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("omnichannel_platform.api.main:app", host="0.0.0.0", port=8000, reload=True)
