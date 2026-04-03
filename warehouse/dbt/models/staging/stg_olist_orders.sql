{{ config(materialized='view') }}

-- TODO: replace this placeholder with raw.olist_orders normalization once the
-- local Postgres raw layer is populated.
select
    cast(null as varchar) as order_id,
    cast(null as varchar) as customer_id,
    cast(null as timestamp) as order_purchase_ts,
    cast(null as varchar) as order_status,
    cast('olist' as varchar) as source_system
where 1 = 0

