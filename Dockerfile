FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .
COPY LICENSE .
COPY src/ src/
COPY config/ config/
COPY data/ data/
COPY sql/ sql/
COPY quality/ quality/
COPY warehouse/ warehouse/
COPY kafka/ kafka/
COPY orchestration/ orchestration/
COPY dashboard/ dashboard/
COPY Makefile .

RUN pip install --no-cache-dir -e ".[batch,streaming,warehouse,nosql,quality,dashboard,api]"

# ---------------------------------------------------------------------------
# Stage: pipeline -- batch, streaming, quality CLI entry points
# ---------------------------------------------------------------------------
FROM base AS pipeline

ENV ENVIRONMENT=dev
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=commerce_platform
ENV POSTGRES_USER=commerce
ENV POSTGRES_PASSWORD=commerce
ENV MONGO_URI=mongodb://mongo:27017
ENV KAFKA_BOOTSTRAP_SERVERS=redpanda:29092

ENTRYPOINT ["python", "-m"]
CMD ["omnichannel_platform.batch.commerce_batch_ingestion", "--env", "dev"]

# ---------------------------------------------------------------------------
# Stage: dashboard -- Streamlit frontend
# ---------------------------------------------------------------------------
FROM base AS dashboard

ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=commerce_platform
ENV POSTGRES_USER=commerce
ENV POSTGRES_PASSWORD=commerce
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f "http://localhost:${PORT}/_stcore/health" || exit 1

ENTRYPOINT ["/bin/sh", "-lc"]
CMD ["streamlit run dashboard/app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]

# ---------------------------------------------------------------------------
# Stage: api -- FastAPI REST API
# ---------------------------------------------------------------------------
FROM base AS api

ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=commerce_platform
ENV POSTGRES_USER=commerce
ENV POSTGRES_PASSWORD=commerce
ENV API_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f "http://localhost:${API_PORT}/api/v1/health" || exit 1

CMD ["uvicorn", "omnichannel_platform.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
