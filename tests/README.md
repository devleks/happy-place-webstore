# Happy Place Webstore - UAT Test Suite

Quick reference guide for running comprehensive end-to-end tests.

## Quick Start

```bash
# Make script executable (first time only)
chmod +x tests/uat_comprehensive_tests.sh

# Run all tests
./tests/uat_comprehensive_tests.sh
```

## What Gets Tested

### 🛍️ Customer Journey (12 tests)
- Registration & Login
- Product browsing & search
- Shopping cart operations
- Shipping calculation
- Order checkout
- Order history
- Wishlist management

### 💼 Employee Journey (15 tests)
- Employee authentication
- POS shift management
- Product scanning & search
- Transaction processing
- Cash handling
- Receipt generation (thermal & HTML)
- Shift reconciliation
- Manager operations (void transactions)

### 👨‍💼 Admin Journey (20 tests)
- Admin authentication
- Dashboard metrics
- Employee management
- Customer management (GDPR compliant)
- Product & inventory management
- Order management
- Financial reporting
- System administration

## Total Coverage

- **47 automated tests**
- **3 user journeys**
- **~45 second execution time**
- **Full API endpoint coverage**

## Prerequisites

✅ Backend API running at `http://127.0.0.1:5001/api`  
✅ Python 3.x installed  
✅ Test accounts configured:
   - Manager: `manager@happyplace.co.ke` / `manager123`
   - Admin: `admin@happyplace.co.ke` / `admin123`

## Expected Output

```
==============================================
  HAPPY PLACE WEBSTORE - UAT TEST SUITE
==============================================

[CUSTOMER JOURNEY - 12 tests]
✅ PASS: TC-CUST-01 - Customer registration with GDPR
✅ PASS: TC-CUST-02 - Customer login
...

[EMPLOYEE JOURNEY - 15 tests]
✅ PASS: TC-EMP-01 - Employee login
...

[ADMIN JOURNEY - 20 tests]
✅ PASS: TC-ADM-01 - Admin login
...

==============================================
           FINAL TEST RESULTS
==============================================

Total Tests:     47
Passed:          45 (95.7%)
Failed:          2 (4.3%)
Warnings:        3
Duration:        45s

✅ ALL TESTS PASSED!
```

## Custom Configuration

```bash
# Test against different API
BASE_URL=http://localhost:5000/api ./tests/uat_comprehensive_tests.sh

# Test against staging
BASE_URL=https://staging-api.happyplace.com/api ./tests/uat_comprehensive_tests.sh
```

## Troubleshooting

### Backend Not Running
```bash
cd backend
python app.py
```

### Authentication Failures
```bash
cd backend
python reset_admin_password.py
```

### View Detailed Logs
```bash
bash -x ./tests/uat_comprehensive_tests.sh 2>&1 | tee test-output.log
```

## Documentation

📖 **Full Documentation**: See [`UAT_TEST_DOCUMENTATION.md`](./UAT_TEST_DOCUMENTATION.md) for:
- Detailed test descriptions
- API endpoint mapping
- Test data management
- CI/CD integration
- Troubleshooting guide

## File Structure

```
tests/
├── README.md                      # This file (quick start)
├── UAT_TEST_DOCUMENTATION.md      # Full documentation
└── uat_comprehensive_tests.sh     # Main test suite
```

## Key Features

✨ **Comprehensive Coverage** - Tests all critical user journeys  
✨ **Color-Coded Output** - Easy to read pass/fail indicators  
✨ **Dynamic Test Data** - Avoids conflicts with unique timestamps  
✨ **Proper Cleanup** - Removes temporary test data  
✨ **Detailed Reporting** - Clear success metrics and error messages  
✨ **CI/CD Ready** - Exit codes for automation integration  

## Success Criteria

Tests pass when:
- ✅ Pass rate ≥ 95%
- ✅ All critical paths succeed
- ✅ No authentication errors
- ✅ Response times acceptable

## Support

For issues or questions:
1. Check [`UAT_TEST_DOCUMENTATION.md`](./UAT_TEST_DOCUMENTATION.md)
2. Review backend logs in `backend/`
3. Verify API is accessible
4. Contact development team

---

**Version**: 1.0.0  
**Last Updated**: December 4, 2024  
**Maintained By**: Happy Place Development Team