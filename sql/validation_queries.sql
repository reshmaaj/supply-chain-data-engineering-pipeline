-- ============================================================
-- Logistics Data Engineering Project
-- Warehouse Validation Queries
-- ============================================================


-- 1. Validate fact table grain
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT order_item_id) AS unique_order_items,
    COUNT(DISTINCT order_id) AS unique_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(DISTINCT product_id) AS unique_products
FROM fact_order_items;


-- 2. Check for orphan customer keys
SELECT COUNT(*) AS orphan_customers
FROM fact_order_items f
LEFT JOIN dim_customer c
    ON f.customer_id = c.customer_id
WHERE c.customer_id IS NULL;


-- 3. Check for orphan product keys
SELECT COUNT(*) AS orphan_products
FROM fact_order_items f
LEFT JOIN dim_product p
    ON f.product_id = p.product_id
WHERE p.product_id IS NULL;


-- 4. Check for orphan date keys
SELECT COUNT(*) AS orphan_dates
FROM fact_order_items f
LEFT JOIN dim_date d
    ON f.date_id = d.date_id
WHERE d.date_id IS NULL;


-- 5. Validate dashboard KPIs
SELECT
    ROUND(SUM(sales)::numeric, 2) AS total_sales,
    ROUND(SUM(order_profit_per_order)::numeric, 2) AS total_profit,
    COUNT(DISTINCT order_item_id) AS order_items,
    ROUND(AVG(late_delivery_risk) * 100, 2) AS late_delivery_risk_pct
FROM fact_order_items;