#!/bin/bash
# Agent SchemaSage: Database analysis and optimization helper
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
SQL_FILE="$ROOT_DIR/ci_workflows/helpers/schemasage_explain.sql"
mkdir -p "$REPORTS_DIR"

SCHEMA_REPORT="$REPORTS_DIR/schemasage_schema.txt"
EXPLAIN_REPORT="$REPORTS_DIR/schemasage_explain.txt"
MIGRATION_LOG="$REPORTS_DIR/schemasage_migration.log"
PROC_LOG="$REPORTS_DIR/schemasage_procedure.log"
SUMMARY_REPORT="$REPORTS_DIR/db_audit.md"

require_database_url() {
  if [ -z "${DATABASE_URL:-}" ]; then
    echo "[SchemaSage] Set DATABASE_URL before running (e.g., export DATABASE_URL=postgresql://...)" >&2
    exit 1
  fi
}

require_psql() {
  if ! command -v psql >/dev/null 2>&1; then
    echo "[SchemaSage] psql is required and was not found on PATH" >&2
    exit 1
  fi
}

snapshot_schema() {
  echo "[SchemaSage] Capturing table list"
  psql "$DATABASE_URL" -c "\dt" >"$SCHEMA_REPORT"
}

collect_plans() {
  if [ ! -f "$SQL_FILE" ]; then
    echo "[SchemaSage] Missing SQL probe file: $SQL_FILE" >&2
    exit 1
  fi

  echo "[SchemaSage] Running EXPLAIN ANALYZE probes"
  psql "$DATABASE_URL" -f "$SQL_FILE" >"$EXPLAIN_REPORT"
}

validate_migrations() {
  echo "[SchemaSage] Dry-running migration script"
  pushd "$ROOT_DIR/backend" >/dev/null
  python3 scripts/migrate_database.py --dry-run >"$MIGRATION_LOG" 2>&1 || true
  popd >/dev/null
}

verify_procedures() {
  echo "[SchemaSage] Replaying stored procedure definitions (no-op if already installed)"
  psql "$DATABASE_URL" -f "$ROOT_DIR/backend/scripts/create_stored_procedures.sql" >"$PROC_LOG" 2>&1 || true
}

write_summary() {
  cat >"$SUMMARY_REPORT" <<MARKDOWN
# SchemaSage Report
Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

- Table inventory snapshot: \`reports/$(basename "$SCHEMA_REPORT")\`
- Query plan output: \`reports/$(basename "$EXPLAIN_REPORT")\`
- Migration dry-run log: \`reports/$(basename "$MIGRATION_LOG")\`
- Stored procedure replay log: \`reports/$(basename "$PROC_LOG")\`

Next actions:
1. Review EXPLAIN output for sequential scans with high buffer hits.
2. Compare tables listed above with \`DATABASE_SCHEMA_FINAL.md\` to spot drift.
3. Update indexes or constraints where plans show repeated full scans.
MARKDOWN
}

main() {
  echo "[SchemaSage] Starting database audit"
  require_database_url
  require_psql
  snapshot_schema
  collect_plans
  validate_migrations
  verify_procedures
  write_summary
  echo "[SchemaSage] Completed → artifacts stored in $REPORTS_DIR"
}

main "$@"
