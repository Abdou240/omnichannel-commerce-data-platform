{{ config(materialized='view') }}

with ordered_events as (
    select
        event_id,
        visitor_id,
        event_type,
        item_id,
        transaction_id,
        event_ts,
        lag(event_ts) over (
            partition by visitor_id
            order by event_ts, event_id
        ) as previous_event_ts
    from {{ ref('stg_retailrocket_events') }}
),

flagged_events as (
    select
        *,
        case
            when previous_event_ts is null then 1
            when {{ dbt.datediff("previous_event_ts", "event_ts", "minute") }} > 30 then 1
            else 0
        end as is_new_session
    from ordered_events
),

sessionized_events as (
    select
        *,
        sum(is_new_session) over (
            partition by visitor_id
            order by event_ts, event_id
            rows between unbounded preceding and current row
        ) as session_number
    from flagged_events
)

select
    visitor_id || '-' || cast(session_number as {{ dbt.type_string() }}) as session_key,
    visitor_id,
    min(event_ts) as session_start_ts,
    max(event_ts) as session_end_ts,
    count(*) as event_count,
    sum(case when event_type = 'view' then 1 else 0 end) as view_count,
    sum(case when event_type = 'addtocart' then 1 else 0 end) as addtocart_count,
    sum(case when event_type = 'transaction' then 1 else 0 end) as transaction_count,
    min(item_id) as sample_item_id
from sessionized_events
group by 1, 2
