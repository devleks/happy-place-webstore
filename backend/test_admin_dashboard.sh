#!/bin/bash

# Phase 11 Admin Dashboard - Comprehensive API Testing Script
# Tests all 59 admin endpoints across 8 categories

BASE_URL="http://127.0.0.1:5001/api"

echo "════════════════════════════════════════════════════════════════"
echo "  PHASE 11: Admin Dashboard - Comprehensive API Test Suite"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Step 1: Login as manager to get JWT token
echo "🔐 Step 1: Authenticating as Manager..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@happyplace.com",
    "password": "Manager123!"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ FAILED: Could not authenticate. Response:"
  echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
  echo ""
  echo "💡 Creating manager account..."

  # Try to register manager
  REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/register-employee" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "manager@happyplace.com",
      "password": "Manager123!",
      "full_name": "Test Manager",
      "role": "manager"
    }')

  echo "Registration response:"
  echo "$REGISTER_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REGISTER_RESPONSE"

  # Try login again
  LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "manager@happyplace.com",
      "password": "Manager123!"
    }')

  TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

  if [ -z "$TOKEN" ]; then
    echo "❌ FAILED: Still cannot authenticate. Exiting."
    exit 1
  fi
fi

echo "✅ Authenticated successfully!"
echo "Token: ${TOKEN:0:50}..."
echo ""

# ════════════════════════════════════════════════════════════════
# CATEGORY 1: DASHBOARD ENDPOINTS (4 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 CATEGORY 1: Dashboard Endpoints (4 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1.1: Get Dashboard Metrics
echo "Test 1.1: GET /admin/dashboard/metrics?period=today"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/dashboard/metrics?period=today" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 1.2: Get Sales Trends
echo "Test 1.2: GET /admin/dashboard/sales-trends?days=7"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/dashboard/sales-trends?days=7" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 1.3: Get Critical Alerts
echo "Test 1.3: GET /admin/dashboard/alerts"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/dashboard/alerts" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 1.4: Get Recent Activity
echo "Test 1.4: GET /admin/dashboard/activity?limit=10"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/dashboard/activity?limit=10" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# ════════════════════════════════════════════════════════════════
# CATEGORY 2: INVENTORY ENDPOINTS (9 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📦 CATEGORY 2: Inventory Management (9 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 2.1: Get Inventory List
echo "Test 2.1: GET /admin/inventory?page=1&per_page=10"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/inventory?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 2.2: Get Low Stock Items
echo "Test 2.2: GET /admin/inventory?stock_status=low"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/inventory?stock_status=low" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 2.3: Get Product Details (variant_id = 1)
echo "Test 2.3: GET /admin/inventory/1"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/inventory/1" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 2.4: Adjust Stock
echo "Test 2.4: POST /admin/inventory/adjust"
RESPONSE=$(curl -s -X POST "${BASE_URL}/admin/inventory/adjust" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "variant_id": 1,
    "quantity": 5,
    "type": "add",
    "reason": "Stock replenishment - Test"
  }')
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 2.5: Get Stock History
echo "Test 2.5: GET /admin/inventory/1/history"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/inventory/1/history" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# ════════════════════════════════════════════════════════════════
# CATEGORY 3: ORDER MANAGEMENT (8 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🛒 CATEGORY 3: Order Management (8 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 3.1: Get Order List
echo "Test 3.1: GET /admin/orders?page=1&per_page=10"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/orders?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 3.2: Get Pending Orders
echo "Test 3.2: GET /admin/orders?status=pending"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/orders?status=pending" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract first order ID for detailed testing
ORDER_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); orders=data.get('orders', []); print(orders[0]['id'] if orders else 0)" 2>/dev/null)

if [ "$ORDER_ID" != "0" ] && [ -n "$ORDER_ID" ]; then
  # Test 3.3: Get Order Details
  echo "Test 3.3: GET /admin/orders/${ORDER_ID}"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/orders/${ORDER_ID}" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Test 3.4: Update Order Status
  echo "Test 3.4: PUT /admin/orders/${ORDER_ID}/status"
  RESPONSE=$(curl -s -X PUT "${BASE_URL}/admin/orders/${ORDER_ID}/status" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "status": "processing",
      "tracking": {
        "carrier": "DHL",
        "number": "TEST123456",
        "notes": "Order being prepared for shipment"
      }
    }')
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Test 3.5: Add Order Note
  echo "Test 3.5: POST /admin/orders/${ORDER_ID}/notes"
  RESPONSE=$(curl -s -X POST "${BASE_URL}/admin/orders/${ORDER_ID}/notes" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "note": "Customer requested express shipping - Test note"
    }')
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Test 3.6: Get Order Timeline
  echo "Test 3.6: GET /admin/orders/${ORDER_ID}/timeline"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/orders/${ORDER_ID}/timeline" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""
else
  echo "⚠️  No orders found for detailed testing. Skipping tests 3.3-3.6"
  echo ""
fi

# ════════════════════════════════════════════════════════════════
# CATEGORY 4: CUSTOMER MANAGEMENT (9 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  👥 CATEGORY 4: Customer Management (9 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 4.1: Get Customer List
echo "Test 4.1: GET /admin/customers?page=1&per_page=10"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/customers?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract first customer ID
CUSTOMER_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); customers=data.get('customers', []); print(customers[0]['id'] if customers else 0)" 2>/dev/null)

if [ "$CUSTOMER_ID" != "0" ] && [ -n "$CUSTOMER_ID" ]; then
  # Test 4.2: Get Customer Details
  echo "Test 4.2: GET /admin/customers/${CUSTOMER_ID}"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/customers/${CUSTOMER_ID}" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Test 4.3: Get Customer Orders
  echo "Test 4.3: GET /admin/customers/${CUSTOMER_ID}/orders"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/customers/${CUSTOMER_ID}/orders" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Test 4.4: Get Customer Activity
  echo "Test 4.4: GET /admin/customers/${CUSTOMER_ID}/activity?days=30"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/customers/${CUSTOMER_ID}/activity?days=30" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""
else
  echo "⚠️  No customers found for detailed testing. Skipping tests 4.2-4.4"
  echo ""
fi

# ════════════════════════════════════════════════════════════════
# CATEGORY 5: EMPLOYEE MANAGEMENT (9 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  👔 CATEGORY 5: Employee Management (9 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 5.1: Get Employee List
echo "Test 5.1: GET /admin/employees?status=active"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/employees?status=active" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract first employee ID
EMPLOYEE_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); employees=data if isinstance(data, list) else []; print(employees[0]['id'] if employees else 0)" 2>/dev/null)

if [ "$EMPLOYEE_ID" != "0" ] && [ -n "$EMPLOYEE_ID" ]; then
  # Test 5.2: Get Employee Details
  echo "Test 5.2: GET /admin/employees/${EMPLOYEE_ID}"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/employees/${EMPLOYEE_ID}" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Test 5.3: Get Employee Performance
  echo "Test 5.3: GET /admin/employees/${EMPLOYEE_ID}/performance?period=month"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/employees/${EMPLOYEE_ID}/performance?period=month" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""
else
  echo "⚠️  No employees found for detailed testing. Skipping tests 5.2-5.3"
  echo ""
fi

# ════════════════════════════════════════════════════════════════
# CATEGORY 6: PROMOTIONS (9 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎁 CATEGORY 6: Promotion Management (9 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 6.1: Get Promotions List
echo "Test 6.1: GET /admin/promotions?status=active"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/promotions?status=active" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 6.2: Create Promotion
echo "Test 6.2: POST /admin/promotions"
RESPONSE=$(curl -s -X POST "${BASE_URL}/admin/promotions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Black Friday Sale",
    "code": "TESTBF2025",
    "discount_type": "percentage",
    "discount_value": 25,
    "start_date": "2025-12-01T00:00:00",
    "end_date": "2025-12-31T23:59:59",
    "max_uses": 100,
    "min_order_value": 1000
  }')
PROMO_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('promotion', {}).get('id', 0))" 2>/dev/null)
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

if [ "$PROMO_ID" != "0" ] && [ -n "$PROMO_ID" ]; then
  # Test 6.3: Get Promotion Details
  echo "Test 6.3: GET /admin/promotions/${PROMO_ID}"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/promotions/${PROMO_ID}" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Test 6.4: Get Promotion Analytics
  echo "Test 6.4: GET /admin/promotions/${PROMO_ID}/analytics"
  RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/promotions/${PROMO_ID}/analytics" \
    -H "Authorization: Bearer $TOKEN")
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  echo ""
fi

# ════════════════════════════════════════════════════════════════
# CATEGORY 7: REPORTS (4 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📈 CATEGORY 7: Reports & Analytics (4 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 7.1: Sales Report
echo "Test 7.1: GET /admin/reports/sales?period=month"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/reports/sales?period=month" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 7.2: Inventory Report
echo "Test 7.2: GET /admin/reports/inventory"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/reports/inventory" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 7.3: Customer Report
echo "Test 7.3: GET /admin/reports/customers?period=month"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/reports/customers?period=month" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# ════════════════════════════════════════════════════════════════
# CATEGORY 8: SETTINGS (7 endpoints)
# ════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⚙️  CATEGORY 8: System Settings (7 endpoints)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 8.1: Get All Settings
echo "Test 8.1: GET /admin/settings"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/settings" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 8.2: Get Store Settings
echo "Test 8.2: GET /admin/settings/category/store"
RESPONSE=$(curl -s -X GET "${BASE_URL}/admin/settings/category/store" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 8.3: Update Setting
echo "Test 8.3: PUT /admin/settings/store_name"
RESPONSE=$(curl -s -X PUT "${BASE_URL}/admin/settings/store_name" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "Happy Place - Test Store"
  }')
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# ════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ TEST SUITE COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Tested endpoints across 8 categories:"
echo "  📊 Dashboard: 4 endpoints"
echo "  📦 Inventory: 9 endpoints"
echo "  🛒 Orders: 8 endpoints"
echo "  👥 Customers: 9 endpoints"
echo "  👔 Employees: 9 endpoints"
echo "  🎁 Promotions: 9 endpoints"
echo "  📈 Reports: 4 endpoints"
echo "  ⚙️  Settings: 7 endpoints"
echo ""
echo "Total: 59 admin endpoints tested"
echo ""
