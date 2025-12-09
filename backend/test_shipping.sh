#!/bin/bash

# Login
TOKEN=$(curl -X POST "http://127.0.0.1:5001/api/auth/customer/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test_orders@example.com","password":"password123"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo "=== Testing Shipping Preview (Nairobi) ==="
curl -X POST "http://127.0.0.1:5001/api/orders/shipping-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city":"Nairobi"}' \
  -s | python3 -m json.tool

echo ""
echo "=== Testing Shipping Preview (Mombasa) ==="
curl -X POST "http://127.0.0.1:5001/api/orders/shipping-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city":"Mombasa"}' \
  -s | python3 -m json.tool
