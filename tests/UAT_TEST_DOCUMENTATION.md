# UAT Comprehensive Test Suite Documentation

## Overview

The comprehensive UAT test suite (`uat_comprehensive_tests.sh`) provides end-to-end testing for the Happy Place Webstore across three critical user journeys:

1. **Customer Journey** (12 tests) - Online shopping experience
2. **Employee Journey** (15 tests) - POS operations and shift management  
3. **Admin Journey** (20 tests) - System administration and management

**Total Tests: 47**

## Prerequisites

### System Requirements
- Bash shell (macOS/Linux)
- Python 3.x (for JSON parsing)
- curl (for API requests)
- Running Happy Place backend API at `http://127.0.0.1:5001/api`

### Database Setup
Ensure the following test accounts exist:
- **Manager Account**: `manager@happyplace.co.ke` / `manager123`
- **Admin Account**: `admin@happyplace.co.ke` / `admin123`

## Running the Tests

### Basic Usage

```bash
# Run all tests
cd /path/to/happy_place_webstore
./tests/uat_comprehensive_tests.sh
```

### Custom Base URL

```bash
# Test against different environment
BASE_URL=http://localhost:5000/api ./tests/uat_comprehensive_tests.sh
```

### Output Format

The test suite provides color-coded output:
- ✅ **Green (PASS)** - Test passed successfully
- ❌ **Red (FAIL)** - Test failed
- ⚠️  **Yellow (WARN)** - Test skipped or non-critical issue

## Test Journey Details

### Customer Journey (TC-CUST-01 to TC-CUST-12)

Tests the complete online shopping experience from registration to wishlist management.

#### TC-CUST-01: Customer Registration with GDPR
- **Endpoint**: `POST /api/auth/customer/register`
- **Purpose**: Verify customer can register with GDPR consent
- **Validates**: 
  - Email uniqueness
  - Password requirements
  - GDPR consent requirement
  - JWT token generation

#### TC-CUST-02: Customer Login
- **Endpoint**: `POST /api/auth/customer/login`
- **Purpose**: Authenticate existing customer
- **Validates**:
  - Credential verification
  - Token generation
  - User session creation

#### TC-CUST-03: Browse Products by Category
- **Endpoint**: `GET /api/products?page=1&per_page=12`
- **Purpose**: Retrieve product catalog
- **Validates**:
  - Product listing
  - Pagination
  - Product data structure

#### TC-CUST-04: Search Products
- **Endpoint**: `GET /api/products?search=dress`
- **Purpose**: Test product search functionality
- **Validates**:
  - Search query processing
  - Result filtering
  - Relevance sorting

#### TC-CUST-05: View Product Details with Variants
- **Endpoint**: `GET /api/products/{slug}`
- **Purpose**: Display product with size/color variants
- **Validates**:
  - Product detail retrieval
  - Variant information
  - Inventory availability
  - Images and descriptions

#### TC-CUST-06: Add Items to Cart
- **Endpoint**: `POST /api/cart/items`
- **Purpose**: Add product variant to shopping cart
- **Validates**:
  - Cart item creation
  - Quantity handling
  - Inventory reservation
  - Cart total calculation

#### TC-CUST-07: Update Cart Quantities
- **Endpoint**: `PATCH /api/cart/items/{variant_id}`
- **Purpose**: Modify item quantities in cart
- **Validates**:
  - Quantity updates
  - Inventory checks
  - Cart recalculation
  - Minimum/maximum quantity rules

#### TC-CUST-08: Calculate Shipping Costs
- **Endpoint**: `POST /api/orders/shipping-preview`
- **Purpose**: Preview shipping costs before checkout
- **Validates**:
  - Nairobi free shipping (KSh 0)
  - Upcountry shipping calculation
  - Weight-based pricing
  - Free shipping threshold (KSh 5000+)

#### TC-CUST-09: Checkout and Create Order
- **Endpoint**: `POST /api/orders`
- **Purpose**: Complete purchase and create order
- **Validates**:
  - Order creation
  - Address validation
  - Payment processing
  - Order number generation
  - Cart clearing
  - Inventory deduction

#### TC-CUST-10: View Order History
- **Endpoint**: `GET /api/orders?page=1&per_page=10`
- **Purpose**: Retrieve customer's past orders
- **Validates**:
  - Order listing
  - Order details
  - Status tracking
  - Pagination

#### TC-CUST-11: Add Items to Wishlist
- **Endpoint**: `POST /api/wishlist`
- **Purpose**: Save items for later
- **Validates**:
  - Wishlist creation
  - Duplicate prevention
  - Customer association

#### TC-CUST-12: View Wishlist
- **Endpoint**: `GET /api/wishlist`
- **Purpose**: Display saved wishlist items
- **Validates**:
  - Wishlist retrieval
  - Product availability check
  - Price updates

---

### Employee Journey (TC-EMP-01 to TC-EMP-15)

Tests POS operations, shift management, and cashier workflows.

#### TC-EMP-01: Employee Login
- **Endpoint**: `POST /api/auth/employee/login`
- **Purpose**: Authenticate staff member
- **Validates**:
  - Employee credentials
  - Role-based access
  - JWT token with employee claims

#### TC-EMP-02: Check Current Shift
- **Endpoint**: `GET /api/pos/shifts/current`
- **Purpose**: Verify if shift is already open
- **Validates**:
  - Active shift detection
  - Shift status retrieval
  - Employee-shift association

#### TC-EMP-03: Start POS Shift with Opening Float
- **Endpoint**: `POST /api/pos/shifts/start`
- **Purpose**: Begin cashier shift with starting cash
- **Validates**:
  - Shift creation
  - Opening float recording
  - Store location assignment
  - Single active shift per employee

#### TC-EMP-04: Search Products by SKU
- **Endpoint**: `GET /api/products?search=FMD`
- **Purpose**: Find products quickly for POS
- **Validates**:
  - SKU-based search
  - Quick product lookup
  - Variant identification

#### TC-EMP-05: Scan Barcode (Simulated)
- **Endpoint**: `GET /api/products?sku=FMD-S-BLUE`
- **Purpose**: Simulate barcode scanner input
- **Validates**:
  - Exact SKU match
  - Product retrieval
  - Inventory check

#### TC-EMP-06: Create POS Transaction
- **Endpoint**: `POST /api/pos/transactions`
- **Purpose**: Process in-store sale
- **Validates**:
  - Transaction creation
  - Multi-item support
  - Payment processing
  - Inventory deduction
  - Receipt generation

#### TC-EMP-07: Process Cash Payment
- **Purpose**: Validate cash handling
- **Validates**:
  - Cash tendered amount
  - Change calculation
  - Cash drawer tracking

#### TC-EMP-08: Generate Thermal Receipt (58mm)
- **Endpoint**: `GET /api/pos/transactions/{id}/receipt/thermal?width=58`
- **Purpose**: Print receipt for customer
- **Validates**:
  - Receipt formatting
  - 58mm width compliance
  - Store branding
  - Transaction details

#### TC-EMP-09: Generate HTML Receipt
- **Endpoint**: `GET /api/pos/transactions/{id}/receipt/html`
- **Purpose**: Email/digital receipt generation
- **Validates**:
  - HTML formatting
  - Responsive design
  - Complete transaction details

#### TC-EMP-10: Record Cash Movement
- **Endpoint**: `POST /api/pos/cash-movements`
- **Purpose**: Track cash additions/removals
- **Validates**:
  - Cash in/out recording
  - Reason documentation
  - Audit trail
  - Shift balance updates

#### TC-EMP-11: Get Shift Summary
- **Endpoint**: `GET /api/pos/shifts/{id}`
- **Purpose**: View shift performance metrics
- **Validates**:
  - Transaction count
  - Total sales
  - Cash movements
  - Expected vs actual cash

#### TC-EMP-12: View All Transactions in Shift
- **Endpoint**: `GET /api/pos/shifts/{id}/transactions`
- **Purpose**: List all shift transactions
- **Validates**:
  - Transaction listing
  - Payment methods
  - Void status
  - Timestamps

#### TC-EMP-13: Close Shift with Reconciliation
- **Endpoint**: `POST /api/pos/shifts/{id}/close`
- **Purpose**: End shift and reconcile cash
- **Validates**:
  - Shift closure
  - Cash reconciliation
  - Variance calculation
  - Final reporting

#### TC-EMP-14: Manager Void Transaction
- **Endpoint**: `POST /api/pos/transactions/{id}/void`
- **Purpose**: Cancel transaction (manager only)
- **Validates**:
  - Manager permission check
  - Void reason requirement
  - Inventory restoration
  - Audit trail

#### TC-EMP-15: Get Employee Performance Metrics
- **Endpoint**: `GET /api/pos/employee/metrics`
- **Purpose**: View personal performance
- **Validates**:
  - Sales statistics
  - Transaction counts
  - Average sale value

---

### Admin Journey (TC-ADM-01 to TC-ADM-20)

Tests system administration, reporting, and management functions.

#### TC-ADM-01: Admin Login
- **Endpoint**: `POST /api/auth/employee/login`
- **Purpose**: Authenticate system administrator
- **Validates**:
  - Admin credentials
  - Full system access
  - Admin role verification

#### TC-ADM-02: Get Dashboard Metrics
- **Endpoint**: `GET /api/admin/dashboard`
- **Purpose**: Display key business metrics
- **Validates**:
  - Today's sales
  - Order counts
  - Low stock alerts
  - Customer count
  - Pending returns

#### TC-ADM-03: List All Employees
- **Endpoint**: `GET /api/admin/employees`
- **Purpose**: View employee directory
- **Validates**:
  - Employee listing
  - Role information
  - Active status
  - Contact details

#### TC-ADM-04: Create Employee
- **Endpoint**: `POST /api/admin/employees`
- **Purpose**: Add new staff member
- **Validates**:
  - Employee creation
  - Password hashing
  - Role assignment
  - Email uniqueness

#### TC-ADM-05: Update Employee
- **Endpoint**: `PATCH /api/admin/employees/{id}`
- **Purpose**: Modify employee details
- **Validates**:
  - Profile updates
  - Role changes
  - Active status toggle

#### TC-ADM-06: List Customers with GDPR Compliance
- **Endpoint**: `GET /api/admin/customers?page=1&per_page=10`
- **Purpose**: View customer database
- **Validates**:
  - Customer listing
  - GDPR compliance
  - Access logging
  - Data encryption

#### TC-ADM-07: View Customer Details
- **Endpoint**: `GET /api/admin/customers/{id}`
- **Purpose**: Access customer PII
- **Validates**:
  - PII decryption
  - GDPR access logging
  - Complete customer data
  - Order history

#### TC-ADM-08: Create Product with Variants
- **Endpoint**: `POST /api/admin/products`
- **Purpose**: Add new product to catalog
- **Validates**:
  - Product creation
  - Multi-variant support
  - Initial inventory
  - Category assignment

#### TC-ADM-09: Update Product
- **Endpoint**: `PATCH /api/admin/products/{id}`
- **Purpose**: Modify product details
- **Validates**:
  - Product updates
  - Price changes
  - Status changes
  - Image management

#### TC-ADM-10: Update Inventory
- **Endpoint**: `PATCH /api/variants/{id}/inventory`
- **Purpose**: Adjust stock levels
- **Validates**:
  - Inventory updates
  - Set/add/subtract operations
  - Low stock detection
  - Audit trail

#### TC-ADM-11: List All Orders
- **Endpoint**: `GET /api/admin/orders?page=1&per_page=20`
- **Purpose**: View complete order history
- **Validates**:
  - Order listing
  - Status filtering
  - Date range filtering
  - Customer information

#### TC-ADM-12: Update Order Status
- **Endpoint**: `PATCH /api/admin/orders/{id}/status`
- **Purpose**: Change order state
- **Validates**:
  - Status updates
  - Valid transitions
  - Customer notifications
  - Status history

#### TC-ADM-13: View Financial Summary
- **Endpoint**: `GET /api/admin/reports/financial-summary`
- **Purpose**: Financial overview
- **Validates**:
  - Revenue totals
  - Payment methods
  - Refunds
  - Tax collection

#### TC-ADM-14: Sales Report
- **Endpoint**: `GET /api/admin/reports/sales?start_date=...&end_date=...`
- **Purpose**: Detailed sales analysis
- **Validates**:
  - Date range filtering
  - Category breakdown
  - Product performance
  - Trend analysis

#### TC-ADM-15: Inventory Report
- **Endpoint**: `GET /api/admin/reports/inventory`
- **Purpose**: Stock level analysis
- **Validates**:
  - Current inventory
  - Stock movements
  - Valuation
  - Turnover rates

#### TC-ADM-16: Low Stock Alerts
- **Endpoint**: `GET /api/admin/inventory/low-stock`
- **Purpose**: Identify reorder needs
- **Validates**:
  - Low stock detection
  - Threshold checking
  - Product details
  - Reorder suggestions

#### TC-ADM-17: Create Promotion
- **Endpoint**: `POST /api/admin/promotions`
- **Purpose**: Add discount codes
- **Validates**:
  - Promotion creation
  - Code uniqueness
  - Date validation
  - Usage limits

#### TC-ADM-18: View System Logs
- **Endpoint**: `GET /api/admin/logs?page=1&per_page=20`
- **Purpose**: Audit system activity
- **Validates**:
  - Log retrieval
  - User actions
  - Error tracking
  - Security events

#### TC-ADM-19: GDPR Data Export
- **Endpoint**: `GET /api/admin/customers/{id}/gdpr-export`
- **Purpose**: Provide customer data export
- **Validates**:
  - Complete data export
  - Encrypted data
  - Order history
  - PII inclusion

#### TC-ADM-20: System Backup Trigger
- **Endpoint**: `POST /api/admin/system/backup`
- **Purpose**: Initiate database backup
- **Validates**:
  - Backup initiation
  - Admin permissions
  - Async processing

---

## Test Data Management

### Dynamic Test Data
The suite generates unique test data to avoid conflicts:
- Customer email: `uat.test.{timestamp}@happyplace.com`
- Employee email: `uat.staff.{timestamp}@happyplace.com`
- Product SKU: `UAT-{timestamp}`
- Promotion code: `UAT{timestamp}`

### Data Persistence
- Test orders are kept for audit trail
- Test employees remain in system
- Test products can be manually cleaned
- Wishlist items are cleaned automatically

### Manual Cleanup

```sql
-- Remove UAT test products
DELETE FROM products WHERE sku LIKE 'UAT-%';

-- Remove UAT test employees  
DELETE FROM employees WHERE email LIKE 'uat.staff.%@happyplace.com';

-- Remove UAT test customers
DELETE FROM customers WHERE email LIKE 'uat.test.%@happyplace.com';
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused
```
Error: Failed to connect to http://127.0.0.1:5001/api
```
**Solution**: Ensure backend server is running:
```bash
cd backend
python app.py
```

#### 2. Authentication Failures
```
TC-EMP-01: Employee login failed (HTTP 401)
```
**Solution**: Verify test account credentials in database:
```bash
cd backend
python reset_admin_password.py
```

#### 3. Missing Dependencies
```
bash: python3: command not found
```
**Solution**: Install Python 3:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt-get install python3
```

#### 4. JSON Parsing Errors
```
KeyError: 'access_token'
```
**Solution**: Check API response format matches expected structure

#### 5. Shift Already Active
```
TC-EMP-03: Shift already active - close existing shift first
```
**Solution**: Close active shift or use different employee account

### Debug Mode

Enable verbose output:
```bash
# Add set -x to see all commands
bash -x ./tests/uat_comprehensive_tests.sh
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: UAT Tests

on: [push, pull_request]

jobs:
  uat:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Start API server
        run: |
          cd backend
          python app.py &
          sleep 10
      
      - name: Run UAT tests
        run: ./tests/uat_comprehensive_tests.sh
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: uat-results
          path: test-results/
```

## Test Coverage Summary

| Journey | Tests | Endpoints | Coverage |
|---------|-------|-----------|----------|
| Customer | 12 | 10 | E-commerce flow |
| Employee | 15 | 12 | POS operations |
| Admin | 20 | 18 | System admin |
| **Total** | **47** | **40** | **Full stack** |

## Success Criteria

The test suite considers deployment ready when:
- ✅ Pass rate ≥ 95%
- ✅ All P0 critical paths pass
- ✅ No authentication failures
- ✅ No data corruption
- ✅ Response times < 2s

## Reporting

### Test Summary
After execution, you'll see:
```
==============================================
           FINAL TEST RESULTS
==============================================

Total Tests:     47
Passed:          45 (95.7%)
Failed:          2 (4.3%)
Warnings:        3
Duration:        45s
```

### Detailed Logs
Each test provides:
- Test ID (TC-XXX-##)
- Test description
- HTTP status code
- Pass/Fail/Warn status
- Relevant IDs (order, transaction, etc.)

## Continuous Improvement

### Adding New Tests

1. Follow naming convention: `TC-{JOURNEY}-{NUMBER}`
2. Use helper functions for consistency
3. Store relevant IDs for subsequent tests
4. Add cleanup for test data
5. Document in this file

### Example New Test

```bash
# TC-CUST-13: Apply promotion code
echo "TC-CUST-13: Testing apply promotion..."
PROMO_DATA=$(cat <<EOF
{
  "promotion_code": "WELCOME10"
}
EOF
)

PROMO_RESPONSE=$(api_call "POST" "/orders/$ORDER_ID/promotions" "$PROMO_DATA" "$CUSTOMER_TOKEN")
HTTP_CODE=$(get_http_code "$PROMO_RESPONSE")

if [ "$HTTP_CODE" = "200" ]; then
    print_test_result "pass" "TC-CUST-13" "Apply promotion (HTTP $HTTP_CODE)"
else
    print_test_result "fail" "TC-CUST-13" "Apply promotion failed (HTTP $HTTP_CODE)"
fi
```

## Support

For issues or questions:
1. Check troubleshooting section
2. Review API documentation
3. Examine backend logs
4. Contact development team

---

**Last Updated**: December 4, 2024  
**Version**: 1.0.0  
**Maintained By**: Happy Place Development Team