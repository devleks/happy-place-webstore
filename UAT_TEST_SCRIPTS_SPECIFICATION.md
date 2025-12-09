# UAT Test Scripts - Technical Specification
## Happy Place Webstore - December 8, 2025

This document specifies the automated test scripts to be implemented for comprehensive UAT testing of the Happy Place Webstore platform.

---

## Script Architecture

### Test Script Suite (3 scripts)

1. **`uat_smoke_tests.sh`** - Quick critical path validation (5-10 min)
2. **`uat_regression_tests.sh`** - Previously failed scenarios (15-20 min)
3. **`uat_comprehensive_2025.sh`** - Full test suite (3-4 hours)

### Common Infrastructure

All scripts share these components:

**Configuration Variables:**
```bash
BASE_URL="${BASE_URL:-http://127.0.0.1:5001/api}"
CURL_TIMEOUT=10
MAX_RETRIES=2
LOG_FILE="uat_results_$(date +%Y%m%d_%H%M%S).log"
```

**Color Codes:**
```bash
GREEN='\033[0;32m'    # Success
RED='\033[0;31m'      # Failure
YELLOW='\033[1;33m'   # Warning
BLUE='\033[0;34m'     # Info
CYAN='\033[0;36m'     # Section headers
NC='\033[0m'          # No color
```

**Test Counters:**
```bash
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNED_TESTS=0
SKIPPED_TESTS=0
```

---

## Script 1: Smoke Tests (`uat_smoke_tests.sh`)

### Purpose
Quick validation that the system is operational and testable. If smoke tests fail, full UAT should not proceed.

### Test Cases (5)

#### SMOKE-001: API Health Check
```bash
echo "[SMOKE-001] API Health Check"
RESPONSE=$(curl -s -m 5 "$BASE_URL/pos/health")
if echo "$RESPONSE" | grep -q "healthy"; then
    pass_test "SMOKE-001"
else
    fail_test "SMOKE-001" "API not responding"
    exit 1  # CRITICAL - stop all testing
fi
```

#### SMOKE-002: Database Connectivity
```bash
echo "[SMOKE-002] Database Connectivity"
RESPONSE=$(curl -s -m 5 "$BASE_URL/products?limit=1")
if echo "$RESPONSE" | grep -q "products"; then
    pass_test "SMOKE-002"
else
    fail_test "SMOKE-002" "Database not accessible"
    exit 1  # CRITICAL
fi
```

#### SMOKE-003: Customer Authentication
```bash
echo "[SMOKE-003] Customer Authentication"
RESPONSE=$(curl -s -m 5 -X POST "$BASE_URL/auth/customer/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"TestPass123!"}')
    
if echo "$RESPONSE" | grep -q "access_token"; then
    CUSTOMER_TOKEN=$(extract_json_field "$RESPONSE" "access_token")
    pass_test "SMOKE-003"
else
    fail_test "SMOKE-003" "Customer auth not working"
    exit 1
fi
```

#### SMOKE-004: Employee Authentication
```bash
echo "[SMOKE-004] Employee Authentication"
RESPONSE=$(curl -s -m 5 -X POST "$BASE_URL/auth/employee/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"manager@happyplace.co.ke","password":"manager123"}')
    
if echo "$RESPONSE" | grep -q "access_token"; then
    EMPLOYEE_TOKEN=$(extract_json_field "$RESPONSE" "access_token")
    pass_test "SMOKE-004"
else
    fail_test "SMOKE-004" "Employee auth not working"
    exit 1
fi
```

#### SMOKE-005: Admin Dashboard Access
```bash
echo "[SMOKE-005] Admin Dashboard Access"
RESPONSE=$(curl -s -m 5 -X GET "$BASE_URL/admin/dashboard/metrics?period=today" \
    -H "Authorization: Bearer $EMPLOYEE_TOKEN")
    
if echo "$RESPONSE" | grep -q "sales"; then
    pass_test "SMOKE-005"
else
    fail_test "SMOKE-005" "Admin dashboard not accessible"
fi
```

**Exit Behavior:**
- If ALL smoke tests pass: Exit 0 (continue to full UAT)
- If ANY smoke test fails: Exit 1 (STOP)

---

## Script 2: Regression Tests (`uat_regression_tests.sh`)

### Purpose
Re-test all scenarios that failed in previous UAT (December 5, 2025). These MUST pass before production deployment.

### Test Cases (3 critical)

#### REGR-001: POS Transaction Creation (Previously TC-EMP-06)
**Previous Status:** ❌ FAILED with HTTP 400  
**Priority:** P0 - BLOCKING

```bash
echo "[REGR-001] POS Transaction Creation FIX VERIFICATION"

# Prerequisites: Valid shift and product
SHIFT_RESPONSE=$(curl -s -m 5 -X POST "$BASE_URL/pos/shifts/start" \
    -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"store_location_id":1,"opening_float":5000}')

SHIFT_ID=$(extract_json_field "$SHIFT_RESPONSE" "shift.shift_id")

# Get valid variant
PRODUCT_RESPONSE=$(curl -s -m 5 "$BASE_URL/products?limit=1")
VARIANT_ID=$(echo "$PRODUCT_RESPONSE" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); \
     print(d['products'][0]['variants'][0]['id'])" 2>/dev/null)

# CRITICAL TEST: Create transaction
TRANSACTION_RESPONSE=$(curl -s -m 5 -X POST "$BASE_URL/pos/transactions" \
    -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"shift_id\": $SHIFT_ID,
        \"payment_method\": \"cash\",
        \"items\": [{\"variant_id\": $VARIANT_ID, \"quantity\": 1}],
        \"cash_tendered\": 10000
    }")

if echo "$TRANSACTION_RESPONSE" | grep -q "transaction_id"; then
    TRANSACTION_ID=$(extract_json_field "$TRANSACTION_RESPONSE" "transaction_id")
    pass_test "REGR-001: POS Transaction Creation"
    
    # Additional validation
    echo "  ↳ Validating inventory was decremented..."
    echo "  ↳ Validating transaction appears in shift..."
    
else
    fail_test "REGR-001: POS Transaction Creation" "STILL FAILING"
    log_error "Response: $TRANSACTION_RESPONSE"
    CRITICAL_FAILURE=true
fi
```

#### REGR-002: Shift Summary Retrieval (Previously TC-EMP-11)
**Previous Status:** ❌ FAILED with HTTP 404  
**Priority:** P0 - BLOCKING

```bash
echo "[REGR-002] Shift Summary Retrieval FIX VERIFICATION"

# Get shift details
SHIFT_DETAIL=$(curl -s -m 5 -X GET "$BASE_URL/pos/shifts/$SHIFT_ID" \
    -H "Authorization: Bearer $EMPLOYEE_TOKEN")

if echo "$SHIFT_DETAIL" | grep -q "shift_number"; then
    pass_test "REGR-002: Shift Summary Retrieval"
    
    # Verify structure
    SHIFT_NUMBER=$(extract_json_field "$SHIFT_DETAIL" "shift.shift_number")
    echo "  ↳ Shift Number: $SHIFT_NUMBER"
    
    # Verify aggregated stats exist
    if echo "$SHIFT_DETAIL" | grep -q "total_sales"; then
        echo "  ↳ Stats aggregation working"
    else
        warn_test "REGR-002" "Stats missing but shift found"
    fi
else
    fail_test "REGR-002: Shift Summary Retrieval" "STILL FAILING"
    log_error "Response: $SHIFT_DETAIL"
    CRITICAL_FAILURE=true
fi
```

#### REGR-003: Complete POS Workflow
**Purpose:** End-to-end validation that POS system works

```bash
echo "[REGR-003] Complete POS Workflow"

# Chain all POS operations
workflow_steps=(
    "Start shift"
    "Get current shift"
    "Create transaction"
    "Get transaction details"
    "Generate thermal receipt"
    "Record cash movement"
    "Get shift transactions"
    "Close shift"
)

WORKFLOW_SUCCESS=true

# Execute each step and track failures
# Implementation details provided in next section
```

**Exit Condition:**
- If REGR-001 OR REGR-002 fails: Report as CRITICAL, recommend fixing before full UAT
- If both pass: Continue to full test suite

---

## Script 3: Comprehensive UAT (`uat_comprehensive_2025.sh`)

### Script Structure

```bash
#!/bin/bash
################################################################################
# Happy Place Webstore - Comprehensive UAT Test Suite
# Version: 2.0
# Date: December 8, 2025
# Coverage: All system features including Phase 10 & 11
################################################################################

# [Configuration section - as defined above]

# [Helper functions section]
source ./uat_helpers.sh  # Extract common functions

# [Test execution sections]
run_smoke_tests
if [ $? -ne 0 ]; then
    echo "SMOKE TESTS FAILED - STOPPING"
    exit 1
fi

run_regression_tests
if [ $CRITICAL_FAILURE = true ]; then
    echo "CRITICAL REGRESSION FAILURES - RECOMMEND STOPPING"
    # Continue but flag for review
fi

run_auth_tests          # Phase 10
run_customer_tests      # E-commerce journey
run_pos_tests           # Employee/POS operations
run_admin_tests         # Phase 11 admin dashboard
run_gdpr_tests          # GDPR compliance
run_integration_tests   # End-to-end scenarios

# [Results compilation and reporting]
generate_test_report
```

### Test Implementation Patterns

#### Pattern 1: Basic GET Request
```bash
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
    else
        fail_test "$test_id" "Expected field not found: $expected_field"
    fi
}
```

#### Pattern 2: POST with JSON Body
```bash
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
        echo "$BODY"  # Return response for chaining
    else
        fail_test "$test_id" "HTTP $HTTP_CODE, expected $expected_code"
    fi
}
```

#### Pattern 3: Authentication Flow
```bash
auth_login() {
    local user_type=$1  # "customer" or "employee"
    local email=$2
    local password=$3
    
    RESPONSE=$(curl -s -m $CURL_TIMEOUT \
        -X POST "$BASE_URL/auth/$user_type/login" \
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
```

### Helper Functions Required

#### JSON Field Extraction
```bash
extract_json_field() {
    local json=$1
    local field=$2
    
    echo "$json" | python3 -c \
        "import sys,json; \
         data=json.load(sys.stdin); \
         fields='$field'.split('.'); \
         val=data; \
         [val:=val.get(f) for f in fields]; \
         print(val if val else '')" 2>/dev/null
}
```

#### Test Result Tracking
```bash
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
```

---

## Test Section Specifications

### Section 1: Authentication Tests (Phase 10)

#### AUTH-001 through AUTH-012
Tests all authentication endpoints from Phase 10.

**Key Validations:**
- Customer registration with GDPR consent
- Customer login returns valid JWT
- Google OAuth flow (if configured)
- Employee login with/without 2FA
- 2FA enable/verify/disable flow
- PIN login for POS
- Token refresh mechanism
- Logout (single & all devices)
- Session management
- Permissions and audit log

**Example Implementation:**
```bash
run_auth_tests() {
    echo -e "\n${CYAN}=====================================${NC}"
    echo -e "${CYAN}AUTHENTICATION TESTS (Phase 10)${NC}"
    echo -e "${CYAN}=====================================${NC}"
    
    # AUTH-001: Customer Registration
    echo -e "\n[AUTH-001] Customer Registration"
    REGISTER_DATA='{
        "email": "uat.customer.'"$(date +%s)"'@test.com",
        "password": "TestPass123!",
        "first_name": "UAT",
        "last_name": "Customer",
        "phone": "+254712345678",
        "gdpr_consent": true,
        "marketing_consent": false
    }'
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -m $CURL_TIMEOUT \
        -X POST "$BASE_URL/auth/customer/register" \
        -H "Content-Type: application/json" \
        -d "$REGISTER_DATA")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" -eq 201 ] && echo "$BODY" | grep -q "customer_id"; then
        CUSTOMER_ID=$(extract_json_field "$BODY" "customer_id")
        NEW_CUSTOMER_EMAIL=$(extract_json_field "$BODY" "customer.email")
        pass_test "AUTH-001"
    else
        fail_test "AUTH-001" "HTTP $HTTP_CODE"
    fi
    
    # AUTH-002: Customer Login
    # ... continue pattern for all auth tests
}
```

### Section 2: Customer Journey Tests

**Flow:**
1. Login → 2. Browse → 3. Add to cart → 4. Checkout → 5. View orders

**Validation Points:**
- Cart persistence
- Shipping calculation (Nairobi vs Upcountry)
- Order creation
- Inventory deduction
- Order number generation
- Order history retrieval

### Section 3: POS Tests

**Critical Path:**
1. Start shift
2. Search product
3. Create transaction (P0 blocker from previous UAT)
4. Generate receipts
5. Cash management
6. Close shift with reconciliation

**Extra Validation:**
- Verify stored procedure `sp_create_pos_transaction` works
- Verify inventory deduction happens
- Verify shift stats aggregate correctly
- Verify cash variance calculation

### Section 4: Admin Dashboard Tests (Phase 11)

**Categories to Test:**

**Dashboard (4 tests):**
- Metrics with period comparison
- Activity feed
- Alerts
- Trends data

**Inventory Management (9 tests):**
- List with filters
- Create product
- Update product
- Adjust stock
- Bulk update
- Transfer
- History
- Delete
- Inventory alerts

**Order Management (8 tests):**
- List orders with filters
- Get details
- Update status
- Cancel with refund
- Add notes
- Timeline
- Notify customer
- Refund processing

**Customer Management (9 tests including GDPR):**
- List customers
- Get details with stats
- Update customer
- View orders
- View activity
- **GDPR: Export data**
- **GDPR: Anonymize** (use test customer only!)
- **GDPR: Delete** (no orders required)
- Consent history

**Employee Management (9 tests):**
- List employees
- Create employee
- Update employee
- Deactivate
- Reset password
- Disable 2FA
- View activity
- Performance metrics
- Employee details

**Promotions (9 tests):**
- List promotions
- Create promotion
- Update promotion
- Get analytics
- Enable/disable
- Duplicate
- Validate code
- Delete

**Reports (4 tests):**
- Sales report
- Inventory report
- Customer report
- Employee performance report

**Settings (6 tests):**
- Get all settings
- Update store settings
- Update business hours
- Update email settings
- Update currency
- Get currency

### Section 5: GDPR Compliance Tests

**Critical Validation:**
```bash
run_gdpr_tests() {
    echo -e "\n${CYAN}=====================================${NC}"
    echo -e "${CYAN}GDPR COMPLIANCE TESTS${NC}"
    echo -e "${CYAN}=====================================${NC}"
    
    # GDPR-001: Consent Tracking
    # Verify registration includes consent timestamp
    
    # GDPR-002: Data Export
    echo "[GDPR-002] Customer Data Export"
    EXPORT=$(curl -s -m 10 -X POST \
        "$BASE_URL/admin/customers/$TEST_CUSTOMER_ID/export" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$EXPORT" | grep -q "customer"; then
        # Validate export structure
        if echo "$EXPORT" | grep -q "addresses" && \
           echo "$EXPORT" | grep -q "orders"; then
            pass_test "GDPR-002"
        else
            fail_test "GDPR-002" "Incomplete export"
        fi
    else
        fail_test "GDPR-002" "Export failed"
    fi
    
    # GDPR-003: Anonymization
    # WARNING: Only use on test customer!
    echo "[GDPR-003] Customer Anonymization"
    ANON=$(curl -s -m 10 -X POST \
        "$BASE_URL/admin/customers/$TEST_CUSTOMER_ID/anonymize" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"confirmation":"ANONYMIZE","reason":"UAT test"}')
    
    if echo "$ANON" | grep -q "success"; then
        pass_test "GDPR-003"
        
        # Verify anonymization worked
        CUSTOMER=$(curl -s "$BASE_URL/admin/customers/$TEST_CUSTOMER_ID" \
            -H "Authorization: Bearer $ADMIN_TOKEN")
        
        if echo "$CUSTOMER" | grep -q "ANONYMIZED"; then
            echo "  ↳ PII properly anonymized"
        fi
    else
        fail_test "GDPR-003" "Anonymization failed"
    fi
}
```

### Section 6: Integration Tests

#### INTEG-001: Complete Customer Purchase
```bash
# End-to-end: Registration → Browse → Cart → Checkout → Order History
1. Register new customer
2. Login and get token
3. Browse products
4. Add 3 items to cart
5. Calculate shipping for Nairobi
6. Create order
7. Verify order in history
8. Verify inventory was decremented for all items
```

#### INTEG-002: Complete POS Sale
```bash
# End-to-end: Login → Shift → Sale → Receipt → Close
1. Employee login
2. Start shift
3. Search products
4. Create 3 transactions
5. Generate receipts for all
6. Record cash movement
7. Close shift
8. Verify cash reconciliation
```

#### INTEG-003: Admin Order Management
```bash
# End-to-end: View → Process → Ship → Track
1. Admin login
2. View pending orders
3. Update order to processing
4. Add internal note
5. Update to shipped with tracking
6. Send customer notification
7. Get order timeline
```

---

## Enhanced Error Reporting

### Error Categories
```bash
declare -A ERROR_CATEGORIES=(
    ["HTTP_400"]="Bad Request - Validation Error"
    ["HTTP_401"]="Unauthorized - Auth Failed"
    ["HTTP_403"]="Forbidden - Permission Denied"
    ["HTTP_404"]="Not Found - Endpoint or Resource Missing"
    ["HTTP_500"]="Internal Server Error - Backend Issue"
    ["TIMEOUT"]="Request Timeout - Performance Issue"
    ["NETWORK"]="Network Error - Connection Failed"
)
```

### Detailed Failure Logging
```bash
log_failure_details() {
    local test_id=$1
    local http_code=$2
    local response=$3
    local request_data=$4
    
    cat >> "$LOG_FILE" << EOF

================================================================================
FAILURE DETAILS: $test_id
================================================================================
Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
HTTP Code: $http_code (${ERROR_CATEGORIES[$http_code]:-Unknown})
Endpoint: $endpoint
Request Data:
$request_data

Response:
$response

Recommendation:
$(get_fix_recommendation "$http_code" "$response")
================================================================================

EOF
}
```

### Automatic Fix Recommendations
```bash
get_fix_recommendation() {
    local http_code=$1
    local response=$2
    
    case $http_code in
        400)
            echo "- Check request data format and required fields"
            echo "- Verify data types match API spec"
            echo "- Check for validation errors in response"
            ;;
        401)
            echo "- Verify JWT token is valid and not expired"
            echo "- Check Authorization header format"
            echo "- Ensure user has active session"
            ;;
        403)
            echo "- Verify user has required role/permissions"
            echo "- Check endpoint access requirements"
            echo "- Ensure employee role is admin/manager if required"
            ;;
        404)
            echo "- Verify endpoint is registered in routes"
            echo "- Check URL pattern matches route definition"
            echo "- Ensure resource exists in database"
            ;;
        500)
            echo "- Check backend logs for stack trace"
            echo "- Verify database connection"
            echo "- Check for missing dependencies or services"
            ;;
    esac
}
```

---

## Test Results Reporting

### JSON Results Output
```bash
generate_json_report() {
    local output_file="uat_results_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$output_file" << EOF
{
  "test_run": {
    "date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "duration_seconds": $DURATION,
    "environment": {
      "base_url": "$BASE_URL",
      "backend_version": "Latest",
      "test_suite_version": "2.0"
    }
  },
  "summary": {
    "total": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "warned": $WARNED_TESTS,
    "skipped": $SKIPPED_TESTS,
    "pass_rate": $(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
  },
  "categories": {
    "smoke": $SMOKE_RESULTS,
    "regression": $REGRESSION_RESULTS,
    "authentication": $AUTH_RESULTS,
    "customer": $CUSTOMER_RESULTS,
    "pos": $POS_RESULTS,
    "admin": $ADMIN_RESULTS,
    "gdpr": $GDPR_RESULTS,
    "integration": $INTEGRATION_RESULTS
  },
  "critical_issues": $(echo "$CRITICAL_FAILURES" | jq -R -s 'split("\n")'),
  "recommendations": $(echo "$RECOMMENDATIONS" | jq -R -s 'split("\n")')
}
EOF
    
    echo "$output_file"
}
```

### Markdown Summary Report
```bash
generate_markdown_report() {
    local output_file="UAT_RESULTS_$(date +%Y-%m-%d).md"
    
    cat > "$output_file" << 'EOF'
# UAT Test Results - December 8, 2025

## Executive Summary

**Test Execution Date:** $(date)  
**Test Duration:** $DURATION seconds  
**Overall Result:** $(get_overall_status)

### Quick Stats
- **Total Tests:** $TOTAL_TESTS
- **Passed:** $PASSED_TESTS ($(calc_percentage $PASSED_TESTS $TOTAL_TESTS)%)
- **Failed:** $FAILED_TESTS ($(calc_percentage $FAILED_TESTS $TOTAL_TESTS)%)
- **Warned:** $WARNED_TESTS
- **Skipped:** $SKIPPED_TESTS

---

## Test Category Results

### Smoke Tests: $(get_category_status "smoke")
- Critical path validation
- Results: $SMOKE_PASSED/$SMOKE_TOTAL passed

### Regression Tests: $(get_category_status "regression")
- Previous P0 issues verification
- REGR-001 (POS Transaction): $(get_test_status "REGR-001")
- REGR-002 (Shift Summary): $(get_test_status "REGR-002")

### Authentication Tests: $(get_category_status "auth")
- Phase 10 features validation
- Results: $AUTH_PASSED/$AUTH_TOTAL passed

### Customer Journey: $(get_category_status "customer")
- E-commerce flow validation
- Results: $CUSTOMER_PASSED/$CUSTOMER_TOTAL passed

### POS System: $(get_category_status "pos")
- Employee operations validation
- Results: $POS_PASSED/$POS_TOTAL passed

### Admin Dashboard: $(get_category_status "admin")
- Phase 11 features validation
- Results: $ADMIN_PASSED/$ADMIN_TOTAL passed

### GDPR Compliance: $(get_category_status "gdpr")
- Data privacy validation
- Results: $GDPR_PASSED/$GDPR_TOTAL passed

### Integration Tests: $(get_category_status "integration")
- End-to-end scenarios
- Results: $INTEG_PASSED/$INTEG_TOTAL passed

---

## Critical Issues

$(list_critical_failures)

---

## Production Readiness Assessment

$(generate_production_recommendation)

---

*Report generated by UAT Comprehensive Test Suite v2.0*
EOF
    
    echo "$output_file"
}
```

---

## Performance Tracking

### Response Time Monitoring
```bash
measure_response_time() {
    local endpoint=$1
    local method=$2
    local data=$3
    local token=$4
    
    START_TIME=$(date +%s%N)
    
    RESPONSE=$(curl -s -m $CURL_TIMEOUT -X $method \
        "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$data")
    
    END_TIME=$(date +%s%N)
    DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))
    
    echo "$DURATION_MS"
}
```

### Performance Thresholds
- **Smoke tests:** < 5000ms each
- **GET requests:** < 500ms
- **POST/PUT requests:** < 1000ms
- **Complex operations (orders, reports):** < 2000ms
- **Database writes:** < 500ms

### Performance Failure Handling
```bash
check_performance() {
    local test_id=$1
    local duration=$2
    local threshold=$3
    
    if [ $duration -gt $threshold ]; then
        warn_test "$test_id" "Slow response: ${duration}ms (threshold: ${threshold}ms)"
        echo "  ↳ Consider performance optimization"
    fi
}
```

---

## Test Data Management

### Setup Test Data
```bash
setup_test_data() {
    echo "Setting up test data..."
    
    # Create test customer (for GDPR testing)
    create_test_customer
    
    # Create test employee (for role testing)
    create_test_employee
    
    # Create test product (for inventory testing)
    create_test_product
    
    echo "Test data setup complete"
}
```

### Cleanup Test Data
```bash
cleanup_test_data() {
    echo "Cleaning up test data..."
    
    # Delete test customers (created during UAT)
    # Delete test employees (created during UAT)
    # Delete test products (created during UAT)
    # Note: Keep orders for audit trail
    
    echo "Cleanup complete"
}
```

---

## Execution Instructions

### Running Individual Scripts

**Smoke Tests Only:**
```bash
cd tests
chmod +x uat_smoke_tests.sh
./uat_smoke_tests.sh
```

**Regression Tests Only:**
```bash
cd tests
chmod +x uat_regression_tests.sh
BASE_URL=http://127.0.0.1:5001/api ./uat_regression_tests.sh
```

**Full Comprehensive Suite:**
```bash
cd tests
chmod +x uat_comprehensive_2025.sh

# With custom configuration
BASE_URL=http://localhost:5001/api \
CURL_TIMEOUT=15 \
./uat_comprehensive_2025.sh
```

### Interpreting Results

**Exit Codes:**
- `0` - All tests passed
- `1` - Critical failures (smoke or regression)
- `2` - Some tests failed but not critical
- `3` - Test suite error (setup/environment issue)

**Output Files Generated:**
- `uat_results_YYYYMMDD_HHMMSS.log` - Detailed execution log
- `uat_results_YYYYMMDD_HHMMSS.json` - Machine-readable results
- `UAT_RESULTS_YYYY-MM-DD.md` - Human-readable summary report

---

## Implementation Checklist

### Script Development
- [ ] Create `uat_helpers.sh` with common functions
- [ ] Implement `uat_smoke_tests.sh` (highest priority)
- [ ] Implement `uat_regression_tests.sh` (P0 fixes)
- [ ] Implement `uat_comprehensive_2025.sh` (full suite)
- [ ] Add error handling and retry logic
- [ ] Add performance monitoring
- [ ] Add detailed logging

### Testing & Validation
- [ ] Test scripts on clean database
- [ ] Verify all JSON parsing works
- [ ] Test error scenarios (server down, invalid data)
- [ ] Verify cleanup functions work
- [ ] Test report generation

### Documentation
- [ ] Create execution guide (next document)
- [ ] Document troubleshooting steps
- [ ] Add examples of expected output
- [ ] Create quick reference card

---

## Next Steps

1. ✅ Test plan created (this document)
2. ⏳ Implement helper functions (`uat_helpers.sh`)
3. ⏳ Implement smoke tests script
4. ⏳ Implement regression tests script
5. ⏳ Implement comprehensive test script
6. ⏳ Create execution guide
7. ⏳ Run test execution
8. ⏳ Generate results report

**Note:** Script implementation requires switching to **Code mode** as Architect mode can only edit Markdown files.

---

**Document Version:** 2.0  
**Created:** December 8, 2025  
**Status:** Ready for Code Implementation  
**Recommended Next Action:** Switch to Code mode to implement scripts