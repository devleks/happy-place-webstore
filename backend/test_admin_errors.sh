#!/bin/bash

echo "================================================"
echo "Testing Admin Dashboard Endpoints with Auth"
echo "================================================"
echo ""

# Login as admin
echo "Step 1: Logging in as admin..."
RESPONSE=$(curl -X POST 'http://127.0.0.1:5001/api/auth/employee/login' \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.co.ke","password":"Admin@123"}' \
  -s)

TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:50}..."
echo ""

# Test each endpoint that showed 400 errors
echo "================================================"
echo "Testing Endpoints That Showed 400 Errors"
echo "================================================"
echo ""

# Test 1: Orders
echo "Test 1: GET /api/admin/orders"
echo "----------------------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/orders' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s -w "%{http_code}" -o /tmp/test_orders_full.json)

echo "HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ FAILED - Response:"
  cat /tmp/test_orders_full.json | python3 -m json.tool 2>/dev/null || cat /tmp/test_orders_full.json
else
  echo "✅ SUCCESS"
  ORDER_COUNT=$(python3 -c "import json; data=json.load(open('/tmp/test_orders_full.json')); print(len(data.get('orders', [])))" 2>/dev/null)
  echo "   Found $ORDER_COUNT orders"
fi
echo ""

# Test 2: Employees
echo "Test 2: GET /api/admin/employees"
echo "----------------------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/employees' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s -w "%{http_code}" -o /tmp/test_employees_full.json)

echo "HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ FAILED - Response:"
  cat /tmp/test_employees_full.json | python3 -m json.tool 2>/dev/null || cat /tmp/test_employees_full.json
else
  echo "✅ SUCCESS"
fi
echo ""

# Test 3: Promotions
echo "Test 3: GET /api/admin/promotions"
echo "----------------------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/promotions' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s -w "%{http_code}" -o /tmp/test_promotions_full.json)

echo "HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ FAILED - Response:"
  cat /tmp/test_promotions_full.json | python3 -m json.tool 2>/dev/null || cat /tmp/test_promotions_full.json
else
  echo "✅ SUCCESS"
fi
echo ""

# Test 4: Sales Report
echo "Test 4: GET /api/admin/reports/sales"
echo "----------------------------------------"
HTTP_CODE=$(curl -X GET 'http://127.0.0.1:5001/api/admin/reports/sales?start_date=2025-01-01&end_date=2025-12-31' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s -w "%{http_code}" -o /tmp/test_sales_report.json)

echo "HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ FAILED - Response:"
  cat /tmp/test_sales_report.json | python3 -m json.tool 2>/dev/null || cat /tmp/test_sales_report.json
else
  echo "✅ SUCCESS"
fi
echo ""

# Test 5: Customer Anonymize (need a customer ID first)
echo "Test 5: POST /api/admin/customers/{id}/anonymize"
echo "----------------------------------------"
CUSTOMER_ID=$(curl -X GET 'http://127.0.0.1:5001/api/admin/customers' \
  -H "Authorization: Bearer $TOKEN" -s | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(data['customers'][0]['id'] if data.get('customers') else '')" 2>/dev/null)

if [ -n "$CUSTOMER_ID" ]; then
  echo "Testing with customer ID: $CUSTOMER_ID"
  HTTP_CODE=$(curl -X POST "http://127.0.0.1:5001/api/admin/customers/$CUSTOMER_ID/anonymize" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"confirmation":"ANONYMIZE","reason":"GDPR request"}' \
    -s -w "%{http_code}" -o /tmp/test_anonymize.json)

  echo "HTTP Status: $HTTP_CODE"
  if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ FAILED - Response:"
    cat /tmp/test_anonymize.json
  else
    echo "✅ SUCCESS"
  fi
else
  echo "⚠️  SKIPPED - No customers found"
fi
echo ""

# Test 6: Stock Adjustment
echo "Test 6: Stock Adjustment Endpoint"
echo "----------------------------------------"
VARIANT_ID=$(curl -X GET 'http://127.0.0.1:5001/api/admin/inventory' \
  -H "Authorization: Bearer $TOKEN" -s | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(data['items'][0]['variant_id'] if data.get('items') else '')" 2>/dev/null)

if [ -n "$VARIANT_ID" ]; then
  echo "Testing stock adjustment for variant ID: $VARIANT_ID"
  echo "Trying: PUT /api/admin/inventory/$VARIANT_ID/stock"
  HTTP_CODE=$(curl -X PUT "http://127.0.0.1:5001/api/admin/inventory/$VARIANT_ID/stock" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"quantity":5,"reason":"Test adjustment"}' \
    -s -w "%{http_code}" -o /tmp/test_stock_put.json)

  echo "HTTP Status: $HTTP_CODE"
  if [ "$HTTP_CODE" = "404" ]; then
    echo "❌ Endpoint does not exist"
    echo "Checking available stock adjustment endpoints..."
    grep -n "stock\|adjust" routes/admin_routes.py | grep "@admin_bp.route" | head -5
  else
    cat /tmp/test_stock_put.json
  fi
fi
echo ""

echo "================================================"
echo "Test Complete"
echo "================================================"
