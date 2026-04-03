{{ config(materialized='view') }}

{% if execute and raw_relation_exists('olist_order_payments') %}
select
    cast(order_id as {{ dbt.type_string() }}) as order_id,
    cast(payment_sequential as {{ dbt.type_int() }}) as payment_sequential,
    cast(payment_type as {{ dbt.type_string() }}) as payment_type,
    cast(payment_installments as {{ dbt.type_int() }}) as payment_installments,
    cast(payment_value as numeric(12, 2)) as payment_value
from {{ source('raw', 'olist_order_payments') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as order_id,
    cast(null as {{ dbt.type_int() }}) as payment_sequential,
    cast(null as {{ dbt.type_string() }}) as payment_type,
    cast(null as {{ dbt.type_int() }}) as payment_installments,
    cast(null as numeric(12, 2)) as payment_value
where 1 = 0
{% endif %}
