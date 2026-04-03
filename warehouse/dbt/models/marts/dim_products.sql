{{ config(materialized='table') }}

select
    product_id,
    product_name,
    brand,
    category,
    price_usd
from {{ ref('stg_dummyjson_products') }}

