# Admin Dashboard Error Fix Plan

## Errors Identified from Backend Logs & Browser Console

### 1. Order/Customer Management Errors
**Error**: `'Order' object has no attribute 'total_amount'` and `'payment_method'`
**Location**: `backend/routes/admin_routes.py` - get_orders() and get_customers()
**Root Cause**: Trying to access `order.total_amount` and `order.payment_method` which don't exist
**Fix**: Use `order.total` and `order.payment.payment_method` (relationship access)
**Status**: Known issue from previous session - needs to be fixed

### 2. Sales Report SQL Error
**Error**: `(psycopg2.errors.UndefinedTable) missing FROM-clause entry for table "orders"`
**SQL**:
```sql
SELECT categories.name AS categories_name, sum(order_items.quantity) AS units_sold, sum(order_items.total_price) AS revenue
FROM categories JOIN order_items ON orders.id = order_items.order_id JOIN products ON order_items.product_id = products.id JOIN categories ON products.category_id = categories.id, orders
WHERE orders.created_at >= %(created_at_1)s AND orders.created_at < %(created_at_2)s AND orders.status != %(status_1)s GROUP BY categories.name ORDER BY revenue DESC
```
**Root Cause**: Old-style cross join syntax `FROM categories ..., orders` without proper JOIN
**Fix**: Need to properly JOIN orders table
**Status**: SQL query needs to be corrected in report service

### 3. Stock Adjustment CORS/404 Error
**Error**: `XMLHttpRequest cannot load http://localhost:5001/api/admin/inventory/undefined/stock`
**Root Cause**: Frontend passing `undefined` as variant_id
**Fix**: AdminInventory.js `handleStockAdjustment()` needs to use correct ID field
**Status**: Frontend fix needed

### 4. Settings Endpoints (404 CORS Preflight)
**Errors**:
- `Preflight response is not successful. Status code: 404` for:
  - `/api/admin/settings/business`
  - `/api/admin/settings/notification`
  - `/api/admin/settings/store`
**Root Cause**: These endpoints don't exist in backend
**Fix**: Need to create these missing endpoints or remove frontend calls
**Status**: Backend endpoints missing

### 5. Customer Orders Endpoint
**Error**: `Failed to fetch customer orders: Error: An error occurred`
**Root Cause**: Likely same as #1 - trying to access wrong Order attributes
**Fix**: Update customerAPI or admin routes
**Status**: Related to #1

### 6. Customer Anonymize Endpoint
**Error**: 400 BAD REQUEST on `/api/admin/customers/:id/anonymize`
**Root Cause**: Need to check backend implementation and required parameters
**Fix**: Debug anonymize endpoint
**Status**: Needs investigation

### 7. Employee & Promotion 400 Errors
**Error**: Various 400 errors on GET requests
**Root Cause**: Likely service errors or missing data handling
**Fix**: Check service implementations
**Status**: Needs investigation

---

## Fix Priority Order

### Priority 1: Critical Blocking Issues
1. ✅ Orders endpoint - Fix `order.total_amount` → `order.total`
2. ✅ Customers endpoint - Fix Order attribute access
3. ⏳ Sales Report - Fix SQL query JOIN syntax
4. ⏳ Stock Adjustment - Fix undefined variant_id

### Priority 2: Missing Endpoints
5. ⏳ Settings endpoints (business, notification, store)

### Priority 3: Data Validation
6. ⏳ Customer anonymize endpoint
7. ⏳ Employee/Promotion endpoints

---

## Fix Implementation Details

### Fix 1: Orders Endpoint (backend/routes/admin_routes.py)
**Line**: ~433-600 (get_orders function)
**Current Code**:
```python
order.total_amount  # WRONG
order.payment_method  # WRONG
```
**Fixed Code**:
```python
order.total  # CORRECT
order.payment.payment_method if order.payment else None  # CORRECT
order.payment.status if order.payment else 'unknown'  # CORRECT
```

### Fix 2: Customers Endpoint (backend/routes/admin_routes.py)
**Location**: get_customers() function
**Issue**: Same as Fix 1 - iterating through customer orders
**Fix**: Update Order attribute access

### Fix 3: Sales Report SQL
**Location**: backend/services/report_service.py (likely)
**Current**: Uses old-style cross join
**Fixed**: Proper INNER JOIN syntax

### Fix 4: Stock Adjustment Frontend
**Location**: frontend/src/pages/admin/AdminInventory.js
**Function**: handleStockAdjustment()
**Current Code**:
```javascript
await adminAPI.updateStock(currentProduct.id, {...})  // WRONG - undefined
```
**Fixed Code**:
```javascript
await adminAPI.updateStock(currentProduct.variant_id, {...})  // CORRECT
```

### Fix 5: Settings Endpoints
**Options**:
A. Create missing endpoints in backend
B. Remove frontend calls to non-existent endpoints
C. Use existing `/api/admin/settings` with query params

**Recommendation**: Option C - consolidate settings into one endpoint

---

## Testing Checklist

After fixes:
- [ ] GET /api/admin/orders - Should return orders without errors
- [ ] GET /api/admin/customers - Should return customers with order totals
- [ ] GET /api/admin/reports/sales - Should return sales data
- [ ] PUT /api/admin/inventory/:variant_id/stock - Should update stock
- [ ] GET /api/admin/settings - Should return all settings
- [ ] POST /api/admin/customers/:id/anonymize - Should anonymize customer
- [ ] GET /api/admin/employees - Should return employees
- [ ] GET /api/admin/promotions - Should return promotions

---

## Expected Results

✅ All admin dashboard pages load without errors
✅ Order list displays correctly with totals
✅ Customer list shows order counts and totals
✅ Sales reports generate without SQL errors
✅ Stock adjustments work with correct variant IDs
✅ Settings page loads all tabs
✅ No CORS preflight 404 errors
✅ No 400 BAD REQUEST errors on valid requests
