{{ config(materialized='table') }}

with olist_products as (
    select
        'olist:' || product_id as product_key,
        product_id,
        cast(null as {{ dbt.type_string() }}) as product_name,
        cast(null as {{ dbt.type_string() }}) as brand,
        product_category_name as category,
        cast(null as numeric(12, 2)) as price_usd,
        cast(null as {{ dbt.type_string() }}) as ecoscore_grade,
        cast(null as {{ dbt.type_string() }}) as image_front_url,
        cast('olist' as {{ dbt.type_string() }}) as source_system
    from {{ ref('stg_olist_products') }}
),

open_food_facts_products as (
    select
        'open_food_facts:' || product_id as product_key,
        product_id,
        product_name,
        brand,
        category,
        cast(null as numeric(12, 2)) as price_usd,
        ecoscore_grade,
        image_front_url,
        cast('open_food_facts' as {{ dbt.type_string() }}) as source_system
    from {{ ref('stg_open_food_facts_products') }}
)

select * from olist_products
union all
select * from open_food_facts_products
