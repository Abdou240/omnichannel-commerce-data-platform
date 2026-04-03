select
    order_id,
    order_status
from {{ ref('stg_olist_orders') }}
where lower(order_status) not in ('approved', 'created', 'delivered', 'invoiced', 'processing', 'shipped')

