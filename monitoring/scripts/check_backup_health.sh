#!/bin/bash

#############################################
# Backup Health Check Script
# Monitors backup system health and alerts on issues
#############################################

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/backups}"
ALERT_THRESHOLD_HOURS=26  # Alert if no backup in 26 hours
MIN_BACKUP_SIZE_KB=100    # Minimum expected backup size

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Initialize status
HEALTH_STATUS="healthy"
ISSUES=()

echo "=============================================="
echo "  Backup System Health Check"
echo "=============================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check 1: Backup directory exists and is writable
if [ ! -d "${BACKUP_DIR}" ]; then
    echo -e "${RED}❌ FAIL: Backup directory does not exist${NC}"
    HEALTH_STATUS="critical"
    ISSUES+=("Backup directory missing")
elif [ ! -w "${BACKUP_DIR}" ]; then
    echo -e "${RED}❌ FAIL: Backup directory not writable${NC}"
    HEALTH_STATUS="critical"
    ISSUES+=("Backup directory not writable")
else
    echo -e "${GREEN}✅ PASS: Backup directory accessible${NC}"
fi

# Check 2: Recent backup exists
LATEST_BACKUP=$(find "${BACKUP_DIR}" -name "happy_place_backup_*.sql.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "${LATEST_BACKUP}" ]; then
    echo -e "${RED}❌ FAIL: No backups found${NC}"
    HEALTH_STATUS="critical"
    ISSUES+=("No backups exist")
else
    echo -e "${GREEN}✅ PASS: Backups exist${NC}"
    
    # Check backup age
    BACKUP_TIME=$(stat -f %m "${LATEST_BACKUP}" 2>/dev/null || stat -c %Y "${LATEST_BACKUP}")
    CURRENT_TIME=$(date +%s)
    HOURS_SINCE_BACKUP=$(( ($CURRENT_TIME - $BACKUP_TIME) / 3600 ))
    
    echo "Latest backup age: ${HOURS_SINCE_BACKUP} hours"
    
    if [ $HOURS_SINCE_BACKUP -gt $ALERT_THRESHOLD_HOURS ]; then
        echo -e "${YELLOW}⚠️  WARNING: Last backup is ${HOURS_SINCE_BACKUP} hours old${NC}"
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            HEALTH_STATUS="degraded"
        fi
        ISSUES+=("Backup stale (${HOURS_SINCE_BACKUP}h old)")
    else
        echo -e "${GREEN}✅ PASS: Backup is recent${NC}"
    fi
    
    # Check backup size
    BACKUP_SIZE_KB=$(du -k "${LATEST_BACKUP}" | cut -f1)
    
    if [ $BACKUP_SIZE_KB -lt $MIN_BACKUP_SIZE_KB ]; then
        echo -e "${YELLOW}⚠️  WARNING: Backup size (${BACKUP_SIZE_KB}KB) is suspiciously small${NC}"
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            HEALTH_STATUS="degraded"
        fi
        ISSUES+=("Backup too small (${BACKUP_SIZE_KB}KB)")
    else
        echo -e "${GREEN}✅ PASS: Backup size looks good (${BACKUP_SIZE_KB}KB)${NC}"
    fi
fi

# Check 3: Disk space
DISK_USAGE=$(df -h "${BACKUP_DIR}" | tail -1 | awk '{print $5}' | sed 's/%//')

echo "Disk usage: ${DISK_USAGE}%"

if [ $DISK_USAGE -gt 90 ]; then
    echo -e "${RED}❌ FAIL: Disk usage critical (> 90%)${NC}"
    HEALTH_STATUS="critical"
    ISSUES+=("Disk space critical (${DISK_USAGE}%)")
elif [ $DISK_USAGE -gt 80 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Disk usage high (> 80%)${NC}"
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        HEALTH_STATUS="degraded"
    fi
    ISSUES+=("Disk space high (${DISK_USAGE}%)")
else
    echo -e "${GREEN}✅ PASS: Disk space OK${NC}"
fi

# Check 4: Backup script exists and is executable
BACKUP_SCRIPT="/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend/scripts/automated_backup.sh"

if [ ! -f "${BACKUP_SCRIPT}" ]; then
    echo -e "${RED}❌ FAIL: Backup script not found${NC}"
    HEALTH_STATUS="critical"
    ISSUES+=("Backup script missing")
elif [ ! -x "${BACKUP_SCRIPT}" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Backup script not executable${NC}"
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        HEALTH_STATUS="degraded"
    fi
    ISSUES+=("Backup script not executable")
else
    echo -e "${GREEN}✅ PASS: Backup script ready${NC}"
fi

# Check 5: Database connectivity
if [ ! -z "$DATABASE_URL" ]; then
    # Extract database details
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    # Test connectivity
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS: Database is accessible${NC}"
    else
        echo -e "${RED}❌ FAIL: Cannot connect to database${NC}"
        HEALTH_STATUS="critical"
        ISSUES+=("Database unreachable")
    fi
else
    echo -e "${YELLOW}⚠️  WARNING: DATABASE_URL not set${NC}"
fi

# Generate report
echo ""
echo "=============================================="
echo "  Health Status: ${HEALTH_STATUS^^}"
echo "=============================================="

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✅ HEALTHY${NC} - All checks passed"
    exit 0
elif [ "$HEALTH_STATUS" = "degraded" ]; then
    echo -e "${YELLOW}⚠️  DEGRADED${NC} - Issues detected:"
    for issue in "${ISSUES[@]}"; do
        echo "  • $issue"
    done
    
    # Send alert
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        ALERT_MESSAGE="⚠️ Backup system degraded: ${ISSUES[*]}"
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"${ALERT_MESSAGE}\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    exit 1
else
    echo -e "${RED}❌ CRITICAL${NC} - Critical issues detected:"
    for issue in "${ISSUES[@]}"; do
        echo "  • $issue"
    done
    
    # Send urgent alert
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        ALERT_MESSAGE="🚨 CRITICAL: Backup system failure: ${ISSUES[*]}"
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"${ALERT_MESSAGE}\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    exit 2
fi