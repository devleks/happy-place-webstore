#!/bin/bash

#############################################
# Backup Verification Script
# Verifies backup integrity and alerts if issues found
#############################################

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/backups}"
MAX_BACKUP_AGE_HOURS=${MAX_BACKUP_AGE_HOURS:-24}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=============================================="
echo "  Backup Verification Report"
echo "=============================================="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Backup Directory: ${BACKUP_DIR}"
echo ""

# Check if backup directory exists
if [ ! -d "${BACKUP_DIR}" ]; then
    echo -e "${RED}❌ ERROR: Backup directory does not exist${NC}"
    echo "Directory: ${BACKUP_DIR}"
    exit 1
fi

# Find most recent backup
LATEST_BACKUP=$(find "${BACKUP_DIR}" -name "happy_place_backup_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "${LATEST_BACKUP}" ]; then
    echo -e "${RED}❌ ERROR: No backups found${NC}"
    exit 1
fi

echo "Latest backup: $(basename ${LATEST_BACKUP})"

# Check backup age
BACKUP_TIME=$(stat -f %m "${LATEST_BACKUP}" 2>/dev/null || stat -c %Y "${LATEST_BACKUP}")
CURRENT_TIME=$(date +%s)
BACKUP_AGE_HOURS=$(( ($CURRENT_TIME - $BACKUP_TIME) / 3600 ))

echo "Backup age: ${BACKUP_AGE_HOURS} hours"

if [ $BACKUP_AGE_HOURS -gt $MAX_BACKUP_AGE_HOURS ]; then
    echo -e "${RED}❌ WARNING: Backup is older than ${MAX_BACKUP_AGE_HOURS} hours${NC}"
    BACKUP_STALE=true
else
    echo -e "${GREEN}✅ Backup is fresh (< ${MAX_BACKUP_AGE_HOURS} hours)${NC}"
    BACKUP_STALE=false
fi

# Check backup file integrity
echo ""
echo "Verifying backup integrity..."

# Test if gzip file is valid
if gunzip -t "${LATEST_BACKUP}" 2>&1 | grep -q "OK\|not in gzip format"; then
    echo -e "${GREEN}✅ Gzip integrity check passed${NC}"
    INTEGRITY_OK=true
else
    echo -e "${RED}❌ ERROR: Backup file is corrupted${NC}"
    INTEGRITY_OK=false
fi

# Check file size
BACKUP_SIZE=$(du -h "${LATEST_BACKUP}" | cut -f1)
BACKUP_SIZE_BYTES=$(du -b "${LATEST_BACKUP}" | cut -f1)

echo "Backup size: ${BACKUP_SIZE}"

if [ $BACKUP_SIZE_BYTES -lt 1000 ]; then
    echo -e "${RED}❌ WARNING: Backup file suspiciously small (< 1KB)${NC}"
    SIZE_OK=false
else
    echo -e "${GREEN}✅ Backup size looks reasonable${NC}"
    SIZE_OK=true
fi

# Count total backups
TOTAL_BACKUPS=$(find "${BACKUP_DIR}" -name "happy_place_backup_*.sql.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)

echo ""
echo "Total backups: ${TOTAL_BACKUPS}"
echo "Total backup storage: ${TOTAL_SIZE}"

# Summary
echo ""
echo "=============================================="
echo "  Verification Summary"
echo "=============================================="

if [ "$BACKUP_STALE" = false ] && [ "$INTEGRITY_OK" = true ] && [ "$SIZE_OK" = true ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo "Backup system is healthy"
    exit 0
else
    echo -e "${RED}❌ ISSUES DETECTED${NC}"
    
    if [ "$BACKUP_STALE" = true ]; then
        echo "  - Backup is stale (older than ${MAX_BACKUP_AGE_HOURS} hours)"
    fi
    
    if [ "$INTEGRITY_OK" = false ]; then
        echo "  - Backup file integrity check failed"
    fi
    
    if [ "$SIZE_OK" = false ]; then
        echo "  - Backup file size is suspicious"
    fi
    
    # Send alert (optional)
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"⚠️ Backup verification failed for Happy Place Webstore\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    exit 1
fi