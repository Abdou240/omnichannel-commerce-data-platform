{{ config(materialized='view') }}

{% if execute and raw_relation_exists('open_food_facts_products') %}
select
    cast(product_code as {{ dbt.type_string() }}) as product_id,
    cast(product_name as {{ dbt.type_string() }}) as product_name,
    cast(brands as {{ dbt.type_string() }}) as brand,
    cast(categories as {{ dbt.type_string() }}) as category,
    cast(ecoscore_grade as {{ dbt.type_string() }}) as ecoscore_grade,
    cast(image_front_url as {{ dbt.type_string() }}) as image_front_url,
    cast(ingested_at as {{ dbt.type_timestamp() }}) as ingested_at
from {{ source('raw', 'open_food_facts_products') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as product_id,
    cast(null as {{ dbt.type_string() }}) as product_name,
    cast(null as {{ dbt.type_string() }}) as brand,
    cast(null as {{ dbt.type_string() }}) as category,
    cast(null as {{ dbt.type_string() }}) as ecoscore_grade,
    cast(null as {{ dbt.type_string() }}) as image_front_url,
    cast(null as {{ dbt.type_timestamp() }}) as ingested_at
where 1 = 0
{% endif %}
