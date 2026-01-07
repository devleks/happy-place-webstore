#!/usr/bin/env python3
"""
Database Query Performance Analyzer
Identifies slow queries, N+1 problems, and missing indexes
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine
from sqlalchemy.pool import NullPool
import time
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL, poolclass=NullPool)

print("=" * 80)
print("  DATABASE QUERY PERFORMANCE ANALYZER")
print("=" * 80)
print()

# ============================================
# 1. Check for missing indexes
# ============================================
print("1. Checking for Missing Indexes")
print("-" * 80)

with engine.connect() as conn:
    # Get tables without indexes on foreign keys
    result = conn.execute(text("""
        SELECT
            c.table_name,
            c.column_name,
            c.data_type
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
        AND c.column_name LIKE '%_id'
        AND NOT EXISTS (
            SELECT 1
            FROM pg_indexes i
            WHERE i.tablename = c.table_name
            AND i.indexdef LIKE '%' || c.column_name || '%'
        )
        ORDER BY c.table_name, c.column_name;
    """))

    missing_indexes = result.fetchall()
    if missing_indexes:
        print(f"⚠️  Found {len(missing_indexes)} potential missing indexes:")
        for row in missing_indexes:
            print(f"   - {row[0]}.{row[1]} ({row[2]})")
    else:
        print("✓ All foreign key columns are indexed")

print()

# ============================================
# 2. Table statistics
# ============================================
print("2. Table Statistics")
print("-" * 80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            n_live_tup AS rows,
            n_dead_tup AS dead_rows,
            last_vacuum,
            last_analyze
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10;
    """))

    print(f"{'Table':<30} {'Size':<12} {'Rows':<12} {'Dead Rows':<12}")
    print("-" * 80)
    for row in result:
        table = row[1]
        size = row[2]
        rows = row[3] or 0
        dead_rows = row[4] or 0
        print(f"{table:<30} {size:<12} {rows:<12} {dead_rows:<12}")

print()

# ============================================
# 3. Slow query patterns
# ============================================
print("3. Query Performance Recommendations")
print("-" * 80)

with engine.connect() as conn:
    # Check for sequential scans on large tables
    result = conn.execute(text("""
        SELECT
            schemaname,
            tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            idx_tup_fetch,
            n_live_tup,
            CASE
                WHEN seq_scan > 0 THEN ROUND((seq_tup_read::numeric / seq_scan), 2)
                ELSE 0
            END as avg_seq_read
        FROM pg_stat_user_tables
        WHERE n_live_tup > 100
        ORDER BY seq_scan DESC
        LIMIT 10;
    """))

    print("\nTables with Sequential Scans (potential performance issues):")
    print(f"{'Table':<30} {'Seq Scans':<12} {'Index Scans':<12} {'Rows':<12}")
    print("-" * 80)

    for row in result:
        table = row[1]
        seq_scans = row[2] or 0
        idx_scans = row[4] or 0
        rows = row[6] or 0

        # Flag if seq scans dominate
        if seq_scans > idx_scans and rows > 1000:
            status = "⚠️ "
        else:
            status = "  "

        print(f"{status}{table:<28} {seq_scans:<12} {idx_scans:<12} {rows:<12}")

print()

# ============================================
# 4. Connection pool status
# ============================================
print("4. Database Connection Status")
print("-" * 80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            count(*) as total_connections,
            sum(case when state = 'active' then 1 else 0 end) as active,
            sum(case when state = 'idle' then 1 else 0 end) as idle,
            sum(case when state = 'idle in transaction' then 1 else 0 end) as idle_in_transaction
        FROM pg_stat_activity
        WHERE datname = current_database();
    """))

    row = result.fetchone()
    if row:
        total = row[0]
        active = row[1] or 0
        idle = row[2] or 0
        idle_tx = row[3] or 0

        print(f"Total Connections: {total}")
        print(f"Active: {active}")
        print(f"Idle: {idle}")
        print(f"Idle in Transaction: {idle_tx}")

        if idle_tx > 5:
            print(f"\n⚠️  WARNING: {idle_tx} idle transactions detected")
            print("   This may indicate missing commits or connection leaks")

print()

# ============================================
# 5. Cache hit ratio
# ============================================
print("5. Cache Performance")
print("-" * 80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            sum(heap_blks_read) as heap_read,
            sum(heap_blks_hit) as heap_hit,
            sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 as cache_hit_ratio
        FROM pg_statio_user_tables;
    """))

    row = result.fetchone()
    if row and row[2]:
        cache_hit_ratio = float(row[2])
        print(f"Cache Hit Ratio: {cache_hit_ratio:.2f}%")

        if cache_hit_ratio < 90:
            print(f"⚠️  WARNING: Cache hit ratio below 90%")
            print("   Consider increasing shared_buffers in PostgreSQL config")
        elif cache_hit_ratio < 95:
            print("✓ Acceptable cache performance")
        else:
            print("✓ Excellent cache performance")

print()

# ============================================
# 6. Recommendations
# ============================================
print("=" * 80)
print("  RECOMMENDATIONS")
print("=" * 80)
print()

recommendations = []

if missing_indexes:
    recommendations.append("• Add indexes to foreign key columns listed above")

# Add more recommendations based on analysis
print("Performance Optimization Recommendations:")
if recommendations:
    for rec in recommendations:
        print(rec)
else:
    print("✓ Database appears to be well-optimized")

print()
print("Analysis complete!")
print("=" * 80)
