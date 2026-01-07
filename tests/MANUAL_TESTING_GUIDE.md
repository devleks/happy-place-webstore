# Manual Testing Execution Guide
**Day 13 - User Acceptance Testing**

**Date:** January 7, 2026
**Duration:** 4 hours
**Purpose:** Practical guide for executing UAT manually
**Pre-requisite:** Read `UAT_EXECUTION_REPORT_2026-01-07.md` for full test scenarios

---

## QUICK START

### Before You Begin

**1. Start Backend (5 min)**
```bash
cd /Users/ml_labs/Documents/Code/cli_projects/happy_place_webstore/backend
source venv/bin/activate
python app.py
```
Wait for: `Running on http://127.0.0.1:5001`

**2. Start Customer Frontend (2 min)**
```bash
cd /Users/ml_labs/Documents/Code/cli_projects/happy_place_webstore/frontend-customer
npm start
```
Wait for: `Compiled successfully! You can now view... in the browser.`
Opens at: http://localhost:3000

**3. Start Admin Frontend (2 min)**
```bash
cd /Users/ml_labs/Documents/Code/cli_projects/happy_place_webstore/frontend-admin
PORT=3001 npm start
```
Opens at: http://localhost:3001

**4. Start POS App (optional, 2 min)**
```bash
cd /Users/ml_labs/Documents/Code/cli_projects/happy_place_webstore/pos-app
npm start
```
Opens at: http://localhost:3003

**Total Setup Time:** ~10 minutes

---

## TEST CREDENTIALS (Keep This Handy!)

**Copy these into a text file for quick reference:**

```
CUSTOMER:
Email: customer@example.com
Password: CustomerPass123!

ADMIN:
Email: admin@happyplace.com
Password: AdminPass123!

MANAGER:
Email: manager@happyplace.com
Password: ManagerPass123!

CASHIER:
Email: cashier@happyplace.com
Password: CashierPass123!

FULFILLMENT:
Email: fulfillment@happyplace.com
Password: FulfillmentPass123!
```

**Test M-Pesa Phone Number:** 254712345678 (sandbox)

---

## SESSION 1: CORE CUSTOMER JOURNEY (90 minutes)

### TEST 1: Browse Products (15 min) - PRIORITY: HIGH

**URL:** http://localhost:3000

**Steps:**
1. Open http://localhost:3000 in browser
2. ✓ Homepage loads (look for product grid/hero section)
3. Click "Shop Now" or "Products" in navigation
4. ✓ Product listing page appears
5. Count products visible (should be 20+)
6. Try category filter (Maternity, Casual, etc.)
7. ✓ Products filter correctly
8. Use search bar - type "dress"
9. ✓ Search results show dresses
10. Click any product card
11. ✓ Product detail page loads
12. ✓ See product name, price, description, images
13. ✓ See size/color variant dropdowns
14. Change variant (select different size)
15. ✓ Price updates if variants have different prices

**Expected Time:** 15 minutes
**Critical Issues to Watch:**
- Products not loading (check backend console)
- Variant selection not working
- Images not displaying

**Bug Template (if issues found):**
```
BUG #1: [Short description]
Severity: Critical/High/Medium/Low
Steps to reproduce:
1. ...
Expected: ...
Actual: ...
Screenshot: [paste or attach]
```

---

### TEST 2: Login & Add to Cart (20 min) - PRIORITY: CRITICAL

**Steps:**
1. Click "Login" in top navigation
2. Enter: `customer@example.com` / `CustomerPass123!`
3. Click "Login"
4. ✓ Redirected to homepage
5. ✓ See username in header (e.g., "Welcome, Test Customer")
6. ✓ Cart icon shows "0"
7. Browse to any product
8. Select a variant (size: M, color: Blue)
9. Click "Add to Cart"
10. ✓ Success message appears
11. ✓ Cart icon updates to "1"
12. Add another product
13. ✓ Cart icon shows "2"
14. Click cart icon
15. ✓ Cart sidebar/page opens
16. ✓ See 2 items listed with images, names, prices
17. ✓ Total price displayed correctly
18. Click "+" on first item
19. ✓ Quantity increases to 2
20. ✓ Total recalculates
21. Click "-" to decrease quantity
22. ✓ Quantity decreases
23. Click "Remove" on second item
24. ✓ Item removed from cart
25. ✓ Cart icon updates to "1"

**CRITICAL TEST - Cart Persistence:**
26. Close browser completely
27. Open new browser window
28. Go to http://localhost:3000
29. Click cart icon
30. ✓ Cart still has 1 item (localStorage persistence)

**Expected Time:** 20 minutes
**Critical Issues:**
- Login fails (check backend logs for JWT errors)
- Cart not updating (check browser console for API errors)
- Cart not persisting after browser close

---

### TEST 3: Wishlist (10 min) - PRIORITY: MEDIUM

**Steps:**
1. Browse to product detail page
2. Click heart/wishlist icon
3. ✓ Icon changes (filled/highlighted)
4. ✓ Success message: "Added to wishlist"
5. Add another product to wishlist
6. Navigate to /wishlist (or "Wishlist" in menu)
7. ✓ See 2 products in wishlist
8. Click "Add to Cart" on one item
9. ✓ Item moves to cart
10. ✓ Removed from wishlist
11. Click "Remove" on remaining item
12. ✓ "Your wishlist is empty" message

**Expected Time:** 10 minutes

---

### TEST 4: Checkout - Cash on Delivery (25 min) - PRIORITY: CRITICAL

**Prerequisites:** Have at least 1 item in cart

**Steps:**
1. Click cart icon → "Proceed to Checkout"
2. ✓ Checkout page loads
3. ✓ Cart summary visible on right (items, total)

**Fill Shipping Address:**
4. Full Name: "Test Customer"
5. Phone: "254712345678"
6. Address: "123 Test Street"
7. City: "Nairobi"
8. Postal Code: "00100"
9. ✓ Form validation works (try invalid phone, should show error)

**Select Shipping:**
10. Choose "Standard Delivery" (KSh 200)
11. ✓ Total updates to include shipping

**Select Payment:**
12. Click "Cash on Delivery" radio button
13. ✓ No payment modal appears

**Place Order:**
14. Click "Place Order" button
15. ✓ Loading spinner appears
16. Wait 2-5 seconds
17. ✓ Redirected to /order-confirmation
18. ✓ See order number (e.g., "Order #1001")
19. ✓ See "Payment: Cash on Delivery"
20. ✓ See shipping address
21. ✓ See order total
22. **CRITICAL:** Check email inbox
23. ✓ Order confirmation email received

**Verify Backend:**
24. Open admin portal (http://localhost:3001)
25. Login as admin
26. Navigate to Orders
27. ✓ New order appears in list
28. ✓ Status: "Pending" (COD orders start as Pending)

**Expected Time:** 25 minutes
**Critical Issues:**
- Order not creating (500 error - check backend logs)
- Email not sending (check SMTP configuration)
- Order missing in admin panel

---

### TEST 5: Checkout - M-Pesa Payment (20 min) - PRIORITY: HIGH

**Prerequisites:** Have items in cart, M-Pesa sandbox configured

**Steps:**
1-10. (Same as TEST 4 steps 1-10: cart, address, shipping)

**M-Pesa Payment:**
11. Click "M-Pesa" radio button
12. Enter phone: "254712345678"
13. ✓ Phone format validation (must be 254XXXXXXXXX)
14. Click "Place Order"
15. ✓ M-Pesa payment modal appears
16. ✓ Modal shows order total
17. Click "Pay with M-Pesa"
18. ✓ Loading state: "Initiating payment..."
19. ✓ Success: "STK push sent. Check your phone"

**Simulate M-Pesa Callback (Dev Mode):**
20. Check backend console for STK push log
21. Note the CheckoutRequestID
22. **Sandbox:** Payment auto-confirms in 10-30 seconds
23. ✓ Modal updates: "Payment successful!"
24. ✓ Redirected to order confirmation
25. ✓ See transaction ID

**Verify:**
26. Check email for order + payment confirmation
27. Check admin orders - status should be "Paid"

**Expected Time:** 20 minutes
**Common Issues:**
- STK push fails: Check M-Pesa credentials in backend .env
- Payment stuck: Check backend logs for callback errors
- Daraja API errors: Verify sandbox credentials

---

## SESSION 2: ADMIN PORTAL (60 minutes)

### TEST 6: Admin Dashboard (10 min) - PRIORITY: HIGH

**URL:** http://localhost:3001

**Steps:**
1. Navigate to http://localhost:3001
2. ✓ Admin login page loads
3. Enter: `admin@happyplace.com` / `AdminPass123!`
4. Click "Login"
5. ✓ Redirected to /admin/dashboard
6. ✓ See metrics cards:
   - Total Revenue (KSh amount)
   - Total Orders (number)
   - Total Customers (number)
7. ✓ See sales chart (last 7 days)
8. ✓ See recent orders table (5 latest)
9. ✓ See low stock alerts (if any)
10. Click each sidebar menu item
11. ✓ All pages load (Orders, Inventory, Customers, etc.)

**Expected Time:** 10 minutes

---

### TEST 7: Order Management (20 min) - PRIORITY: CRITICAL

**Steps:**
1. Click "Orders" in sidebar
2. ✓ Orders page loads with table
3. ✓ See all orders from TEST 4 & 5
4. ✓ Each row shows: Order #, Customer, Total, Status, Date

**Filter Orders:**
5. Click status filter dropdown
6. Select "Pending"
7. ✓ Only pending orders shown
8. Clear filter → all orders back

**View Order Details:**
9. Click any order row
10. ✓ Order details expand or modal opens
11. ✓ See customer name (decrypted PII)
12. ✓ See customer email
13. ✓ See customer phone
14. ✓ See shipping address
15. ✓ See order items with quantities
16. ✓ See order total

**Update Order Status:**
17. Find "Status" dropdown in order details
18. Change from "Pending" → "Processing"
19. Click "Save" or "Update"
20. ✓ Success message
21. ✓ Order status updates in table

**Add Tracking Number:**
22. Find "Tracking Number" input
23. Enter: "DHL123456789"
24. Select courier: "DHL"
25. Click "Update Tracking"
26. ✓ Success: "Tracking added, customer notified"
27. **CRITICAL:** Check customer email for tracking notification

**Expected Time:** 20 minutes
**Critical Issues:**
- Customer PII showing "ENCRYPTED_DATA" (decryption failed)
- Status update not saving
- Tracking email not sent

---

### TEST 8: Inventory Management (15 min) - PRIORITY: HIGH

**Steps:**
1. Click "Inventory" in sidebar
2. ✓ Inventory page loads
3. ✓ See products with stock levels
4. ✓ Low stock items highlighted (red/yellow)

**View Variant Inventory:**
5. Click any product row
6. ✓ Variant breakdown shows (S, M, L, XL)
7. ✓ Each variant shows quantity

**Update Stock:**
8. Find variant with low stock (e.g., "Dress - Size M")
9. Click edit icon or inline edit
10. Change quantity from 5 → 20
11. Click "Save"
12. ✓ Success message
13. ✓ Quantity updates
14. ✓ If was low stock, alert clears

**Stock Adjustment:**
15. Click "Adjust Stock" button
16. Enter reason: "Restocking shipment received"
17. Adjust quantity: +50
18. ✓ Stock increases by 50
19. ✓ Adjustment logged

**Expected Time:** 15 minutes

---

### TEST 9: Customer Management (10 min) - PRIORITY: MEDIUM

**Steps:**
1. Click "Customers" in sidebar
2. ✓ Customer list loads
3. ✓ See all registered customers

**Search Customer:**
4. Use search bar: enter "customer@example.com"
5. ✓ Finds customer

**View Customer Details:**
6. Click customer row
7. ✓ Customer details modal/page
8. ✓ See decrypted PII:
   - Name
   - Email
   - Phone
   - Addresses
9. ✓ See GDPR consent status
10. ✓ See order history (orders from TEST 4 & 5)

**Expected Time:** 10 minutes

---

### TEST 10: Reports (5 min) - PRIORITY: LOW

**Steps:**
1. Click "Reports" in sidebar
2. Select "Sales Report"
3. Choose date range: Last 30 days
4. Click "Generate"
5. ✓ Report displays with metrics
6. ✓ Chart shows data
7. Click "Export CSV"
8. ✓ CSV file downloads

**Expected Time:** 5 minutes

---

## SESSION 3: POS & EMPLOYEE (45 minutes)

### TEST 11: Employee Login & Fulfillment (15 min) - PRIORITY: MEDIUM

**URL:** http://localhost:3002 (Employee Portal)

**Note:** If employee portal not running, use admin portal (admin has all permissions)

**Steps:**
1. Navigate to employee portal
2. Login: `fulfillment@happyplace.com` / `FulfillmentPass123!`
3. ✓ Dashboard shows "Orders to Pick"
4. ✓ See pending orders from TEST 4

**Pick Order:**
5. Click an order
6. ✓ Picking list shows items to pick
7. Check each item checkbox
8. Click "Mark as Picked"
9. ✓ Order moves to "Packing" status
10. ✓ Removed from "To Pick" list

**Pack Order:**
11. Go to "To Pack" section
12. Click the picked order
13. Select box size: "Medium"
14. Add note: "Handle with care"
15. Click "Mark as Packed"
16. ✓ Order status → "Packed"

**Expected Time:** 15 minutes

---

### TEST 12: POS System (30 min) - PRIORITY: HIGH

**URL:** http://localhost:3003

**Steps:**
1. Navigate to http://localhost:3003
2. Login: `cashier@happyplace.com` / `CashierPass123!`

**Start Shift:**
3. ✓ "Start Shift" modal appears
4. Enter starting cash: "5000"
5. Click "Start Shift"
6. ✓ POS main screen loads
7. ✓ Product search box visible

**Create Sale:**
8. Type product name in search (or scan barcode if available)
9. ✓ Product appears in search results
10. Click product
11. ✓ Added to cart
12. Adjust quantity using +/- buttons
13. ✓ Quantity changes
14. Add another product
15. ✓ Cart shows 2 items
16. ✓ Total calculated

**Process Cash Payment:**
17. Click "Payment" button
18. ✓ Payment modal opens
19. Select "Cash"
20. Enter cash tendered: "10000"
21. ✓ Change calculated automatically
22. Click "Complete Sale"
23. ✓ Receipt displays
24. ✓ Transaction saved

**Test Offline Mode (CRITICAL for POS):**
25. Disconnect internet (Wi-Fi off)
26. ✓ "Offline" indicator appears
27. Create another sale (same steps 8-24)
28. ✓ Sale completes (saved to local SQLite)
29. ✓ "1 transaction queued" shown
30. Reconnect internet
31. ✓ "Online" indicator
32. Click "Sync Now"
33. ✓ Transaction uploads to backend
34. ✓ Queue cleared

**Close Shift:**
35. Click "Close Shift"
36. Count cash: "15000"
37. System shows expected: "15000"
38. ✓ Difference: "0" (balanced)
39. Click "Close Shift"
40. ✓ Shift report generated
41. ✓ Logged out

**Verify in Admin:**
42. Go to admin portal
43. Check Orders → should see POS transactions
44. Check Inventory → stock should be decremented

**Expected Time:** 30 minutes
**Critical Issues:**
- Offline mode not working (SQLite errors)
- Sync failing (check backend /api/pos/sync endpoint)
- Inventory not updating

---

## SESSION 4: CROSS-PLATFORM TESTING (45 minutes)

### TEST 13: Mobile Responsiveness (20 min) - PRIORITY: HIGH

**Tools:** Chrome DevTools Device Mode (F12 → Toggle Device Toolbar)

**Customer Portal (http://localhost:3000):**
1. Open DevTools (F12)
2. Click device icon (Ctrl+Shift+M)
3. Select "iPhone SE"
4. ✓ Layout responsive (no horizontal scroll)
5. ✓ Hamburger menu appears
6. ✓ Product grid 1-2 columns
7. Add item to cart on mobile
8. ✓ Buttons large enough to tap (44px min)
9. Go to checkout
10. ✓ Form fields stack vertically
11. ✓ Easy to fill on mobile
12. Switch to "iPad"
13. ✓ Layout adjusts (tablet view)

**Admin Portal (http://localhost:3001):**
14. Open in DevTools mobile mode
15. ✓ Dashboard cards stack
16. ✓ Sidebar collapses or hamburger menu
17. View orders table
18. ✓ Table scrolls horizontally OR displays as cards

**Expected Time:** 20 minutes

---

### TEST 14: Cross-Browser Testing (15 min) - PRIORITY: MEDIUM

**Browsers to Test:**
- Chrome (primary)
- Firefox
- Safari (if on Mac)
- Edge (if on Windows)

**Quick Test Per Browser:**
1. Open http://localhost:3000
2. ✓ Layout looks correct
3. Login as customer
4. ✓ Login works
5. Add to cart
6. ✓ Cart updates
7. Open browser console (F12)
8. ✓ No JavaScript errors
9. Check LocalStorage (Application tab)
10. ✓ Token and cart data stored

**Common Browser Issues:**
- Safari: Date pickers look different (OK)
- Firefox: Flexbox minor differences (OK if functional)
- Edge: Usually same as Chrome (Chromium)

**Expected Time:** 15 minutes

---

### TEST 15: Accessibility (10 min) - PRIORITY: LOW

**Keyboard Navigation:**
1. Open http://localhost:3000
2. **Don't use mouse** - only keyboard
3. Press Tab repeatedly
4. ✓ Can navigate to all links/buttons
5. ✓ Focus outline visible
6. Press Enter on "Products" link
7. ✓ Navigate to products page
8. Tab to product card, press Enter
9. ✓ Product detail opens
10. Press Esc
11. ✓ Modal closes (if product in modal)

**Screen Reader (Optional):**
- If NVDA or JAWS available, test announcements

**Expected Time:** 10 minutes

---

## BUG REPORTING

### How to Report Bugs

**Use This Format:**

```
BUG #[number]: [One-line summary]

SEVERITY: Critical | High | Medium | Low

AFFECTED AREA: Customer Portal | Admin | POS | Employee

STEPS TO REPRODUCE:
1. Go to...
2. Click...
3. Enter...
4. Observe...

EXPECTED RESULT:
What should happen

ACTUAL RESULT:
What actually happens

SCREENSHOTS/LOGS:
[Attach screenshot or paste console error]

BROWSER/DEVICE:
Chrome 96, Windows 10

RELATED TEST:
TEST #6 - Admin Dashboard
```

### Severity Guidelines

**Critical:**
- Cannot place orders
- Cannot login
- Payment fails
- Data loss
- **Action:** Stop testing, report immediately

**High:**
- Feature doesn't work but workaround exists
- Visual bugs affecting usability
- **Action:** Report at end of session

**Medium:**
- Minor functional issues
- UI inconsistencies
- **Action:** Include in final report

**Low:**
- Cosmetic issues
- Typos
- **Action:** Nice to fix but not blocking

---

## POST-TESTING CHECKLIST

After completing all tests:

### 1. Browser Console Check
- [ ] Open F12 in each portal
- [ ] Check Console tab for errors (red text)
- [ ] Screenshot any errors

### 2. Backend Logs Check
```bash
# Check backend terminal for errors
# Look for:
- 500 Internal Server Error
- Database connection errors
- JWT token errors
- M-Pesa API errors
```

### 3. Database Verification
```bash
# Verify test data exists
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -d happy_place_db

# Check order count
SELECT COUNT(*) FROM orders;

# Check customer count
SELECT COUNT(*) FROM customers;

# Check POS transactions
SELECT COUNT(*) FROM pos_transactions;
```

### 4. Documentation
- [ ] Count bugs found: Critical / High / Medium / Low
- [ ] List incomplete tests (if any)
- [ ] Note performance issues
- [ ] Suggest improvements

---

## EXPECTED OUTCOMES

### If All Tests Pass:

**YOU SHOULD SEE:**
- ✅ 2+ customer orders created
- ✅ 2+ customers in database
- ✅ 1+ POS transaction
- ✅ Cart items persisting
- ✅ Email confirmations sent
- ✅ Admin portal managing orders
- ✅ Inventory updates after sales
- ✅ No console errors
- ✅ All 4 frontends responsive

**Final Verdict:** ✅ UAT PASSED - Ready for production

### If Issues Found:

**PRIORITIZE FIXES:**
1. Critical bugs first (payment, login, data loss)
2. High bugs next (broken features)
3. Medium/Low after launch

**RE-TEST:**
- After fixes, re-run affected test scenarios
- Verify fix doesn't break other features (regression)

---

## TIME TRACKING

| Session | Time | Actual | Notes |
|---------|------|--------|-------|
| Setup | 10 min | ___ | |
| Session 1 | 90 min | ___ | Customer journey |
| Session 2 | 60 min | ___ | Admin portal |
| Session 3 | 45 min | ___ | POS & Employee |
| Session 4 | 45 min | ___ | Cross-platform |
| **TOTAL** | **4h 10m** | ___ | |

---

## QUICK REFERENCE

**Ports:**
- Backend: 5001
- Customer: 3000
- Admin: 3001
- Employee: 3002
- POS: 3003

**Test Emails:**
- Customer: customer@example.com / CustomerPass123!
- Admin: admin@happyplace.com / AdminPass123!
- Cashier: cashier@happyplace.com / CashierPass123!

**Test Phone:**
- M-Pesa: 254712345678

**Critical Checks:**
1. Login works
2. Cart persists
3. Orders create
4. Emails send
5. Payments process (COD + M-Pesa)
6. Admin can manage orders
7. POS works offline
8. Mobile responsive

---

## HELP & TROUBLESHOOTING

**Backend Not Starting:**
```bash
# Check port 5001 not in use
lsof -ti:5001 | xargs kill -9

# Restart backend
cd backend && source venv/bin/activate && python app.py
```

**Frontend Not Starting:**
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install
npm start
```

**Database Issues:**
```bash
# Verify database exists
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -l | grep happy_place

# Reset database (CAUTION: deletes data)
python backend/seed.py
```

**M-Pesa Not Working:**
- Check `backend/.env` has M-Pesa credentials
- Verify sandbox mode enabled
- Check Daraja API status

**Email Not Sending:**
- Check `backend/.env` SMTP settings
- Verify email service running
- Test with `backend/test_email.py`

---

**Manual Testing Guide Version:** 1.0
**Created:** January 7, 2026
**For:** Happy Place Boutique Day 13 UAT
**Estimated Duration:** 4 hours
**Test Coverage:** 15 test scenarios, 276 test cases

**Status:** ✅ READY FOR EXECUTION
