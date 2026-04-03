{{ config(materialized='view') }}

{% if execute and raw_relation_exists('dummyjson_products') %}
select
    cast(product_id as {{ dbt.type_string() }}) as product_id,
    cast(title as {{ dbt.type_string() }}) as product_name,
    cast(brand as {{ dbt.type_string() }}) as brand,
    cast(category as {{ dbt.type_string() }}) as category,
    cast(price_usd as numeric(12, 2)) as price_usd,
    cast(ingested_at as {{ dbt.type_timestamp() }}) as ingested_at
from {{ source('raw', 'dummyjson_products') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as product_id,
    cast(null as {{ dbt.type_string() }}) as product_name,
    cast(null as {{ dbt.type_string() }}) as brand,
    cast(null as {{ dbt.type_string() }}) as category,
    cast(null as numeric(12, 2)) as price_usd,
    cast(null as {{ dbt.type_timestamp() }}) as ingested_at
where 1 = 0
{% endif %}
