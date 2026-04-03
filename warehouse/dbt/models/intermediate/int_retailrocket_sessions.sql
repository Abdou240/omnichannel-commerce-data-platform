{{ config(materialized='view') }}

select
    cast(null as varchar) as session_key,
    cast(null as varchar) as visitor_id,
    cast(null as timestamp) as session_start_ts,
    cast(null as timestamp) as session_end_ts,
    cast(null as integer) as event_count
where 1 = 0

