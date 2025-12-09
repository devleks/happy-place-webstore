#!/bin/bash

echo "=========================================="
echo "KIOSK FEATURES TEST"
echo "=========================================="
echo ""

# Step 1: Login
echo "Step 1: Employee Login"
echo "------------------------------------------"
LOGIN_RESPONSE=$(curl -X POST http://127.0.0.1:5001/api/auth/employee/login \
  -H "Content-Type: application/json" \
  -d '{"email":"manager@happyplace.co.ke","password":"manager123"}' \
  -s)

echo "$LOGIN_RESPONSE" | python3 -m json.tool

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ ERROR: Failed to get token"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Health check
echo "Step 2: Kiosk Health Check"
echo "------------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/kiosk/health -s | python3 -m json.tool
echo ""

# Step 3: Get quick access products
echo "Step 3: Get Quick Access Products"
echo "------------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/quick-access \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data, indent=2)); print(f'\n✅ Found {data.get(\"count\", 0)} quick access products')"
echo ""

# Step 4: Quick product lookup by SKU
echo "Step 4: Quick Product Lookup by SKU"
echo "------------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/product/quick/COTTEE-M-WHI \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool
echo ""

# Step 5: Scan barcode
echo "Step 5: Scan Barcode"
echo "------------------------------------------"
curl -X POST http://127.0.0.1:5001/api/pos/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"barcode":"HP0000000021"}' \
  -s | python3 -m json.tool
echo ""

# Step 6: Get held transactions (should be empty initially)
echo "Step 6: Get Held Transactions"
echo "------------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/transactions/held \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool
echo ""

# Step 7: Hold a transaction
echo "Step 7: Hold a Transaction"
echo "------------------------------------------"
HOLD_RESPONSE=$(curl -X POST http://127.0.0.1:5001/api/pos/transactions/hold \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shift_id": 1,
    "items": [
      {"variant_id": 21, "quantity": 2, "price": 2999.00},
      {"variant_id": 35, "quantity": 1, "price": 5499.00}
    ],
    "subtotal": 11497.00,
    "tax": 1839.52,
    "total": 13336.52,
    "customer_note": "Customer went to get wallet"
  }' \
  -s)

echo "$HOLD_RESPONSE" | python3 -m json.tool

HOLD_ID=$(echo "$HOLD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('hold_id', ''))" 2>/dev/null)

if [ ! -z "$HOLD_ID" ]; then
  echo "✅ Transaction held (ID: $HOLD_ID)"
else
  echo "⚠️  Hold may have failed"
fi
echo ""

# Step 8: Get held transactions again (should show the held one)
echo "Step 8: Get Held Transactions (after holding)"
echo "------------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/transactions/held \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool
echo ""

# Step 9: Recall transaction
if [ ! -z "$HOLD_ID" ]; then
  echo "Step 9: Recall Held Transaction"
  echo "------------------------------------------"
  curl -X POST http://127.0.0.1:5001/api/pos/transactions/recall/$HOLD_ID \
    -H "Authorization: Bearer $TOKEN" \
    -s | python3 -m json.tool
  echo ""
fi

# Step 10: Get metrics
echo "Step 10: Get Cashier Metrics"
echo "------------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/metrics/current \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ KIOSK FEATURES TEST COMPLETE"
echo "=========================================="
