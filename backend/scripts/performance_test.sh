#!/bin/bash
# Performance Testing Script for Happy Place Boutique
# Tests API endpoints with concurrent requests and measures response times
#
# Usage: ./performance_test.sh [concurrent_users]
# Example: ./performance_test.sh 50

set -e

# Configuration
API_URL="${API_URL:-http://127.0.0.1:5001}"
CONCURRENT_USERS="${1:-50}"
TOTAL_REQUESTS=$((CONCURRENT_USERS * 10))
OUTPUT_DIR="performance_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════"
echo "  🚀 Happy Place Boutique - Performance Testing"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
echo "  API URL: $API_URL"
echo "  Concurrent Users: $CONCURRENT_USERS"
echo "  Total Requests: $TOTAL_REQUESTS"
echo "  Timestamp: $TIMESTAMP"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
REPORT_FILE="$OUTPUT_DIR/performance_report_${TIMESTAMP}.txt"

# Start report
cat > "$REPORT_FILE" <<EOF
PERFORMANCE TEST REPORT
========================
Date: $(date)
API URL: $API_URL
Concurrent Users: $CONCURRENT_USERS
Total Requests: $TOTAL_REQUESTS

EOF

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local name=$2
    local method=${3:-GET}

    echo -e "${BLUE}Testing:${NC} $name"
    echo "  Endpoint: $endpoint"
    echo "  Method: $method"
    echo "  Requests: $TOTAL_REQUESTS (Concurrency: $CONCURRENT_USERS)"

    # Run Apache Bench
    if [ "$method" = "GET" ]; then
        ab -n "$TOTAL_REQUESTS" -c "$CONCURRENT_USERS" -g "$OUTPUT_DIR/${name}_${TIMESTAMP}.tsv" \
           "${API_URL}${endpoint}" > "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" 2>&1
    fi

    # Parse results
    if [ -f "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" ]; then
        local requests_per_sec=$(grep "Requests per second:" "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" | awk '{print $4}')
        local time_per_request=$(grep "Time per request:" "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" | grep "mean" | head -1 | awk '{print $4}')
        local failed_requests=$(grep "Failed requests:" "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" | awk '{print $3}')
        local p50=$(grep "50%" "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" | awk '{print $2}')
        local p95=$(grep "95%" "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" | awk '{print $2}')
        local p99=$(grep "99%" "$OUTPUT_DIR/${name}_${TIMESTAMP}_raw.txt" | awk '{print $2}')

        # Color code based on performance
        if (( $(echo "$time_per_request < 100" | bc -l) )); then
            color=$GREEN
            status="✓ EXCELLENT"
        elif (( $(echo "$time_per_request < 500" | bc -l) )); then
            color=$YELLOW
            status="⚠ ACCEPTABLE"
        else
            color=$RED
            status="✗ SLOW"
        fi

        echo -e "${color}  $status${NC}"
        echo "  Requests/sec: $requests_per_sec"
        echo "  Avg time: ${time_per_request}ms"
        echo "  Failed: $failed_requests"
        echo "  P50: ${p50}ms | P95: ${p95}ms | P99: ${p99}ms"
        echo ""

        # Add to report
        cat >> "$REPORT_FILE" <<EOF
$name ($endpoint)
-----------------
Status: $status
Requests per second: $requests_per_sec
Average time per request: ${time_per_request}ms
Failed requests: $failed_requests
Percentiles:
  P50: ${p50}ms
  P95: ${p95}ms
  P99: ${p99}ms

EOF
    else
        echo -e "${RED}  ✗ FAILED - Could not run test${NC}"
        echo ""
    fi
}

# ============================================
# TEST SUITE
# ============================================

echo "════════════════════════════════════════════════════════════"
echo "  Starting Performance Tests"
echo "════════════════════════════════════════════════════════════"
echo ""

# Test 1: Health Check (simplest endpoint)
test_endpoint "/api/health" "health_check" "GET"

# Test 2: Products List (read-heavy)
test_endpoint "/api/products" "products_list" "GET"

# Test 3: Single Product (read with joins)
test_endpoint "/api/products/1" "product_detail" "GET"

# Test 4: Categories (simple read)
test_endpoint "/api/categories" "categories_list" "GET"

# Test 5: Authentication endpoint would need POST with credentials
# Skipping for now as it requires auth token setup

echo "════════════════════════════════════════════════════════════"
echo "  Performance Test Complete"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✓${NC} Report saved to: $REPORT_FILE"
echo ""

# Summary
echo "Performance Summary:"
echo "-------------------"

# Calculate average from all tests
if [ -f "$REPORT_FILE" ]; then
    grep "Average time per request:" "$REPORT_FILE" | while read -r line; do
        echo "  $line"
    done
fi

echo ""
echo "Detailed results in: $OUTPUT_DIR/"
echo ""

# Check if any tests failed
failed_count=$(grep -c "✗ FAILED" "$REPORT_FILE" || echo "0")
slow_count=$(grep -c "✗ SLOW" "$REPORT_FILE" || echo "0")

if [ "$failed_count" -gt 0 ]; then
    echo -e "${RED}⚠ WARNING: $failed_count test(s) failed${NC}"
    exit 1
elif [ "$slow_count" -gt 0 ]; then
    echo -e "${YELLOW}⚠ WARNING: $slow_count endpoint(s) are slow${NC}"
    exit 0
else
    echo -e "${GREEN}✓ All endpoints performing within acceptable limits${NC}"
    exit 0
fi
