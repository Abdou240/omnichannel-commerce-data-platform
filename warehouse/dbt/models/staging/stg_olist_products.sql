{{ config(materialized='view') }}

{% if execute and raw_relation_exists('olist_products') %}
select
    cast(product_id as {{ dbt.type_string() }}) as product_id,
    cast(product_category_name as {{ dbt.type_string() }}) as product_category_name,
    cast(product_name_length as {{ dbt.type_int() }}) as product_name_length,
    cast(product_description_length as {{ dbt.type_int() }}) as product_description_length,
    cast(product_photos_qty as {{ dbt.type_int() }}) as product_photos_qty,
    cast(product_weight_g as {{ dbt.type_int() }}) as product_weight_g
from {{ source('raw', 'olist_products') }}
{% else %}
select
    cast(null as {{ dbt.type_string() }}) as product_id,
    cast(null as {{ dbt.type_string() }}) as product_category_name,
    cast(null as {{ dbt.type_int() }}) as product_name_length,
    cast(null as {{ dbt.type_int() }}) as product_description_length,
    cast(null as {{ dbt.type_int() }}) as product_photos_qty,
    cast(null as {{ dbt.type_int() }}) as product_weight_g
where 1 = 0
{% endif %}
