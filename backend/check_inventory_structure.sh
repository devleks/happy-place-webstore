#!/bin/bash

# Login
TOKEN=$(curl -X POST 'http://127.0.0.1:5001/api/auth/employee/login' \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.co.ke","password":"Admin@123"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Get first inventory item
curl -X GET 'http://127.0.0.1:5001/api/admin/inventory' \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['items'][0], indent=2))"
