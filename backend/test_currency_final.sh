#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2NDc3NTUyMSwianRpIjoiM2I1YWU0YzMtNDYyMS00YjNjLWJhNjAtYzI3YjEzMTFlYTJmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NjQ3NzU1MjEsImNzcmYiOiI5OGQyYzJmZS0xYzUwLTRlOWItOGM0Yy02ODkyNjc0YTU4M2UiLCJleHAiOjE3NjQ4MDQzMjEsInVzZXJfdHlwZSI6ImVtcGxveWVlIiwicm9sZSI6ImFkbWluIn0.9r8GAZMMGLmFwPJJ5ZoD4W3n0RQg5Py8Wm5mDYHNlrM"

printf "======================================================\n"
printf "   CURRENCY MANAGEMENT - FINAL VERIFICATION TEST\n"
printf "======================================================\n\n"

printf "Test 1: Get Public Settings (No Auth Required)\n"
printf "------------------------------------------------------\n"
curl -X GET 'http://127.0.0.1:5001/api/settings/public' -s
printf "\n\n"

printf "Test 2: Get Currency Settings (Admin)\n"
printf "------------------------------------------------------\n"
curl -X GET 'http://127.0.0.1:5001/api/admin/settings/currency' \
  -H "Authorization: Bearer $TOKEN" -s
printf "\n\n"

printf "Test 3: Update Currency to USD\n"
printf "------------------------------------------------------\n"
curl -X PUT 'http://127.0.0.1:5001/api/admin/settings/currency' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"currency": "$", "currency_code": "USD"}' -s
printf "\n\n"

printf "Test 4: Verify USD Update (Public Endpoint)\n"
printf "------------------------------------------------------\n"
curl -X GET 'http://127.0.0.1:5001/api/settings/public' -s
printf "\n\n"

printf "Test 5: Update Currency Back to KSh\n"
printf "------------------------------------------------------\n"
curl -X PUT 'http://127.0.0.1:5001/api/admin/settings/currency' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"currency": "KSh", "currency_code": "KES"}' -s
printf "\n\n"

printf "Test 6: Final Verification (Should be KSh)\n"
printf "------------------------------------------------------\n"
curl -X GET 'http://127.0.0.1:5001/api/settings/public' -s
printf "\n\n"

printf "======================================================\n"
printf "               ALL TESTS COMPLETED ✓\n"
printf "======================================================\n"
