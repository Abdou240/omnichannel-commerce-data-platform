{{ config(materialized='view') }}

{% if execute and raw_relation_exists('olist_customers') %}
select
    cast(customer_id as {{ dbt.type_string() }}) as customer_id,
    cast(customer_city as {{ dbt.type_string() }}) as customer_city,
    cast(customer_state as {{ dbt.type_string() }}) as customer_state
from {{ source('raw', 'olist_customers') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as customer_id,
    cast(null as {{ dbt.type_string() }}) as customer_city,
    cast(null as {{ dbt.type_string() }}) as customer_state
where 1 = 0
{% endif %}
