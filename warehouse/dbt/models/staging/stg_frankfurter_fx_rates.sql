{{ config(materialized='view') }}

select
    cast(null as date) as rate_date,
    cast(null as varchar) as base_currency,
    cast(null as varchar) as quote_currency,
    cast(null as numeric(18, 8)) as fx_rate
where 1 = 0

