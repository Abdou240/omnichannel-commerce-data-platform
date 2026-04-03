{{ config(materialized='view') }}

{% if execute and raw_relation_exists('olist_orders') %}
select
    cast(order_id as {{ dbt.type_string() }}) as order_id,
    cast(customer_id as {{ dbt.type_string() }}) as customer_id,
    cast(order_status as {{ dbt.type_string() }}) as order_status,
    cast(order_purchase_timestamp as {{ dbt.type_timestamp() }}) as order_purchase_ts,
    cast(order_approved_at as {{ dbt.type_timestamp() }}) as order_approved_ts,
    cast(order_estimated_delivery_date as {{ dbt.type_timestamp() }}) as order_estimated_delivery_ts,
    cast('olist' as {{ dbt.type_string() }}) as source_system
from {{ source('raw', 'olist_orders') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as order_id,
    cast(null as {{ dbt.type_string() }}) as customer_id,
    cast(null as {{ dbt.type_string() }}) as order_status,
    cast(null as {{ dbt.type_timestamp() }}) as order_purchase_ts,
    cast(null as {{ dbt.type_timestamp() }}) as order_approved_ts,
    cast(null as {{ dbt.type_timestamp() }}) as order_estimated_delivery_ts,
    cast('olist' as {{ dbt.type_string() }}) as source_system
where 1 = 0
{% endif %}
