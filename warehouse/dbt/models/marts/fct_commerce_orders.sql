{{ config(materialized='table') }}

select
    order_id,
    customer_id,
    customer_city,
    customer_state,
    order_purchase_ts,
    order_date,
    order_status,
    item_count,
    gross_item_value,
    freight_value,
    payment_value_brl,
    case
        when brl_to_usd_fx_rate is not null
            then payment_value_brl * brl_to_usd_fx_rate
        else null
    end as payment_value_usd,
    payment_type,
    product_id,
    product_category_name,
    product_weight_g,
    avg_temperature_c,
    precipitation_mm,
    brl_to_usd_fx_rate
from {{ ref('int_orders_with_context') }}
