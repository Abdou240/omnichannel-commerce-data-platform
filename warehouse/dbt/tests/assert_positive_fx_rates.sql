select
    *
from {{ ref('stg_frankfurter_fx_rates') }}
where fx_rate <= 0
