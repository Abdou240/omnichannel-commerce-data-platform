{{ config(materialized='view') }}

{% if execute and raw_relation_exists('frankfurter_fx_rates') %}
select
    cast(rate_date as date) as rate_date,
    cast(base_currency as {{ dbt.type_string() }}) as base_currency,
    cast(quote_currency as {{ dbt.type_string() }}) as quote_currency,
    cast(fx_rate as numeric(18, 8)) as fx_rate,
    cast(ingested_at as {{ dbt.type_timestamp() }}) as ingested_at
from {{ source('raw', 'frankfurter_fx_rates') }}
{% else %}
select
    cast(null as date) as rate_date,
    cast(null as {{ dbt.type_string() }}) as base_currency,
    cast(null as {{ dbt.type_string() }}) as quote_currency,
    cast(null as numeric(18, 8)) as fx_rate,
    cast(null as {{ dbt.type_timestamp() }}) as ingested_at
where 1 = 0
{% endif %}
