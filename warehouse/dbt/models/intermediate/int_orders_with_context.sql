{{ config(materialized='view') }}

-- TODO: join Olist orders to item, product, weather, and FX context once raw
-- source loading is implemented.
select
    o.order_id,
    o.customer_id,
    o.order_purchase_ts,
    o.order_status,
    cast(null as varchar) as product_id,
    cast(null as numeric(18, 8)) as brl_to_usd_fx_rate,
    cast(null as numeric(8, 2)) as avg_temperature_c
from {{ ref('stg_olist_orders') }} o

