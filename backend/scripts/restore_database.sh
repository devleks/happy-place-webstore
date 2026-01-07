#!/bin/bash
# Database Restore Script for Happy Place Boutique
# Restore PostgreSQL database from backup
#
# Usage:
#   ./restore_database.sh /path/to/backup/happyplace_db_20260107_120000.sql.gz
#
# IMPORTANT: This will REPLACE the current database!

set -e  # Exit on error

# ============================================
# CONFIGURATION
# ============================================

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "❌ Error: No backup file specified"
    echo ""
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Example: $0 /var/backups/happy_place/happyplace_db_20260107_120000.sql.gz"
    echo ""
    echo "Available backups:"
    ls -lh /var/backups/happy_place/*.sql.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${BACKEND_DIR}/.env.production"

if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "❌ Error: .env.production not found at $ENV_FILE"
    exit 1
fi

# Extract database connection details from DATABASE_URL
DB_URL="${DATABASE_URL}"
DB_NAME=$(echo "$DB_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
DB_USER=$(echo "$DB_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_HOST=$(echo "$DB_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "$DB_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

# ============================================
# SAFETY CONFIRMATION
# ============================================

echo "⚠️  WARNING: DATABASE RESTORE OPERATION"
echo ""
echo "This will COMPLETELY REPLACE the current database:"
echo "  Database: $DB_NAME"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Backup: $(basename "$BACKUP_FILE")"
echo "  Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "  Backup date: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$BACKUP_FILE" 2>/dev/null || stat -c "%y" "$BACKUP_FILE" 2>/dev/null)"
echo ""
echo "⚠️  ALL CURRENT DATA WILL BE LOST!"
echo ""
read -p "Type 'YES' to confirm restore: " CONFIRMATION

if [ "$CONFIRMATION" != "YES" ]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# ============================================
# PRE-RESTORE BACKUP
# ============================================

echo ""
echo "📦 Creating safety backup before restore..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SAFETY_BACKUP="/tmp/happyplace_db_pre_restore_${TIMESTAMP}.sql.gz"

if PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    --format=plain --no-owner --no-acl "$DB_NAME" | gzip > "$SAFETY_BACKUP"; then
    echo "✅ Safety backup created: $SAFETY_BACKUP"
else
    echo "⚠️  Warning: Could not create safety backup"
    read -p "Continue anyway? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        exit 1
    fi
fi

# ============================================
# RESTORE PROCESS
# ============================================

echo ""
echo "🔄 Starting database restore..."

# Decompress and restore
echo "📂 Decompressing backup..."
if gunzip -c "$BACKUP_FILE" > /tmp/restore_temp.sql; then
    echo "✅ Backup decompressed"
else
    echo "❌ ERROR: Failed to decompress backup"
    exit 1
fi

echo "💾 Restoring database..."
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < /tmp/restore_temp.sql 2>&1 | tee /tmp/restore.log; then
    echo "✅ Database restored successfully"
    rm -f /tmp/restore_temp.sql
else
    echo "❌ ERROR: Database restore failed"
    echo "Check /tmp/restore.log for details"
    rm -f /tmp/restore_temp.sql
    exit 1
fi

# ============================================
# VERIFICATION
# ============================================

echo ""
echo "🔍 Verifying restore..."

# Check table count
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

echo "✅ Verification complete"
echo "  📊 Tables restored: $TABLE_COUNT"

# ============================================
# SUMMARY
# ============================================

echo ""
echo "🎉 DATABASE RESTORE COMPLETED!"
echo ""
echo "📊 Summary:"
echo "  ✅ Database: $DB_NAME"
echo "  ✅ Tables: $TABLE_COUNT"
echo "  ✅ Backup restored: $(basename "$BACKUP_FILE")"
echo "  ℹ️  Safety backup: $SAFETY_BACKUP"
echo ""
echo "⚠️  IMPORTANT: Restart the application to apply changes"
echo "  sudo systemctl restart happyplace-backend"

exit 0
