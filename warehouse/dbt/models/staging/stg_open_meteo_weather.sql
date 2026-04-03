{{ config(materialized='view') }}

select
    cast(null as date) as weather_date,
    cast(null as varchar) as city,
    cast(null as numeric(8, 2)) as avg_temperature_c,
    cast(null as numeric(8, 2)) as precipitation_mm
where 1 = 0

