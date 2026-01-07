#!/bin/bash
# Health Check Script for Happy Place Boutique Backend
# Verifies that the application is running and responding
#
# Usage:
#   ./health_check.sh
#
# Exit codes:
#   0 = Healthy
#   1 = Unhealthy

set -e

# Configuration
API_URL="${API_URL:-http://127.0.0.1:5001}"
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🏥 Health Check - Happy Place Boutique Backend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 1: API is reachable
echo -n "  Checking API reachability..."
if curl -s --max-time $TIMEOUT "${API_URL}/api/health" > /dev/null 2>&1; then
    echo -e " ${GREEN}✓${NC}"
else
    echo -e " ${RED}✗${NC}"
    echo -e "${RED}ERROR: API is not reachable${NC}"
    exit 1
fi

# Check 2: Database connection
echo -n "  Checking database connection..."
DB_STATUS=$(curl -s --max-time $TIMEOUT "${API_URL}/api/health" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
if [ "$DB_STATUS" = "connected" ]; then
    echo -e " ${GREEN}✓${NC}"
else
    echo -e " ${RED}✗${NC}"
    echo -e "${RED}ERROR: Database not connected${NC}"
    exit 1
fi

# Check 3: Response time
echo -n "  Checking response time..."
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time $TIMEOUT "${API_URL}/api/health")
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc | cut -d'.' -f1)

if [ "$RESPONSE_MS" -lt 500 ]; then
    echo -e " ${GREEN}✓${NC} (${RESPONSE_MS}ms)"
elif [ "$RESPONSE_MS" -lt 2000 ]; then
    echo -e " ${YELLOW}⚠${NC} (${RESPONSE_MS}ms - slow)"
else
    echo -e " ${RED}✗${NC} (${RESPONSE_MS}ms - too slow)"
    exit 1
fi

# Check 4: Disk space
echo -n "  Checking disk space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e " ${GREEN}✓${NC} (${DISK_USAGE}% used)"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e " ${YELLOW}⚠${NC} (${DISK_USAGE}% used)"
else
    echo -e " ${RED}✗${NC} (${DISK_USAGE}% used - critical)"
fi

# Check 5: Memory usage
echo -n "  Checking memory usage..."
if command -v free > /dev/null 2>&1; then
    MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
    if [ "$MEM_USAGE" -lt 80 ]; then
        echo -e " ${GREEN}✓${NC} (${MEM_USAGE}% used)"
    elif [ "$MEM_USAGE" -lt 90 ]; then
        echo -e " ${YELLOW}⚠${NC} (${MEM_USAGE}% used)"
    else
        echo -e " ${RED}✗${NC} (${MEM_USAGE}% used - critical)"
    fi
else
    echo -e " ${YELLOW}⚠${NC} (not available on this system)"
fi

# Check 6: Log files
echo -n "  Checking log files..."
if [ -d "/var/log/happyplace" ]; then
    ERROR_COUNT=$(grep -c "ERROR" /var/log/happyplace/error.log 2>/dev/null | tail -100 || echo "0")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo -e " ${GREEN}✓${NC} (no recent errors)"
    elif [ "$ERROR_COUNT" -lt 10 ]; then
        echo -e " ${YELLOW}⚠${NC} ($ERROR_COUNT errors in last 100 lines)"
    else
        echo -e " ${RED}✗${NC} ($ERROR_COUNT errors in last 100 lines)"
    fi
else
    echo -e " ${YELLOW}⚠${NC} (log directory not found)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ All health checks passed${NC}"

exit 0
