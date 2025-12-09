#!/bin/bash

#############################################
# Happy Place Webstore - Automated Database Backup
# Supports daily, hourly, and on-demand backups
#############################################

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="happy_place_backup_${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "=============================================="
echo "  Happy Place Database Backup"
echo "=============================================="
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Backup Location: ${BACKUP_PATH}"
echo ""

# Extract database connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/database
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL not set${NC}"
    exit 1
fi

# Parse DATABASE_URL
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

# URL decode password (handle special characters)
DB_PASS=$(echo "$DB_PASS" | sed 's/%20/ /g' | sed 's/%24/$/g')

echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Perform backup
echo "Creating backup..."
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    --format=custom \
    --file="${BACKUP_PATH}" 2>&1 | grep -v "^pg_dump:" || true

# Check if backup was successful
if [ $? -eq 0 ] && [ -f "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    echo -e "${GREEN}✅ Backup completed successfully${NC}"
    echo "Backup file: ${BACKUP_FILE}"
    echo "Size: ${BACKUP_SIZE}"
    
    # Create compressed version
    echo ""
    echo "Compressing backup..."
    gzip -9 "${BACKUP_PATH}"
    COMPRESSED_SIZE=$(du -h "${BACKUP_PATH}.gz" | cut -f1)
    echo -e "${GREEN}✅ Compression complete${NC}"
    echo "Compressed size: ${COMPRESSED_SIZE}"
    
    # Create a symlink to latest backup
    ln -sf "${BACKUP_FILE}.gz" "${BACKUP_DIR}/latest.sql.gz"

else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi

# Cleanup old backups
echo ""
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "happy_place_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete -print | wc -l)

if [ $DELETED_COUNT -gt 0 ]; then
    echo -e "${YELLOW}Deleted ${DELETED_COUNT} old backup(s)${NC}"
else
    echo "No old backups to delete"
fi

# List recent backups
echo ""
echo "Recent backups:"
ls -lh "${BACKUP_DIR}"/happy_place_backup_*.sql.gz 2>/dev/null | tail -5 | awk '{print "  " $9 " (" $5 ")"}'

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}Backup Summary${NC}"
echo "=============================================="
TOTAL_BACKUPS=$(ls -1 "${BACKUP_DIR}"/happy_place_backup_*.sql.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
echo "Total backups: ${TOTAL_BACKUPS}"
echo "Total size: ${TOTAL_SIZE}"
echo "Retention: ${RETENTION_DAYS} days"
echo ""

# Optional: Upload to cloud storage
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp "${BACKUP_PATH}.gz" "s3://${BACKUP_S3_BUCKET}/backups/${BACKUP_FILE}.gz"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Uploaded to S3 successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  S3 upload failed (local backup available)${NC}"
    fi
fi

# Optional: Send notification
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Database backup completed: ${BACKUP_FILE} (${COMPRESSED_SIZE})\"}" \
        "$SLACK_WEBHOOK_URL" 2>/dev/null || true
fi

echo -e "${GREEN}✅ Backup process completed${NC}"
echo ""