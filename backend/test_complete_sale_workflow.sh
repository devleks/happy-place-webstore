#!/bin/bash

echo "=========================================="
echo "COMPLETE POS SALE WORKFLOW TEST"
echo "=========================================="
echo ""

# Step 1: Employee Login
echo "Step 1: Employee Login"
echo "----------------------------------------"
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

# Step 2: Check if shift is open
echo "Step 2: Check Current Shift"
echo "----------------------------------------"
SHIFT_RESPONSE=$(curl -X GET http://127.0.0.1:5001/api/pos/shifts/current \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "$SHIFT_RESPONSE" | python3 -m json.tool

SHIFT_ID=$(echo "$SHIFT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('shift', {}).get('shift_id', ''))" 2>/dev/null)

if [ -z "$SHIFT_ID" ]; then
  echo ""
  echo "No shift open. Starting new shift..."
  echo ""

  # Start a new shift
  echo "Step 2b: Start New Shift"
  echo "----------------------------------------"
  SHIFT_START_RESPONSE=$(curl -X POST http://127.0.0.1:5001/api/pos/shifts/start \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"store_location_id":1,"opening_float":5000.00}' \
    -s)

  echo "$SHIFT_START_RESPONSE" | python3 -m json.tool

  SHIFT_ID=$(echo "$SHIFT_START_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('shift', {}).get('shift_id', ''))" 2>/dev/null)

  if [ -z "$SHIFT_ID" ]; then
    echo "❌ ERROR: Failed to start shift"
    exit 1
  fi

  echo "✅ Shift started successfully (Shift ID: $SHIFT_ID)"
else
  echo "✅ Shift already open (Shift ID: $SHIFT_ID)"
fi

echo ""

# Step 3: Get available products
echo "Step 3: Get Available Products"
echo "----------------------------------------"
PRODUCTS_RESPONSE=$(curl -X GET http://127.0.0.1:5001/api/products \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "$PRODUCTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['products'][:2], indent=2))" 2>/dev/null || echo "$PRODUCTS_RESPONSE"

# Get first product slug
PRODUCT_SLUG=$(echo "$PRODUCTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['products'][0]['slug'])" 2>/dev/null)

if [ -z "$PRODUCT_SLUG" ]; then
  echo "❌ ERROR: No products found"
  exit 1
fi

echo "✅ Products loaded (Using Product: $PRODUCT_SLUG)"
echo ""

# Get product details to get variant ID
echo "Step 3b: Get Product Details for Variants"
echo "----------------------------------------"
PRODUCT_DETAIL=$(curl -X GET "http://127.0.0.1:5001/api/products/$PRODUCT_SLUG" \
  -H "Authorization: Bearer $TOKEN" \
  -s)

# Extract a variant ID from the product
VARIANT_ID=$(echo "$PRODUCT_DETAIL" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['variants'][0]['id'])" 2>/dev/null)

if [ -z "$VARIANT_ID" ]; then
  echo "❌ ERROR: No variants found"
  exit 1
fi

echo "✅ Variant selected (Variant ID: $VARIANT_ID)"
echo ""

# Step 4: Create POS Transaction
echo "Step 4: Create POS Transaction"
echo "----------------------------------------"
TRANSACTION_RESPONSE=$(curl -X POST http://127.0.0.1:5001/api/pos/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"shift_id\": $SHIFT_ID,
    \"payment_method\": \"cash\",
    \"items\": [
      {\"variant_id\": $VARIANT_ID, \"quantity\": 2}
    ],
    \"cash_tendered\": 10000.00
  }" \
  -s)

echo "$TRANSACTION_RESPONSE" | python3 -m json.tool

TRANSACTION_ID=$(echo "$TRANSACTION_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('transaction_id', ''))" 2>/dev/null)

if [ -z "$TRANSACTION_ID" ]; then
  echo "❌ ERROR: Transaction failed"
  echo "$TRANSACTION_RESPONSE"
  exit 1
fi

echo "✅ Transaction created (ID: $TRANSACTION_ID)"
echo ""

# Step 5: Get Transaction Details
echo "Step 5: Get Transaction Details"
echo "----------------------------------------"
TRANSACTION_DETAILS=$(curl -X GET http://127.0.0.1:5001/api/pos/transactions/$TRANSACTION_ID \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "$TRANSACTION_DETAILS" | python3 -m json.tool
echo ""

# Step 6: Get Thermal Receipt
echo "Step 6: Get Thermal Receipt (58mm)"
echo "----------------------------------------"
RECEIPT_RESPONSE=$(curl -X GET "http://127.0.0.1:5001/api/pos/transactions/$TRANSACTION_ID/receipt/thermal?width=58" \
  -H "Authorization: Bearer $TOKEN" \
  -s)

echo "$RECEIPT_RESPONSE" | python3 -m json.tool

RECEIPT_TEXT=$(echo "$RECEIPT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('receipt', ''))" 2>/dev/null)

if [ ! -z "$RECEIPT_TEXT" ]; then
  echo ""
  echo "Receipt Preview:"
  echo "----------------------------------------"
  echo "$RECEIPT_TEXT"
  echo "----------------------------------------"
  echo "✅ Receipt generated successfully"
else
  echo "⚠️  Receipt generation may have issues"
fi

echo ""

# Step 7: Get all receipt formats
echo "Step 7: Get All Receipt Formats"
echo "----------------------------------------"
curl -X GET "http://127.0.0.1:5001/api/pos/transactions/$TRANSACTION_ID/receipt/formats" \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

echo ""

# Step 8: Mark receipt as printed
echo "Step 8: Mark Receipt as Printed"
echo "----------------------------------------"
curl -X PUT "http://127.0.0.1:5001/api/pos/transactions/$TRANSACTION_ID/receipt/printed" \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

echo ""

# Step 9: Get updated shift info
echo "Step 9: Get Updated Shift Info"
echo "----------------------------------------"
curl -X GET http://127.0.0.1:5001/api/pos/shifts/current \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

echo ""
echo "=========================================="
echo "✅ COMPLETE SALE WORKFLOW TEST FINISHED"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Employee logged in successfully"
echo "- Shift opened/verified (ID: $SHIFT_ID)"
echo "- Product selected (Variant ID: $VARIANT_ID)"
echo "- Transaction created (ID: $TRANSACTION_ID)"
echo "- Receipt generated and marked as printed"
echo "- Shift statistics updated"
