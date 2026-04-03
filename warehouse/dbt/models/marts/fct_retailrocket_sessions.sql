{{ config(materialized='table') }}

select
    session_key,
    visitor_id,
    session_start_ts,
    session_end_ts,
    event_count
from {{ ref('int_retailrocket_sessions') }}

