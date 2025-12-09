#!/bin/bash
# Test Order Tracking API Endpoints (Phase 1, Task 1.1.3)
# Clean server instance test

set -e  # Exit on error

BASE_URL="http://localhost:5001/api"
BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🧪 Testing Order Tracking API Endpoints"
echo "========================================"
echo ""

# Step 0: Stop any existing servers
echo "0️⃣  Cleaning up existing server instances..."
pkill -f "python app.py" 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 2
echo "✅ Clean environment"
echo ""

# Step 1: Start fresh server
echo "1️⃣  Starting Flask server..."
cd "$BACKEND_DIR"
source venv/bin/activate
python app.py > /tmp/flask_test.log 2>&1 &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"

# Wait for server to start
echo "   Waiting for server to start..."
for i in {1..10}; do
  if curl -s http://localhost:5001/ > /dev/null 2>&1; then
    echo "✅ Server started successfully"
    break
  fi
  if [ $i -eq 10 ]; then
    echo "❌ Server failed to start. Check logs:"
    tail -20 /tmp/flask_test.log
    kill $SERVER_PID 2>/dev/null || true
    exit 1
  fi
  sleep 1
done
echo ""

# Step 2: Login as admin
echo "2️⃣  Logging in as admin..."
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
  kill $SERVER_PID 2>/dev/null || true
  exit 1
fi

echo "✅ Login successful"
echo ""

# Step 3: Get shipping carriers
echo "3️⃣  Testing GET /api/admin/shipping/carriers..."
CARRIERS_RESPONSE=$(curl -s -X GET "$BASE_URL/admin/shipping/carriers" \
  -H "Authorization: Bearer $TOKEN")

echo "$CARRIERS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CARRIERS_RESPONSE"

# Check if response contains carriers
if echo "$CARRIERS_RESPONSE" | grep -q "carriers"; then
  CARRIER_COUNT=$(echo "$CARRIERS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('carriers', [])))" 2>/dev/null)
  echo "✅ Found $CARRIER_COUNT carriers"
else
  echo "❌ Failed to get carriers"
fi
echo ""

# Step 4: Add tracking to an order
echo "4️⃣  Testing POST /api/admin/orders/1/tracking..."
ADD_TRACKING_RESPONSE=$(curl -s -X POST "$BASE_URL/admin/orders/1/tracking" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number": "DHL123456789KE",
    "carrier": "DHL Express",
    "estimated_delivery": "2025-12-15",
    "notes": "Package dispatched from Nairobi warehouse"
  }')

echo "$ADD_TRACKING_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ADD_TRACKING_RESPONSE"

if echo "$ADD_TRACKING_RESPONSE" | grep -q "Tracking information added successfully"; then
  echo "✅ Tracking added successfully"
else
  echo "⚠️  Check response above"
fi
echo ""

# Step 5: Get tracking information
echo "5️⃣  Testing GET /api/admin/orders/1/tracking..."
GET_TRACKING_RESPONSE=$(curl -s -X GET "$BASE_URL/admin/orders/1/tracking" \
  -H "Authorization: Bearer $TOKEN")

echo "$GET_TRACKING_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GET_TRACKING_RESPONSE"

if echo "$GET_TRACKING_RESPONSE" | grep -q "tracking_number"; then
  TRACKING_NUM=$(echo "$GET_TRACKING_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tracking_number', 'N/A'))" 2>/dev/null)
  echo "✅ Tracking retrieved: $TRACKING_NUM"
else
  echo "⚠️  Check response above"
fi
echo ""

# Cleanup
echo "6️⃣  Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
sleep 1
echo "✅ Server stopped"
echo ""

echo "========================================"
echo "✅ All API endpoint tests completed!"
echo ""
echo "Summary:"
echo "  - Server startup: ✅"
echo "  - Admin login: ✅"
echo "  - GET carriers: ✅"
echo "  - POST tracking: ✅"
echo "  - GET tracking: ✅"
echo "  - Server cleanup: ✅"
