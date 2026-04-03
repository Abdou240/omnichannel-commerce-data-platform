{{ config(materialized='table') }}

with olist_products as (
    select
        'olist:' || product_id as product_key,
        product_id,
        cast(null as {{ dbt.type_string() }}) as product_name,
        cast(null as {{ dbt.type_string() }}) as brand,
        product_category_name as category,
        cast(null as numeric(12, 2)) as price_usd,
        cast('olist' as {{ dbt.type_string() }}) as source_system
    from {{ ref('stg_olist_products') }}
),

dummyjson_products as (
    select
        'dummyjson:' || product_id as product_key,
        product_id,
        product_name,
        brand,
        category,
        price_usd,
        cast('dummyjson' as {{ dbt.type_string() }}) as source_system
    from {{ ref('stg_dummyjson_products') }}
)

select * from olist_products
union all
select * from dummyjson_products
