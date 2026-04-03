{{ config(materialized='view') }}

select
    cast(null as varchar) as product_id,
    cast(null as varchar) as product_name,
    cast(null as varchar) as brand,
    cast(null as varchar) as category,
    cast(null as numeric(12, 2)) as price_usd
where 1 = 0

