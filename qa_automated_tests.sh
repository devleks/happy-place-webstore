#!/bin/bash

# Happy Place Boutique - Automated QA Test Script
# Tests critical backend API endpoints

echo "======================================"
echo "Happy Place Boutique - QA Testing"
echo "======================================"
echo ""

BASE_URL="http://127.0.0.1:5001/api"
TOKEN=""
ORDER_ID=""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper function to print test results
print_test_result() {
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo "===================================="
echo "TEST CATEGORY 1: Authentication Flow"
echo "===================================="
echo ""

# TC-AUTH-01: User Registration
echo "TC-AUTH-01: Testing user registration..."
TEST_EMAIL="qa.test.$(date +%s)@happyplace.com"
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/customer/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"first_name\": \"QA\",
    \"last_name\": \"Tester\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"TestPass123\",
    \"phone\": \"254712345678\",
    \"gdpr_consent\": true
  }")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$REGISTER_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "201" ] || [ "$HTTP_CODE" == "409" ]; then
    print_test_result 0 "User registration (HTTP $HTTP_CODE)"
else
    print_test_result 1 "User registration (Expected 201/409, got $HTTP_CODE)"
fi
echo ""

# TC-AUTH-02: User Login
echo "TC-AUTH-02: Testing user login..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/customer/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"TestPass123\"
  }")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    print_test_result 0 "User login (HTTP $HTTP_CODE)"
else
    print_test_result 1 "User login (Expected 200, got $HTTP_CODE)"
fi
echo "Token: ${TOKEN:0:20}..."
echo ""

echo "===================================="
echo "TEST CATEGORY 2: Product Endpoints"
echo "===================================="
echo ""

# TC-PROD-01: Get all products
echo "TC-PROD-01: Testing get all products..."
PRODUCTS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/products?page=1&per_page=12")
HTTP_CODE=$(echo "$PRODUCTS_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "200" ]; then
    print_test_result 0 "Get all products (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Get all products (Expected 200, got $HTTP_CODE)"
fi
echo ""

# TC-PROD-02: Get single product
echo "TC-PROD-02: Testing get single product..."
PRODUCT_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/products/elegant-silk-blouse")
HTTP_CODE=$(echo "$PRODUCT_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "200" ]; then
    print_test_result 0 "Get single product (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Get single product (Expected 200, got $HTTP_CODE)"
fi
echo ""

echo "===================================="
echo "TEST CATEGORY 3: Shopping Cart"
echo "===================================="
echo ""

# TC-CART-01: Get empty cart
echo "TC-CART-01: Testing get cart..."
CART_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/cart" \
  -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$CART_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "200" ]; then
    print_test_result 0 "Get cart (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Get cart (Expected 200, got $HTTP_CODE)"
fi
echo ""

# TC-CART-02: Add item to cart
echo "TC-CART-02: Testing add item to cart..."
ADD_CART_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/cart/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "variant_id": 21,
    "quantity": 2
  }')
HTTP_CODE=$(echo "$ADD_CART_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "201" ]; then
    print_test_result 0 "Add item to cart (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Add item to cart (Expected 201, got $HTTP_CODE)"
fi
echo ""

# TC-CART-03: Get cart with items
echo "TC-CART-03: Testing get cart with items..."
CART_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/cart" \
  -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$CART_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "200" ]; then
    print_test_result 0 "Get cart with items (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Get cart with items (Expected 200, got $HTTP_CODE)"
fi
echo ""

echo "===================================="
echo "TEST CATEGORY 4: Shipping Calculation"
echo "===================================="
echo ""

# TC-SHIP-01: Nairobi free shipping
echo "TC-SHIP-01: Testing Nairobi free shipping..."
SHIP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/orders/shipping-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city": "Nairobi"}')
HTTP_CODE=$(echo "$SHIP_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$SHIP_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    IS_NAIROBI=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['is_nairobi'])" 2>/dev/null)
    SHIPPING_COST=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['shipping_cost'])" 2>/dev/null)

    if [ "$IS_NAIROBI" == "True" ] && [ "$SHIPPING_COST" == "0" ]; then
        print_test_result 0 "Nairobi free shipping (Cost: $SHIPPING_COST)"
    else
        print_test_result 1 "Nairobi free shipping (Expected cost 0, got $SHIPPING_COST)"
    fi
else
    print_test_result 1 "Nairobi free shipping (Expected 200, got $HTTP_CODE)"
fi
echo ""

# TC-SHIP-02: Upcountry shipping
echo "TC-SHIP-02: Testing upcountry shipping..."
SHIP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/orders/shipping-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city": "Mombasa"}')
HTTP_CODE=$(echo "$SHIP_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$SHIP_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    IS_NAIROBI=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['is_nairobi'])" 2>/dev/null)
    SHIPPING_COST=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['shipping_cost'])" 2>/dev/null)

    if [ "$IS_NAIROBI" == "False" ] && [ "$SHIPPING_COST" != "0" ]; then
        print_test_result 0 "Upcountry shipping (Cost: KSh $SHIPPING_COST)"
    else
        print_test_result 1 "Upcountry shipping (Expected cost > 0, got $SHIPPING_COST)"
    fi
else
    print_test_result 1 "Upcountry shipping (Expected 200, got $HTTP_CODE)"
fi
echo ""

echo "===================================="
echo "TEST CATEGORY 5: Order Creation"
echo "===================================="
echo ""

# TC-ORD-01: Create order
echo "TC-ORD-01: Testing order creation..."
ORDER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "street": "123 Test Street",
      "city": "Nairobi",
      "state": "Nairobi County",
      "zip": "00100",
      "phone": "+254712345678"
    },
    "billing_address": {
      "street": "123 Test Street",
      "city": "Nairobi",
      "state": "Nairobi County",
      "zip": "00100",
      "phone": "+254712345678"
    }
  }')
HTTP_CODE=$(echo "$ORDER_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$ORDER_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "201" ]; then
    ORDER_ID=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['order']['id'])" 2>/dev/null)
    ORDER_NUMBER=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['order']['order_number'])" 2>/dev/null)
    print_test_result 0 "Order creation (HTTP $HTTP_CODE, Order #$ORDER_NUMBER)"
else
    print_test_result 1 "Order creation (Expected 201, got $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
fi
echo ""

# TC-ORD-02: Get order details
if [ ! -z "$ORDER_ID" ]; then
    echo "TC-ORD-02: Testing get order details..."
    ORDER_DETAIL_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/orders/$ORDER_ID" \
      -H "Authorization: Bearer $TOKEN")
    HTTP_CODE=$(echo "$ORDER_DETAIL_RESPONSE" | tail -n 1)

    if [ "$HTTP_CODE" == "200" ]; then
        print_test_result 0 "Get order details (HTTP $HTTP_CODE)"
    else
        print_test_result 1 "Get order details (Expected 200, got $HTTP_CODE)"
    fi
    echo ""
fi

# TC-ORD-03: Get order history
echo "TC-ORD-03: Testing get order history..."
ORDER_HISTORY_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/orders?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$ORDER_HISTORY_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "200" ]; then
    print_test_result 0 "Get order history (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Get order history (Expected 200, got $HTTP_CODE)"
fi
echo ""

# TC-CART-04: Verify cart cleared
echo "TC-CART-04: Testing cart cleared after order..."
CART_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/cart" \
  -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$CART_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$CART_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    ITEM_COUNT=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['items']))" 2>/dev/null || echo "0")
    if [ "$ITEM_COUNT" == "0" ]; then
        print_test_result 0 "Cart cleared after order (Items: $ITEM_COUNT)"
    else
        print_test_result 1 "Cart not cleared after order (Items: $ITEM_COUNT)"
    fi
else
    print_test_result 1 "Get cart after order (Expected 200, got $HTTP_CODE)"
fi
echo ""

echo "===================================="
echo "TEST CATEGORY 6: Error Handling"
echo "===================================="
echo ""

# TC-ERR-01: Unauthorized access
echo "TC-ERR-01: Testing unauthorized cart access..."
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/cart")
HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "401" ] || [ "$HTTP_CODE" == "422" ]; then
    print_test_result 0 "Unauthorized access blocked (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Unauthorized access (Expected 401/422, got $HTTP_CODE)"
fi
echo ""

# TC-ERR-02: Invalid product
echo "TC-ERR-02: Testing get non-existent product..."
INVALID_PROD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/products/non-existent-product-99999")
HTTP_CODE=$(echo "$INVALID_PROD_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" == "404" ]; then
    print_test_result 0 "Non-existent product error (HTTP $HTTP_CODE)"
else
    print_test_result 1 "Non-existent product (Expected 404, got $HTTP_CODE)"
fi
echo ""

echo "===================================="
echo "TEST SUMMARY"
echo "===================================="
echo ""
echo -e "Total Tests: $TESTS_TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  SOME TESTS FAILED${NC}"
    exit 1
fi
