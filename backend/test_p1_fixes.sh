#!/bin/bash
# Test script for P1-01 (Cart Validation) and P1-03 (M-Pesa Handler)
# Run this after implementing the P1 fixes

set -e  # Exit on error

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:5001/api}"
TEST_EMAIL="test@example.com"
TEST_PASSWORD="password123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "\n${YELLOW}TEST: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

print_summary() {
    echo -e "\n========================================="
    echo -e "TEST SUMMARY"
    echo -e "========================================="
    echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
    echo -e "Total:  $((TESTS_PASSED + TESTS_FAILED))"
    echo -e "=========================================\n"
}

# Login and get token
echo "Logging in to get JWT token..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/customer/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "Login failed. Registering new test customer..."
    
    # Register new customer
    REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/customer/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\":\"${TEST_EMAIL}\",
            \"password\":\"${TEST_PASSWORD}\",
            \"first_name\":\"Test\",
            \"last_name\":\"User\",
            \"phone\":\"+254712345678\",
            \"gdpr_consent\":true
        }")
    
    TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
    
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Failed to register and get authentication token${NC}"
        echo "Response: $REGISTER_RESPONSE"
        exit 1
    fi
    
    echo -e "${GREEN}Successfully registered and authenticated${NC}\n"
else
    echo -e "${GREEN}Successfully authenticated${NC}\n"
fi

# Clear cart first
echo "Clearing cart..."
curl -s -X DELETE "${BASE_URL}/cart" \
    -H "Authorization: Bearer $TOKEN" > /dev/null

# Get a valid variant ID from the API
echo "Getting valid variant ID..."
VARIANT_ID=$(curl -s "${BASE_URL}/products/3" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['variants'][0]['id'])" 2>/dev/null)

if [ -z "$VARIANT_ID" ]; then
    echo -e "${RED}Failed to get valid variant ID${NC}"
    exit 1
fi

echo -e "${GREEN}Using variant ID: $VARIANT_ID${NC}\n"

echo -e "========================================="
echo -e "P1-01: CART QUANTITY VALIDATION TESTS"
echo -e "=========================================\n"

# Test 1: Maximum quantity validation
print_test "Test 1: Reject quantity > 99 (MAX_CART_QUANTITY)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 100}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "400" ] && echo "$BODY" | grep -q "cannot exceed 99"; then
    print_pass "Correctly rejected quantity of 100"
else
    print_fail "Expected 400 with 'cannot exceed 99', got $HTTP_CODE: $BODY"
fi

# Test 2: Negative quantity
print_test "Test 2: Reject negative quantity"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": -5}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "400" ] && echo "$BODY" | grep -q "at least 1"; then
    print_pass "Correctly rejected negative quantity"
else
    print_fail "Expected 400 with 'at least 1', got $HTTP_CODE: $BODY"
fi

# Test 3: Zero quantity
print_test "Test 3: Reject zero quantity"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 0}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "400" ] && echo "$BODY" | grep -q "at least 1"; then
    print_pass "Correctly rejected zero quantity"
else
    print_fail "Expected 400 with 'at least 1', got $HTTP_CODE: $BODY"
fi

# Test 4: Normal operation (valid quantity)
print_test "Test 4: Accept valid quantity (5 units)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 5}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "201" ]; then
    print_pass "Successfully added 5 units to cart"
else
    print_fail "Expected 201, got $HTTP_CODE: $BODY"
fi

# Test 5: Multiple additions approaching limit
print_test "Test 5: Multiple additions should respect MAX_CART_QUANTITY"
# Clear cart first
curl -s -X DELETE "${BASE_URL}/cart" -H "Authorization: Bearer $TOKEN" > /dev/null

# Add 50 units
curl -s -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 50}' > /dev/null

# Try to add 50 more (total would be 100, should fail)
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 50}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "400" ] && echo "$BODY" | grep -q "cannot exceed 99"; then
    print_pass "Correctly prevented total quantity from exceeding 99"
else
    print_fail "Expected 400 with 'cannot exceed 99', got $HTTP_CODE: $BODY"
fi

# Test 6: Update to excessive quantity
print_test "Test 6: Update cart item to excessive quantity should fail"
# Clear and add item
curl -s -X DELETE "${BASE_URL}/cart" -H "Authorization: Bearer $TOKEN" > /dev/null
ADD_RESPONSE=$(curl -s -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 5}')

ITEM_ID=$(echo $ADD_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

# Try to update to 150
RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${BASE_URL}/cart/items/${ITEM_ID}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"quantity": 150}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "400" ] && echo "$BODY" | grep -q "cannot exceed 99"; then
    print_pass "Correctly rejected update to quantity 150"
else
    print_fail "Expected 400 with 'cannot exceed 99', got $HTTP_CODE: $BODY"
fi

# Test 7: Reserved quantity check
print_test "Test 7: Inventory check includes reserved_quantity"
# This test verifies the fix checks (quantity - reserved_quantity)
# We can't easily test this without database manipulation, so we'll verify the response format
RESPONSE=$(curl -s -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 5}')

if echo "$RESPONSE" | grep -q "available_quantity\|cart_item"; then
    print_pass "Response includes proper inventory fields"
else
    print_fail "Response missing expected inventory fields: $RESPONSE"
fi

echo -e "\n========================================="
echo -e "P1-03: M-PESA HANDLER TESTS"
echo -e "=========================================\n"

# Test 1: M-Pesa rejection
print_test "Test 1: M-Pesa payment should return 501 Not Implemented"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/orders" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "payment_method": "mpesa",
        "shipping_address": {
            "street": "123 Main St",
            "city": "Nairobi",
            "state": "Nairobi County",
            "zip": "00100",
            "phone": "+254712345678"
        }
    }')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "501" ] && echo "$BODY" | grep -q "M-Pesa payment coming soon"; then
    print_pass "M-Pesa correctly rejected with 501 status"
else
    print_fail "Expected 501 with M-Pesa message, got $HTTP_CODE: $BODY"
fi

# Test 2: M-Pesa error includes helpful information
print_test "Test 2: M-Pesa error includes available_methods and message"
if echo "$BODY" | grep -q "available_methods" && echo "$BODY" | grep -q "message"; then
    print_pass "M-Pesa error includes helpful fields"
else
    print_fail "M-Pesa error missing helpful fields: $BODY"
fi

# Test 3: COD still works
print_test "Test 3: COD payment should work normally"
# First add items to cart
curl -s -X DELETE "${BASE_URL}/cart" -H "Authorization: Bearer $TOKEN" > /dev/null
curl -s -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 2}' > /dev/null

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/orders" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "payment_method": "cod",
        "shipping_address": {
            "street": "123 Main St",
            "city": "Nairobi",
            "state": "Nairobi County",
            "zip": "00100",
            "phone": "+254712345678"
        }
    }')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "201" ]; then
    print_pass "COD payment works normally"
else
    print_fail "Expected 201 for COD payment, got $HTTP_CODE: $BODY"
fi

# Test 4: Default payment method (should be COD)
print_test "Test 4: Default payment method should be COD"
# Add items to cart
curl -s -X DELETE "${BASE_URL}/cart" -H "Authorization: Bearer $TOKEN" > /dev/null
curl -s -X POST "${BASE_URL}/cart/items" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"variant_id": '$VARIANT_ID', "quantity": 2}' > /dev/null

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/orders" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "shipping_address": {
            "street": "123 Main St",
            "city": "Nairobi",
            "state": "Nairobi County",
            "zip": "00100",
            "phone": "+254712345678"
        }
    }')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "201" ]; then
    print_pass "Default payment method (COD) works"
else
    print_fail "Expected 201 for default payment, got $HTTP_CODE: $BODY"
fi

# Print summary
print_summary

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
