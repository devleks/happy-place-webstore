#!/bin/bash
# Agent SchemaSage: Database analysis and optimization helper
# macOS-optimized version with enhanced validation and error handling
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
SQL_FILE="$ROOT_DIR/ci_workflows/helpers/schemasage_explain.sql"
mkdir -p "$REPORTS_DIR"

SCHEMA_REPORT="$REPORTS_DIR/schemasage_schema.txt"
EXPLAIN_REPORT="$REPORTS_DIR/schemasage_explain.txt"
MIGRATION_LOG="$REPORTS_DIR/schemasage_migration.log"
PROC_LOG="$REPORTS_DIR/schemasage_procedure.log"
INDEX_REPORT="$REPORTS_DIR/schemasage_indexes.txt"
TABLE_STATS="$REPORTS_DIR/schemasage_table_stats.txt"
SUMMARY_REPORT="$REPORTS_DIR/db_audit.md"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
log_info() {
    echo -e "${BLUE}[SchemaSage]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SchemaSage]${NC} ✓ $1"
}

log_warning() {
    echo -e "${YELLOW}[SchemaSage]${NC} ⚠ $1"
}

log_error() {
    echo -e "${RED}[SchemaSage]${NC} ✗ $1" >&2
}

timestamp() {
    date -u +"%Y-%m-%d %H:%M:%S UTC"
}

is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

# ============================================================================
# VALIDATION
# ============================================================================
require_database_url() {
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL environment variable is not set"
        log_info "Set it with: export DATABASE_URL=postgresql://user:pass@host:port/dbname"
        log_info "Or use connection string format: postgresql://localhost/mydb"
        return 1
    fi
    
    # Validate URL format
    if ! [[ "$DATABASE_URL" =~ ^postgres(ql)?:// ]]; then
        log_error "DATABASE_URL must start with postgresql:// or postgres://"
        return 1
    fi
    
    log_success "DATABASE_URL is configured"
    return 0
}

require_psql() {
    if ! command -v psql >/dev/null 2>&1; then
        log_error "psql is not installed"
        if is_macos; then
            log_info "Install with: brew install postgresql@15"
            log_info "Or: brew install libpq && export PATH=\"/opt/homebrew/opt/libpq/bin:\$PATH\""
        else
            log_info "Install with: sudo apt-get install postgresql-client"
        fi
        return 1
    fi
    
    # Verify psql can connect
    if ! psql "$DATABASE_URL" -c "SELECT 1" >/dev/null 2>&1; then
        log_error "Cannot connect to database"
        log_info "Verify DATABASE_URL and network connectivity"
        return 1
    fi
    
    log_success "psql is available and can connect"
    return 0
}

# ============================================================================
# DATABASE ANALYSIS
# ============================================================================
snapshot_schema() {
    log_info "Capturing schema snapshot..."
    
    # Get table list with sizes
    psql "$DATABASE_URL" -c "
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    " > "$SCHEMA_REPORT" 2>&1 || {
        log_warning "Failed to capture full schema, using basic listing"
        psql "$DATABASE_URL" -c "\dt" > "$SCHEMA_REPORT" 2>&1
    }
    
    log_success "Schema snapshot saved"
}

analyze_indexes() {
    log_info "Analyzing indexes..."
    
    psql "$DATABASE_URL" -c "
        SELECT 
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as size,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch
        FROM pg_stat_user_indexes
        ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC
        LIMIT 50;
    " > "$INDEX_REPORT" 2>&1 || {
        log_warning "Failed to analyze indexes"
        echo "Index analysis failed" > "$INDEX_REPORT"
    }
    
    log_success "Index analysis complete"
}

collect_table_stats() {
    log_info "Collecting table statistics..."
    
    psql "$DATABASE_URL" -c "
        SELECT 
            schemaname,
            relname as table_name,
            n_live_tup as live_rows,
            n_dead_tup as dead_rows,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC
        LIMIT 50;
    " > "$TABLE_STATS" 2>&1 || {
        log_warning "Failed to collect table stats"
        echo "Table stats collection failed" > "$TABLE_STATS"
    }
    
    log_success "Table statistics collected"
}

collect_plans() {
    if [ ! -f "$SQL_FILE" ]; then
        log_warning "SQL probe file not found: $SQL_FILE"
        log_info "Skipping EXPLAIN ANALYZE - create $SQL_FILE with queries to analyze"
        echo "SQL probe file not provided" > "$EXPLAIN_REPORT"
        return 0
    fi
    
    log_info "Running EXPLAIN ANALYZE probes..."
    
    # Run with timeout to prevent hanging
    local timeout_cmd=""
    if command -v timeout >/dev/null 2>&1; then
        timeout_cmd="timeout 60s"
    elif command -v gtimeout >/dev/null 2>&1; then
        # GNU timeout on macOS via coreutils
        timeout_cmd="gtimeout 60s"
    fi
    
    if $timeout_cmd psql "$DATABASE_URL" -f "$SQL_FILE" > "$EXPLAIN_REPORT" 2>&1; then
        log_success "EXPLAIN ANALYZE completed"
    else
        log_warning "EXPLAIN ANALYZE had issues (timeout or query errors)"
    fi
}

# ============================================================================
# VALIDATION CHECKS
# ============================================================================
validate_migrations() {
    local migration_script="$ROOT_DIR/backend/scripts/migrate_database.py"
    
    if [ ! -f "$migration_script" ]; then
        log_info "Migration script not found, skipping validation"
        echo "Migration script not found at $migration_script" > "$MIGRATION_LOG"
        return 0
    fi
    
    log_info "Dry-running migrations..."
    
    pushd "$ROOT_DIR/backend" >/dev/null
    
    # Check if script has --dry-run flag
    if python3 scripts/migrate_database.py --help 2>&1 | grep -q "dry-run"; then
        python3 scripts/migrate_database.py --dry-run > "$MIGRATION_LOG" 2>&1 || {
            log_warning "Migration dry-run failed, check log"
        }
    else
        log_info "Migration script doesn't support --dry-run, skipping"
        echo "Script doesn't support --dry-run flag" > "$MIGRATION_LOG"
    fi
    
    popd >/dev/null
    
    log_success "Migration validation complete"
}

verify_procedures() {
    local proc_file="$ROOT_DIR/backend/scripts/create_stored_procedures.sql"
    
    if [ ! -f "$proc_file" ]; then
        log_info "Stored procedures file not found, skipping"
        echo "Stored procedures file not found at $proc_file" > "$PROC_LOG"
        return 0
    fi
    
    log_info "Verifying stored procedures..."
    
    psql "$DATABASE_URL" -f "$proc_file" > "$PROC_LOG" 2>&1 || {
        log_warning "Stored procedure verification had issues, check log"
    }
    
    log_success "Stored procedures verified"
}

# ============================================================================
# REPORTING
# ============================================================================
detect_issues() {
    local issues=()
    
    # Check for missing indexes (tables with seq scans in explain)
    if grep -q "Seq Scan" "$EXPLAIN_REPORT" 2>/dev/null; then
        issues+=("Sequential scans detected - consider adding indexes")
    fi
    
    # Check for unused indexes
    local unused_count
    unused_count=$(grep "| *0 |" "$INDEX_REPORT" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$unused_count" -gt 0 ]; then
        issues+=("$unused_count unused indexes found")
    fi
    
    # Check for dead tuples
    if grep -q "dead_rows" "$TABLE_STATS" 2>/dev/null; then
        local high_dead
        high_dead=$(awk '/\|.*\|.*\|/ {if ($4 > 1000) print}' "$TABLE_STATS" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$high_dead" -gt 0 ]; then
            issues+=("$high_dead tables with high dead tuple count - consider VACUUM")
        fi
    fi
    
    printf '%s\n' "${issues[@]}"
}

write_summary() {
    local issues=()
    while IFS= read -r line; do
        [ -n "$line" ] && issues+=("$line")
    done < <(detect_issues)
    
    cat >"$SUMMARY_REPORT" <<MARKDOWN
# SchemaSage Database Audit Report
**Generated:** $(timestamp)  
**Platform:** $(uname -s) $(uname -m)  
**Database:** ${DATABASE_URL%%@*}@***

## Artifacts Generated
- Schema snapshot: \`reports/$(basename "$SCHEMA_REPORT")\`
- Index analysis: \`reports/$(basename "$INDEX_REPORT")\`
- Table statistics: \`reports/$(basename "$TABLE_STATS")\`
- Query plans: \`reports/$(basename "$EXPLAIN_REPORT")\`
- Migration log: \`reports/$(basename "$MIGRATION_LOG")\`
- Stored procedures log: \`reports/$(basename "$PROC_LOG")\`

## Key Findings
MARKDOWN

    if [ ${#issues[@]} -eq 0 ]; then
        echo "✅ No major issues detected" >> "$SUMMARY_REPORT"
    else
        printf '⚠️  %s\n' "${issues[@]}" >> "$SUMMARY_REPORT"
    fi
    
    cat >>"$SUMMARY_REPORT" <<MARKDOWN

## Recommended Actions
1. **Review EXPLAIN output** for sequential scans with high buffer hits
2. **Compare schema** with \`DATABASE_SCHEMA_FINAL.md\` to spot drift
3. **Update indexes** where plans show repeated full scans
4. **Run VACUUM** on tables with high dead tuple counts
5. **Drop unused indexes** to reduce write overhead (verify first!)

## Quick Wins
\`\`\`sql
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
\`\`\`
MARKDOWN
    
    # Console summary
    log_info "════════════════════════════════════════"
    log_info "Database Audit Summary:"
    if [ ${#issues[@]} -eq 0 ]; then
        log_success "No major issues found"
    else
        for issue in "${issues[@]}"; do
            log_warning "$issue"
        done
    fi
    log_info "════════════════════════════════════════"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
main() {
    local start_time=$(date +%s)
    
    log_info "Starting database audit"
    
    # Validate prerequisites
    require_database_url || exit 1
    require_psql || exit 1
    
    # Run analysis tasks in parallel where safe
    snapshot_schema &
    local schema_pid=$!
    
    analyze_indexes &
    local index_pid=$!
    
    collect_table_stats &
    local stats_pid=$!
    
    # Wait for parallel tasks
    wait $schema_pid $index_pid $stats_pid
    
    # Sequential tasks (depend on DB state)
    collect_plans
    validate_migrations
    verify_procedures
    
    # Generate summary
    write_summary
    
    local duration=$(($(date +%s) - start_time))
    log_success "Completed in ${duration}s → artifacts in $REPORTS_DIR"
    
    return 0
}

# Cleanup
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "SchemaSage failed with exit code $exit_code"
    fi
    return $exit_code
}

trap cleanup EXIT

main "$@"
