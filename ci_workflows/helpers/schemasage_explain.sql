-- SchemaSage diagnostic queries
-- Ensure DATABASE_URL points to the Happy Place database before running.

EXPLAIN (ANALYZE, BUFFERS)
SELECT o.id,
       o.order_number,
       o.total,
       o.created_at
FROM orders o
WHERE o.created_at >= NOW() - INTERVAL '30 days'
ORDER BY o.created_at DESC
LIMIT 50;

EXPLAIN (ANALYZE, BUFFERS)
SELECT ci.variant_id,
       SUM(ci.quantity) AS total_quantity
FROM cart_items ci
JOIN carts c ON ci.cart_id = c.id
WHERE c.updated_at >= NOW() - INTERVAL '7 days'
GROUP BY ci.variant_id
ORDER BY total_quantity DESC
LIMIT 10;

EXPLAIN (ANALYZE, BUFFERS)
SELECT p.id,
       p.name,
       COALESCE(p.sale_price, p.price) AS active_price
FROM products p
WHERE p.is_active = TRUE
ORDER BY p.updated_at DESC
LIMIT 25;
