#!/bin/bash

echo "======================================"
echo "Happy Place - Order API Testing Script"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://127.0.0.1:5001/api"

# Function to print test header
print_test() {
    echo ""
    echo -e "${YELLOW}=== $1 ===${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Login as existing customer
print_test "Step 1: Customer Login"
LOGIN_RESPONSE=$(curl -X POST "$BASE_URL/auth/customer/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  -s)

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    print_error "Login failed. Creating new test customer..."

    # Register new customer
    curl -X POST "$BASE_URL/auth/customer/register" \
      -H "Content-Type: application/json" \
      -d '{
        "email":"test_orders@example.com",
        "password":"password123",
        "first_name":"Order",
        "last_name":"Tester",
        "phone":"+254712345678",
        "gdpr_consent":true
      }' \
      -s | python3 -m json.tool

    # Login with new account
    LOGIN_RESPONSE=$(curl -X POST "$BASE_URL/auth/customer/login" \
      -H "Content-Type: application/json" \
      -d '{"email":"test_orders@example.com","password":"password123"}' \
      -s)

    TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
fi

if [ -z "$TOKEN" ]; then
    print_error "Failed to get authentication token"
    exit 1
fi

print_success "Logged in successfully"
echo "Token: ${TOKEN:0:50}..."

# Step 2: Clear cart
print_test "Step 2: Clear Cart"
curl -X DELETE "$BASE_URL/cart" \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

print_success "Cart cleared"

# Step 3: Add items to cart
print_test "Step 3: Add Items to Cart"

# Add first item (variant_id: 21)
curl -X POST "$BASE_URL/cart/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variant_id":21,"quantity":2}' \
  -s | python3 -m json.tool

print_success "Added item 1 to cart"

# Add second item (variant_id: 41)
curl -X POST "$BASE_URL/cart/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variant_id":41,"quantity":1}' \
  -s | python3 -m json.tool

print_success "Added item 2 to cart"

# Step 4: View cart
print_test "Step 4: View Cart"
CART_RESPONSE=$(curl -X GET "$BASE_URL/cart" \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "$CART_RESPONSE" | python3 -m json.tool

CART_ITEMS=$(echo $CART_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))")
print_success "Cart has $CART_ITEMS items"

# Step 5: Preview shipping (Nairobi)
print_test "Step 5: Preview Shipping Cost (Nairobi)"
curl -X POST "$BASE_URL/orders/shipping-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city":"Nairobi"}' \
  -s | python3 -m json.tool

print_success "Shipping preview for Nairobi (should be free)"

# Step 6: Preview shipping (Upcountry)
print_test "Step 6: Preview Shipping Cost (Mombasa)"
curl -X POST "$BASE_URL/orders/shipping-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city":"Mombasa"}' \
  -s | python3 -m json.tool

print_success "Shipping preview for Mombasa (Upcountry rates)"

# Step 7: Create Order (Nairobi - Free Shipping)
print_test "Step 7: Create Order (Nairobi Address)"
ORDER_RESPONSE=$(curl -X POST "$BASE_URL/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "street": "123 Kimathi Street, Apt 4B",
      "city": "Nairobi",
      "state": "Nairobi County",
      "zip": "00100",
      "phone": "+254712345678"
    }
  }' \
  -s)

echo "$ORDER_RESPONSE" | python3 -m json.tool

ORDER_ID=$(echo $ORDER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('order', {}).get('id', ''))" 2>/dev/null)
ORDER_NUMBER=$(echo $ORDER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('order', {}).get('order_number', ''))" 2>/dev/null)

if [ -z "$ORDER_ID" ]; then
    print_error "Order creation failed"
else
    print_success "Order created successfully - ID: $ORDER_ID, Number: $ORDER_NUMBER"
fi

# Step 8: Get Order by ID
if [ ! -z "$ORDER_ID" ]; then
    print_test "Step 8: Get Order Details by ID"
    curl -X GET "$BASE_URL/orders/$ORDER_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -s | python3 -m json.tool

    print_success "Retrieved order $ORDER_ID"
fi

# Step 9: Get Order by Number
if [ ! -z "$ORDER_NUMBER" ]; then
    print_test "Step 9: Get Order by Order Number"
    curl -X GET "$BASE_URL/orders/number/$ORDER_NUMBER" \
      -H "Authorization: Bearer $TOKEN" \
      -s | python3 -m json.tool

    print_success "Retrieved order $ORDER_NUMBER"
fi

# Step 10: Get Customer Order History
print_test "Step 10: Get Customer Order History"
curl -X GET "$BASE_URL/orders?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

print_success "Retrieved order history"

# Step 11: Verify cart is empty after order
print_test "Step 11: Verify Cart Empty After Order"
FINAL_CART=$(curl -X GET "$BASE_URL/cart" \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "$FINAL_CART" | python3 -m json.tool

FINAL_CART_COUNT=$(echo $FINAL_CART | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))")

if [ "$FINAL_CART_COUNT" = "0" ]; then
    print_success "Cart successfully cleared after order creation"
else
    print_error "Cart still has items: $FINAL_CART_COUNT"
fi

echo ""
echo "======================================"
echo "Testing Complete!"
echo "======================================"
