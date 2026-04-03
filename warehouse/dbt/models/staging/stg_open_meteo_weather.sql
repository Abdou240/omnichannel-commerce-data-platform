{{ config(materialized='view') }}

{% if execute and raw_relation_exists('open_meteo_weather') %}
select
    cast(weather_date as date) as weather_date,
    cast(city as {{ dbt.type_string() }}) as city,
    cast(avg_temperature_c as numeric(8, 2)) as avg_temperature_c,
    cast(precipitation_mm as numeric(8, 2)) as precipitation_mm,
    cast(ingested_at as {{ dbt.type_timestamp() }}) as ingested_at
from {{ source('raw', 'open_meteo_weather') }}
{% else %}
select
    cast(null as date) as weather_date,
    cast(null as {{ dbt.type_string() }}) as city,
    cast(null as numeric(8, 2)) as avg_temperature_c,
    cast(null as numeric(8, 2)) as precipitation_mm,
    cast(null as {{ dbt.type_timestamp() }}) as ingested_at
where 1 = 0
{% endif %}
