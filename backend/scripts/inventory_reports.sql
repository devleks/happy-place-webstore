-- ====================================================================
-- INVENTORY REPORTING QUERIES
-- ====================================================================
-- Helpful queries for inventory management and analysis
-- ====================================================================

-- ====================================================================
-- 1. INVENTORY SUMMARY - All Products
-- ====================================================================

-- View current inventory status for all products
SELECT * FROM v_inventory_summary
ORDER BY stock_status, product_name;

-- ====================================================================
-- 2. LOW STOCK ALERT
-- ====================================================================

-- Products that need restocking
SELECT
    product_name,
    sku,
    size,
    color,
    total_quantity,
    online_available,
    store_available,
    stock_status
FROM v_inventory_summary
WHERE stock_status IN ('low_stock', 'out_of_stock')
ORDER BY total_quantity ASC;

-- ====================================================================
-- 3. SALES BY CHANNEL (Last 30 Days)
-- ====================================================================

SELECT
    channel,
    COUNT(*) AS number_of_sales,
    SUM(ABS(quantity)) AS total_units_sold,
    COUNT(DISTINCT variant_id) AS unique_products
FROM inventory_movements
WHERE movement_type = 'sale'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY channel
ORDER BY total_units_sold DESC;

-- ====================================================================
-- 4. TOP SELLING PRODUCTS BY CHANNEL
-- ====================================================================

-- Online top sellers
SELECT
    p.name AS product_name,
    pv.sku,
    pv.size,
    pv.color,
    SUM(ABS(im.quantity)) AS units_sold,
    COUNT(*) AS number_of_orders
FROM inventory_movements im
JOIN product_variants pv ON pv.id = im.variant_id
JOIN products p ON p.id = pv.product_id
WHERE im.movement_type = 'sale'
  AND im.channel = 'online'
  AND im.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.name, pv.sku, pv.size, pv.color
ORDER BY units_sold DESC
LIMIT 10;

-- Store top sellers
SELECT
    p.name AS product_name,
    pv.sku,
    pv.size,
    pv.color,
    SUM(ABS(im.quantity)) AS units_sold,
    COUNT(*) AS number_of_transactions
FROM inventory_movements im
JOIN product_variants pv ON pv.id = im.variant_id
JOIN products p ON p.id = pv.product_id
WHERE im.movement_type = 'sale'
  AND im.channel IN ('store', 'pos')
  AND im.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.name, pv.sku, pv.size, pv.color
ORDER BY units_sold DESC
LIMIT 10;

-- ====================================================================
-- 5. INVENTORY VELOCITY (How fast items sell)
-- ====================================================================

SELECT
    p.name AS product_name,
    pv.sku,
    i.total_quantity AS current_stock,
    SUM(ABS(im.quantity)) AS sold_last_30_days,
    ROUND(SUM(ABS(im.quantity))::NUMERIC / 30, 2) AS avg_daily_sales,
    CASE
        WHEN SUM(ABS(im.quantity)) > 0 THEN
            ROUND((i.total_quantity::NUMERIC / (SUM(ABS(im.quantity))::NUMERIC / 30)), 0)
        ELSE NULL
    END AS days_of_stock_remaining
FROM v_inventory_summary i
JOIN product_variants pv ON pv.id = i.variant_id
JOIN products p ON p.id = pv.product_id
LEFT JOIN inventory_movements im ON im.variant_id = i.variant_id
    AND im.movement_type = 'sale'
    AND im.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.name, pv.sku, i.total_quantity
HAVING SUM(ABS(im.quantity)) > 0
ORDER BY days_of_stock_remaining ASC;

-- ====================================================================
-- 6. CHANNEL PERFORMANCE COMPARISON
-- ====================================================================

SELECT
    DATE(im.created_at) AS sale_date,
    im.channel,
    COUNT(*) AS transactions,
    SUM(ABS(im.quantity)) AS units_sold
FROM inventory_movements im
WHERE im.movement_type = 'sale'
  AND im.created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(im.created_at), im.channel
ORDER BY sale_date DESC, channel;

-- ====================================================================
-- 7. DISPLAY UNITS REPORT
-- ====================================================================

SELECT
    p.name AS product_name,
    pv.sku,
    pv.size,
    pv.color,
    i.total_quantity,
    i.store_display_units,
    i.online_available,
    i.store_available
FROM v_inventory_summary i
JOIN product_variants pv ON pv.id = i.variant_id
JOIN products p ON p.id = pv.product_id
WHERE i.store_display_units > 0
ORDER BY i.store_display_units DESC;

-- ====================================================================
-- 8. INVENTORY MOVEMENTS AUDIT TRAIL
-- ====================================================================

-- Recent movements for a specific product
SELECT
    product_name,
    sku,
    movement_type,
    channel,
    quantity,
    quantity_before,
    quantity_after,
    reference_type,
    reference_id,
    performed_by_email,
    notes,
    created_at
FROM v_inventory_movements_summary
WHERE sku = 'YOUR-SKU-HERE' -- Replace with actual SKU
ORDER BY created_at DESC
LIMIT 50;

-- ====================================================================
-- 9. RESTOCKING RECOMMENDATIONS
-- ====================================================================

WITH sales_velocity AS (
    SELECT
        im.variant_id,
        p.name AS product_name,
        pv.sku,
        SUM(ABS(im.quantity)) AS sold_last_30_days,
        ROUND(SUM(ABS(im.quantity))::NUMERIC / 30, 2) AS avg_daily_sales
    FROM inventory_movements im
    JOIN product_variants pv ON pv.id = im.variant_id
    JOIN products p ON p.id = pv.product_id
    WHERE im.movement_type = 'sale'
      AND im.created_at >= NOW() - INTERVAL '30 days'
    GROUP BY im.variant_id, p.name, pv.sku
)
SELECT
    sv.product_name,
    sv.sku,
    i.total_quantity AS current_stock,
    sv.sold_last_30_days,
    sv.avg_daily_sales,
    CASE
        WHEN sv.avg_daily_sales > 0 THEN
            ROUND((i.total_quantity::NUMERIC / sv.avg_daily_sales), 0)
        ELSE NULL
    END AS days_until_stockout,
    CASE
        WHEN sv.avg_daily_sales > 0 THEN
            ROUND(sv.avg_daily_sales * 14, 0)  -- 2 weeks of stock
        ELSE 10
    END AS recommended_reorder_quantity
FROM sales_velocity sv
JOIN v_inventory_summary i ON i.variant_id = sv.variant_id
WHERE i.total_quantity < (sv.avg_daily_sales * 14)  -- Less than 2 weeks stock
ORDER BY days_until_stockout ASC NULLS LAST;

-- ====================================================================
-- 10. CHANNEL SPLIT ANALYSIS
-- ====================================================================

-- What percentage of sales come from each channel?
SELECT
    channel,
    COUNT(*) AS transactions,
    SUM(ABS(quantity)) AS units_sold,
    ROUND(COUNT(*)::NUMERIC * 100 / SUM(COUNT(*)) OVER (), 2) AS pct_of_transactions,
    ROUND(SUM(ABS(quantity))::NUMERIC * 100 / SUM(SUM(ABS(quantity))) OVER (), 2) AS pct_of_units
FROM inventory_movements
WHERE movement_type = 'sale'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY channel
ORDER BY units_sold DESC;

-- ====================================================================
-- 11. DEAD STOCK ANALYSIS
-- ====================================================================

-- Products with inventory but no sales in 30 days
SELECT
    p.name AS product_name,
    pv.sku,
    pv.size,
    pv.color,
    i.total_quantity,
    i.primary_location,
    i.last_restocked_at,
    COALESCE(last_sale.last_sold, 'Never') AS last_sale_date
FROM v_inventory_summary i
JOIN product_variants pv ON pv.id = i.variant_id
JOIN products p ON p.id = pv.product_id
LEFT JOIN LATERAL (
    SELECT MAX(created_at)::TEXT AS last_sold
    FROM inventory_movements
    WHERE variant_id = i.variant_id
      AND movement_type = 'sale'
) AS last_sale ON TRUE
WHERE i.total_quantity > 0
  AND NOT EXISTS (
      SELECT 1
      FROM inventory_movements im
      WHERE im.variant_id = i.variant_id
        AND im.movement_type = 'sale'
        AND im.created_at >= NOW() - INTERVAL '30 days'
  )
ORDER BY i.total_quantity DESC;

-- ====================================================================
-- 12. HOURLY SALES PATTERN
-- ====================================================================

-- When do most sales happen?
SELECT
    EXTRACT(HOUR FROM created_at) AS hour_of_day,
    channel,
    COUNT(*) AS transactions,
    SUM(ABS(quantity)) AS units_sold
FROM inventory_movements
WHERE movement_type = 'sale'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY EXTRACT(HOUR FROM created_at), channel
ORDER BY hour_of_day, channel;

-- ====================================================================
-- 13. INVENTORY VALUE BY LOCATION
-- ====================================================================

SELECT
    i.primary_location,
    COUNT(DISTINCT i.variant_id) AS unique_products,
    SUM(i.total_quantity) AS total_units,
    SUM(i.total_quantity * p.price) AS estimated_value
FROM v_inventory_summary i
JOIN product_variants pv ON pv.id = i.variant_id
JOIN products p ON p.id = pv.product_id
GROUP BY i.primary_location
ORDER BY estimated_value DESC;

-- ====================================================================
-- END OF REPORTING QUERIES
-- ====================================================================
