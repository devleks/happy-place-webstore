#!/bin/bash
# Database Backup Script for Happy Place Boutique
# Automated PostgreSQL backup with rotation
#
# Setup:
# 1. Make executable: chmod +x backup_database.sh
# 2. Test manually: ./backup_database.sh
# 3. Add to crontab for daily backups:
#    crontab -e
#    0 2 * * * /var/www/happyplace/backend/scripts/backup_database.sh

set -e  # Exit on error

# ============================================
# CONFIGURATION
# ============================================

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

# Backup directory
BACKUP_DIR="${BACKUP_DIR:-/var/backups/happy_place}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Extract database connection details from DATABASE_URL
# Format: postgresql://user:pass@host:port/dbname
DB_URL="${DATABASE_URL}"
DB_NAME=$(echo "$DB_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
DB_USER=$(echo "$DB_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_HOST=$(echo "$DB_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "$DB_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

# Backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/happyplace_db_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

# Log file
LOG_FILE="${BACKUP_DIR}/backup.log"

# ============================================
# FUNCTIONS
# ============================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ============================================
# MAIN BACKUP PROCESS
# ============================================

log "🚀 Starting database backup..."

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    log "📁 Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Check PostgreSQL connection
log "🔌 Testing database connection..."
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    log "❌ ERROR: Cannot connect to database"
    exit 1
fi
log "✅ Database connection successful"

# Perform backup
log "💾 Backing up database: $DB_NAME"
log "📂 Backup file: $BACKUP_FILE_GZ"

if PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    --format=plain \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    "$DB_NAME" > "$BACKUP_FILE" 2>&1; then

    log "✅ Database dump created successfully"

    # Compress backup
    log "🗜️  Compressing backup..."
    gzip "$BACKUP_FILE"

    BACKUP_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
    log "✅ Backup compressed: $BACKUP_SIZE"

else
    log "❌ ERROR: Database backup failed"
    rm -f "$BACKUP_FILE" "$BACKUP_FILE_GZ"
    exit 1
fi

# ============================================
# BACKUP ROTATION (Delete old backups)
# ============================================

log "🗑️  Cleaning up old backups (older than ${BACKUP_RETENTION_DAYS} days)..."

OLD_BACKUPS=$(find "$BACKUP_DIR" -name "happyplace_db_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS})
if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read -r old_backup; do
        log "  Deleting: $(basename "$old_backup")"
        rm -f "$old_backup"
    done
    DELETED_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
    log "✅ Deleted $DELETED_COUNT old backup(s)"
else
    log "ℹ️  No old backups to delete"
fi

# ============================================
# BACKUP VERIFICATION
# ============================================

log "🔍 Verifying backup integrity..."

if gunzip -t "$BACKUP_FILE_GZ" 2>/dev/null; then
    log "✅ Backup integrity verified"
else
    log "❌ ERROR: Backup file is corrupted!"
    exit 1
fi

# ============================================
# SUMMARY
# ============================================

TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "happyplace_db_*.sql.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "📊 BACKUP SUMMARY"
log "  ✅ Backup completed successfully"
log "  📂 Backup file: $(basename "$BACKUP_FILE_GZ")"
log "  📏 Backup size: $BACKUP_SIZE"
log "  🗄️  Total backups: $TOTAL_BACKUPS"
log "  💾 Total storage: $TOTAL_SIZE"
log "  🕐 Retention: $BACKUP_RETENTION_DAYS days"
log "🎉 Backup process completed!"

exit 0
