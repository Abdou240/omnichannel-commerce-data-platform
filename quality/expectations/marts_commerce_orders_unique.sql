select
    order_id,
    count(*) as duplicate_count
from marts.fct_commerce_orders
group by 1
having count(*) > 1
