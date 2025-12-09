#!/bin/bash

echo "=============================================="
echo "  POS SYSTEM - SIMPLE UAT TEST"
echo "=============================================="

BASE_URL="http://127.0.0.1:5001/api"
PASSED=0
FAILED=0

# Test 1: Health Check
echo -e "\n[TEST 1] Health Check"
HEALTH=$(curl -s -m 5 "$BASE_URL/pos/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ PASS"
    ((PASSED++))
else
    echo "✗ FAIL: $HEALTH"
    ((FAILED++))
fi

# Test 2: Employee Login
echo -e "\n[TEST 2] Employee Login"
LOGIN=$(curl -s -m 5 -X POST "$BASE_URL/auth/employee/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"manager@happyplace.co.ke","password":"manager123"}')

if echo "$LOGIN" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    echo "✓ PASS - Token: ${TOKEN:0:20}..."
    ((PASSED++))
else
    echo "✗ FAIL: $LOGIN"
    ((FAILED++))
    exit 1
fi

# Test 3: Get Current Shift
echo -e "\n[TEST 3] Get Current Shift"
SHIFT=$(curl -s -m 5 -X GET "$BASE_URL/pos/shifts/current" \
    -H "Authorization: Bearer $TOKEN")

if echo "$SHIFT" | grep -q "shift_id"; then
    SHIFT_ID=$(echo "$SHIFT" | python3 -c "import sys,json; print(json.load(sys.stdin)['shift_id'])" 2>/dev/null)
    echo "✓ PASS - Shift ID: $SHIFT_ID"
    ((PASSED++))
else
    echo "No open shift, starting new one..."
    
    # Test 4: Start Shift
    echo -e "\n[TEST 4] Start Shift"
    START=$(curl -s -m 5 -X POST "$BASE_URL/pos/shifts/start" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"store_location_id":1,"opening_float":5000}')
    
    if echo "$START" | grep -q "shift_id"; then
        SHIFT_ID=$(echo "$START" | python3 -c "import sys,json; print(json.load(sys.stdin)['shift_id'])" 2>/dev/null)
        echo "✓ PASS - Shift ID: $SHIFT_ID"
        ((PASSED++))
    else
        echo "✗ FAIL: $START"
        ((FAILED++))
        exit 1
    fi
fi

# Test 5: Get Shift Summary
echo -e "\n[TEST 5] Get Shift Summary"
SUMMARY=$(curl -s -m 5 -X GET "$BASE_URL/pos/shifts/$SHIFT_ID" \
    -H "Authorization: Bearer $TOKEN")

if echo "$SUMMARY" | grep -q "shift_number"; then
    SHIFT_NUM=$(echo "$SUMMARY" | python3 -c "import sys,json; print(json.load(sys.stdin)['shift_number'])" 2>/dev/null)
    echo "✓ PASS - Shift: $SHIFT_NUM"
    ((PASSED++))
else
    echo "✗ FAIL: $SUMMARY"
    ((FAILED++))
fi

# Test 6: Get Products
echo -e "\n[TEST 6] Get Products"
PRODUCTS=$(curl -s -m 5 -X GET "$BASE_URL/products?limit=5" \
    -H "Authorization: Bearer $TOKEN")

if echo "$PRODUCTS" | grep -q "products"; then
    VARIANT=$(echo "$PRODUCTS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['products'][0]['variants'][0]['id'] if d.get('products') and len(d['products'])>0 else '')" 2>/dev/null)
    if [ -n "$VARIANT" ]; then
        echo "✓ PASS - Variant ID: $VARIANT"
        ((PASSED++))
    else
        echo "✗ FAIL - No variants found"
        ((FAILED++))
        VARIANT=1  # Fallback
    fi
else
    echo "✗ FAIL: $PRODUCTS"
    ((FAILED++))
    VARIANT=1  # Fallback
fi

# Test 7: Create Transaction
echo -e "\n[TEST 7] Create Transaction"
TXN=$(curl -s -m 5 -X POST "$BASE_URL/pos/transactions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"shift_id\":$SHIFT_ID,\"payment_method\":\"cash\",\"items\":[{\"variant_id\":$VARIANT,\"quantity\":1}],\"cash_tendered\":10000}")

if echo "$TXN" | grep -q "transaction_id"; then
    TXN_ID=$(echo "$TXN" | python3 -c "import sys,json; print(json.load(sys.stdin)['transaction_id'])" 2>/dev/null)
    echo "✓ PASS - Transaction ID: $TXN_ID"
    ((PASSED++))
else
    echo "✗ FAIL: $TXN"
    ((FAILED++))
fi

# Test 8: Cash Movement
echo -e "\n[TEST 8] Cash Movement"
CASH=$(curl -s -m 5 -X POST "$BASE_URL/pos/cash-movements" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"shift_id\":$SHIFT_ID,\"movement_type\":\"cash_out\",\"amount\":1000,\"reason\":\"Test\"}")

if echo "$CASH" | grep -q "success"; then
    echo "✓ PASS"
    ((PASSED++))
else
    echo "✗ FAIL: $CASH"
    ((FAILED++))
fi

# Test 9: Close Shift
echo -e "\n[TEST 9] Close Shift"
CLOSE=$(curl -s -m 5 -X POST "$BASE_URL/pos/shifts/$SHIFT_ID/close" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"closing_cash":9000,"notes":"UAT test"}')

if echo "$CLOSE" | grep -q "success"; then
    echo "✓ PASS"
    ((PASSED++))
else
    echo "✗ FAIL: $CLOSE"
    ((FAILED++))
fi

# Summary
echo ""
echo "=============================================="
echo "  SUMMARY"
echo "=============================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "=============================================="

if [ $FAILED -eq 0 ]; then
    echo "✓ ALL TESTS PASSED!"
    exit 0
else
    echo "✗ SOME TESTS FAILED"
    exit 1
fi
