#!/bin/bash

echo "=== Testing Stock Adjustment with variant_id ==="
echo ""

# Login
TOKEN=$(curl -X POST 'http://127.0.0.1:5001/api/auth/employee/login' \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.co.ke","password":"Admin@123"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Get first inventory item
echo "Getting first inventory item..."
VARIANT_ID=$(curl -X GET 'http://127.0.0.1:5001/api/admin/inventory' \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['items'][0]['variant_id'])" 2>/dev/null)

echo "Variant ID: $VARIANT_ID"
echo "SKU: $(curl -X GET 'http://127.0.0.1:5001/api/admin/inventory' -H "Authorization: Bearer $TOKEN" -s | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['items'][0]['sku'])" 2>/dev/null)"
echo ""

# Test stock adjustment
echo "Adjusting stock by +5 units..."
HTTP_CODE=$(curl -X PUT "http://127.0.0.1:5001/api/admin/inventory/$VARIANT_ID/stock" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantity":5,"reason":"Test stock adjustment - verification"}' \
  -s -w "%{http_code}" -o /tmp/stock_adjustment_result.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Stock adjustment successful: HTTP 200"
  cat /tmp/stock_adjustment_result.json | python3 -m json.tool 2>/dev/null || cat /tmp/stock_adjustment_result.json
else
  echo "❌ Stock adjustment failed: HTTP $HTTP_CODE"
  cat /tmp/stock_adjustment_result.json
fi
