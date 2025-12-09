#!/bin/bash

# Test Order Creation Flow

echo "=== Testing Order Creation Flow ==="
echo ""

# Step 1: Register or Login
echo "Step 1: Login as customer..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5001/api/auth/customer/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123!"
  }')

echo "Login response: $LOGIN_RESPONSE"
echo ""

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed or no token received"
  exit 1
fi

echo "✅ Token received: ${TOKEN:0:50}..."
echo ""

# Step 2: Check cart
echo "Step 2: Checking cart..."
CART_RESPONSE=$(curl -s -X GET http://localhost:5001/api/cart \
  -H "Authorization: Bearer $TOKEN")

echo "Cart response: $CART_RESPONSE"
echo ""

# Step 3: Create order
echo "Step 3: Creating order..."
ORDER_RESPONSE=$(curl -s -X POST http://localhost:5001/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "shipping_address": {
      "street": "123 Test Street, Apt 4B",
      "city": "Nairobi",
      "state": "Nairobi County",
      "zip": "00100",
      "phone": "0712345678"
    }
  }')

echo "Order response: $ORDER_RESPONSE"
echo ""

# Check if order was created
if echo "$ORDER_RESPONSE" | grep -q "order_id\|Order created"; then
  echo "✅ Order created successfully!"
else
  echo "❌ Order creation failed"
  echo "Response: $ORDER_RESPONSE"
fi
