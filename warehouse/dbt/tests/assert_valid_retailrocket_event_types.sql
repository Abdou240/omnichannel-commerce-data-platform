select
    *
from {{ ref('stg_retailrocket_events') }}
where lower(event_type) not in ('view', 'addtocart', 'transaction')
