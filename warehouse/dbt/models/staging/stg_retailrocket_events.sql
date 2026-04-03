{{ config(materialized='view') }}

{% if execute and raw_relation_exists('retailrocket_events') %}
select
    cast(event_id as {{ dbt.type_string() }}) as event_id,
    cast(visitor_id as {{ dbt.type_string() }}) as visitor_id,
    lower(cast(event_type as {{ dbt.type_string() }})) as event_type,
    cast(item_id as {{ dbt.type_string() }}) as item_id,
    cast(transaction_id as {{ dbt.type_string() }}) as transaction_id,
    cast(event_ts as {{ dbt.type_timestamp() }}) as event_ts,
    cast(kafka_topic as {{ dbt.type_string() }}) as kafka_topic
from {{ source('raw', 'retailrocket_events') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as event_id,
    cast(null as {{ dbt.type_string() }}) as visitor_id,
    cast(null as {{ dbt.type_string() }}) as event_type,
    cast(null as {{ dbt.type_string() }}) as item_id,
    cast(null as {{ dbt.type_string() }}) as transaction_id,
    cast(null as {{ dbt.type_timestamp() }}) as event_ts,
    cast(null as {{ dbt.type_string() }}) as kafka_topic
where 1 = 0
{% endif %}
