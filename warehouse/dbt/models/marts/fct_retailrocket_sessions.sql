{{ config(materialized='table') }}

select
    session_key,
    visitor_id,
    session_start_ts,
    session_end_ts,
    event_count,
    view_count,
    addtocart_count,
    transaction_count,
    sample_item_id
from {{ ref('int_retailrocket_sessions') }}
