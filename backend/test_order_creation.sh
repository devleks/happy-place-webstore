#!/bin/bash

echo "=== Order Creation Test ==="

# Login
TOKEN=$(curl -X POST "http://127.0.0.1:5001/api/auth/customer/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test_orders@example.com","password":"password123"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo "✓ Logged in"

# Clear cart
curl -X DELETE "http://127.0.0.1:5001/api/cart" \
  -H "Authorization: Bearer $TOKEN" \
  -s > /dev/null

echo "✓ Cart cleared"

# Add items to cart
curl -X POST "http://127.0.0.1:5001/api/cart/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variant_id":21,"quantity":1}' \
  -s > /dev/null

curl -X POST "http://127.0.0.1:5001/api/cart/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variant_id":41,"quantity":1}' \
  -s > /dev/null

echo "✓ Items added to cart"

# View cart
echo ""
echo "Cart contents:"
curl -X GET "http://127.0.0.1:5001/api/cart" \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

echo ""
echo "=== Creating Order with Nairobi Address ==="
ORDER_RESPONSE=$(curl -X POST "http://127.0.0.1:5001/api/orders" \
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

# Extract order ID
ORDER_ID=$(echo "$ORDER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('order', {}).get('id', ''))" 2>/dev/null)

if [ -n "$ORDER_ID" ]; then
    echo ""
    echo "✓ Order created successfully! Order ID: $ORDER_ID"

    echo ""
    echo "=== Getting Order Details ==="
    curl -X GET "http://127.0.0.1:5001/api/orders/$ORDER_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -s | python3 -m json.tool

    echo ""
    echo "=== Checking Cart After Order ==="
    curl -X GET "http://127.0.0.1:5001/api/cart" \
      -H "Authorization: Bearer $TOKEN" \
      -s | python3 -m json.tool
else
    echo ""
    echo "✗ Order creation failed"
fi
