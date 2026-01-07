#!/bin/bash
################################################################################
# UAT Helper Functions
# Happy Place Webstore - December 8, 2025
# Shared utilities for all UAT test scripts
################################################################################

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNED_TESTS=0
SKIPPED_TESTS=0

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:5001/api}"
CURL_TIMEOUT=10
MAX_RETRIES=2
LOG_FILE="uat_results_$(date +%Y%m%d_%H%M%S).log"

# Critical failure flag
CRITICAL_FAILURE=false

# Test result tracking
pass_test() {
    local test_id=$1
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "${GREEN}✓ PASS${NC} - $test_id" | tee -a "$LOG_FILE"
}

fail_test() {
    local test_id=$1
    local reason=$2
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}✗ FAIL${NC} - $test_id: $reason" | tee -a "$LOG_FILE"
}

warn_test() {
    local test_id=$1
    local reason=$2
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    WARNED_TESTS=$((WARNED_TESTS + 1))
    echo -e "${YELLOW}⚠ WARN${NC} - $test_id: $reason" | tee -a "$LOG_FILE"
}

skip_test() {
    local test_id=$1
    local reason=$2
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    echo -e "${BLUE}⏭ SKIP${NC} - $test_id: $reason" | tee -a "$LOG_FILE"
}

# JSON field extraction using Python
extract_json_field() {
    local json=$1
    local field=$2
    
    echo "$json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    fields = '$field'.split('.')
    val = data
    for f in fields:
        if isinstance(val, dict):
            val = val.get(f)
        else:
            val = None
            break
    print(val if val is not None else '')
except:
    print('')
" 2>/dev/null
}

# Authentication helpers
auth_customer_login() {
    local email=$1
    local password=$2
    
    RESPONSE=$(curl -s -m $CURL_TIMEOUT \
        -X POST "$BASE_URL/auth/customer/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"password\":\"$password\"}")
    
    if echo "$RESPONSE" | grep -q "access_token"; then
        TOKEN=$(extract_json_field "$RESPONSE" "access_token")
        echo "$TOKEN"
        return 0
    else
        return 1
    fi
}

auth_employee_login() {
    local email=$1
    local password=$2
    
    RESPONSE=$(curl -s -m $CURL_TIMEOUT \
        -X POST "$BASE_URL/auth/employee/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"password\":\"$password\"}")
    
    if echo "$RESPONSE" | grep -q "access_token"; then
        TOKEN=$(extract_json_field "$RESPONSE" "access_token")
        echo "$TOKEN"
        return 0
    else
        return 1
    fi
}

# HTTP request helpers
test_get_endpoint() {
    local test_id=$1
    local endpoint=$2
    local token=$3
    local expected_field=$4
    
    echo "[$test_id] Testing GET $endpoint"
    
    RESPONSE=$(curl -s -m $CURL_TIMEOUT -X GET "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $token")
    
    if echo "$RESPONSE" | grep -q "$expected_field"; then
        pass_test "$test_id"
        echo "$RESPONSE"
    else
        fail_test "$test_id" "Expected field not found: $expected_field"
        echo "$RESPONSE"
    fi
}

test_post_endpoint() {
    local test_id=$1
    local endpoint=$2
    local token=$3
    local data=$4
    local expected_code=$5
    local expected_field=$6
    
    echo "[$test_id] Testing POST $endpoint"
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -m $CURL_TIMEOUT \
        -X POST "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$data")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" -eq "$expected_code" ] && \
       echo "$BODY" | grep -q "$expected_field"; then
        pass_test "$test_id"
        echo "$BODY"
    else
        fail_test "$test_id" "HTTP $HTTP_CODE, expected $expected_code"
        echo "$BODY"
    fi
}

# Error logging
log_error() {
    local message=$1
    echo -e "${RED}ERROR:${NC} $message" | tee -a "$LOG_FILE"
}

log_info() {
    local message=$1
    echo -e "${BLUE}INFO:${NC} $message" | tee -a "$LOG_FILE"
}

# Performance measurement
measure_response_time() {
    local endpoint=$1
    local method=$2
    local data=$3
    local token=$4
    
    START_TIME=$(date +%s%N)
    
    if [ "$method" = "GET" ]; then
        RESPONSE=$(curl -s -m $CURL_TIMEOUT -X GET \
            "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token")
    else
        RESPONSE=$(curl -s -m $CURL_TIMEOUT -X $method \
            "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    END_TIME=$(date +%s%N)
    DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))
    
    echo "$DURATION_MS"
}

# Performance checking
check_performance() {
    local test_id=$1
    local duration=$2
    local threshold=$3
    
    if [ $duration -gt $threshold ]; then
        warn_test "$test_id" "Slow response: ${duration}ms (threshold: ${threshold}ms)"
        echo "  ↳ Consider performance optimization"
    fi
}

# Results summary
print_summary() {
    echo ""
    echo -e "${CYAN}=====================================${NC}"
    echo -e "${CYAN}TEST EXECUTION SUMMARY${NC}"
    echo -e "${CYAN}=====================================${NC}"
    echo -e "Total Tests:    $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC}         $PASSED_TESTS"
    echo -e "${RED}Failed:${NC}         $FAILED_TESTS"
    echo -e "${YELLOW}Warned:${NC}         $WARNED_TESTS"
    echo -e "${BLUE}Skipped:${NC}        $SKIPPED_TESTS"
    
    if [ $TOTAL_TESTS -gt 0 ]; then
        PASS_RATE=$(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
        echo -e "Pass Rate:      ${PASS_RATE}%"
    fi
    
    echo -e "${CYAN}=====================================${NC}"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ SOME TESTS FAILED${NC}"
        return 1
    fi
}

# Generate JSON report
generate_json_report() {
    local output_file="uat_results_$(date +%Y%m%d_%H%M%S).json"
    
    PASS_RATE=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        PASS_RATE=$(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
    fi
    
    cat > "$output_file" << EOF
{
  "test_run": {
    "date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "environment": {
      "base_url": "$BASE_URL",
      "test_suite_version": "2.0"
    }
  },
  "summary": {
    "total": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "warned": $WARNED_TESTS,
    "skipped": $SKIPPED_TESTS,
    "pass_rate": $PASS_RATE
  },
  "critical_failure": $CRITICAL_FAILURE
}
EOF
    
    echo "$output_file"
}

# Section header
print_section() {
    local title=$1
    echo ""
    echo -e "${CYAN}=====================================${NC}"
    echo -e "${CYAN}$title${NC}"
    echo -e "${CYAN}=====================================${NC}"
    echo ""
}

# Export functions for use in other scripts
export -f pass_test fail_test warn_test skip_test
export -f extract_json_field
export -f auth_customer_login auth_employee_login
export -f test_get_endpoint test_post_endpoint
export -f log_error log_info
export -f measure_response_time check_performance
export -f print_summary generate_json_report print_section
