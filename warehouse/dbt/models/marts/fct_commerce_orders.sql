{{ config(materialized='table') }}

select
    order_id,
    customer_id,
    order_purchase_ts,
    order_status,
    product_id,
    brl_to_usd_fx_rate,
    avg_temperature_c
from {{ ref('int_orders_with_context') }}

