#!/bin/bash

#############################################
# Happy Place Webstore - OPTIMIZED UAT
# Fast End-to-End Testing Suite
#############################################

echo "=============================================="
echo "  HAPPY PLACE - OPTIMIZED UAT TEST SUITE"
echo "=============================================="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:5001/api}"
START_TIME=$(date +%s)
CURL_TIMEOUT=10  # 10 second timeout for all requests
MAX_RETRIES=2

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test data
EMPLOYEE_TOKEN=""
SHIFT_ID=""
TRANSACTION_ID=""

#############################################
# Helper Functions
#############################################

# Optimized curl with timeout
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    
    local headers=(-H "Content-Type: application/json")
    
    if [ -n "$token" ]; then
        headers+=(-H "Authorization: Bearer $token")
    fi
    
    if [ "$method" = "GET" ]; then
        curl -s -m $CURL_TIMEOUT -X GET "${headers[@]}" "$BASE_URL$endpoint"
    else
        curl -s -m $CURL_TIMEOUT -X $method "${headers[@]}" -d "$data" "$BASE_URL$endpoint"
    fi
}

# Test result
test_result() {
    local test_name=$1
    local status=$2
    local message=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} - $test_name: $message"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

#############################################
# Pre-Flight Checks
#############################################

echo -e "${BLUE}[PRE-FLIGHT]${NC} Checking server health..."

HEALTH_CHECK=$(api_call GET "/pos/health" "" "")
if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Server is healthy"
else
    echo -e "${RED}✗ Server health check failed!${NC}"
    echo "Response: $HEALTH_CHECK"
    exit 1
fi

#############################################
# EMPLOYEE TESTS
#############################################

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}EMPLOYEE POS TESTS${NC}"
echo -e "${CYAN}========================================${NC}"

# TC-EMP-01: Employee Login
echo -e "\n${BLUE}[TC-EMP-01]${NC} Employee Login"
LOGIN_RESPONSE=$(api_call POST "/auth/employee/login" '{
    "email": "manager@happyplace.co.ke",
    "password": "manager123"
}' "")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    EMPLOYEE_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    EMPLOYEE_ID=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['employee']['id'])" 2>/dev/null)
    test_result "TC-EMP-01: Employee Login" "PASS" ""
else
    test_result "TC-EMP-01: Employee Login" "FAIL" "No access token received"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# TC-EMP-02: Get Current Shift
echo -e "\n${BLUE}[TC-EMP-02]${NC} Get Current Shift"
CURRENT_SHIFT=$(api_call GET "/pos/shifts/current" "" "$EMPLOYEE_TOKEN")

if echo "$CURRENT_SHIFT" | grep -q "shift_id"; then
    SHIFT_ID=$(echo "$CURRENT_SHIFT" | python3 -c "import sys, json; print(json.load(sys.stdin)['shift_id'])" 2>/dev/null)
    test_result "TC-EMP-02: Get Current Shift" "PASS" "Shift ID: $SHIFT_ID"
else
    # No open shift, need to start one
    echo "  No open shift found, starting new shift..."
    
    # TC-EMP-03: Start Shift
    echo -e "\n${BLUE}[TC-EMP-03]${NC} Start New Shift"
    START_SHIFT=$(api_call POST "/pos/shifts/start" '{
        "store_location_id": 1,
        "opening_float": 5000
    }' "$EMPLOYEE_TOKEN")
    
    if echo "$START_SHIFT" | grep -q "shift_id"; then
        SHIFT_ID=$(echo "$START_SHIFT" | python3 -c "import sys, json; print(json.load(sys.stdin)['shift_id'])" 2>/dev/null)
        test_result "TC-EMP-03: Start Shift" "PASS" "Shift ID: $SHIFT_ID"
    else
        test_result "TC-EMP-03: Start Shift" "FAIL" "Failed to start shift"
        echo "Response: $START_SHIFT"
        exit 1
    fi
fi

# TC-EMP-04: Get Products
echo -e "\n${BLUE}[TC-EMP-04]${NC} Get Products for POS"
PRODUCTS=$(api_call GET "/pos/products?limit=5" "" "$EMPLOYEE_TOKEN")

if echo "$PRODUCTS" | grep -q "products"; then
    VARIANT_ID=$(echo "$PRODUCTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['products'][0]['variants'][0]['id'] if data['products'] else '')" 2>/dev/null)
    test_result "TC-EMP-04: Get Products" "PASS" "Variant ID: $VARIANT_ID"
else
    test_result "TC-EMP-04: Get Products" "FAIL" "No products returned"
fi

# TC-EMP-05: Create Transaction
echo -e "\n${BLUE}[TC-EMP-05]${NC} Create POS Transaction"
CREATE_TXN=$(api_call POST "/pos/transactions" '{"shift_id":'$SHIFT_ID',"payment_method":"cash","items":[{"variant_id":'$VARIANT_ID',"quantity":1}],"cash_tendered":10000}' "$EMPLOYEE_TOKEN")

if echo "$CREATE_TXN" | grep -q "transaction_id"; then
    TRANSACTION_ID=$(echo "$CREATE_TXN" | python3 -c "import sys, json; print(json.load(sys.stdin)['transaction_id'])" 2>/dev/null)
    test_result "TC-EMP-05: Create Transaction" "PASS" "Transaction ID: $TRANSACTION_ID"
else
    test_result "TC-EMP-05: Create Transaction" "FAIL" "Transaction creation failed"
    echo "Response: $CREATE_TXN"
fi

# TC-EMP-06: Get Transaction Details
echo -e "\n${BLUE}[TC-EMP-06]${NC} Get Transaction Details"
if [ -n "$TRANSACTION_ID" ]; then
    TXN_DETAILS=$(api_call GET "/pos/transactions/$TRANSACTION_ID" "" "$EMPLOYEE_TOKEN")
    
    if echo "$TXN_DETAILS" | grep -q "transaction_number"; then
        test_result "TC-EMP-06: Get Transaction Details" "PASS" ""
    else
        test_result "TC-EMP-06: Get Transaction Details" "FAIL" "No transaction details"
    fi
else
    test_result "TC-EMP-06: Get Transaction Details" "FAIL" "No transaction ID"
fi

# TC-EMP-07: Get Shift Summary
echo -e "\n${BLUE}[TC-EMP-07]${NC} Get Shift Summary"
SHIFT_SUMMARY=$(api_call GET "/pos/shifts/$SHIFT_ID" "" "$EMPLOYEE_TOKEN")

if echo "$SHIFT_SUMMARY" | grep -q "shift_number"; then
    test_result "TC-EMP-07: Get Shift Summary" "PASS" ""
else
    test_result "TC-EMP-07: Get Shift Summary" "FAIL" "No shift summary"
    echo "Response: $SHIFT_SUMMARY"
fi

# TC-EMP-08: Cash Movement
echo -e "\n${BLUE}[TC-EMP-08]${NC} Record Cash Movement"
CASH_MOVEMENT=$(api_call POST "/pos/cash-movements" '{"shift_id":'$SHIFT_ID',"movement_type":"cash_out","amount":1000,"reason":"Bank deposit"}' "$EMPLOYEE_TOKEN")

if echo "$CASH_MOVEMENT" | grep -q "success"; then
    test_result "TC-EMP-08: Cash Movement" "PASS" ""
else
    test_result "TC-EMP-08: Cash Movement" "FAIL" "Cash movement failed"
fi

# TC-EMP-09: Close Shift
echo -e "\n${BLUE}[TC-EMP-09]${NC} Close Shift"
CLOSE_SHIFT=$(api_call POST "/pos/shifts/$SHIFT_ID/close" '{
    "closing_cash": 9000,
    "notes": "UAT test shift"
}' "$EMPLOYEE_TOKEN")

if echo "$CLOSE_SHIFT" | grep -q "success"; then
    test_result "TC-EMP-09: Close Shift" "PASS" ""
else
    test_result "TC-EMP-09: Close Shift" "FAIL" "Shift close failed"
    echo "Response: $CLOSE_SHIFT"
fi

#############################################
# FINAL REPORT
#############################################

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "=============================================="
echo "  TEST SUMMARY"
echo "=============================================="
echo -e "Total Tests:  ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
echo -e "Duration:     ${YELLOW}${DURATION}s${NC}"
echo "=============================================="

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
