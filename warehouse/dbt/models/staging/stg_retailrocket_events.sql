{{ config(materialized='view') }}

select
    cast(null as varchar) as event_id,
    cast(null as varchar) as visitor_id,
    cast(null as varchar) as event_type,
    cast(null as varchar) as item_id,
    cast(null as varchar) as transaction_id,
    cast(null as timestamp) as event_ts,
    cast(null as varchar) as kafka_topic
where 1 = 0

