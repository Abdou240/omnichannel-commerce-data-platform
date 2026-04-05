-- ============================================================================
-- 001: Schema-Initialisierung fuer das lokale PostgreSQL-Warehouse
-- Wird beim ersten Start des PostgreSQL-Containers automatisch ausgefuehrt
-- (via docker-entrypoint-initdb.d).
-- ============================================================================

-- 3 Schemas: raw (Landing), staging (dbt Views), marts (dbt Tabellen)
create schema if not exists raw;
create schema if not exists staging;
create schema if not exists marts;

-- Audit-Tabelle: Protokolliert jeden Batch-Ingestion-Lauf
-- (source_name + batch_id = Composite Primary Key, Upsert-faehig)
create table if not exists raw.ingestion_audit (
    source_name text not null,
    batch_id text not null,
    loaded_at timestamptz not null default now(),
    row_count bigint,
    primary key (source_name, batch_id)
);
