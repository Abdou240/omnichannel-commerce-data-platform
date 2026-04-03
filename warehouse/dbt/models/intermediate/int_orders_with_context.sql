{{ config(materialized='view') }}

with orders as (
    select * from {{ ref('stg_olist_orders') }}
),

customers as (
    select * from {{ ref('stg_olist_customers') }}
),

order_items as (
    select * from {{ ref('stg_olist_order_items') }}
),

payments as (
    select * from {{ ref('stg_olist_order_payments') }}
),

products as (
    select * from {{ ref('stg_olist_products') }}
),

weather as (
    select * from {{ ref('stg_open_meteo_weather') }}
),

fx_daily as (
    select
        rate_date,
        max(case when quote_currency = 'USD' then fx_rate end) as eur_to_usd_fx_rate,
        max(case when quote_currency = 'BRL' then fx_rate end) as eur_to_brl_fx_rate
    from {{ ref('stg_frankfurter_fx_rates') }}
    group by 1
),

items_per_order as (
    select
        order_id,
        count(*) as item_count,
        sum(item_price) as gross_item_value,
        sum(freight_value) as freight_value,
        min(product_id) as primary_product_id
    from order_items
    group by 1
),

payments_per_order as (
    select
        order_id,
        sum(payment_value) as payment_value_brl,
        min(payment_type) as payment_type
    from payments
    group by 1
)

select
    orders.order_id,
    orders.customer_id,
    customers.customer_city,
    customers.customer_state,
    orders.order_purchase_ts,
    cast(orders.order_purchase_ts as date) as order_date,
    orders.order_status,
    coalesce(items_per_order.item_count, 0) as item_count,
    coalesce(items_per_order.gross_item_value, 0) as gross_item_value,
    coalesce(items_per_order.freight_value, 0) as freight_value,
    coalesce(
        payments_per_order.payment_value_brl,
        items_per_order.gross_item_value + items_per_order.freight_value,
        0
    ) as payment_value_brl,
    payments_per_order.payment_type,
    items_per_order.primary_product_id as product_id,
    products.product_category_name,
    products.product_weight_g,
    weather.avg_temperature_c,
    weather.precipitation_mm,
    case
        when fx_daily.eur_to_usd_fx_rate is not null
         and fx_daily.eur_to_brl_fx_rate is not null
         and fx_daily.eur_to_brl_fx_rate != 0
            then fx_daily.eur_to_usd_fx_rate / fx_daily.eur_to_brl_fx_rate
        else null
    end as brl_to_usd_fx_rate
from orders
left join customers
    on orders.customer_id = customers.customer_id
left join items_per_order
    on orders.order_id = items_per_order.order_id
left join payments_per_order
    on orders.order_id = payments_per_order.order_id
left join products
    on items_per_order.primary_product_id = products.product_id
left join weather
    on cast(orders.order_purchase_ts as date) = weather.weather_date
   and customers.customer_city = weather.city
left join fx_daily
    on cast(orders.order_purchase_ts as date) = fx_daily.rate_date
