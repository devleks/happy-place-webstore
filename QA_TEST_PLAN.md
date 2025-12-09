# Quality Assurance Test Plan
## Happy Place Boutique - Phase 6A Checkout & Order Management

**Date**: November 25, 2025
**Version**: 1.0
**Scope**: Complete end-to-end testing of e-commerce checkout flow
**Testing Environment**:
- Backend: http://127.0.0.1:5001
- Frontend: http://localhost:3000
- Database: MySQL (happy_place_db)

---

## Test Categories

### 1. User Authentication Flow
### 2. Product Browsing & Selection
### 3. Quantity Selection Validation
### 4. Shopping Cart Operations
### 5. Checkout Flow
### 6. Shipping Calculation
### 7. Order Creation
### 8. Order Confirmation Display
### 9. Order History & Filtering
### 10. Error Handling & Edge Cases
### 11. Responsive Design Testing
### 12. Performance Testing
### 13. Security Testing

---

## 1. User Authentication Flow

### TC-AUTH-01: User Registration
**Objective**: Verify new user can register successfully
**Steps**:
1. Navigate to /register
2. Fill form with valid data:
   - First Name: Jane
   - Last Name: Tester
   - Email: qa.test@happyplace.com
   - Password: TestPass123!
   - Phone: +254712345678
3. Submit form
**Expected Result**:
- User registered successfully
- Redirected to login or products page
- JWT token stored in localStorage
**Priority**: HIGH

### TC-AUTH-02: User Login
**Objective**: Verify registered user can login
**Steps**:
1. Navigate to /login
2. Enter credentials
3. Submit form
**Expected Result**:
- Login successful
- JWT token stored as 'token' in localStorage
- Welcome message shows user first name
- "My Orders" link visible in header
**Priority**: HIGH

### TC-AUTH-03: Logout
**Objective**: Verify user can logout
**Steps**:
1. Login as user
2. Click Logout button
**Expected Result**:
- User logged out
- Token removed from localStorage
- Redirected to products page
- Header shows Login/Register links
**Priority**: MEDIUM

### TC-AUTH-04: Protected Route Access
**Objective**: Verify unauthenticated users cannot access protected routes
**Steps**:
1. Clear localStorage
2. Navigate to /checkout
3. Navigate to /orders
**Expected Result**:
- Redirected to /login
- Toast warning message displayed
**Priority**: HIGH

---

## 2. Product Browsing & Selection

### TC-PROD-01: View All Products
**Objective**: Verify products page displays correctly
**Steps**:
1. Navigate to /products
2. Observe product grid
**Expected Result**:
- Products displayed in grid
- Each card shows image, name, price
- Category filter works
- Products are clickable
**Priority**: HIGH

### TC-PROD-02: Product Detail View
**Objective**: Verify product detail page displays correctly
**Steps**:
1. Click on a product
2. Observe product details
**Expected Result**:
- Product image displayed
- Product name and description visible
- Price shown
- Size and color selectors visible
- Availability status shown
**Priority**: HIGH

### TC-PROD-03: Variant Selection
**Objective**: Verify variant selection updates availability
**Steps**:
1. On product detail page
2. Select different sizes
3. Select different colors
**Expected Result**:
- Availability updates based on variant
- "Add to Cart" enabled only if available
- Price may update if variant has different price
**Priority**: HIGH

---

## 3. Quantity Selection Validation

### TC-QTY-01: Default Quantity
**Objective**: Verify default quantity is 1
**Steps**:
1. Select a variant
2. Observe quantity selector
**Expected Result**:
- Quantity input shows 1
- Minus button is disabled
**Priority**: MEDIUM

### TC-QTY-02: Increase Quantity
**Objective**: Verify quantity can be increased
**Steps**:
1. Select variant with stock > 1
2. Click plus button multiple times
**Expected Result**:
- Quantity increases up to available stock
- Plus button disables at max
**Priority**: HIGH

### TC-QTY-03: Decrease Quantity
**Objective**: Verify quantity can be decreased
**Steps**:
1. Increase quantity to 3
2. Click minus button
**Expected Result**:
- Quantity decreases
- Cannot go below 1
- Minus button disables at 1
**Priority**: MEDIUM

### TC-QTY-04: Manual Input Validation
**Objective**: Verify manual quantity input validation
**Steps**:
1. Type 0 in quantity input
2. Type value > available stock
3. Type negative number
**Expected Result**:
- 0 or negative → auto-corrects to 1
- Value > stock → auto-corrects to max, shows toast warning
**Priority**: HIGH

### TC-QTY-05: Quantity Reset on Variant Change
**Objective**: Verify quantity resets when variant changes
**Steps**:
1. Set quantity to 5
2. Change size or color
**Expected Result**:
- Quantity resets to 1
**Priority**: MEDIUM

---

## 4. Shopping Cart Operations

### TC-CART-01: Add Item to Cart
**Objective**: Verify item can be added to cart
**Steps**:
1. Select variant and quantity
2. Click "Add to Cart"
**Expected Result**:
- Success toast message
- Cart count badge updates
- Item appears in cart page
**Priority**: HIGH

### TC-CART-02: View Cart
**Objective**: Verify cart displays items correctly
**Steps**:
1. Navigate to /cart
**Expected Result**:
- All cart items displayed
- Product images, names, variants shown
- Quantities correct
- Prices calculated correctly
- Subtotal and total displayed
**Priority**: HIGH

### TC-CART-03: Update Cart Item Quantity
**Objective**: Verify cart item quantity can be updated
**Steps**:
1. In cart, change item quantity
2. Observe updates
**Expected Result**:
- Quantity updates
- Item total updates
- Cart subtotal updates
- Toast confirmation shown
**Priority**: HIGH

### TC-CART-04: Remove Cart Item
**Objective**: Verify item can be removed from cart
**Steps**:
1. Click remove/delete on cart item
**Expected Result**:
- Item removed from cart
- Cart total updates
- Success message shown
**Priority**: HIGH

### TC-CART-05: Clear Cart
**Objective**: Verify entire cart can be cleared
**Steps**:
1. Click "Clear Cart" button
**Expected Result**:
- All items removed
- Empty cart message shown
- Cart count badge shows 0
**Priority**: MEDIUM

### TC-CART-06: Empty Cart State
**Objective**: Verify empty cart displays correctly
**Steps**:
1. Clear all items from cart
**Expected Result**:
- Empty cart icon/message shown
- "Continue Shopping" button visible
- No checkout button
**Priority**: LOW

---

## 5. Checkout Flow

### TC-CHECK-01: Access Checkout
**Objective**: Verify checkout page can be accessed
**Steps**:
1. Add items to cart
2. Click "Proceed to Checkout"
**Expected Result**:
- Redirected to /checkout
- Cart items shown in order summary
**Priority**: HIGH

### TC-CHECK-02: Shipping Address Validation
**Objective**: Verify shipping address form validation
**Steps**:
1. Submit form with empty fields
2. Enter invalid data (short street, invalid phone)
3. Submit valid data
**Expected Result**:
- Empty fields show "required" errors
- Invalid data shows format errors
- Valid data passes validation
**Priority**: HIGH

### TC-CHECK-03: Phone Number Validation
**Objective**: Verify Kenyan phone number validation
**Steps**:
1. Enter: 0712345678 (valid)
2. Enter: +254712345678 (valid)
3. Enter: 0612345678 (invalid - not 7 or 1)
4. Enter: 12345 (invalid - too short)
**Expected Result**:
- Valid formats accepted
- Invalid formats show error message
**Priority**: HIGH

### TC-CHECK-04: Billing Address Toggle
**Objective**: Verify "Same as shipping" checkbox works
**Steps**:
1. Uncheck "Same as shipping address"
2. Observe billing address fields
3. Check checkbox again
**Expected Result**:
- Unchecked: Billing fields appear and become required
- Checked: Billing fields hidden and not required
**Priority**: MEDIUM

### TC-CHECK-05: Order Summary Display
**Objective**: Verify order summary shows correct information
**Steps**:
1. Observe right sidebar
**Expected Result**:
- All cart items listed
- Product images shown
- Variant details visible
- Quantities correct
- Subtotal calculated
- Shipping cost displayed
- Total calculated correctly
**Priority**: HIGH

---

## 6. Shipping Calculation

### TC-SHIP-01: Nairobi Free Shipping
**Objective**: Verify Nairobi gets free shipping
**Steps**:
1. In checkout, enter city: "Nairobi"
2. Observe shipping preview
**Expected Result**:
- Shipping cost: KSh 0 (FREE)
- Free shipping badge displayed
- Delivery: 2-3 business days
**Priority**: HIGH

### TC-SHIP-02: Upcountry Shipping Cost
**Objective**: Verify upcountry shipping calculation
**Steps**:
1. Enter city: "Mombasa"
2. Observe shipping preview
**Expected Result**:
- Shipping cost: KSh 300 base + (weight * 50)
- Delivery: 5-7 business days
**Priority**: HIGH

### TC-SHIP-03: Real-time Shipping Preview
**Objective**: Verify shipping updates as city changes
**Steps**:
1. Type "Nairobi" → wait 500ms
2. Change to "Kisumu" → wait 500ms
**Expected Result**:
- Preview updates after debounce delay
- No API call on every keystroke
- Loading indicator during fetch
**Priority**: MEDIUM

### TC-SHIP-04: Shipping Preview Error Handling
**Objective**: Verify error handling for shipping preview
**Steps**:
1. Enter empty city
2. Enter invalid city
**Expected Result**:
- Empty city: No API call
- Invalid city: Error message shown
**Priority**: LOW

---

## 7. Order Creation

### TC-ORD-01: Successful Order Creation
**Objective**: Verify order can be created successfully
**Steps**:
1. Fill all required checkout fields
2. Click "Place Order"
**Expected Result**:
- HTTP 201 response
- Order created in database
- Order number generated (HP-YYYYMMDD-XXXX format)
- Cart automatically cleared
- Redirected to /order-confirmation/:orderId
**Priority**: CRITICAL

### TC-ORD-02: Order Creation with Empty Cart
**Objective**: Verify order creation fails with empty cart
**Steps**:
1. Clear cart
2. Navigate to /checkout (via URL)
3. Try to place order
**Expected Result**:
- Error message shown
- Order not created
**Priority**: HIGH

### TC-ORD-03: Order Creation Validation
**Objective**: Verify backend validates order data
**Steps**:
1. Submit order with invalid address
2. Submit order without authentication
**Expected Result**:
- Validation errors returned
- Order not created
- Error messages displayed
**Priority**: HIGH

### TC-ORD-04: Inventory Update on Order
**Objective**: Verify inventory decreases after order
**Steps**:
1. Note variant stock before order
2. Create order with quantity 2
3. Check variant stock after
**Expected Result**:
- Stock decreased by ordered quantity
- Variant availability updated
**Priority**: HIGH

### TC-ORD-05: Order Number Uniqueness
**Objective**: Verify each order gets unique number
**Steps**:
1. Create order 1
2. Create order 2
**Expected Result**:
- Both orders have different order numbers
- Format: HP-YYYYMMDD-XXXX
**Priority**: MEDIUM

---

## 8. Order Confirmation Display

### TC-CONF-01: Order Confirmation Page Load
**Objective**: Verify order confirmation displays correctly
**Steps**:
1. After successful order, observe confirmation page
**Expected Result**:
- Success checkmark animation shown
- "Order Placed Successfully!" message
- Order number displayed in gold
- Order date shown
**Priority**: HIGH

### TC-CONF-02: Order Items Display
**Objective**: Verify ordered items are shown
**Steps**:
1. Observe "Order Items" section
**Expected Result**:
- All ordered items listed
- Product images shown
- Variant details (size, color) displayed
- Quantities correct
- Item prices shown
**Priority**: HIGH

### TC-CONF-03: Shipping Address Display
**Objective**: Verify shipping address is displayed
**Steps**:
1. Observe "Shipping Address" section
**Expected Result**:
- Street, city, state, zip shown
- Phone number displayed
- Address matches what was entered
**Priority**: HIGH

### TC-CONF-04: Order Summary Sidebar
**Objective**: Verify order summary shows correct totals
**Steps**:
1. Observe right sidebar
**Expected Result**:
- Subtotal matches order items
- Shipping cost correct (Free or calculated)
- Tax shown (if applicable)
- Total calculated correctly
- Status badge displayed
**Priority**: HIGH

### TC-CONF-05: What's Next Section
**Objective**: Verify next steps guide is shown
**Steps**:
1. Observe "What's Next?" section
**Expected Result**:
- 3 steps shown (Processing, Shipping, Delivery)
- Dynamic shipping message (Nairobi vs Upcountry)
- Correct delivery timeframe shown
**Priority**: MEDIUM

### TC-CONF-06: Navigation Actions
**Objective**: Verify navigation buttons work
**Steps**:
1. Click "View Order History"
2. Go back, click "Continue Shopping"
**Expected Result**:
- First button → /orders
- Second button → /products
**Priority**: MEDIUM

### TC-CONF-07: Order Not Found Error
**Objective**: Verify error state for invalid order ID
**Steps**:
1. Navigate to /order-confirmation/99999
**Expected Result**:
- Error icon shown
- "Order Not Found" message
- "Continue Shopping" button visible
**Priority**: MEDIUM

---

## 9. Order History & Filtering

### TC-HIST-01: View Order History
**Objective**: Verify order history page displays
**Steps**:
1. Click "My Orders" in header
**Expected Result**:
- Redirected to /orders
- All customer orders listed
- Pagination shown if > 10 orders
**Priority**: HIGH

### TC-HIST-02: Order Card Information
**Objective**: Verify each order card shows correct info
**Steps**:
1. Observe order cards
**Expected Result**:
- Order number (gold color)
- Status badge (color-coded)
- Order date (formatted)
- Item count
- Shipping location (Nairobi/Upcountry)
- Total price
- Product thumbnails (first 3)
- "+X more" if > 3 items
**Priority**: HIGH

### TC-HIST-03: Filter by Status
**Objective**: Verify status filtering works
**Steps**:
1. Click "Pending" tab
2. Click "Processing" tab
3. Click "Shipped" tab
4. Click "Delivered" tab
5. Click "All Orders" tab
**Expected Result**:
- Each filter shows only matching orders
- "All Orders" shows all statuses
- Page resets to 1 on filter change
**Priority**: HIGH

### TC-HIST-04: Pagination
**Objective**: Verify pagination works
**Steps**:
1. If > 10 orders, click "Next"
2. Click "Previous"
**Expected Result**:
- Shows 10 orders per page
- Page info displays correctly
- Previous disabled on page 1
- Next disabled on last page
- Scrolls to top on page change
**Priority**: MEDIUM

### TC-HIST-05: Click to View Order
**Objective**: Verify clicking order navigates to details
**Steps**:
1. Click on any order card
**Expected Result**:
- Redirected to /order-confirmation/:orderId
- Order details displayed
**Priority**: HIGH

### TC-HIST-06: Empty Order History
**Objective**: Verify empty state for no orders
**Steps**:
1. Filter by status with no matching orders
**Expected Result**:
- Empty state icon shown
- "No Orders Found" message
- Dynamic message based on filter
- "Start Shopping" button visible
**Priority**: MEDIUM

---

## 10. Error Handling & Edge Cases

### TC-ERR-01: Network Error Handling
**Objective**: Verify app handles network errors gracefully
**Steps**:
1. Stop backend server
2. Try to create order
3. Try to fetch order history
**Expected Result**:
- Error toast messages shown
- Loading states clear
- User not left in broken state
**Priority**: HIGH

### TC-ERR-02: JWT Token Expiration
**Objective**: Verify expired token handling
**Steps**:
1. Use expired JWT token
2. Try to access protected route
**Expected Result**:
- Redirected to login
- Error message shown
- Token cleared from localStorage
**Priority**: HIGH

### TC-ERR-03: Insufficient Stock
**Objective**: Verify order fails if stock unavailable
**Steps**:
1. Add item with quantity 5
2. Reduce stock in database to 2
3. Try to place order
**Expected Result**:
- Order creation fails
- Error message explains stock issue
- Cart remains intact
**Priority**: HIGH

### TC-ERR-04: Invalid Form Submission
**Objective**: Verify form validation prevents submission
**Steps**:
1. Try to submit checkout with errors
**Expected Result**:
- Form does not submit
- Error messages shown at field level
- Focus moves to first error
**Priority**: MEDIUM

### TC-ERR-05: Duplicate Order Prevention
**Objective**: Verify user cannot submit order twice
**Steps**:
1. Click "Place Order"
2. Immediately click again
**Expected Result**:
- Button disabled during submission
- Loading state shown
- Only one order created
**Priority**: HIGH

---

## 11. Responsive Design Testing

### TC-RESP-01: Mobile View (375px)
**Objective**: Verify mobile layout works
**Test Cases**:
- Product grid: 1 column
- Product detail: Stacked layout
- Checkout: Single column, sticky summary at bottom
- Order confirmation: Single column
- Order history: Full-width cards
**Priority**: HIGH

### TC-RESP-02: Tablet View (768px)
**Objective**: Verify tablet layout works
**Test Cases**:
- Product grid: 2 columns
- Checkout: Adjusted spacing
- Order confirmation: Adjusted layout
**Priority**: MEDIUM

### TC-RESP-03: Desktop View (1024px+)
**Objective**: Verify desktop layout works
**Test Cases**:
- Product grid: 3-4 columns
- Checkout: Two columns, sticky sidebar
- Order confirmation: Two columns
- Order history: Standard cards with hover effects
**Priority**: MEDIUM

### TC-RESP-04: Touch Interactions
**Objective**: Verify touch-friendly on mobile
**Test Cases**:
- Buttons are at least 44x44px
- Form inputs are large enough
- Tap targets have adequate spacing
**Priority**: MEDIUM

---

## 12. Performance Testing

### TC-PERF-01: Page Load Times
**Objective**: Verify pages load quickly
**Test Cases**:
- Products page: < 2 seconds
- Product detail: < 1 second
- Checkout: < 2 seconds
- Order confirmation: < 1 second
**Priority**: MEDIUM

### TC-PERF-02: API Response Times
**Objective**: Verify API calls are fast
**Test Cases**:
- Product fetch: < 300ms
- Cart operations: < 200ms
- Order creation: < 500ms
- Order fetch: < 300ms
**Priority**: MEDIUM

### TC-PERF-03: Bundle Size
**Objective**: Verify production build is optimized
**Expected Result**:
- JS bundle: < 150 kB gzipped
- CSS bundle: < 20 kB gzipped
**Priority**: LOW

---

## 13. Security Testing

### TC-SEC-01: JWT Token Security
**Objective**: Verify token is properly secured
**Test Cases**:
- Token stored in localStorage (not sessionStorage)
- Token sent in Authorization header
- Token validated on backend
**Priority**: HIGH

### TC-SEC-02: Address Encryption
**Objective**: Verify addresses are encrypted in database
**Steps**:
1. Create order with address
2. Check database directly
**Expected Result**:
- Address fields are encrypted (not plaintext)
- Can be decrypted on fetch
**Priority**: HIGH

### TC-SEC-03: SQL Injection Prevention
**Objective**: Verify SQLAlchemy prevents SQL injection
**Steps**:
1. Try injecting SQL in form fields
**Expected Result**:
- Input sanitized
- No SQL executed
**Priority**: HIGH

### TC-SEC-04: XSS Prevention
**Objective**: Verify React escapes user input
**Steps**:
1. Try entering `<script>alert('XSS')</script>` in form
**Expected Result**:
- Script not executed
- Rendered as text
**Priority**: HIGH

---

## Test Execution Summary

**Total Test Cases**: 73
**Critical**: 1
**High Priority**: 47
**Medium Priority**: 21
**Low Priority**: 4

---

## Test Results Template

| Test ID | Description | Status | Notes | Tester | Date |
|---------|-------------|--------|-------|--------|------|
| TC-AUTH-01 | User Registration | ⏳ | | | |
| TC-AUTH-02 | User Login | ⏳ | | | |
| ... | ... | ... | ... | ... | ... |

**Status Codes**:
- ⏳ Not Started
- 🔄 In Progress
- ✅ Passed
- ❌ Failed
- ⚠️ Passed with Issues
- ⏭️ Skipped

---

## Bug Report Template

**Bug ID**: BUG-XXX
**Severity**: Critical / High / Medium / Low
**Test Case**: TC-XXX-XX
**Description**: [Brief description]
**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Result**: [What should happen]
**Actual Result**: [What actually happened]
**Screenshots**: [If applicable]
**Browser**: Chrome / Safari / Firefox
**Device**: Desktop / Mobile / Tablet
**Date Found**: YYYY-MM-DD
**Status**: Open / In Progress / Fixed / Closed

---

## Sign-off

**QA Lead**: _________________
**Date**: _________________
**Status**: READY FOR TESTING

---

*End of QA Test Plan*
