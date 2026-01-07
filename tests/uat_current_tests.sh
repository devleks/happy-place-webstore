#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/uat_current_helpers.sh"

preflight_backend

print_section "UAT CURRENT INSTANCE"
echo "BASE_URL=$BASE_URL" | tee -a "$LOG_FILE"
echo "RUN_ID=$RUN_ID" | tee -a "$LOG_FILE"

CUSTOMER_EMAIL="uat.current.$(date +%s)@happyplace.com"
CUSTOMER_PASSWORD="TestPass123!"

EMP_EMAIL="${EMP_EMAIL:-manager@happyplace.com}"
EMP_PASSWORD="${EMP_PASSWORD:-Manager123!}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@happyplace.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin123!}"

CUSTOMER_TOKEN=""
EMPLOYEE_TOKEN=""
ADMIN_TOKEN=""

PRODUCT_SLUG=""
VARIANT_ID=""
ORDER_ID=""
SHIFT_ID=""
TRANSACTION_ID=""
CART_ITEM_ID=""
POS_VARIANT_ID=""

# -----------------------------
# CUSTOMER
# -----------------------------
print_section "CUSTOMER"

# CUST-01 Register
REGISTER_DATA=$(cat <<EOF
{
  "email": "$CUSTOMER_EMAIL",
  "password": "$CUSTOMER_PASSWORD",
  "first_name": "UAT",
  "last_name": "Customer",
  "phone": "+254712345678",
  "gdpr_consent": true,
  "marketing_consent": false
}
EOF
)
REGISTER_RESP=$(api_call "POST" "/auth/customer/register" "$REGISTER_DATA" "")
REGISTER_CODE=$(get_http_code "$REGISTER_RESP")
REGISTER_BODY=$(get_body "$REGISTER_RESP")

if [ "$REGISTER_CODE" = "201" ]; then
  CUSTOMER_TOKEN=$(json_get "$REGISTER_BODY" "access_token")
  pass_test "CUST-01"
else
  fail_test "CUST-01" "register failed (HTTP $REGISTER_CODE)"
fi

# CUST-02 Login
LOGIN_DATA=$(cat <<EOF
{
  "email": "$CUSTOMER_EMAIL",
  "password": "$CUSTOMER_PASSWORD"
}
EOF
)
LOGIN_RESP=$(api_call "POST" "/auth/customer/login" "$LOGIN_DATA" "")
LOGIN_CODE=$(get_http_code "$LOGIN_RESP")
LOGIN_BODY=$(get_body "$LOGIN_RESP")

if [ "$LOGIN_CODE" = "200" ]; then
  CUSTOMER_TOKEN=$(json_get "$LOGIN_BODY" "access_token")
  pass_test "CUST-02"
else
  fail_test "CUST-02" "login failed (HTTP $LOGIN_CODE)"
fi

# CUST-03 Browse products
PROD_RESP=$(api_call "GET" "/products?page=1&per_page=12" "" "")
PROD_CODE=$(get_http_code "$PROD_RESP")
PROD_BODY=$(get_body "$PROD_RESP")

if [ "$PROD_CODE" = "200" ]; then
  PRODUCT_SLUG=$(json_get "$PROD_BODY" "products[0].slug")
  if [ -n "$PRODUCT_SLUG" ]; then
    pass_test "CUST-03"
  else
    warn_test "CUST-03" "no products returned"
  fi
else
  fail_test "CUST-03" "browse products failed (HTTP $PROD_CODE)"
fi

# CUST-04 Product details (needs slug)
if [ -n "$PRODUCT_SLUG" ]; then
  DETAIL_RESP=$(api_call "GET" "/products/$PRODUCT_SLUG" "" "")
  DETAIL_CODE=$(get_http_code "$DETAIL_RESP")
  DETAIL_BODY=$(get_body "$DETAIL_RESP")

  if [ "$DETAIL_CODE" = "200" ]; then
    VARIANT_ID=$(json_get "$DETAIL_BODY" "variants[0].id")
    pass_test "CUST-04"
  else
    fail_test "CUST-04" "product detail failed (HTTP $DETAIL_CODE)"
  fi
else
  warn_test "CUST-04" "skipped - missing product slug"
fi

# CUST-05 Add to cart (needs token + variant)
if [ -n "$CUSTOMER_TOKEN" ] && [ -n "$VARIANT_ID" ]; then
  ADD_CART_DATA=$(cat <<EOF
{
  "variant_id": $VARIANT_ID,
  "quantity": 2
}
EOF
)
  CART_ADD_RESP=$(api_call "POST" "/cart/items" "$ADD_CART_DATA" "$CUSTOMER_TOKEN")
  CART_ADD_CODE=$(get_http_code "$CART_ADD_RESP")
  CART_ADD_BODY=$(get_body "$CART_ADD_RESP")
  if [ "$CART_ADD_CODE" = "201" ]; then
    CART_ITEM_ID=$(json_get "$CART_ADD_BODY" "cart_item.id")
    pass_test "CUST-05"
  elif [ "$CART_ADD_CODE" = "400" ]; then
    warn_test "CUST-05" "add to cart unavailable (HTTP 400 - likely out of stock)"
  else
    fail_test "CUST-05" "add to cart failed (HTTP $CART_ADD_CODE)"
  fi
else
  warn_test "CUST-05" "skipped - missing token or variant"
fi

# CUST-06 Update cart quantity (route supports PATCH /cart/items/<item_id_or_variant_id>)
if [ -n "$CUSTOMER_TOKEN" ] && [ -n "$VARIANT_ID" ]; then
  if [ -z "$CART_ITEM_ID" ]; then
    CART_VIEW_RESP=$(api_call "GET" "/cart" "" "$CUSTOMER_TOKEN")
    CART_VIEW_CODE=$(get_http_code "$CART_VIEW_RESP")
    CART_VIEW_BODY=$(get_body "$CART_VIEW_RESP")
    if [ "$CART_VIEW_CODE" = "200" ]; then
      CART_ITEM_ID=$(json_get "$CART_VIEW_BODY" "items[0].id")
    fi
  fi

  if [ -z "$CART_ITEM_ID" ]; then
    warn_test "CUST-06" "skipped - no cart item to update"
  else

  UPDATE_CART_DATA=$(cat <<EOF
{
  "quantity": 3
}
EOF
)
  CART_UPD_RESP=$(api_call "PATCH" "/cart/items/$CART_ITEM_ID" "$UPDATE_CART_DATA" "$CUSTOMER_TOKEN")
  CART_UPD_CODE=$(get_http_code "$CART_UPD_RESP")
  if [ "$CART_UPD_CODE" = "200" ]; then
    pass_test "CUST-06"
  else
    fail_test "CUST-06" "update cart failed (HTTP $CART_UPD_CODE)"
  fi
  fi
else
  warn_test "CUST-06" "skipped - missing token or variant"
fi

# CUST-07 Shipping preview (no auth required)
SHIP_PREVIEW_DATA='{"city":"Nairobi"}'
SHIP_RESP=$(api_call "POST" "/orders/shipping-preview" "$SHIP_PREVIEW_DATA" "")
SHIP_CODE=$(get_http_code "$SHIP_RESP")
if [ "$SHIP_CODE" = "200" ]; then
  pass_test "CUST-07"
else
  fail_test "CUST-07" "shipping preview failed (HTTP $SHIP_CODE)"
fi

# CUST-08 Create order (requires token + non-empty cart)
if [ -n "$CUSTOMER_TOKEN" ] && [ -n "$CART_ITEM_ID" ]; then
  ORDER_DATA=$(cat <<EOF
{
  "payment_method": "cod",
  "shipping_address": {
    "street": "123 Test Street, Apt 4B",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  },
  "billing_address": {
    "street": "123 Test Street, Apt 4B",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  }
}
EOF
)
  ORDER_RESP=$(api_call "POST" "/orders" "$ORDER_DATA" "$CUSTOMER_TOKEN")
  ORDER_CODE=$(get_http_code "$ORDER_RESP")
  ORDER_BODY=$(get_body "$ORDER_RESP")

  if [ "$ORDER_CODE" = "201" ]; then
    ORDER_ID=$(json_get "$ORDER_BODY" "order.id")
    pass_test "CUST-08"
  else
    fail_test "CUST-08" "create order failed (HTTP $ORDER_CODE)"
  fi
else
  warn_test "CUST-08" "skipped - missing customer token or cart item"
fi

# CUST-09 List orders
if [ -n "$CUSTOMER_TOKEN" ]; then
  ORDERS_RESP=$(api_call "GET" "/orders?page=1&per_page=10" "" "$CUSTOMER_TOKEN")
  ORDERS_CODE=$(get_http_code "$ORDERS_RESP")
  if [ "$ORDERS_CODE" = "200" ]; then
    pass_test "CUST-09"
  else
    fail_test "CUST-09" "list orders failed (HTTP $ORDERS_CODE)"
  fi
else
  warn_test "CUST-09" "skipped - missing token"
fi

# CUST-10 Wishlist add + view
if [ -n "$CUSTOMER_TOKEN" ] && [ -n "$VARIANT_ID" ]; then
  WISH_DATA=$(cat <<EOF
{
  "variant_id": $VARIANT_ID
}
EOF
)
  WISH_ADD_RESP=$(api_call "POST" "/wishlist" "$WISH_DATA" "$CUSTOMER_TOKEN")
  WISH_ADD_CODE=$(get_http_code "$WISH_ADD_RESP")
  if [ "$WISH_ADD_CODE" = "201" ] || [ "$WISH_ADD_CODE" = "200" ]; then
    pass_test "CUST-10A"
  else
    fail_test "CUST-10A" "wishlist add failed (HTTP $WISH_ADD_CODE)"
  fi

  WISH_VIEW_RESP=$(api_call "GET" "/wishlist" "" "$CUSTOMER_TOKEN")
  WISH_VIEW_CODE=$(get_http_code "$WISH_VIEW_RESP")
  if [ "$WISH_VIEW_CODE" = "200" ]; then
    pass_test "CUST-10B"
  else
    fail_test "CUST-10B" "wishlist view failed (HTTP $WISH_VIEW_CODE)"
  fi
else
  warn_test "CUST-10" "skipped - missing token or variant"
fi

# -----------------------------
# EMPLOYEE / POS
# -----------------------------
print_section "EMPLOYEE/POS"

EMP_LOGIN_DATA=$(cat <<EOF
{
  "email": "$EMP_EMAIL",
  "password": "$EMP_PASSWORD"
}
EOF
)
EMP_LOGIN_RESP=$(api_call "POST" "/auth/employee/login" "$EMP_LOGIN_DATA" "")
EMP_LOGIN_CODE=$(get_http_code "$EMP_LOGIN_RESP")
EMP_LOGIN_BODY=$(get_body "$EMP_LOGIN_RESP")

if [ "$EMP_LOGIN_CODE" = "200" ]; then
  EMPLOYEE_TOKEN=$(json_get "$EMP_LOGIN_BODY" "access_token")
  pass_test "EMP-01"
else
  fail_test "EMP-01" "employee login failed (HTTP $EMP_LOGIN_CODE)"
fi

# POS-01 Current shift
if [ -n "$EMPLOYEE_TOKEN" ]; then
  CUR_SHIFT_RESP=$(api_call "GET" "/pos/shifts/current" "" "$EMPLOYEE_TOKEN")
  CUR_SHIFT_CODE=$(get_http_code "$CUR_SHIFT_RESP")
  CUR_SHIFT_BODY=$(get_body "$CUR_SHIFT_RESP")

  if [ "$CUR_SHIFT_CODE" = "200" ]; then
    SHIFT_ID=$(json_get "$CUR_SHIFT_BODY" "shift.shift_id")
    pass_test "POS-01"
  else
    fail_test "POS-01" "get current shift failed (HTTP $CUR_SHIFT_CODE)"
  fi
else
  warn_test "POS-01" "skipped - missing employee token"
fi

# POS-02 Start shift if none
if [ -n "$EMPLOYEE_TOKEN" ] && [ -z "$SHIFT_ID" ]; then
  START_SHIFT_DATA='{"store_location_id":1,"opening_float":5000.00}'
  START_SHIFT_RESP=$(api_call "POST" "/pos/shifts/start" "$START_SHIFT_DATA" "$EMPLOYEE_TOKEN")
  START_SHIFT_CODE=$(get_http_code "$START_SHIFT_RESP")
  START_SHIFT_BODY=$(get_body "$START_SHIFT_RESP")

  if [ "$START_SHIFT_CODE" = "201" ] || [ "$START_SHIFT_CODE" = "200" ]; then
    SHIFT_ID=$(json_get "$START_SHIFT_BODY" "shift.shift_id")
    pass_test "POS-02"
  else
    fail_test "POS-02" "start shift failed (HTTP $START_SHIFT_CODE)"
  fi
fi

# POS-03 Create transaction
if [ -n "$EMPLOYEE_TOKEN" ] && [ -n "$SHIFT_ID" ]; then
  if [ -z "$POS_VARIANT_ID" ]; then
    POS_PROD_RESP=$(api_call "GET" "/products/with-variants" "" "")
    POS_PROD_CODE=$(get_http_code "$POS_PROD_RESP")
    POS_PROD_BODY=$(get_body "$POS_PROD_RESP")

    if [ "$POS_PROD_CODE" = "200" ]; then
      POS_VARIANT_ID=$(python3 -c "import json,sys
try:
    data=json.load(sys.stdin)
except Exception:
    print(''); raise SystemExit(0)

products = data.get('products') or []
for p in products:
    for v in (p.get('variants') or []):
        try:
            if (v.get('pos_stock') or 0) > 0 and v.get('id') is not None:
                print(v.get('id'))
                raise SystemExit(0)
        except Exception:
            continue

print('')
" <<<"$POS_PROD_BODY" 2>/dev/null)
    fi
  fi

  if [ -z "$POS_VARIANT_ID" ]; then
    warn_test "POS-03" "skipped - no POS variant with stock available"
  else
  TXN_DATA=$(cat <<EOF
{
  "shift_id": $SHIFT_ID,
  "payment_method": "cash",
  "items": [{"variant_id": $POS_VARIANT_ID, "quantity": 1}],
  "cash_tendered": 10000.00
}
EOF
)
  TXN_RESP=$(api_call "POST" "/pos/transactions" "$TXN_DATA" "$EMPLOYEE_TOKEN")
  TXN_CODE=$(get_http_code "$TXN_RESP")
  TXN_BODY=$(get_body "$TXN_RESP")

  if [ "$TXN_CODE" = "201" ]; then
    TRANSACTION_ID=$(json_get "$TXN_BODY" "transaction_id")
    pass_test "POS-03"
  else
    fail_test "POS-03" "create transaction failed (HTTP $TXN_CODE)"
  fi
  fi
else
  warn_test "POS-03" "skipped - missing employee token or shift"
fi

# POS-04 Thermal receipt
if [ -n "$EMPLOYEE_TOKEN" ] && [ -n "$TRANSACTION_ID" ]; then
  THERM_RESP=$(api_call "GET" "/pos/transactions/$TRANSACTION_ID/receipt/thermal?width=58" "" "$EMPLOYEE_TOKEN")
  THERM_CODE=$(get_http_code "$THERM_RESP")
  if [ "$THERM_CODE" = "200" ]; then
    pass_test "POS-04"
  else
    fail_test "POS-04" "thermal receipt failed (HTTP $THERM_CODE)"
  fi
else
  warn_test "POS-04" "skipped - missing transaction"
fi

# POS-05 HTML receipt
if [ -n "$EMPLOYEE_TOKEN" ] && [ -n "$TRANSACTION_ID" ]; then
  HTML_RESP=$(api_call "GET" "/pos/transactions/$TRANSACTION_ID/receipt/html" "" "$EMPLOYEE_TOKEN")
  HTML_CODE=$(get_http_code "$HTML_RESP")
  if [ "$HTML_CODE" = "200" ]; then
    pass_test "POS-05"
  else
    fail_test "POS-05" "html receipt failed (HTTP $HTML_CODE)"
  fi
else
  warn_test "POS-05" "skipped - missing transaction"
fi

# -----------------------------
# ADMIN
# -----------------------------
print_section "ADMIN"

ADMIN_LOGIN_DATA=$(cat <<EOF
{
  "email": "$ADMIN_EMAIL",
  "password": "$ADMIN_PASSWORD"
}
EOF
)
ADMIN_LOGIN_RESP=$(api_call "POST" "/auth/employee/login" "$ADMIN_LOGIN_DATA" "")
ADMIN_LOGIN_CODE=$(get_http_code "$ADMIN_LOGIN_RESP")
ADMIN_LOGIN_BODY=$(get_body "$ADMIN_LOGIN_RESP")

if [ "$ADMIN_LOGIN_CODE" = "200" ]; then
  ADMIN_TOKEN=$(json_get "$ADMIN_LOGIN_BODY" "access_token")
  pass_test "ADM-01"
else
  fail_test "ADM-01" "admin login failed (HTTP $ADMIN_LOGIN_CODE)"
fi

# ADM-02 Dashboard metrics (correct route)
if [ -n "$ADMIN_TOKEN" ]; then
  METRICS_RESP=$(api_call "GET" "/admin/dashboard/metrics?period=today" "" "$ADMIN_TOKEN")
  METRICS_CODE=$(get_http_code "$METRICS_RESP")
  if [ "$METRICS_CODE" = "200" ]; then
    pass_test "ADM-02"
  else
    fail_test "ADM-02" "dashboard metrics failed (HTTP $METRICS_CODE)"
  fi
else
  warn_test "ADM-02" "skipped - missing admin token"
fi

# ADM-03 Add order tracking + fetch tracking
if [ -n "$ADMIN_TOKEN" ] && [ -n "$ORDER_ID" ]; then
  TRACK_DATA=$(cat <<EOF
{
  "tracking_number": "UAT-$RUN_ID",
  "carrier": "DHL Express",
  "estimated_delivery": "2025-12-31",
  "notes": "UAT tracking set"
}
EOF
)
  TRACK_ADD_RESP=$(api_call "POST" "/admin/orders/$ORDER_ID/tracking" "$TRACK_DATA" "$ADMIN_TOKEN")
  TRACK_ADD_CODE=$(get_http_code "$TRACK_ADD_RESP")
  if [ "$TRACK_ADD_CODE" = "200" ]; then
    pass_test "ADM-03A"
  else
    fail_test "ADM-03A" "add tracking failed (HTTP $TRACK_ADD_CODE)"
  fi

  TRACK_GET_RESP=$(api_call "GET" "/admin/orders/$ORDER_ID/tracking" "" "$ADMIN_TOKEN")
  TRACK_GET_CODE=$(get_http_code "$TRACK_GET_RESP")
  if [ "$TRACK_GET_CODE" = "200" ]; then
    pass_test "ADM-03B"
  else
    fail_test "ADM-03B" "get tracking failed (HTTP $TRACK_GET_CODE)"
  fi
else
  warn_test "ADM-03" "skipped - missing admin token or order id"
fi

print_summary
