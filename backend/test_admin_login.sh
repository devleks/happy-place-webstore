#!/bin/bash

echo "=== Testing New Admin Login Endpoint ==="
echo ""

# Test 1: Admin login via new endpoint
echo "Test 1: Login as admin via /api/auth/admin/login"
HTTP_CODE=$(curl -X POST 'http://127.0.0.1:5001/api/auth/admin/login' \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.co.ke","password":"Admin@123"}' \
  -s -w "%{http_code}" -o /tmp/admin_login_response.json)

echo "HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ SUCCESS - Admin login successful"
  cat /tmp/admin_login_response.json | python3 -m json.tool 2>/dev/null | head -15
else
  echo "❌ FAILED"
  cat /tmp/admin_login_response.json
fi
echo ""

echo "=== Test Complete ==="
