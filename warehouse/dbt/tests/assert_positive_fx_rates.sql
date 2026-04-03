select
    rate_date,
    quote_currency,
    fx_rate
from {{ ref('stg_frankfurter_fx_rates') }}
where fx_rate <= 0

