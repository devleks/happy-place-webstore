# Comprehensive UAT Test Plan
## Happy Place Webstore - December 8, 2025

**Version:** 2.0  
**Test Environment:** Development  
**Backend:** http://127.0.0.1:5001/api  
**Previous UAT:** December 5, 2025 (94.4% pass rate)  
**Focus:** Regression testing + Phase 10 & 11 new features

---

## Test Suite Organization

### Test Categories

1. **SMOKE** - Critical path smoke tests (15 min)
2. **REGR** - Regression tests for previously failed scenarios (30 min)
3. **AUTH** - Phase 10 authentication tests (45 min)
4. **CUST** - Customer journey tests (30 min)
5. **POS** - Employee POS system tests (45 min)
6. **ADMIN** - Phase 11 admin dashboard tests (90 min)
7. **GDPR** - GDPR compliance tests (20 min)
8. **INTEG** - End-to-end integration tests (30 min)

**Total Estimated Time:** 4 hours 45 minutes

---

## Test Case Catalog

### SMOKE Tests (Priority: P0 - BLOCKING)

#### SMOKE-001: API Health Check
**Objective:** Verify backend is running and responsive  
**Endpoint:** `GET /api/pos/health`  
**Expected:** HTTP 200, `{"status": "healthy"}`  
**Execution Time:** 5 seconds

#### SMOKE-002: Database Connectivity
**Objective:** Verify database is accessible  
**Method:** Check seeded data existence  
**Expected:** Products, employees, and customers exist  
**Execution Time:** 10 seconds

#### SMOKE-003: Customer Login
**Objective:** Verify basic customer authentication  
**Endpoint:** `POST /api/auth/customer/login`  
**Credentials:** Existing test customer  
**Expected:** HTTP 200, access_token returned  
**Execution Time:** 5 seconds

#### SMOKE-004: Employee Login
**Objective:** Verify basic employee authentication  
**Endpoint:** `POST /api/auth/employee/login`  
**Credentials:** `manager@happyplace.co.ke / manager123`  
**Expected:** HTTP 200, access_token returned  
**Execution Time:** 5 seconds

#### SMOKE-005: Admin Dashboard Access
**Objective:** Verify admin endpoints are accessible  
**Endpoint:** `GET /api/admin/dashboard/metrics`  
**Auth:** Manager token  
**Expected:** HTTP 200, metrics returned  
**Execution Time:** 5 seconds

**SMOKE GATE:** If any smoke test fails, STOP and fix before proceeding.

---

### REGR Tests (Priority: P0 - MUST FIX)

#### REGR-001: POS Transaction Creation (Previously TC-EMP-06)
**Status:** ❌ FAILED in previous UAT with HTTP 400  
**Objective:** Verify POS transaction can be created  
**Endpoint:** `POST /api/pos/transactions`  
**Prerequisites:**
- Valid employee token
- Open shift (shift_id)
- Valid variant_id with stock

**Test Data:**
```json
{
  "shift_id": <current_shift_id>,
  "payment_method": "cash",
  "items": [
    {"variant_id": <valid_id>, "quantity": 1}
  ],
  "cash_tendered": 10000
}
```

**Expected Result:**
- HTTP 201
- Returns: transaction_id, transaction_number, total, change_given
- Inventory is decremented
- Transaction appears in shift transactions

**Validation Steps:**
1. Verify transaction created
2. Check inventory was decremented
3. Verify transaction appears in `GET /api/pos/shifts/:id/transactions`
4. Verify receipt can be generated

**Critical:** This blocks all POS functionality. MUST pass.

#### REGR-002: Shift Summary Retrieval (Previously TC-EMP-11)
**Status:** ❌ FAILED in previous UAT with HTTP 404  
**Objective:** Verify shift details can be retrieved after creation  
**Endpoint:** `GET /api/pos/shifts/:id`  
**Prerequisites:**
- Create a new shift successfully
-  Note the returned shift_id

**Expected Result:**
- HTTP 200
- Returns: shift_number, employee info, store info, start_time, stats
- All fields properly populated

**Validation Steps:**
1. Start shift and capture shift_id
2. Retrieve shift by ID
3. Verify all returned fields match created shift
4. Verify aggregated stats (total_sales, transaction_count) are accurate

#### REGR-003: Shift Transactions List
**Status:** Related to REGR-001/002  
**Objective:** Verify transactions can be retrieved for a shift  
**Endpoint:** `GET /api/pos/shifts/:id/transactions`  
**Prerequisites:** Completed REGR-001 and REGR-002

**Expected Result:**
- HTTP 200
- Returns array of transactions for the shift
- Each transaction includes all required fields

---

### AUTH Tests (Phase 10 - NEW)

#### AUTH-001: Customer Registration with GDPR
**Endpoint:** `POST /api/auth/customer/register`  
**Test Data:**
```json
{
  "email": "uat.customer@test.com",
  "password": "TestPass123!",
  "first_name": "UAT",
  "last_name": "Customer",
  "phone": "+254712345678",
  "gdpr_consent": true,
  "marketing_consent": false
}
```
**Expected:** HTTP 201, customer_id returned  
**Validation:** Can login with new credentials

#### AUTH-002: Customer Login (Email/Password)
**Endpoint:** `POST /api/auth/customer/login`  
**Expected:** HTTP 200, access_token, refresh_token  
**Validation:** Token works for authenticated requests

#### AUTH-003: Customer Google OAuth (if configured)
**Endpoint:** `POST /api/auth/customer/google-oauth`  
**Note:** Requires Google OAuth credentials configured  
**Status:** Optional - skip if not configured

#### AUTH-004: Employee Login WITHOUT 2FA
**Endpoint:** `POST /api/auth/employee/login`  
**Test Data:** Employee without 2FA enabled  
**Expected:** HTTP 200, immediate access_token

#### AUTH-005: Employee Enable 2FA
**Endpoint:** `POST /api/auth/employee/enable-2fa`  
**Prerequisites:** Valid employee token  
**Expected:** HTTP 200, qr_code (base64), backup_codes array  
**Validation:** QR code is valid base64 PNG

#### AUTH-006: Employee Login WITH 2FA
**Endpoint:** `POST /api/auth/employee/login`  
**Test Data:** Employee with 2FA enabled  
**Step 1:** Login with email/password  
**Expected:** HTTP 200, `requires_2fa: true`, NO access_token  
**Step 2:** Login with TOTP code  
**Expected:** HTTP 200, access_token received

#### AUTH-007: Employee PIN Login
**Endpoint:** `POST /api/auth/employee/pin-login`  
**Test Data:** Valid 4-6 digit PIN  
**Expected:** HTTP 200, access_token (8-hour session)  
**Validation:** Token has correct expiry

#### AUTH-008: Token Refresh
**Endpoint:** `POST /api/auth/refresh`  
**Headers:** `Authorization: Bearer <refresh_token>`  
**Expected:** HTTP 200, new access_token  
**Validation:** New token works, old token still valid until expiry

#### AUTH-009: Logout Single Device
**Endpoint:** `POST /api/auth/logout`  
**Expected:** HTTP 200, token blacklisted  
**Validation:** Token no longer works for requests

#### AUTH-010: Logout All Devices
**Endpoint:** `POST /api/auth/logout-all`  
**Prerequisites:** Multiple active sessions  
**Expected:** HTTP 200, all tokens blacklisted  
**Validation:** All previous tokens fail

#### AUTH-011: List Active Sessions
**Endpoint:** `GET /api/auth/sessions`  
**Expected:** HTTP 200, array of sessions with device info  
**Validation:** Shows IP, user_agent, created_at

#### AUTH-012: Revoke Specific Session
**Endpoint:** `DELETE /api/auth/sessions/:id`  
**Expected:** HTTP 200, session revoked  
**Validation:** That specific token stops working

---

### CUST Tests (Customer Journey)

#### CUST-001: Browse Products
**Endpoint:** `GET /api/products?limit=10`  
**Expected:** HTTP 200, products array with variants

#### CUST-002: View Product Details
**Endpoint:** `GET /api/products/:slug`  
**Expected:** HTTP 200, full product details, variants, inventory

#### CUST-003: Add to Cart
**Endpoint:** `POST /api/cart/items`  
**Test Data:** Valid variant_id, quantity  
**Expected:** HTTP 201, cart item created

#### CUST-004: View Cart
**Endpoint:** `GET /api/cart`  
**Expected:** HTTP 200, cart items with totals

#### CUST-005: Update Cart Quantity
**Endpoint:** `PUT /api/cart/items/:id`  
**Test Data:** New quantity within stock limits  
**Expected:** HTTP 200, cart updated

####CUST-006: Calculate Shipping (Nairobi)
**Endpoint:** `POST /api/shipping/calculate`  
**Test Data:** `{"city": "Nairobi", "cart_id": <id>}`  
**Expected:** HTTP 200, `{"cost": 0, "delivery_time": "2-3 days"}`

#### CUST-007: Calculate Shipping (Upcountry)
**Endpoint:** `POST /api/shipping/calculate`  
**Test Data:** `{"city": "Mombasa", "cart_id": <id>}`  
**Expected:** HTTP 200, cost = 300 + (weight * 50)

#### CUST-008: Create Order
**Endpoint:** `POST /api/orders`  
**Test Data:** Complete shipping/billing address  
**Expected:** HTTP 201, order created, cart cleared  
**Validation:** 
- Order number format: `ORD-YYYYMMDD-XXXXX`
- Inventory decremented
- Order appears in history

#### CUST-009: View Order History
**Endpoint:** `GET /api/orders`  
**Expected:** HTTP 200, paginated orders list

#### CUST-010: View Order Details
**Endpoint:** `GET /api/orders/:id`  
**Expected:** HTTP 200, complete order with items and addresses

---

### POS Tests (Employee Journey)

#### POS-001: Start Shift
**Endpoint:** `POST /api/pos/shifts/start`  
**Test Data:**
```json
{
  "store_location_id": 1,
  "opening_float": 5000
}
```
**Expected:** HTTP 201, shift created with shift_number  
**Validation:** Shift number format: `YYYYMMDD-LOC1-EMP2-001`

#### POS-002: Get Current Shift
**Endpoint:** `GET /api/pos/shifts/current`  
**Expected:** HTTP 200, current open shift details

#### POS-003: Get Shift by ID
**Endpoint:** `GET /api/pos/shifts/:id`  
**Expected:** HTTP 200, shift details with stats  
**Critical:** This was REGR-002

#### POS-004: Search Products (for POS)
**Endpoint:** `GET /api/products?search=dress`  
**Expected:** HTTP 200, filtered products

#### POS-005: Create Transaction (CRITICAL)
**Endpoint:** `POST /api/pos/transactions`  
**See REGR-001 for full details**  
**This is the P0 blocker from previous UAT**

#### POS-006: Get Transaction Details
**Endpoint:** `GET /api/pos/transactions/:id`  
**Prerequisites:** Completed POS-005  
**Expected:** HTTP 200, transaction with items

#### POS-007: Generate Thermal Receipt (58mm)
**Endpoint:** `GET /api/pos/transactions/:id/receipt/thermal?width=58`  
**Expected:** HTTP 200, formatted text receipt

#### POS-008: Generate HTML Receipt
**Endpoint:** `GET /api/pos/transactions/:id/receipt/html`  
**Expected:** HTTP 200, HTML receipt

#### POS-009: Record Cash Movement (Cash Out)
**Endpoint:** `POST /api/pos/cash-movements`  
**Test Data:**
```json
{
  "shift_id": <current_shift>,
  "movement_type": "cash_out",
  "amount": 1000,
  "reason": "Bank deposit"
}
```
**Expected:** HTTP 201, movement_id returned

#### POS-010: Get Shift Transactions
**Endpoint:** `GET /api/pos/shifts/:id/transactions`  
**Expected:** HTTP 200, array of transactions

#### POS-011: Get Today's Transactions
**Endpoint:** `GET /api/pos/transactions/today`  
**Expected:** HTTP 200, all transactions for current date

#### POS-012: Void Transaction (Manager Only)
**Endpoint:** `POST /api/pos/transactions/:id/void`  
**Auth:** Manager or Admin token required  
**Test Data:** `{"void_reason": "Customer returned items"}`  
**Expected:** HTTP 200, transaction voided, inventory restored

#### POS-013: Close Shift
**Endpoint:** `POST /api/pos/shifts/:id/close`  
**Test Data:**
```json
{
  "closing_cash": 9000,
  "notes": "UAT test shift"
}
```
**Expected:** HTTP 200, shift closed with variance calculation  
**Validation:** Cash variance = closing_cash - (opening_float + sales)

---

### ADMIN Tests (Phase 11 - NEW)

#### ADMIN-001: Dashboard Metrics
**Endpoint:** `GET /api/admin/dashboard/metrics?period=today`  
**Expected:** HTTP 200, KPIs: sales, orders, customers, inventory

#### ADMIN-002: Dashboard Activity Feed
**Endpoint:** `GET /api/admin/dashboard/activity?limit=10`  
**Expected:** HTTP 200, recent activity items

#### ADMIN-003: Dashboard Alerts
**Endpoint:** `GET /api/admin/dashboard/alerts`  
**Expected:** HTTP 200, system alerts (low stock, pending orders, etc.)

#### ADMIN-004: Sales Trends
**Endpoint:** `GET /api/admin/dashboard/trends?period=week`  
**Expected:** HTTP 200, time-series sales data

#### ADMIN-005: List Inventory
**Endpoint:** `GET /api/admin/inventory?page=1&limit=20`  
**Expected:** HTTP 200, paginated product list

#### ADMIN-006: Get Product Details
**Endpoint:** `GET /api/admin/inventory/:id`  
**Expected:** HTTP 200, full product/variant details

#### ADMIN-007: Create Product
**Endpoint:** `POST /api/admin/inventory`  
**Test Data:**
```json
{
  "name": "UAT Test Product",
  "description": "Created during UAT",
  "category_id": 1,
  "price": 2999,
  "sku": "UAT-001",
  "stock_quantity": 50
}
```
**Expected:** HTTP 201, product_id and variant_id returned

#### ADMIN-008: Update Product
**Endpoint:** `PATCH /api/admin/products/:id`  
**Test Data:** `{"price": 3499, "is_active": true}`  
**Expected:** HTTP 200, product updated

#### ADMIN-009: Adjust Inventory
**Endpoint:** `POST /api/admin/inventory/adjust`  
**Test Data:**
```json
{
  "product_id": <id>,
  "quantity": -5,
  "reason": "damaged",
  "notes": "Water damage"
}
```
**Expected:** HTTP 200, inventory adjusted, logged in history

#### ADMIN-010: Bulk Update Inventory
**Endpoint:** `POST /api/admin/inventory/bulk-update`  
**Test Data:** Array of updates for multiple products  
**Expected:** HTTP 200, all updates applied

#### ADMIN-011: Get Inventory History
**Endpoint:** `GET /api/admin/inventory/:id/history`  
**Expected:** HTTP 200, audit trail of changes

#### ADMIN-012: List Orders
**Endpoint:** `GET /api/admin/orders?page=1&status=pending`  
**Expected:** HTTP 200, filtered orders list

#### ADMIN-013: Get Order Details
**Endpoint:** `GET /api/admin/orders/:id`  
**Expected:** HTTP 200, complete order with customer info

#### ADMIN-014: Update Order Status
**Endpoint:** `PUT /api/admin/orders/:id/status`  
**Test Data:** `{"status": "processing"}`  
**Expected:** HTTP 200, status updated

#### ADMIN-015: Cancel Order with Refund
**Endpoint:** `POST /api/admin/orders/:id/cancel`  
**Test Data:** `{"reason": "customer_request", "notes": "UAT test"}`  
**Expected:** HTTP 200, order cancelled, inventory restored

#### ADMIN-016: Add Order Note
**Endpoint:** `POST /api/admin/orders/:id/notes`  
**Test Data:** `{"note": "Customer called to confirm address"}`  
**Expected:** HTTP 200, note added

#### ADMIN-017: Get Order Timeline
**Endpoint:** `GET /api/admin/orders/:id/timeline`  
**Expected:** HTTP 200, chronological order events

#### ADMIN-018: List Customers
**Endpoint:** `GET /api/admin/customers?page=1&limit=20`  
**Expected:** HTTP 200, customer list with stats

#### ADMIN-019: Get Customer Details
**Endpoint:** `GET /api/admin/customers/:id`  
**Expected:** HTTP 200, profile with order count, total spent

#### ADMIN-020: Get Customer Orders
**Endpoint:** `GET /api/admin/customers/:id/orders`  
**Expected:** HTTP 200, customer's order history

#### ADMIN-021: Export Customer Data (GDPR)
**Endpoint:** `POST /api/admin/customers/:id/export`  
**Expected:** HTTP 200, JSON data export  
**Validation:** Contains all customer PII, orders, addresses

#### ADMIN-022: List Employees
**Endpoint:** `GET /api/admin/employees`  
**Expected:** HTTP 200, employee list

#### ADMIN-023: Create Employee
**Endpoint:** `POST /api/admin/employees`  
**Test Data:**
```json
{
  "email": "uat.employee@test.com",
  "full_name": "UAT Test Employee",
  "role": "cashier"
}
```
**Expected:** HTTP 201, employee created with temp password  
**Validation:** Temp password returned

#### ADMIN-024: Update Employee
**Endpoint:** `PUT /api/admin/employees/:id`  
**Test Data:** `{"role": "manager"}`  
**Expected:** HTTP 200, employee updated

#### ADMIN-025: Get Employee Performance
**Endpoint:** `GET /api/admin/employees/:id/performance?period=month`  
**Expected:** HTTP 200, sales metrics, transaction count

#### ADMIN-026: Reset Employee Password
**Endpoint:** `POST /api/admin/employees/:id/reset-password`  
**Expected:** HTTP 200, new temp password generated

#### ADMIN-027: Disable Employee 2FA
**Endpoint:** `POST /api/admin/employees/:id/disable-2fa`  
**Expected:** HTTP 200, 2FA disabled

#### ADMIN-028: List Promotions
**Endpoint:** `GET /api/admin/promotions?status=active`  
**Expected:** HTTP 200, promotions list

#### ADMIN-029: Create Promotion
**Endpoint:** `POST /api/admin/promotions`  
**Test Data:**
```json
{
  "code": "UATTEST20",
  "name": "UAT Test Promotion",
  "discount_type": "percentage",
  "discount_value": 20,
  "start_date": "2025-12-08",
  "end_date": "2025-12-31",
  "min_order_value": 1000,
  "max_uses": 100
}
```
**Expected:** HTTP 201, promotion created

#### ADMIN-030: Get Promotion Analytics
**Endpoint:** `GET /api/admin/promotions/:id/analytics`  
**Expected:** HTTP 200, usage stats, revenue impact

#### ADMIN-031: Sales Report
**Endpoint:** `GET /api/admin/reports/sales?start_date=2025-12-01&end_date=2025-12-08`  
**Expected:** HTTP 200, sales summary, trends

#### ADMIN-032: Inventory Report
**Endpoint:** `GET /api/admin/reports/inventory`  
**Expected:** HTTP 200, stock levels, turnover, low stock items

#### ADMIN-033: Customer Report
**Endpoint:** `GET /api/admin/reports/customers?period=month`  
**Expected:** HTTP 200, acquisition, retention, LTV

#### ADMIN-034: Get All Settings
**Endpoint:** `GET /api/admin/settings`  
**Expected:** HTTP 200, system settings by category

#### ADMIN-035: Update Store Settings
**Endpoint:** `PUT /api/admin/settings/store`  
**Test Data:** `{"store_name": "Happy Place Boutique (UAT)"}`  
**Expected:** HTTP 200, settings updated

---

### GDPR Tests (Compliance)

#### GDPR-001: Customer Consent Tracking
**Validation:** Registration includes `gdpr_consent` flag  
**Expected:** Consent recorded with timestamp

#### GDPR-002: Export Customer Data
**See ADMIN-021**  
**Validation:** Complete, portable JSON format

#### GDPR-003: Anonymize Customer
**Endpoint:** `POST /api/admin/customers/:id/anonymize`  
**Test Data:** `{"confirmation": "ANONYMIZE", "reason": "Customer request"}`  
**Expected:** HTTP 200, PII replaced with placeholders  
**Validation:**
- First/last name → "ANONYMIZED" / "USER"
- Email → "deleted_{id}@anonymized.local"
- Phone → NULL
- Orders preserved but anonymized

#### GDPR-004: Delete Customer
**Endpoint:** `DELETE /api/admin/customers/:id`  
**Prerequisites:** Customer has NO orders  
**Expected:** HTTP 200, account fully deleted

#### GDPR-005: Get Consent History
**Endpoint:** `GET /api/admin/customers/:id/consent-history`  
**Expected:** HTTP 200, audit trail of consent changes

---

### INTEG Tests (End-to-End)

#### INTEG-001: Complete Customer Purchase Flow
**Steps:**
1. Register new customer
2. Browse products
3. Add multiple items to cart
4. Calculate shipping
5. Create order
6. Verify order confirmation
7. Check order in history

**Validation:** All steps complete successfully

#### INTEG-002: Complete POS Sale Flow
**Steps:**
1. Employee login
2. Start shift
3. Search product
4. Create transaction
5. Generate receipt
6. Verify inventory decreased
7. Close shift

**Validation:** Complete cycle with cash reconciliation

#### INTEG-003: Admin Order Management Flow
**Steps:**
1. Admin login
2. View pending orders
3. Update order status to processing
4. Add internal note
5. Update status to shipped with tracking
6. Generate timeline
7. Send customer notification

**Validation:** All order lifecycle stages work

#### INTEG-004: Employee Management Flow
**Steps:**
1. Admin creates new employee
2. Employee receives temp password
3. Employee logs in and enables 2FA
4. Employee completes POS transaction
5. Admin views employee performance
6. Admin resets employee password

**Validation:** Complete employee lifecycle

#### INTEG-005: Promotion Usage Flow
**Steps:**
1. Admin creates promotion
2. Customer applies promo code at checkout
3. Order created with discount
4. Admin views promotion analytics
5. Admin disables promotion

**Validation:** Promotion properly applied and tracked

---

## Test Execution Guidelines

### Prerequisites Checklist
- [ ] PostgreSQL running
- [ ] Backend server running on port 5001
- [ ] All migrations applied (including 007 & 008)
- [ ] Seed data loaded
- [ ] Test credentials ready
- [ ] Database backup created

### Execution Order
1. **SMOKE** tests first (GO/NO-GO decision)
2. **REGR** tests (verify P0 fixes)
3. **AUTH** tests (Phase 10 validation)
4. **CUST** tests (customer journey)
5. **POS** tests (employee operations)
6. **ADMIN** tests (Phase 11 dashboard)
7. **GDPR** tests (compliance)
8. **INTEG** tests (end-to-end validation)

### Test Data Management
- Use consistent test customer: `uat.customer@test.com`
- Use consistent test employee: `uat.employee@test.com`
- Clean up test data after UAT completion
- Never test GDPR on real customer data

### Result Recording
For each test, record:
- ✅ PASS - Test passed completely
- ❌ FAIL - Test failed with error
- ⚠️ WARN - Test passed with minor issues
- ⏭️ SKIP - Test skipped (dependencies failed)
- 🔄 BLOCK - Test blocked by environment issue

---

## Success Criteria

### Minimum Acceptance (GO/NO-GO)
- 100% SMOKE tests pass
- 100% REGR tests pass (P0 fixes verified)
- 95%+ AUTH tests pass
- 95%+ CUST tests pass
- 90%+ POS tests pass
- 85%+ ADMIN tests pass
- 100% GDPR tests pass

### Production Ready
- No P0 or P1 defects open
- All critical business flows working
- Performance within limits
- Security validated
- GDPR compliance verified

---

**Document Version:** 2.0  
**Created:** December 8, 2025  
**Total Test Cases:** 127  
**Estimated Execution Time:** 4 hours 45 minutes  
**Status:** Ready for Implementation