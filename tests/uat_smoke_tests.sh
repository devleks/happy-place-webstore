#!/bin/bash
################################################################################
# UAT Smoke Tests
# Happy Place Webstore - December 8, 2025
# Quick critical path validation (5-10 minutes)
# If ANY smoke test fails, full UAT should NOT proceed
################################################################################

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source helper functions
source "$SCRIPT_DIR/uat_helpers.sh"

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:5001/api}"
LOG_FILE="uat_smoke_$(date +%Y%m%d_%H%M%S).log"

echo "=====================================" | tee "$LOG_FILE"
echo "UAT SMOKE TESTS" | tee -a "$LOG_FILE"
echo "Happy Place Webstore" | tee -a "$LOG_FILE"
echo "$(date)" | tee -a "$LOG_FILE"
echo "=====================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Base URL: $BASE_URL" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

START_TIME=$(date +%s)

# SMOKE-001: API Health Check
echo "[SMOKE-001] API Health Check" | tee -a "$LOG_FILE"
RESPONSE=$(curl -s -m 5 "$BASE_URL/pos/health" 2>/dev/null)
if echo "$RESPONSE" | grep -q "healthy"; then
    pass_test "SMOKE-001: API Health Check"
else
    fail_test "SMOKE-001: API Health Check" "API not responding or unhealthy"
    log_error "Response: $RESPONSE"
    echo "" | tee -a "$LOG_FILE"
    echo "CRITICAL: API is not healthy. Cannot proceed with testing." | tee -a "$LOG_FILE"
    print_summary
    exit 1
fi

# SMOKE-002: Database Connectivity
echo "[SMOKE-002] Database Connectivity" | tee -a "$LOG_FILE"
RESPONSE=$(curl -s -m 5 "$BASE_URL/products?limit=1" 2>/dev/null)
if echo "$RESPONSE" | grep -q "products"; then
    pass_test "SMOKE-002: Database Connectivity"
else
    fail_test "SMOKE-002: Database Connectivity" "Database not accessible"
    log_error "Response: $RESPONSE"
    echo "" | tee -a "$LOG_FILE"
    echo "CRITICAL: Database is not accessible. Cannot proceed with testing." | tee -a "$LOG_FILE"
    print_summary
    exit 1
fi

# SMOKE-003: Customer Authentication
echo "[SMOKE-003] Customer Authentication" | tee -a "$LOG_FILE"

# First, try to register a test customer
UNIQUE_EMAIL="smoke.test.$(date +%s)@test.com"
REGISTER_RESPONSE=$(curl -s -m 5 -X POST "$BASE_URL/auth/customer/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$UNIQUE_EMAIL\",\"password\":\"TestPass123!\",\"first_name\":\"Smoke\",\"last_name\":\"Test\",\"phone\":\"+254700000000\",\"gdpr_consent\":true}" 2>/dev/null)

# Now try to login
RESPONSE=$(curl -s -m 5 -X POST "$BASE_URL/auth/customer/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$UNIQUE_EMAIL\",\"password\":\"TestPass123!\"}" 2>/dev/null)

if echo "$RESPONSE" | grep -q "access_token"; then
    CUSTOMER_TOKEN=$(extract_json_field "$RESPONSE" "access_token")
    pass_test "SMOKE-003: Customer Authentication"
    log_info "Customer token obtained successfully"
else
    fail_test "SMOKE-003: Customer Authentication" "Customer auth not working"
    log_error "Register Response: $REGISTER_RESPONSE"
    log_error "Login Response: $RESPONSE"
    echo "" | tee -a "$LOG_FILE"
    echo "CRITICAL: Customer authentication is broken. Cannot proceed with testing." | tee -a "$LOG_FILE"
    print_summary
    exit 1
fi

# SMOKE-004: Employee Authentication
echo "[SMOKE-004] Employee Authentication" | tee -a "$LOG_FILE"
RESPONSE=$(curl -s -m 5 -X POST "$BASE_URL/auth/employee/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"manager@happyplace.co.ke","password":"manager123"}' 2>/dev/null)

if echo "$RESPONSE" | grep -q "access_token"; then
    EMPLOYEE_TOKEN=$(extract_json_field "$RESPONSE" "access_token")
    pass_test "SMOKE-004: Employee Authentication"
    log_info "Employee token obtained successfully"
else
    fail_test "SMOKE-004: Employee Authentication" "Employee auth not working"
    log_error "Response: $RESPONSE"
    echo "" | tee -a "$LOG_FILE"
    echo "CRITICAL: Employee authentication is broken. Cannot proceed with testing." | tee -a "$LOG_FILE"
    print_summary
    exit 1
fi

# SMOKE-005: Admin Dashboard Access
echo "[SMOKE-005] Admin Dashboard Access" | tee -a "$LOG_FILE"
RESPONSE=$(curl -s -m 5 -X GET "$BASE_URL/admin/dashboard/metrics?period=today" \
    -H "Authorization: Bearer $EMPLOYEE_TOKEN" 2>/dev/null)

if echo "$RESPONSE" | grep -q "totalSales\|sales"; then
    pass_test "SMOKE-005: Admin Dashboard Access"
    log_info "Admin dashboard is accessible"
else
    fail_test "SMOKE-005: Admin Dashboard Access" "Admin dashboard not accessible"
    log_error "Response: $RESPONSE"
    # This is not critical enough to stop all testing
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "" | tee -a "$LOG_FILE"
echo "Smoke tests completed in ${DURATION} seconds" | tee -a "$LOG_FILE"

# Print summary
print_summary

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo -e "${GREEN}✓ ALL SMOKE TESTS PASSED - System is ready for full UAT${NC}" | tee -a "$LOG_FILE"
    exit 0
else
    echo "" | tee -a "$LOG_FILE"
    echo -e "${RED}✗ SMOKE TESTS FAILED - DO NOT PROCEED WITH FULL UAT${NC}" | tee -a "$LOG_FILE"
    echo "Fix critical issues before running comprehensive tests." | tee -a "$LOG_FILE"
    exit 1
fi
