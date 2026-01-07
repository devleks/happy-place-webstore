# UAT / Evaluation Documentation (Current)

This document defines the **current** UAT/evaluation approach for the Happy Place Webstore.

## Archive Notice

Historical UAT docs, scripts, and logs (created/modified before **2025-12-15**) were moved to:

- `tests/test_bck/`

This file replaces the archived `tests/test_bck/UAT_TEST_DOCUMENTATION.md`.

## Scope: Journeys to Validate

The current evaluation is organized by real user journeys:

1. **Customer (Online Store)**
   - Browse products
   - View product + variants
   - Cart operations
   - Checkout (COD)
   - View order history
   - Track order

2. **Admin (Operations)**
   - Admin login
   - Inventory management
   - Order management
   - Add/update tracking
   - Customer management
   - Employee management

3. **Employee (Fulfillment / Operations)**
   - Employee login
   - Packing dashboard
   - Shipping dashboard

4. **POS (In-store / PWA)**
   - POS login
   - Open shift
   - Create sale
   - Receipt
   - Close shift
   - Offline queue + sync

## Test Types

- **API UAT (bash/curl)**
  - Goal: deterministic verification of backend endpoints for each journey.

- **Journey Walkthrough Checks (manual or scripted)**
  - Goal: validate UX flows and that frontends call the correct backend endpoints.

## Current Status Tracking

When new tests are created/executed, record:

- Date/time
- Branch/commit
- Environment notes (ports, DB used)
- Pass/fail summary
- Any blockers (auth, missing endpoints, etc.)

## Next Steps

- Create a fresh UAT runner for the current instance (post 2025-12-15 baseline)
- Ensure the test suite covers:
  - Auth flows for customer/employee/admin
  - Cart/wishlist endpoints
  - Admin endpoints
  - POS shift endpoints
