create table if not exists raw.olist_orders (
    order_id text,
    customer_id text,
    order_status text,
    order_purchase_timestamp timestamptz,
    order_approved_at timestamptz,
    order_estimated_delivery_date timestamptz
);

create table if not exists raw.olist_order_items (
    order_id text,
    order_item_id integer,
    product_id text,
    seller_id text,
    price numeric(12, 2),
    freight_value numeric(12, 2)
);

create table if not exists raw.olist_customers (
    customer_id text,
    customer_city text,
    customer_state text
);

create table if not exists raw.olist_products (
    product_id text,
    product_category_name text,
    product_name_length integer,
    product_description_length integer,
    product_photos_qty integer,
    product_weight_g integer
);

create table if not exists raw.olist_order_payments (
    order_id text,
    payment_sequential integer,
    payment_type text,
    payment_installments integer,
    payment_value numeric(12, 2)
);

create table if not exists raw.retailrocket_events (
    event_id text,
    visitor_id text,
    event_type text,
    item_id text,
    transaction_id text,
    event_ts timestamptz,
    kafka_topic text
);

create table if not exists raw.dummyjson_products (
    product_id text,
    title text,
    brand text,
    category text,
    price_usd numeric(12, 2),
    ingested_at timestamptz
);

create table if not exists raw.open_meteo_weather (
    weather_date date,
    city text,
    avg_temperature_c numeric(8, 2),
    precipitation_mm numeric(8, 2),
    ingested_at timestamptz
);

create table if not exists raw.frankfurter_fx_rates (
    rate_date date,
    base_currency text,
    quote_currency text,
    fx_rate numeric(18, 8),
    ingested_at timestamptz
);
