create schema if not exists raw;
create schema if not exists staging;
create schema if not exists marts;

create table if not exists raw.ingestion_audit (
    source_name text not null,
    batch_id text not null,
    loaded_at timestamptz not null default now(),
    row_count bigint,
    primary key (source_name, batch_id)
);
