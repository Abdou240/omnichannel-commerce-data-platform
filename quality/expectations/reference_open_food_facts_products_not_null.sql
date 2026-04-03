select
    product_code,
    product_name
from raw.open_food_facts_products
where product_code is null
   or nullif(trim(product_code), '') is null
   or product_name is null
   or nullif(trim(product_name), '') is null;
