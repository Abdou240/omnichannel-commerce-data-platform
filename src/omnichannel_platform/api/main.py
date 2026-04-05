"""FastAPI REST API fuer die Omnichannel Commerce Data Platform.

Data-Access-Layer zwischen PostgreSQL-Warehouse und Clients (Dashboard, BI-Tools).
4 Router: Orders, Sessions, Enrichments (Products/Weather/FX), Pipeline-Status.

Aufruf:
  uvicorn omnichannel_platform.api.main:app --reload --port 8000
  python -m omnichannel_platform.api.main

Swagger-Docs: http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI

from omnichannel_platform.api.routes import enrichments, orders, pipeline, sessions

# ── FastAPI-App mit 4 Routern ───────────────────────────────────────────────
app = FastAPI(
    title="Omnichannel Commerce Data Platform API",
    description=(
        "REST API fuer Commerce-Orders, Clickstream-Sessions, "
        "Wetter-/FX-Enrichments und Pipeline-Status. "
        "Datenquelle: PostgreSQL Warehouse (raw/staging/marts)."
    ),
    version="0.1.0",
)

# Router registrieren: /api/v1/orders, /api/v1/sessions, /api/v1/products|weather|fx-rates, /api/v1/health|pipeline
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
