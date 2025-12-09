#!/bin/bash

echo "========================================"
echo "Admin Dashboard Fixes Verification"
echo "========================================"
echo ""

# Get fresh token
echo "Step 1: Login as admin..."
RESPONSE=$(curl -X POST 'http://127.0.0.1:5001/api/auth/employee/login' \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.co.ke","password":"Admin@123"}' \
  -s)

TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Test 1: Inventory
echo "Test 1: Inventory Endpoint"
echo "----------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/inventory' \
  -H "Authorization: Bearer $TOKEN" \
  -s -w "%{http_code}" -o /tmp/test_inventory.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Inventory: HTTP 200"
  ITEM_COUNT=$(python3 -c "import json; data=json.load(open('/tmp/test_inventory.json')); print(len(data.get('items', [])))" 2>/dev/null)
  echo "   Found $ITEM_COUNT inventory items"
else
  echo "❌ Inventory: HTTP $HTTP_CODE"
  cat /tmp/test_inventory.json
fi
echo ""

# Test 2: Orders
echo "Test 2: Orders Endpoint"
echo "------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/orders' \
  -H "Authorization: Bearer $TOKEN" \
  -s -w "%{http_code}" -o /tmp/test_orders.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Orders: HTTP 200"
  ORDER_COUNT=$(python3 -c "import json; data=json.load(open('/tmp/test_orders.json')); print(len(data.get('orders', [])))" 2>/dev/null)
  echo "   Found $ORDER_COUNT orders"
else
  echo "❌ Orders: HTTP $HTTP_CODE"
  cat /tmp/test_orders.json
fi
echo ""

# Test 3: Customers
echo "Test 3: Customers Endpoint"
echo "---------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/customers' \
  -H "Authorization: Bearer $TOKEN" \
  -s -w "%{http_code}" -o /tmp/test_customers.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Customers: HTTP 200"
  CUSTOMER_COUNT=$(python3 -c "import json; data=json.load(open('/tmp/test_customers.json')); print(len(data.get('customers', [])))" 2>/dev/null)
  echo "   Found $CUSTOMER_COUNT customers"
else
  echo "❌ Customers: HTTP $HTTP_CODE"
  cat /tmp/test_customers.json
fi
echo ""

# Test 4: Employees
echo "Test 4: Employees Endpoint"
echo "---------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/employees' \
  -H "Authorization: Bearer $TOKEN" \
  -s -w "%{http_code}" -o /tmp/test_employees.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Employees: HTTP 200"
else
  echo "❌ Employees: HTTP $HTTP_CODE"
  cat /tmp/test_employees.json
fi
echo ""

# Test 5: Promotions
echo "Test 5: Promotions Endpoint"
echo "----------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/promotions' \
  -H "Authorization: Bearer $TOKEN" \
  -s -w "%{http_code}" -o /tmp/test_promotions.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Promotions: HTTP 200"
else
  echo "❌ Promotions: HTTP $HTTP_CODE"
  cat /tmp/test_promotions.json
fi
echo ""

# Test 6: Settings - Currency
echo "Test 6: Settings Currency Endpoint"
echo "------------------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/settings/currency' \
  -H "Authorization: Bearer $TOKEN" \
  -s -w "%{http_code}" -o /tmp/test_settings_currency.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Settings Currency: HTTP 200"
else
  echo "❌ Settings Currency: HTTP $HTTP_CODE"
  cat /tmp/test_settings_currency.json
fi
echo ""

# Test 7: Dashboard Metrics
echo "Test 7: Dashboard Metrics"
echo "--------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/dashboard/metrics?period=today' \
  -H "Authorization: Bearer $TOKEN" \
  -s -w "%{http_code}" -o /tmp/test_metrics.json)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Dashboard Metrics: HTTP 200"
else
  echo "❌ Dashboard Metrics: HTTP $HTTP_CODE"
  cat /tmp/test_metrics.json
fi
echo ""

echo "========================================"
echo "Verification Complete"
echo "========================================"
