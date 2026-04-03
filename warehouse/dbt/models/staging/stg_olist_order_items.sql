{{ config(materialized='view') }}

{% if execute and raw_relation_exists('olist_order_items') %}
select
    cast(order_id as {{ dbt.type_string() }}) as order_id,
    cast(order_item_id as {{ dbt.type_int() }}) as order_item_id,
    cast(product_id as {{ dbt.type_string() }}) as product_id,
    cast(seller_id as {{ dbt.type_string() }}) as seller_id,
    cast(price as numeric(12, 2)) as item_price,
    cast(freight_value as numeric(12, 2)) as freight_value
from {{ source('raw', 'olist_order_items') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as order_id,
    cast(null as {{ dbt.type_int() }}) as order_item_id,
    cast(null as {{ dbt.type_string() }}) as product_id,
    cast(null as {{ dbt.type_string() }}) as seller_id,
    cast(null as numeric(12, 2)) as item_price,
    cast(null as numeric(12, 2)) as freight_value
where 1 = 0
{% endif %}
