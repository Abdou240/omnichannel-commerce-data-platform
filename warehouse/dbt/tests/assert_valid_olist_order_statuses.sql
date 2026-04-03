select
    *
from {{ ref('stg_olist_orders') }}
where lower(order_status) not in ('delivered', 'shipped', 'processing', 'invoiced', 'approved')
