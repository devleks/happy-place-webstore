#!/bin/bash

echo "=========================================="
echo "POS ENDPOINT TESTING"
echo "=========================================="

# Step 1: Login
echo ""
echo "Step 1: Employee Login"
echo "----------------------------------------"
LOGIN_RESPONSE=$(curl -X POST http://127.0.0.1:5001/api/auth/employee/login \
  -H "Content-Type: application/json" \
  -d '{"email":"manager@happyplace.co.ke","password":"manager123"}' \
  -s)

echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "ERROR: Failed to get token"
  exit 1
fi

echo ""
echo "Token obtained: ${TOKEN:0:50}..."

# Step 2: Get current shift
echo ""
echo "Step 2: Get Current Shift"
echo "----------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/shifts/current \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

# Step 3: Start shift
echo ""
echo "Step 3: Start New Shift"
echo "----------------------------------------"
curl -X POST http://127.0.0.1:5001/api/pos/shifts/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"store_location_id":1,"opening_float":5000.00}' \
  -s | python3 -m json.tool

# Step 4: Get current shift again
echo ""
echo "Step 4: Get Current Shift (after starting)"
echo "----------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/shifts/current \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

echo ""
echo "=========================================="
echo "Testing Complete"
echo "=========================================="
