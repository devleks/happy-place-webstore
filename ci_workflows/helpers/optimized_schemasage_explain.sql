-- ==============================================================================
-- SchemaSage Diagnostic Queries - Optimized Edition
-- ==============================================================================
-- Comprehensive PostgreSQL performance analysis queries
-- Ensure DATABASE_URL points to your database before running
-- Safe to run on production (read-only queries with EXPLAIN ANALYZE)
-- ==============================================================================

-- ==============================================================================
-- SECTION 1: QUERY PERFORMANCE ANALYSIS
-- ==============================================================================

-- Query 1: Recent orders with potential index opportunities
-- Monitors: Sequential scans, buffer usage, execution time
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT o.id,
       o.order_number,
       o.total,
       o.created_at,
       o.status
FROM orders o
WHERE o.created_at >= NOW() - INTERVAL '30 days'
  AND o.status IN ('pending', 'processing', 'completed')
ORDER BY o.created_at DESC
LIMIT 50;

-- Query 2: Cart analytics with join performance
-- Monitors: Join strategy, aggregation performance
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT ci.variant_id,
       SUM(ci.quantity) AS total_quantity,
       COUNT(DISTINCT ci.cart_id) AS num_carts,
       AVG(ci.price) AS avg_price
FROM cart_items ci
JOIN carts c ON ci.cart_id = c.id
WHERE c.updated_at >= NOW() - INTERVAL '7 days'
  AND c.status = 'active'
GROUP BY ci.variant_id
HAVING SUM(ci.quantity) > 0
ORDER BY total_quantity DESC
LIMIT 10;

-- Query 3: Active products with pricing logic
-- Monitors: Function calls, computed columns, filtering
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT p.id,
       p.name,
       p.sku,
       COALESCE(p.sale_price, p.price) AS active_price,
       p.inventory_count,
       p.category_id
FROM products p
WHERE p.is_active = TRUE
  AND p.inventory_count > 0
ORDER BY p.updated_at DESC
LIMIT 25;

-- Query 4: User authentication lookup
-- Monitors: Index usage on email lookups (critical for auth)
EXPLAIN (ANALYZE, BUFFERS)
SELECT u.id,
       u.email,
       u.password_hash,
       u.is_active,
       u.created_at
FROM users u
WHERE u.email = 'test@example.com'
  AND u.is_active = TRUE;

-- Query 5: Order history with user join
-- Monitors: Multi-table join performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT o.id,
       o.order_number,
       o.total,
       u.email AS customer_email,
       o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.id = 123
  AND o.created_at >= NOW() - INTERVAL '90 days'
ORDER BY o.created_at DESC
LIMIT 20;

-- ==============================================================================
-- SECTION 2: INDEX EFFECTIVENESS ANALYSIS
-- ==============================================================================

-- Query 6: Find unused indexes (candidates for removal)
-- These indexes consume disk space and slow down writes
SELECT schemaname,
       tablename,
       indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
       idx_scan AS scans,
       idx_tup_read,
       idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%pkey'  -- Exclude primary keys
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

-- Query 7: Find tables with low index usage (sequential scan heavy)
-- Tables that might benefit from additional indexes
SELECT schemaname,
       tablename,
       seq_scan,
       seq_tup_read,
       idx_scan,
       idx_tup_fetch,
       ROUND(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 2) AS idx_scan_pct
FROM pg_stat_user_tables
WHERE seq_scan + idx_scan > 0
ORDER BY seq_scan DESC
LIMIT 20;

-- Query 8: Index bloat detection
-- Identifies indexes that need REINDEX
SELECT schemaname,
       tablename,
       indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
       idx_scan,
       pg_size_pretty(pg_table_size(tablename::regclass)) AS table_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

-- ==============================================================================
-- SECTION 3: TABLE MAINTENANCE ANALYSIS
-- ==============================================================================

-- Query 9: Tables needing VACUUM (high dead tuple count)
-- Dead tuples slow down queries and waste space
SELECT schemaname,
       relname AS tablename,
       n_live_tup AS live_rows,
       n_dead_tup AS dead_rows,
       ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
       last_vacuum,
       last_autovacuum,
       pg_size_pretty(pg_table_size(schemaname||'.'||relname)) AS table_size
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 20;

-- Query 10: Tables needing ANALYZE (outdated statistics)
-- Stale statistics lead to poor query plans
SELECT schemaname,
       relname AS tablename,
       n_live_tup,
       n_mod_since_analyze AS modifications_since_analyze,
       last_analyze,
       last_autoanalyze,
       ROUND(100.0 * n_mod_since_analyze / NULLIF(n_live_tup, 0), 2) AS mod_pct
FROM pg_stat_user_tables
WHERE n_mod_since_analyze > 1000
ORDER BY n_mod_since_analyze DESC
LIMIT 20;

-- ==============================================================================
-- SECTION 4: SLOW QUERY IDENTIFICATION
-- ==============================================================================

-- Query 11: Slowest queries (requires pg_stat_statements extension)
-- Uncomment if pg_stat_statements is enabled
/*
SELECT 
    SUBSTRING(query, 1, 100) AS short_query,
    calls,
    ROUND(total_exec_time::numeric, 2) AS total_time_ms,
    ROUND(mean_exec_time::numeric, 2) AS avg_time_ms,
    ROUND((100 * total_exec_time / SUM(total_exec_time) OVER())::numeric, 2) AS pct_total_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
*/

-- ==============================================================================
-- SECTION 5: TABLE SIZE & BLOAT ANALYSIS
-- ==============================================================================

-- Query 12: Largest tables by total size (table + indexes)
SELECT schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
       pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) AS table_size,
       pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                      pg_table_size(schemaname||'.'||tablename) - 
                      pg_indexes_size(schemaname||'.'||tablename)) AS toast_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;

-- Query 13: Table bloat estimation
-- Estimates wasted space in tables
SELECT schemaname,
       tablename,
       pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) AS table_size,
       n_live_tup,
       n_dead_tup,
       ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS bloat_pct
FROM pg_stat_user_tables
WHERE n_live_tup + n_dead_tup > 0
ORDER BY n_dead_tup DESC
LIMIT 20;

-- ==============================================================================
-- SECTION 6: CONSTRAINT & FOREIGN KEY ANALYSIS
-- ==============================================================================

-- Query 14: Missing foreign key indexes
-- Foreign keys without indexes can cause lock contention
SELECT tc.table_schema,
       tc.table_name,
       kcu.column_name,
       ccu.table_name AS foreign_table_name,
       ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY tc.table_name, kcu.column_name;

-- ==============================================================================
-- SECTION 7: CONNECTION & LOCK MONITORING
-- ==============================================================================

-- Query 15: Active queries and their duration
SELECT pid,
       usename,
       application_name,
       client_addr,
       state,
       query_start,
       NOW() - query_start AS duration,
       SUBSTRING(query, 1, 100) AS current_query
FROM pg_stat_activity
WHERE state != 'idle'
  AND pid != pg_backend_pid()
ORDER BY query_start
LIMIT 20;

-- Query 16: Blocking queries (lock conflicts)
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- ==============================================================================
-- SECTION 8: CACHE HIT RATIO ANALYSIS
-- ==============================================================================

-- Query 17: Table cache hit ratio (should be >99%)
SELECT schemaname,
       tablename,
       heap_blks_read + heap_blks_hit AS total_reads,
       ROUND(100.0 * heap_blks_hit / NULLIF(heap_blks_read + heap_blks_hit, 0), 2) AS cache_hit_ratio
FROM pg_statio_user_tables
WHERE heap_blks_read + heap_blks_hit > 0
ORDER BY heap_blks_read DESC
LIMIT 20;

-- Query 18: Index cache hit ratio (should be >99%)
SELECT schemaname,
       tablename,
       indexname,
       idx_blks_read + idx_blks_hit AS total_reads,
       ROUND(100.0 * idx_blks_hit / NULLIF(idx_blks_read + idx_blks_hit, 0), 2) AS cache_hit_ratio
FROM pg_statio_user_indexes
WHERE idx_blks_read + idx_blks_hit > 0
ORDER BY idx_blks_read DESC
LIMIT 20;

-- ==============================================================================
-- SECTION 9: RECOMMENDED ACTIONS SUMMARY
-- ==============================================================================

-- Query 19: Priority actions summary
SELECT 
    'VACUUM' AS action,
    COUNT(*) AS count,
    'High dead tuple count' AS reason
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
UNION ALL
SELECT 
    'ANALYZE' AS action,
    COUNT(*) AS count,
    'Stale statistics' AS reason
FROM pg_stat_user_tables
WHERE n_mod_since_analyze > 1000
UNION ALL
SELECT 
    'DROP INDEX' AS action,
    COUNT(*) AS count,
    'Unused indexes' AS reason
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%pkey'
UNION ALL
SELECT 
    'ADD INDEX' AS action,
    COUNT(*) AS count,
    'High sequential scan ratio' AS reason
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan * 10
  AND seq_scan > 100;

-- ==============================================================================
-- EXECUTION NOTES
-- ==============================================================================
-- 
-- For best results:
-- 1. Run during representative load (not peak, not idle)
-- 2. Focus on EXPLAIN queries with high execution times
-- 3. Look for "Seq Scan" in EXPLAIN output → consider adding indexes
-- 4. Review cache hit ratios - aim for >99%
-- 5. Address high dead tuple counts with VACUUM
-- 6. Update stale statistics with ANALYZE
-- 
-- Safe commands to run after analysis:
--   VACUUM ANALYZE tablename;       -- Clean + update stats
--   REINDEX INDEX indexname;        -- Rebuild bloated index
--   DROP INDEX indexname;           -- Remove unused index
-- 
-- ==============================================================================
