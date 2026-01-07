# SchemaSage Database Audit Report
**Generated:** 2025-12-20 15:59:10 UTC  
**Platform:** Darwin x86_64  
**Database:** postgresql://postgres:Alway%24%20B3l13ving@***

## Artifacts Generated
- Schema snapshot: `reports/schemasage_schema.txt`
- Index analysis: `reports/schemasage_indexes.txt`
- Table statistics: `reports/schemasage_table_stats.txt`
- Query plans: `reports/schemasage_explain.txt`
- Migration log: `reports/schemasage_migration.log`
- Stored procedures log: `reports/schemasage_procedure.log`

## Key Findings
✅ No major issues detected

## Recommended Actions
1. **Review EXPLAIN output** for sequential scans with high buffer hits
2. **Compare schema** with `DATABASE_SCHEMA_FINAL.md` to spot drift
3. **Update indexes** where plans show repeated full scans
4. **Run VACUUM** on tables with high dead tuple counts
5. **Drop unused indexes** to reduce write overhead (verify first!)

## Quick Wins
```sql
-- Find slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Find missing indexes
SELECT schemaname, tablename, seq_scan, idx_scan 
FROM pg_stat_user_tables 
WHERE seq_scan > idx_scan 
ORDER BY seq_scan DESC;

-- Find bloated tables
SELECT schemaname, tablename, n_dead_tup 
FROM pg_stat_user_tables 
WHERE n_dead_tup > 1000 
ORDER BY n_dead_tup DESC;
```
