{{ config(materialized='view') }}

select
    cast(null as varchar) as order_id,
    cast(null as integer) as order_item_id,
    cast(null as varchar) as product_id,
    cast(null as varchar) as seller_id,
    cast(null as numeric(12, 2)) as item_price,
    cast(null as numeric(12, 2)) as freight_value
where 1 = 0

