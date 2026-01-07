# 12 - Database Migration Workflow

Comprehensive workflow for planning, executing, and validating database schema changes and data migrations across any database technology.

---

## Overview

This workflow ensures safe, reversible database migrations with zero or minimal downtime, complete audit trails, and rollback capabilities.

## When to Use

- Schema changes (add/modify/drop tables, columns, indexes)
- Data transformations or backfills
- Database version upgrades
- Cross-database migrations
- Sharding or partitioning changes
- Production data fixes

---

## Quick Start

```bash
./blackbox.sh start "migration-[ticket]-[description]"
```

---

## Cascade Prompt

```
Execute Database Migration workflow for: [DESCRIPTION]

Migration type: [schema/data/hybrid]
Database: [PostgreSQL/MySQL/MongoDB/etc.]
Environment: [dev/staging/production]

Steps:
1. Analyze current schema state
2. Design migration strategy
3. Create migration scripts
4. Test in lower environments
5. Plan rollback procedure
6. Execute with monitoring
7. Validate and document

Reference: workflows/tier-2/12-database-migration.md
Session: [CURRENT-SESSION-ID]
```

---

## Pre-Migration Checklist

```markdown
## Pre-Migration Checklist

### Planning
- [ ] Migration scope documented
- [ ] Affected tables/collections identified
- [ ] Data volume estimated
- [ ] Downtime requirements assessed
- [ ] Stakeholders notified

### Safety
- [ ] Backup strategy confirmed
- [ ] Rollback plan documented
- [ ] Point-in-time recovery tested
- [ ] Read replicas considered

### Testing
- [ ] Migration tested on dev
- [ ] Migration tested on staging
- [ ] Performance impact measured
- [ ] Data integrity validated

### Dependencies
- [ ] Application compatibility verified
- [ ] API changes coordinated
- [ ] Cache invalidation planned
- [ ] Queue draining considered
```

---

## Phase 1: Analysis

### Current State Assessment

```sql
-- PostgreSQL: Get table info
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
    (SELECT count(*) FROM information_schema.columns 
     WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;

-- Check foreign key dependencies
SELECT
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

### Migration Impact Analysis

```markdown
## Impact Analysis Template

### Tables Affected
| Table | Rows | Size | Operation | Risk |
|-------|------|------|-----------|------|
| users | 1M | 500MB | ADD COLUMN | Low |
| orders | 10M | 5GB | ALTER TYPE | High |

### Estimated Duration
- Schema changes: [X minutes]
- Data backfill: [X minutes]
- Index creation: [X minutes]
- Total: [X minutes]

### Lock Requirements
| Operation | Lock Type | Duration |
|-----------|-----------|----------|
| ADD COLUMN | ACCESS EXCLUSIVE | < 1s |
| CREATE INDEX CONCURRENTLY | SHARE UPDATE EXCLUSIVE | [varies] |

### Application Impact
- [ ] Read operations: [affected/not affected]
- [ ] Write operations: [affected/not affected]
- [ ] API endpoints: [list affected]
```

---

## Phase 2: Migration Design

### Migration Strategy Selection

| Strategy | Use When | Downtime |
|----------|----------|----------|
| **Direct** | Small tables, dev/staging | Yes |
| **Expand-Contract** | Production, backward compat needed | Minimal |
| **Dual-Write** | Zero downtime critical | None |
| **Shadow** | High-risk transformations | None |
| **Blue-Green** | Major version upgrades | Switchover only |

### Expand-Contract Pattern

```
Phase 1: EXPAND
├── Add new column (nullable)
├── Deploy app that writes to both
├── Backfill existing data
└── Verify data consistency

Phase 2: MIGRATE
├── Deploy app that reads from new
├── Monitor for issues
└── Validate all reads successful

Phase 3: CONTRACT
├── Remove old column writes from app
├── Drop old column
└── Clean up
```

### Migration Script Template

```sql
-- migrations/V20241217_001__add_user_preferences.sql

-- ============================================
-- Migration: Add user preferences column
-- Author: [name]
-- Session: CONV-2024-12-17-001
-- Ticket: PROJ-1234
-- ============================================

-- Pre-migration validation
DO $$
BEGIN
    -- Check preconditions
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'users' AND column_name = 'preferences') THEN
        RAISE EXCEPTION 'Column preferences already exists';
    END IF;
END $$;

-- Migration
BEGIN;

-- Add column (nullable for backward compatibility)
ALTER TABLE users 
ADD COLUMN preferences JSONB DEFAULT '{}';

-- Add index for JSON queries
CREATE INDEX CONCURRENTLY idx_users_preferences 
ON users USING GIN (preferences);

-- Log migration
INSERT INTO schema_migrations (version, description, applied_at)
VALUES ('V20241217_001', 'Add user preferences column', NOW());

COMMIT;

-- Post-migration validation
DO $$
DECLARE
    col_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'preferences'
    ) INTO col_exists;
    
    IF NOT col_exists THEN
        RAISE EXCEPTION 'Migration validation failed: column not created';
    END IF;
END $$;
```

---

## Phase 3: Rollback Planning

### Rollback Script Template

```sql
-- rollbacks/V20241217_001__add_user_preferences_ROLLBACK.sql

-- ============================================
-- ROLLBACK: Add user preferences column
-- ============================================

BEGIN;

-- Remove index first
DROP INDEX IF EXISTS idx_users_preferences;

-- Remove column
ALTER TABLE users DROP COLUMN IF EXISTS preferences;

-- Remove migration record
DELETE FROM schema_migrations WHERE version = 'V20241217_001';

COMMIT;
```

### Rollback Decision Matrix

| Scenario | Action | Time Limit |
|----------|--------|------------|
| Migration fails | Immediate rollback | N/A |
| Data corruption detected | Restore from backup | 15 min |
| Performance degradation | Rollback if > 20% impact | 1 hour |
| Application errors spike | Rollback if > 1% error rate | 30 min |
| Business logic issues | Assess and decide | 24 hours |

---

## Phase 4: Execution

### Pre-Execution Checklist

```bash
#!/bin/bash
# pre-migration-checks.sh

echo "🔍 Pre-Migration Checks"
echo "======================="

# 1. Verify backup
echo "1. Checking backup status..."
pg_dump --version > /dev/null && echo "   ✅ pg_dump available"

# 2. Check disk space
echo "2. Checking disk space..."
df -h /var/lib/postgresql | tail -1

# 3. Check replication lag
echo "3. Checking replication lag..."
psql -c "SELECT client_addr, state, sent_lsn, write_lsn, 
         pg_wal_lsn_diff(sent_lsn, write_lsn) as lag_bytes 
         FROM pg_stat_replication;"

# 4. Check active connections
echo "4. Checking active connections..."
psql -c "SELECT count(*) as connections FROM pg_stat_activity 
         WHERE state = 'active';"

# 5. Check long-running queries
echo "5. Checking long-running queries..."
psql -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
         FROM pg_stat_activity 
         WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"

echo ""
echo "Ready to proceed? (y/n)"
```

### Execution Script

```bash
#!/bin/bash
# execute-migration.sh

set -e  # Exit on error

MIGRATION_FILE=$1
LOG_FILE="migration_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 Starting Migration" | tee -a $LOG_FILE
echo "===================" | tee -a $LOG_FILE
echo "File: $MIGRATION_FILE" | tee -a $LOG_FILE
echo "Time: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Create backup point
echo "📸 Creating backup point..." | tee -a $LOG_FILE
pg_dump -Fc $DATABASE_URL > "backup_pre_migration_$(date +%Y%m%d_%H%M%S).dump"

# Execute migration
echo "⚡ Executing migration..." | tee -a $LOG_FILE
psql $DATABASE_URL -f $MIGRATION_FILE 2>&1 | tee -a $LOG_FILE

# Verify
echo "✅ Verifying migration..." | tee -a $LOG_FILE
psql $DATABASE_URL -c "SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 1;"

echo "" | tee -a $LOG_FILE
echo "🎉 Migration complete!" | tee -a $LOG_FILE
```

### Monitoring During Migration

```sql
-- Monitor migration progress (for long-running operations)

-- Check table bloat during migration
SELECT schemaname, relname, 
       pg_size_pretty(pg_total_relation_size(relid)) as total_size,
       pg_size_pretty(pg_relation_size(relid)) as table_size,
       pg_size_pretty(pg_indexes_size(relid)) as index_size
FROM pg_stat_user_tables
WHERE relname = 'your_table';

-- Monitor locks
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity 
    ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity 
    ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

---

## Phase 5: Validation

### Data Integrity Checks

```sql
-- Validation queries template

-- 1. Row count comparison (before/after)
SELECT 'Before' as stage, count(*) FROM users_backup
UNION ALL
SELECT 'After' as stage, count(*) FROM users;

-- 2. Null check on required fields
SELECT count(*) as null_count 
FROM users 
WHERE required_field IS NULL;

-- 3. Referential integrity
SELECT u.id, u.company_id
FROM users u
LEFT JOIN companies c ON u.company_id = c.id
WHERE u.company_id IS NOT NULL AND c.id IS NULL;

-- 4. Data format validation
SELECT id, email
FROM users
WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

-- 5. Business logic validation
SELECT id, created_at, updated_at
FROM users
WHERE updated_at < created_at;
```

### Post-Migration Checklist

```markdown
## Post-Migration Checklist

### Immediate (< 5 min)
- [ ] Migration completed without errors
- [ ] Application responding normally
- [ ] No error spikes in monitoring
- [ ] Basic functionality verified

### Short-term (< 1 hour)
- [ ] All critical paths tested
- [ ] Performance metrics stable
- [ ] No data inconsistencies reported
- [ ] Rollback window passed

### Documentation
- [ ] Migration logged in Black Box
- [ ] Runbook updated
- [ ] Schema documentation updated
- [ ] Team notified of completion
```

---

## Database-Specific Guidelines

### PostgreSQL

```sql
-- Use CONCURRENTLY for index creation
CREATE INDEX CONCURRENTLY idx_name ON table(column);

-- Use batched updates for large tables
WITH batch AS (
    SELECT id FROM large_table 
    WHERE needs_update = true 
    LIMIT 10000
)
UPDATE large_table SET column = 'value'
WHERE id IN (SELECT id FROM batch);

-- Add columns with defaults safely (PG 11+)
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
```

### MySQL

```sql
-- Use pt-online-schema-change for large tables
-- pt-online-schema-change --alter "ADD COLUMN status VARCHAR(20)" D=db,t=users

-- Or use gh-ost
-- gh-ost --alter="ADD COLUMN status VARCHAR(20)" --database=db --table=users

-- Batched deletes
DELETE FROM large_table WHERE condition LIMIT 10000;
```

### MongoDB

```javascript
// Add field with default
db.users.updateMany(
    { preferences: { $exists: false } },
    { $set: { preferences: {} } }
);

// Rename field
db.users.updateMany(
    {},
    { $rename: { "oldField": "newField" } }
);

// Background index creation
db.users.createIndex(
    { email: 1 },
    { background: true, unique: true }
);
```

---

## Black Box Integration

```bash
# Start migration session
./blackbox.sh start "migration-PROJ-1234-add-preferences"

# Log key events
./blackbox.sh checkpoint "Pre-migration backup complete"
./blackbox.sh action "Executed schema migration" "success"
./blackbox.sh decision "Used CONCURRENTLY for index" "Avoid table locks"
./blackbox.sh milestone "Migration validated"

# End session
./blackbox.sh end "Migration complete, monitoring for 24h"
```

---

## Templates

### Migration Request Template

```markdown
## Migration Request

**Ticket:** [PROJ-XXXX]
**Requested by:** [Name]
**Target date:** [Date]

### Description
[What needs to change and why]

### Schema Changes
```sql
[SQL statements]
```

### Data Changes
[Description of data transformations]

### Rollback Plan
[How to reverse if needed]

### Testing Done
- [ ] Local
- [ ] Dev
- [ ] Staging

### Sign-offs
- [ ] DBA Review
- [ ] Tech Lead
- [ ] Product Owner (if data change)
```

---

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Start migration session | `./blackbox.sh start "migration-[id]"` |
| Create backup | `pg_dump -Fc > backup.dump` |
| Check locks | `SELECT * FROM pg_locks WHERE NOT granted;` |
| Monitor progress | `SELECT * FROM pg_stat_progress_create_index;` |
| Validate counts | `SELECT count(*) FROM table;` |
| Rollback | Execute rollback script |

---

*Database Migration Workflow v1.0*
*Integrates with Black Box for full audit trail*
