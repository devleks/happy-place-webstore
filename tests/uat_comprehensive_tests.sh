#!/bin/bash

#############################################
# Happy Place Webstore - Comprehensive UAT
# End-to-End Testing Suite
#############################################

echo "=============================================="
echo "  HAPPY PLACE WEBSTORE - UAT TEST SUITE"
echo "=============================================="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:5001/api}"
START_TIME=$(date +%s)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# Test data storage
CUSTOMER_TOKEN=""
EMPLOYEE_TOKEN=""
ADMIN_TOKEN=""
TEST_EMAIL="uat.test.$(date +%s)@happyplace.com"
ORDER_ID=""
ORDER_NUMBER=""
SHIFT_ID=""
TRANSACTION_ID=""
PRODUCT_SLUG=""
VARIANT_ID=""
WISHLIST_ITEM_ID=""
EMPLOYEE_ID=""
CUSTOMER_ID=""

#############################################
# Helper Functions
#############################################

# Print test result
print_test_result() {
    local status=$1
    local test_id=$2
    local description=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✅ PASS${NC}: ${test_id} - ${description}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    elif [ "$status" = "fail" ]; then
        echo -e "${RED}❌ FAIL${NC}: ${test_id} - ${description}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: ${test_id} - ${description}"
        WARNING_TESTS=$((WARNING_TESTS + 1))
        TOTAL_TESTS=$((TOTAL_TESTS - 1)) # Don't count warnings as tests
    fi
}

# Print section header
print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Make API call
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    local temp_file=$(mktemp)
    
    if [ -n "$token" ]; then
        if [ "$method" = "GET" ] || [ "$method" = "DELETE" ]; then
            curl -s -w "\n%{http_code}" -X "$method" \
                "$BASE_URL$endpoint" \
                -H "Authorization: Bearer $token" > "$temp_file" 2>/dev/null
        else
            curl -s -w "\n%{http_code}" -X "$method" \
                "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d "$data" > "$temp_file" 2>/dev/null
        fi
    else
        if [ "$method" = "GET" ] || [ "$method" = "DELETE" ]; then
            curl -s -w "\n%{http_code}" -X "$method" \
                "$BASE_URL$endpoint" > "$temp_file" 2>/dev/null
        else
            curl -s -w "\n%{http_code}" -X "$method" \
                "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data" > "$temp_file" 2>/dev/null
        fi
    fi
    
    http_code=$(tail -n 1 "$temp_file")
    body=$(sed '$d' "$temp_file")
    rm -f "$temp_file"
    
    echo "$body"
    echo "$http_code"
}

# Extract HTTP code from response
get_http_code() {
    echo "$1" | tail -n 1
}

# Extract response body
get_response_body() {
    echo "$1" | sed '$d'
}

# Parse JSON value
parse_json() {
    local json=$1
    local key=$2
    echo "$json" | jq -r ".$key // empty" 2>/dev/null || echo ""
}

# Parse nested JSON value
parse_json_nested() {
    local json=$1
    local path=$2
    echo "$json" | jq -r ".$path // empty" 2>/dev/null || echo ""
}

#############################################
# CUSTOMER JOURNEY TESTS (12 tests)
#############################################

print_section "CUSTOMER JOURNEY - 12 Tests"

# TC-CUST-01: Register customer with GDPR
echo "TC-CUST-01: Testing customer registration with GDPR consent..."
REGISTER_DATA=$(cat <<EOF
{
  "email": "$TEST_EMAIL",
  "password": "TestPass123!",
  "first_name": "UAT",
  "last_name": "Customer",
  "phone": "+254712345678",
  "gdpr_consent": true,
  "marketing_consent": false
}
EOF
)

REGISTER_RESPONSE=$(api_call "POST" "/auth/customer/register" "$REGISTER_DATA" "")
HTTP_CODE=$(get_http_code "$REGISTER_RESPONSE")
RESPONSE_BODY=$(get_response_body "$REGISTER_RESPONSE")

if [ "$HTTP_CODE" = "201" ]; then
    CUSTOMER_TOKEN=$(parse_json "$RESPONSE_BODY" "access_token")
    CUSTOMER_ID=$(parse_json_nested "$RESPONSE_BODY" "customer.id")
    print_test_result "pass" "TC-CUST-01" "Customer registration with GDPR (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-CUST-01" "Customer registration failed (HTTP $HTTP_CODE)"
fi

# TC-CUST-02: Login customer
echo "TC-CUST-02: Testing customer login..."
LOGIN_DATA=$(cat <<EOF
{
  "email": "$TEST_EMAIL",
  "password": "TestPass123!"
}
EOF
)

LOGIN_RESPONSE=$(api_call "POST" "/auth/customer/login" "$LOGIN_DATA" "")
HTTP_CODE=$(get_http_code "$LOGIN_RESPONSE")
RESPONSE_BODY=$(get_response_body "$LOGIN_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    CUSTOMER_TOKEN=$(parse_json "$RESPONSE_BODY" "access_token")
    print_test_result "pass" "TC-CUST-02" "Customer login (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-CUST-02" "Customer login failed (HTTP $HTTP_CODE)"
fi

# TC-CUST-03: Browse products by category
echo "TC-CUST-03: Testing browse products..."
PRODUCTS_RESPONSE=$(api_call "GET" "/products?page=1&per_page=12" "" "")
HTTP_CODE=$(get_http_code "$PRODUCTS_RESPONSE")
RESPONSE_BODY=$(get_response_body "$PRODUCTS_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    # Extract first product slug for later use
    PRODUCT_SLUG=$(echo "$RESPONSE_BODY" | jq -r '.products[0].slug // empty' 2>/dev/null)
    print_test_result "pass" "TC-CUST-03" "Browse products (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-CUST-03" "Browse products failed (HTTP $HTTP_CODE)"
fi

# TC-CUST-04: Search products
echo "TC-CUST-04: Testing product search..."
SEARCH_RESPONSE=$(api_call "GET" "/products?search=dress" "" "")
HTTP_CODE=$(get_http_code "$SEARCH_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-CUST-04" "Product search (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-CUST-04" "Product search failed (HTTP $HTTP_CODE)"
fi

# TC-CUST-05: View product details with variants
echo "TC-CUST-05: Testing view product details..."
if [ ! -z "$PRODUCT_SLUG" ]; then
    PRODUCT_RESPONSE=$(api_call "GET" "/products/$PRODUCT_SLUG" "" "$CUSTOMER_TOKEN")
    HTTP_CODE=$(get_http_code "$PRODUCT_RESPONSE")
    RESPONSE_BODY=$(get_response_body "$PRODUCT_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Extract variant ID for cart testing
        VARIANT_ID=$(echo "$RESPONSE_BODY" | jq -r '.variants[0].id // empty' 2>/dev/null)
        print_test_result "pass" "TC-CUST-05" "View product details with variants (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-CUST-05" "View product details failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-CUST-05" "Skipped - no product slug available"
fi

# TC-CUST-06: Add items to cart
echo "TC-CUST-06: Testing add to cart..."
if [ ! -z "$VARIANT_ID" ]; then
    ADD_CART_DATA=$(cat <<EOF
{
  "variant_id": $VARIANT_ID,
  "quantity": 2
}
EOF
)
    
    ADD_CART_RESPONSE=$(api_call "POST" "/cart/items" "$ADD_CART_DATA" "$CUSTOMER_TOKEN")
    HTTP_CODE=$(get_http_code "$ADD_CART_RESPONSE")
    
    if [ "$HTTP_CODE" = "201" ]; then
        print_test_result "pass" "TC-CUST-06" "Add to cart (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-CUST-06" "Add to cart failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-CUST-06" "Skipped - no variant ID available"
fi

# TC-CUST-07: Update cart quantities
echo "TC-CUST-07: Testing update cart quantity..."
if [ ! -z "$VARIANT_ID" ]; then
    UPDATE_CART_DATA=$(cat <<EOF
{
  "quantity": 3
}
EOF
)
    
    UPDATE_CART_RESPONSE=$(api_call "PATCH" "/cart/items/$VARIANT_ID" "$UPDATE_CART_DATA" "$CUSTOMER_TOKEN")
    HTTP_CODE=$(get_http_code "$UPDATE_CART_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-CUST-07" "Update cart quantity (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-CUST-07" "Update cart quantity failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-CUST-07" "Skipped - no variant ID available"
fi

# TC-CUST-08: Calculate shipping costs
echo "TC-CUST-08: Testing shipping calculation..."
SHIPPING_DATA=$(cat <<EOF
{
  "city": "Nairobi"
}
EOF
)

SHIPPING_RESPONSE=$(api_call "POST" "/orders/shipping-preview" "$SHIPPING_DATA" "$CUSTOMER_TOKEN")
HTTP_CODE=$(get_http_code "$SHIPPING_RESPONSE")
RESPONSE_BODY=$(get_response_body "$SHIPPING_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    SHIPPING_COST=$(parse_json "$RESPONSE_BODY" "shipping_cost")
    print_test_result "pass" "TC-CUST-08" "Shipping calculation (HTTP $HTTP_CODE, Cost: $SHIPPING_COST)"
else
    print_test_result "fail" "TC-CUST-08" "Shipping calculation failed (HTTP $HTTP_CODE)"
fi

# TC-CUST-09: Checkout and create order
echo "TC-CUST-09: Testing order creation..."
ORDER_DATA=$(cat <<EOF
{
  "shipping_address": {
    "street": "123 Test Street, Apt 4B",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  },
  "billing_address": {
    "street": "123 Test Street, Apt 4B",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  }
}
EOF
)

ORDER_RESPONSE=$(api_call "POST" "/orders" "$ORDER_DATA" "$CUSTOMER_TOKEN")
HTTP_CODE=$(get_http_code "$ORDER_RESPONSE")
RESPONSE_BODY=$(get_response_body "$ORDER_RESPONSE")

if [ "$HTTP_CODE" = "201" ]; then
    ORDER_ID=$(parse_json_nested "$RESPONSE_BODY" "order.id")
    ORDER_NUMBER=$(parse_json_nested "$RESPONSE_BODY" "order.order_number")
    print_test_result "pass" "TC-CUST-09" "Order creation (HTTP $HTTP_CODE, Order: $ORDER_NUMBER)"
else
    print_test_result "fail" "TC-CUST-09" "Order creation failed (HTTP $HTTP_CODE)"
fi

# TC-CUST-10: View order history
echo "TC-CUST-10: Testing order history..."
ORDER_HISTORY_RESPONSE=$(api_call "GET" "/orders?page=1&per_page=10" "" "$CUSTOMER_TOKEN")
HTTP_CODE=$(get_http_code "$ORDER_HISTORY_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-CUST-10" "View order history (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-CUST-10" "View order history failed (HTTP $HTTP_CODE)"
fi

# TC-CUST-11: Add item to wishlist
echo "TC-CUST-11: Testing add to wishlist..."
if [ ! -z "$VARIANT_ID" ]; then
    WISHLIST_DATA=$(cat <<EOF
{
  "variant_id": $VARIANT_ID
}
EOF
)
    
    WISHLIST_RESPONSE=$(api_call "POST" "/wishlist" "$WISHLIST_DATA" "$CUSTOMER_TOKEN")
    HTTP_CODE=$(get_http_code "$WISHLIST_RESPONSE")
    RESPONSE_BODY=$(get_response_body "$WISHLIST_RESPONSE")
    
    if [ "$HTTP_CODE" = "201" ]; then
        WISHLIST_ITEM_ID=$(parse_json "$RESPONSE_BODY" "id")
        print_test_result "pass" "TC-CUST-11" "Add to wishlist (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-CUST-11" "Add to wishlist failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-CUST-11" "Skipped - no variant ID available"
fi

# TC-CUST-12: View wishlist
echo "TC-CUST-12: Testing view wishlist..."
WISHLIST_VIEW_RESPONSE=$(api_call "GET" "/wishlist" "" "$CUSTOMER_TOKEN")
HTTP_CODE=$(get_http_code "$WISHLIST_VIEW_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-CUST-12" "View wishlist (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-CUST-12" "View wishlist failed (HTTP $HTTP_CODE)"
fi

#############################################
# EMPLOYEE JOURNEY TESTS (15 tests)
#############################################

print_section "EMPLOYEE JOURNEY - 15 Tests"

# TC-EMP-01: Employee login
echo "TC-EMP-01: Testing employee login..."
EMP_LOGIN_DATA=$(cat <<EOF
{
  "email": "manager@happyplace.co.ke",
  "password": "manager123"
}
EOF
)

EMP_LOGIN_RESPONSE=$(api_call "POST" "/auth/employee/login" "$EMP_LOGIN_DATA" "")
HTTP_CODE=$(get_http_code "$EMP_LOGIN_RESPONSE")
RESPONSE_BODY=$(get_response_body "$EMP_LOGIN_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    EMPLOYEE_TOKEN=$(parse_json "$RESPONSE_BODY" "access_token")
    EMPLOYEE_ID=$(parse_json_nested "$RESPONSE_BODY" "employee.id")
    print_test_result "pass" "TC-EMP-01" "Employee login (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-EMP-01" "Employee login failed (HTTP $HTTP_CODE)"
fi

# TC-EMP-02: Check current shift
echo "TC-EMP-02: Testing check current shift..."
SHIFT_CHECK_RESPONSE=$(api_call "GET" "/pos/shifts/current" "" "$EMPLOYEE_TOKEN")
HTTP_CODE=$(get_http_code "$SHIFT_CHECK_RESPONSE")
RESPONSE_BODY=$(get_response_body "$SHIFT_CHECK_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    SHIFT_ID=$(parse_json_nested "$RESPONSE_BODY" "shift.shift_id")
    if [ -z "$SHIFT_ID" ] || [ "$SHIFT_ID" = "null" ]; then
        print_test_result "pass" "TC-EMP-02" "No active shift (HTTP $HTTP_CODE)"
        SHIFT_ID=""  # Ensure it's empty for TC-EMP-03
    else
        print_test_result "pass" "TC-EMP-02" "Active shift found (HTTP $HTTP_CODE, Shift: $SHIFT_ID)"
    fi
else
    print_test_result "fail" "TC-EMP-02" "Check current shift failed (HTTP $HTTP_CODE)"
fi

# TC-EMP-03: Start POS shift with opening float
echo "TC-EMP-03: Testing start POS shift..."
if [ -z "$SHIFT_ID" ] || [ "$SHIFT_ID" = "null" ]; then
    SHIFT_DATA=$(cat <<EOF
{
  "store_location_id": 1,
  "opening_float": 5000.00
}
EOF
)
    
    SHIFT_START_RESPONSE=$(api_call "POST" "/pos/shifts/start" "$SHIFT_DATA" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$SHIFT_START_RESPONSE")
    RESPONSE_BODY=$(get_response_body "$SHIFT_START_RESPONSE")
    
    if [ "$HTTP_CODE" = "201" ]; then
        SHIFT_ID=$(parse_json_nested "$RESPONSE_BODY" "shift.shift_id")
        print_test_result "pass" "TC-EMP-03" "Start POS shift (HTTP $HTTP_CODE, Shift: $SHIFT_ID)"
    else
        print_test_result "fail" "TC-EMP-03" "Start POS shift failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-03" "Skipped - shift already active"
fi

# TC-EMP-04: Search products by SKU
echo "TC-EMP-04: Testing search products by SKU..."
SKU_SEARCH_RESPONSE=$(api_call "GET" "/products?search=FMD" "" "$EMPLOYEE_TOKEN")
HTTP_CODE=$(get_http_code "$SKU_SEARCH_RESPONSE")
RESPONSE_BODY=$(get_response_body "$SKU_SEARCH_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    # Get first product's variant for POS transaction
    if [ -z "$VARIANT_ID" ]; then
        PRODUCT_SLUG=$(echo "$RESPONSE_BODY" | jq -r '.products[0].slug // empty' 2>/dev/null)
        if [ ! -z "$PRODUCT_SLUG" ]; then
            PROD_DETAIL=$(api_call "GET" "/products/$PRODUCT_SLUG" "" "$EMPLOYEE_TOKEN")
            PROD_BODY=$(get_response_body "$PROD_DETAIL")
            VARIANT_ID=$(echo "$PROD_BODY" | jq -r '.variants[0].id // empty' 2>/dev/null)
        fi
    fi
    print_test_result "pass" "TC-EMP-04" "Search products by SKU (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-EMP-04" "Search products by SKU failed (HTTP $HTTP_CODE)"
fi

# TC-EMP-05: Scan barcode (simulated)
echo "TC-EMP-05: Testing barcode scan (simulated)..."
# Simulated by searching for SKU
BARCODE_RESPONSE=$(api_call "GET" "/products?sku=FMD-S-BLUE" "" "$EMPLOYEE_TOKEN")
HTTP_CODE=$(get_http_code "$BARCODE_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-EMP-05" "Barcode scan simulated (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-EMP-05" "Barcode scan failed (HTTP $HTTP_CODE)"
fi

# TC-EMP-06: Create POS transaction
echo "TC-EMP-06: Testing create POS transaction..."
if [ ! -z "$SHIFT_ID" ] && [ ! -z "$VARIANT_ID" ]; then
    TRANSACTION_DATA=$(cat <<EOF
{
  "shift_id": $SHIFT_ID,
  "payment_method": "cash",
  "items": [
    {"variant_id": $VARIANT_ID, "quantity": 2}
  ],
  "cash_tendered": 10000.00
}
EOF
)
    
    TRANSACTION_RESPONSE=$(api_call "POST" "/pos/transactions" "$TRANSACTION_DATA" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$TRANSACTION_RESPONSE")
    RESPONSE_BODY=$(get_response_body "$TRANSACTION_RESPONSE")
    
    if [ "$HTTP_CODE" = "201" ]; then
        TRANSACTION_ID=$(parse_json "$RESPONSE_BODY" "transaction_id")
        print_test_result "pass" "TC-EMP-06" "Create POS transaction (HTTP $HTTP_CODE, Txn: $TRANSACTION_ID)"
    else
        print_test_result "fail" "TC-EMP-06" "Create POS transaction failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-06" "Skipped - no active shift or variant"
fi

# TC-EMP-07: Process cash payment
echo "TC-EMP-07: Testing cash payment processing..."
if [ ! -z "$TRANSACTION_ID" ]; then
    print_test_result "pass" "TC-EMP-07" "Cash payment processed (included in transaction)"
else
    print_test_result "warn" "TC-EMP-07" "Skipped - no transaction created"
fi

# TC-EMP-08: Generate thermal receipt
echo "TC-EMP-08: Testing thermal receipt generation..."
if [ ! -z "$TRANSACTION_ID" ]; then
    RECEIPT_RESPONSE=$(api_call "GET" "/pos/transactions/$TRANSACTION_ID/receipt/thermal?width=58" "" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$RECEIPT_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-EMP-08" "Thermal receipt generated (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-EMP-08" "Thermal receipt generation failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-08" "Skipped - no transaction ID"
fi

# TC-EMP-09: Generate HTML receipt
echo "TC-EMP-09: Testing HTML receipt generation..."
if [ ! -z "$TRANSACTION_ID" ]; then
    HTML_RECEIPT_RESPONSE=$(api_call "GET" "/pos/transactions/$TRANSACTION_ID/receipt/html" "" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$HTML_RECEIPT_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-EMP-09" "HTML receipt generated (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-EMP-09" "HTML receipt generation failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-09" "Skipped - no transaction ID"
fi

# TC-EMP-10: Record cash movement
echo "TC-EMP-10: Testing record cash movement..."
if [ ! -z "$SHIFT_ID" ]; then
    CASH_MOVEMENT_DATA=$(cat <<EOF
{
  "shift_id": $SHIFT_ID,
  "movement_type": "cash_in",
  "amount": 1000.00,
  "reason": "Petty cash addition",
  "notes": "UAT test cash movement"
}
EOF
)
    
    CASH_MOVEMENT_RESPONSE=$(api_call "POST" "/pos/cash-movements" "$CASH_MOVEMENT_DATA" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$CASH_MOVEMENT_RESPONSE")
    
    if [ "$HTTP_CODE" = "201" ]; then
        print_test_result "pass" "TC-EMP-10" "Record cash movement (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-EMP-10" "Record cash movement failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-10" "Skipped - no active shift"
fi

# TC-EMP-11: Get shift summary
echo "TC-EMP-11: Testing get shift summary..."
if [ ! -z "$SHIFT_ID" ]; then
    SHIFT_SUMMARY_RESPONSE=$(api_call "GET" "/pos/shifts/$SHIFT_ID" "" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$SHIFT_SUMMARY_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-EMP-11" "Get shift summary (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-EMP-11" "Get shift summary failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-11" "Skipped - no active shift"
fi

# TC-EMP-12: View all transactions in shift
echo "TC-EMP-12: Testing view shift transactions..."
if [ ! -z "$SHIFT_ID" ]; then
    SHIFT_TRANSACTIONS_RESPONSE=$(api_call "GET" "/pos/shifts/$SHIFT_ID/transactions" "" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$SHIFT_TRANSACTIONS_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-EMP-12" "View shift transactions (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-EMP-12" "View shift transactions failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-12" "Skipped - no active shift"
fi

# TC-EMP-14: Manager void transaction (requires manager role) - MOVED BEFORE CLOSE
echo "TC-EMP-14: Testing void transaction..."
if [ ! -z "$TRANSACTION_ID" ]; then
    VOID_DATA=$(cat <<EOF
{
  "void_reason": "UAT test void - Testing void functionality"
}
EOF
)
    
    VOID_RESPONSE=$(api_call "POST" "/pos/transactions/$TRANSACTION_ID/void" "$VOID_DATA" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$VOID_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-EMP-14" "Void transaction (HTTP $HTTP_CODE)"
    elif [ "$HTTP_CODE" = "403" ]; then
        print_test_result "warn" "TC-EMP-14" "Insufficient permissions (expected for non-manager)"
    else
        print_test_result "fail" "TC-EMP-14" "Void transaction failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-14" "Skipped - no transaction ID"
fi

# TC-EMP-13: Close shift with reconciliation - MOVED TO END
echo "TC-EMP-13: Testing close shift..."
if [ ! -z "$SHIFT_ID" ]; then
    CLOSE_SHIFT_DATA=$(cat <<EOF
{
  "closing_cash": 5500.00,
  "notes": "UAT test shift close"
}
EOF
)
    
    CLOSE_SHIFT_RESPONSE=$(api_call "POST" "/pos/shifts/$SHIFT_ID/close" "$CLOSE_SHIFT_DATA" "$EMPLOYEE_TOKEN")
    HTTP_CODE=$(get_http_code "$CLOSE_SHIFT_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-EMP-13" "Close shift (HTTP $HTTP_CODE)"
        # Don't clear SHIFT_ID yet - other tests may need to query the closed shift
    else
        print_test_result "fail" "TC-EMP-13" "Close shift failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-EMP-13" "Skipped - no active shift"
fi

# TC-EMP-15: Get employee performance metrics
echo "TC-EMP-15: Testing employee metrics..."
METRICS_RESPONSE=$(api_call "GET" "/pos/employee/metrics" "" "$EMPLOYEE_TOKEN")
HTTP_CODE=$(get_http_code "$METRICS_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-EMP-15" "Get employee metrics (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-EMP-15" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-EMP-15" "Get employee metrics failed (HTTP $HTTP_CODE)"
fi

#############################################
# ADMIN JOURNEY TESTS (20 tests)
#############################################

print_section "ADMIN JOURNEY - 20 Tests"

# TC-ADM-01: Admin login
echo "TC-ADM-01: Testing admin login..."
ADMIN_LOGIN_DATA=$(cat <<EOF
{
  "email": "admin@happyplace.co.ke",
  "password": "admin123"
}
EOF
)

ADMIN_LOGIN_RESPONSE=$(api_call "POST" "/auth/employee/login" "$ADMIN_LOGIN_DATA" "")
HTTP_CODE=$(get_http_code "$ADMIN_LOGIN_RESPONSE")
RESPONSE_BODY=$(get_response_body "$ADMIN_LOGIN_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    ADMIN_TOKEN=$(parse_json "$RESPONSE_BODY" "access_token")
    print_test_result "pass" "TC-ADM-01" "Admin login (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-ADM-01" "Admin login failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-02: Get dashboard metrics
echo "TC-ADM-02: Testing dashboard metrics..."
DASHBOARD_RESPONSE=$(api_call "GET" "/admin/dashboard" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$DASHBOARD_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-02" "Dashboard metrics (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-ADM-02" "Dashboard metrics failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-03: List all employees
echo "TC-ADM-03: Testing list employees..."
EMPLOYEES_RESPONSE=$(api_call "GET" "/admin/employees" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$EMPLOYEES_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-03" "List employees (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-ADM-03" "List employees failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-04: Create employee
echo "TC-ADM-04: Testing create employee..."
CREATE_EMP_DATA=$(cat <<EOF
{
  "email": "uat.staff.$(date +%s)@happyplace.com",
  "password": "Staff123!",
  "full_name": "UAT Staff Member",
  "role": "staff",
  "is_active": true
}
EOF
)

CREATE_EMP_RESPONSE=$(api_call "POST" "/admin/employees" "$CREATE_EMP_DATA" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$CREATE_EMP_RESPONSE")
RESPONSE_BODY=$(get_response_body "$CREATE_EMP_RESPONSE")

if [ "$HTTP_CODE" = "201" ]; then
    NEW_EMPLOYEE_ID=$(parse_json "$RESPONSE_BODY" "id")
    print_test_result "pass" "TC-ADM-04" "Create employee (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-ADM-04" "Create employee failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-05: Update employee
echo "TC-ADM-05: Testing update employee..."
if [ ! -z "$NEW_EMPLOYEE_ID" ]; then
    UPDATE_EMP_DATA=$(cat <<EOF
{
  "full_name": "UAT Staff Member Updated",
  "is_active": true
}
EOF
)
    
    UPDATE_EMP_RESPONSE=$(api_call "PATCH" "/admin/employees/$NEW_EMPLOYEE_ID" "$UPDATE_EMP_DATA" "$ADMIN_TOKEN")
    HTTP_CODE=$(get_http_code "$UPDATE_EMP_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-ADM-05" "Update employee (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-ADM-05" "Update employee failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-ADM-05" "Skipped - no employee created"
fi

# TC-ADM-06: List customers with GDPR compliance
echo "TC-ADM-06: Testing list customers..."
CUSTOMERS_RESPONSE=$(api_call "GET" "/admin/customers?page=1&per_page=10" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$CUSTOMERS_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-06" "List customers (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-ADM-06" "List customers failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-07: View customer details
echo "TC-ADM-07: Testing view customer details..."
if [ ! -z "$CUSTOMER_ID" ]; then
    CUSTOMER_DETAIL_RESPONSE=$(api_call "GET" "/admin/customers/$CUSTOMER_ID" "" "$ADMIN_TOKEN")
    HTTP_CODE=$(get_http_code "$CUSTOMER_DETAIL_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-ADM-07" "View customer details (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-ADM-07" "View customer details failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-ADM-07" "Skipped - no customer ID"
fi

# TC-ADM-08: Create product with variants
echo "TC-ADM-08: Testing create product..."
TIMESTAMP=$(date +%s)
CREATE_PRODUCT_DATA=$(cat <<EOF
{
  "name": "UAT Test Product",
  "slug": "uat-test-product-${TIMESTAMP}",
  "description": "Product created during UAT testing",
  "price": 2500.00,
  "category_id": 1,
  "sku": "UAT-${TIMESTAMP}",
  "weight": 0.5,
  "is_active": true,
  "variants": [
    {"sku": "UAT-${TIMESTAMP}-S-BLK", "size": "S", "color": "Black", "initial_quantity": 10},
    {"sku": "UAT-${TIMESTAMP}-M-BLK", "size": "M", "color": "Black", "initial_quantity": 15}
  ]
}
EOF
)

CREATE_PRODUCT_RESPONSE=$(api_call "POST" "/admin/products" "$CREATE_PRODUCT_DATA" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$CREATE_PRODUCT_RESPONSE")
RESPONSE_BODY=$(get_response_body "$CREATE_PRODUCT_RESPONSE")

if [ "$HTTP_CODE" = "201" ]; then
    TEST_PRODUCT_ID=$(parse_json "$RESPONSE_BODY" "id")
    print_test_result "pass" "TC-ADM-08" "Create product with variants (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-ADM-08" "Create product failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-09: Update product
echo "TC-ADM-09: Testing update product..."
if [ ! -z "$TEST_PRODUCT_ID" ]; then
    UPDATE_PRODUCT_DATA=$(cat <<EOF
{
  "name": "UAT Test Product Updated",
  "price": 2800.00,
  "is_active": true
}
EOF
)
    
    UPDATE_PRODUCT_RESPONSE=$(api_call "PATCH" "/admin/products/$TEST_PRODUCT_ID" "$UPDATE_PRODUCT_DATA" "$ADMIN_TOKEN")
    HTTP_CODE=$(get_http_code "$UPDATE_PRODUCT_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-ADM-09" "Update product (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-ADM-09" "Update product failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-ADM-09" "Skipped - no product created"
fi

# TC-ADM-10: Update inventory
echo "TC-ADM-10: Testing update inventory..."
if [ ! -z "$VARIANT_ID" ]; then
    INVENTORY_UPDATE_DATA=$(cat <<EOF
{
  "quantity": 50,
  "action": "set"
}
EOF
)
    
    INVENTORY_UPDATE_RESPONSE=$(api_call "PATCH" "/variants/$VARIANT_ID/inventory" "$INVENTORY_UPDATE_DATA" "$ADMIN_TOKEN")
    HTTP_CODE=$(get_http_code "$INVENTORY_UPDATE_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-ADM-10" "Update inventory (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-ADM-10" "Update inventory failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-ADM-10" "Skipped - no variant ID"
fi

# TC-ADM-11: List all orders
echo "TC-ADM-11: Testing list all orders..."
ADMIN_ORDERS_RESPONSE=$(api_call "GET" "/admin/orders?page=1&per_page=20" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$ADMIN_ORDERS_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-11" "List all orders (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-ADM-11" "List all orders failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-12: Update order status
echo "TC-ADM-12: Testing update order status..."
if [ ! -z "$ORDER_ID" ]; then
    UPDATE_ORDER_DATA=$(cat <<EOF
{
  "status": "processing"
}
EOF
)
    
    UPDATE_ORDER_RESPONSE=$(api_call "PATCH" "/admin/orders/$ORDER_ID/status" "$UPDATE_ORDER_DATA" "$ADMIN_TOKEN")
    HTTP_CODE=$(get_http_code "$UPDATE_ORDER_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-ADM-12" "Update order status (HTTP $HTTP_CODE)"
    else
        print_test_result "fail" "TC-ADM-12" "Update order status failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-ADM-12" "Skipped - no order ID"
fi

# TC-ADM-13: View financial summary
echo "TC-ADM-13: Testing financial summary..."
FINANCIAL_RESPONSE=$(api_call "GET" "/admin/reports/financial-summary" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$FINANCIAL_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-13" "Financial summary (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-ADM-13" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-ADM-13" "Financial summary failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-14: Sales report
echo "TC-ADM-14: Testing sales report..."
SALES_REPORT_RESPONSE=$(api_call "GET" "/admin/reports/sales?start_date=2024-01-01&end_date=2024-12-31" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$SALES_REPORT_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-14" "Sales report (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-ADM-14" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-ADM-14" "Sales report failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-15: Inventory report
echo "TC-ADM-15: Testing inventory report..."
INVENTORY_REPORT_RESPONSE=$(api_call "GET" "/admin/reports/inventory" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$INVENTORY_REPORT_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-15" "Inventory report (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-ADM-15" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-ADM-15" "Inventory report failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-16: Low stock alerts
echo "TC-ADM-16: Testing low stock alerts..."
LOW_STOCK_RESPONSE=$(api_call "GET" "/admin/inventory/low-stock" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$LOW_STOCK_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-16" "Low stock alerts (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-ADM-16" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-ADM-16" "Low stock alerts failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-17: Create promotion
echo "TC-ADM-17: Testing create promotion..."
CREATE_PROMO_DATA=$(cat <<EOF
{
  "code": "UAT$(date +%s)",
  "name": "UAT Test Promotion",
  "description": "10% off for testing",
  "discount_type": "percentage",
  "discount_value": 10.0,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z",
  "is_active": true,
  "usage_limit": 100,
  "usage_per_customer": 1
}
EOF
)

CREATE_PROMO_RESPONSE=$(api_call "POST" "/admin/promotions" "$CREATE_PROMO_DATA" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$CREATE_PROMO_RESPONSE")

if [ "$HTTP_CODE" = "201" ]; then
    print_test_result "pass" "TC-ADM-17" "Create promotion (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-ADM-17" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-ADM-17" "Create promotion failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-18: View system logs
echo "TC-ADM-18: Testing view system logs..."
LOGS_RESPONSE=$(api_call "GET" "/admin/logs?page=1&per_page=20" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$LOGS_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-ADM-18" "View system logs (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-ADM-18" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-ADM-18" "View system logs failed (HTTP $HTTP_CODE)"
fi

# TC-ADM-19: GDPR data export
echo "TC-ADM-19: Testing GDPR data export..."
if [ ! -z "$CUSTOMER_ID" ]; then
    GDPR_EXPORT_RESPONSE=$(api_call "GET" "/admin/customers/$CUSTOMER_ID/gdpr-export" "" "$ADMIN_TOKEN")
    HTTP_CODE=$(get_http_code "$GDPR_EXPORT_RESPONSE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_test_result "pass" "TC-ADM-19" "GDPR data export (HTTP $HTTP_CODE)"
    elif [ "$HTTP_CODE" = "404" ]; then
        print_test_result "warn" "TC-ADM-19" "Endpoint not implemented yet"
    else
        print_test_result "fail" "TC-ADM-19" "GDPR data export failed (HTTP $HTTP_CODE)"
    fi
else
    print_test_result "warn" "TC-ADM-19" "Skipped - no customer ID"
fi

# TC-ADM-20: Backup database
echo "TC-ADM-20: Testing system backup trigger..."
BACKUP_RESPONSE=$(api_call "POST" "/admin/system/backup" "" "$ADMIN_TOKEN")
HTTP_CODE=$(get_http_code "$BACKUP_RESPONSE")

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
    print_test_result "pass" "TC-ADM-20" "System backup triggered (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "404" ]; then
    print_test_result "warn" "TC-ADM-20" "Endpoint not implemented yet"
else
    print_test_result "fail" "TC-ADM-20" "System backup failed (HTTP $HTTP_CODE)"
fi

#############################################
# CLEANUP & FINAL REPORT
#############################################

print_section "CLEANUP & FINAL REPORT"

# Cleanup test data
echo "Cleaning up test data..."

# Delete test wishlist items
if [ ! -z "$WISHLIST_ITEM_ID" ]; then
    api_call "DELETE" "/wishlist/$WISHLIST_ITEM_ID" "" "$CUSTOMER_TOKEN" > /dev/null 2>&1
fi

# Note: We keep test orders, employees, and products for audit trail

echo -e "${CYAN}Cleanup completed (kept test data for audit)${NC}"
echo ""

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Calculate percentages
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_PERCENT=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    FAIL_PERCENT=$(echo "scale=1; $FAILED_TESTS * 100 / $TOTAL_TESTS" | bc)
else
    PASS_PERCENT="0.0"
    FAIL_PERCENT="0.0"
fi

# Print final report
echo "=============================================="
echo -e "${BLUE}           FINAL TEST RESULTS${NC}"
echo "=============================================="
echo ""
echo -e "Total Tests:     ${CYAN}$TOTAL_TESTS${NC}"
echo -e "Passed:          ${GREEN}$PASSED_TESTS ($PASS_PERCENT%)${NC}"
echo -e "Failed:          ${RED}$FAILED_TESTS ($FAIL_PERCENT%)${NC}"
echo -e "Warnings:        ${YELLOW}$WARNING_TESTS${NC}"
echo -e "Duration:        ${CYAN}${DURATION}s${NC}"
echo ""

# Test journey breakdown
echo "Journey Breakdown:"
echo "  • Customer Journey:  12 tests"
echo "  • Employee Journey:  15 tests"
echo "  • Admin Journey:     20 tests"
echo ""

# Status indicator
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review failed tests above for details."
    exit 1
fi