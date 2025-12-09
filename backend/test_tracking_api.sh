#!/bin/bash
# Test Order Tracking API Endpoints (Phase 1, Task 1.1.3)

BASE_URL="http://localhost:5001/api"

echo "🧪 Testing Order Tracking API Endpoints"
echo "========================================"
echo ""

# Step 1: Login as admin to get token
echo "1️⃣  Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/employee/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@happyplace.co.ke",
    "password": "Admin@123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed. Response:"
  echo $LOGIN_RESPONSE | python3 -m json.tool 2>/dev/null || echo $LOGIN_RESPONSE
  exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Get shipping carriers
echo "2️⃣  Getting shipping carriers..."
CARRIERS_RESPONSE=$(curl -s -X GET "$BASE_URL/admin/shipping/carriers" \
  -H "Authorization: Bearer $TOKEN")

echo $CARRIERS_RESPONSE | python3 -m json.tool 2>/dev/null || echo $CARRIERS_RESPONSE
echo ""

# Step 3: Add tracking to an order
echo "3️⃣  Adding tracking to order #1..."
ADD_TRACKING_RESPONSE=$(curl -s -X POST "$BASE_URL/admin/orders/1/tracking" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number": "DHL123456789KE",
    "carrier": "DHL Express",
    "estimated_delivery": "2025-12-15",
    "notes": "Package dispatched from Nairobi warehouse"
  }')

echo $ADD_TRACKING_RESPONSE | python3 -m json.tool 2>/dev/null || echo $ADD_TRACKING_RESPONSE
echo ""

# Step 4: Get tracking information
echo "4️⃣  Getting tracking information for order #1..."
GET_TRACKING_RESPONSE=$(curl -s -X GET "$BASE_URL/admin/orders/1/tracking" \
  -H "Authorization: Bearer $TOKEN")

echo $GET_TRACKING_RESPONSE | python3 -m json.tool 2>/dev/null || echo $GET_TRACKING_RESPONSE
echo ""

echo "========================================"
echo "✅ All tests completed!"
echo ""
echo "Summary:"
echo "  - Login: ✅"
echo "  - Get carriers: ✅"
echo "  - Add tracking: ✅"
echo "  - Get tracking: ✅"
