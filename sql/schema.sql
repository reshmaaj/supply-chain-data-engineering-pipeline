dim_customer
dim_product
dim_date
dim_location
fact_order_items
pipeline_metadata
pipeline_log

CREATE TABLE logistics_raw (
    order_type VARCHAR(50),
    actual_shipping_days INTEGER,
    scheduled_shipping_days INTEGER,
    benefit_per_order NUMERIC,
    sales_per_customer NUMERIC,
    delivery_status VARCHAR(50),
    late_delivery_risk INTEGER,
    category_id INTEGER,
    category_name VARCHAR(100),
    customer_city VARCHAR(100),
    customer_country VARCHAR(100),
    customer_id INTEGER,
    customer_segment VARCHAR(50),
    customer_state VARCHAR(100),
    customer_zipcode NUMERIC,
    department_id INTEGER,
    department_name VARCHAR(100),
    market VARCHAR(50),
    order_city VARCHAR(100),
    order_country VARCHAR(100),
    order_customer_id INTEGER,
    order_date TIMESTAMP,
    order_id INTEGER,
    order_item_product_id INTEGER,
    order_item_discount NUMERIC,
    order_item_discount_rate NUMERIC,
    order_item_id INTEGER,
    order_item_product_price NUMERIC,
    order_item_profit_ratio NUMERIC,
    order_item_quantity INTEGER,
    sales NUMERIC,
    order_item_total NUMERIC,
    order_profit_per_order NUMERIC,
    order_region VARCHAR(100),
    order_state VARCHAR(100),
    order_status VARCHAR(50),
    product_id INTEGER,
    product_category_id INTEGER,
    product_name VARCHAR(255),
    product_price NUMERIC,
    product_status INTEGER,
    shipping_date TIMESTAMP,
    shipping_mode VARCHAR(50)
);

CREATE TABLE dim_product (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(255),
    product_category_id INTEGER,
    category_id INTEGER,
    category_name VARCHAR(100),
    department_id INTEGER,
    department_name VARCHAR(100),
    product_price NUMERIC,
    product_status INTEGER
);

INSERT INTO dim_product (
    product_id,
    product_name,
    product_category_id,
    category_id,
    category_name,
    department_id,
    department_name,
    product_price,
    product_status
)
SELECT DISTINCT
    product_id,
    product_name,
    product_category_id,
    category_id,
    category_name,
    department_id,
    department_name,
    product_price,
    product_status
FROM logistics_raw;

CREATE TABLE dim_customer (
    customer_id INTEGER PRIMARY KEY,
    customer_segment VARCHAR(50),
    customer_city VARCHAR(100),
    customer_state VARCHAR(100),
    customer_country VARCHAR(100),
    customer_zipcode NUMERIC
);

INSERT INTO dim_customer (
    customer_id,
    customer_segment,
    customer_city,
    customer_state,
    customer_country,
    customer_zipcode
)
SELECT DISTINCT
    customer_id,
    customer_segment,
    customer_city,
    customer_state,
    customer_country,
    customer_zipcode
FROM logistics_raw;

CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,
    date DATE,
    year INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    quarter INTEGER,
    day INTEGER
);

INSERT INTO dim_date (
    date_id,
    date,
    year,
    month,
    month_name,
    quarter,
    day
)
SELECT DISTINCT
    TO_CHAR(order_date, 'YYYYMMDD')::INTEGER AS date_id,
    order_date::DATE AS date,
    EXTRACT(YEAR FROM order_date)::INTEGER AS year,
    EXTRACT(MONTH FROM order_date)::INTEGER AS month,
    TO_CHAR(order_date, 'Month') AS month_name,
    EXTRACT(QUARTER FROM order_date)::INTEGER AS quarter,
    EXTRACT(DAY FROM order_date)::INTEGER AS day
FROM logistics_raw;

CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    order_city VARCHAR(100),
    order_state VARCHAR(100),
    order_country VARCHAR(100),
    order_region VARCHAR(100)
);

INSERT INTO dim_location (
    order_city,
    order_state,
    order_country,
    order_region
)
SELECT DISTINCT
    order_city,
    order_state,
    order_country,
    order_region
FROM logistics_raw;

INSERT INTO fact_order_items (
    order_item_id,
    order_id,
    customer_id,
    product_id,
    date_id,
    location_id,
    order_type,
    order_item_quantity,
    sales,
    order_item_discount,
    order_item_discount_rate,
    order_item_total,
    order_profit_per_order,
    actual_shipping_days,
    scheduled_shipping_days,
    late_delivery_risk,
    delivery_status,
    order_status,
    shipping_mode
)
SELECT
    r.order_item_id,
    r.order_id,
    r.customer_id,
    r.product_id,
    d.date_id,
    l.location_id,
    r.order_type,
    r.order_item_quantity,
    r.sales,
    r.order_item_discount,
    r.order_item_discount_rate,
    r.order_item_total,
    r.order_profit_per_order,
    r.actual_shipping_days,
    r.scheduled_shipping_days,
    r.late_delivery_risk,
    r.delivery_status,
    r.order_status,
    r.shipping_mode

FROM logistics_raw r

JOIN dim_date d
    ON r.order_date::DATE = d.date

JOIN dim_location l
    ON r.order_city = l.order_city
    AND r.order_state = l.order_state
    AND r.order_country = l.order_country
    AND r.order_region = l.order_region;

ALTER TABLE fact_order_items
ADD CONSTRAINT fk_fact_customer
FOREIGN KEY (customer_id)
REFERENCES dim_customer(customer_id);

ALTER TABLE fact_order_items
ADD CONSTRAINT fk_fact_product
FOREIGN KEY (product_id)
REFERENCES dim_product(product_id);

ALTER TABLE fact_order_items
ADD CONSTRAINT fk_fact_date
FOREIGN KEY (date_id)
REFERENCES dim_date(date_id);

ALTER TABLE fact_order_items
ADD CONSTRAINT fk_fact_location
FOREIGN KEY (location_id)
REFERENCES dim_location(location_id);