# UAT Bug Report Template
**Day 13 - User Acceptance Testing**

**Date:** January 7, 2026
**Testing Phase:** Pre-Production UAT
**Tester:** [Your Name]
**Session:** [Session 1-4 or Test #]

---

## HOW TO USE THIS TEMPLATE

1. **Copy the bug report format below** for each bug found
2. **Number bugs sequentially** (BUG #1, BUG #2, etc.)
3. **Fill all fields** - more detail helps developers fix faster
4. **Take screenshots** - attach or paste image links
5. **Save this file** with bugs documented
6. **Prioritize** by severity for fix order

---

## BUG REPORT FORMAT

```markdown
## BUG #[number]: [One-line summary - what's broken]

**Reported:** [Date/Time]
**Tester:** [Your name]
**Affected Area:** [ ] Customer Portal  [ ] Admin Portal  [ ] Employee Portal  [ ] POS  [ ] Backend API
**Severity:** [ ] Critical  [ ] High  [ ] Medium  [ ] Low
**Related Test:** TEST #[X] - [Test name from MANUAL_TESTING_GUIDE.md]

### STEPS TO REPRODUCE
1. Navigate to...
2. Click on...
3. Enter...
4. Click...
5. Observe...

### EXPECTED RESULT
[What should happen - describe the correct behavior]

### ACTUAL RESULT
[What actually happens - describe what you see instead]

### SCREENSHOTS/LOGS
[Paste screenshot or attach file]
[Paste browser console errors if any]
[Paste backend logs if relevant]

### BROWSER/DEVICE
- Browser: [Chrome 96 / Firefox 95 / Safari 15 / Edge 96]
- OS: [Windows 10 / macOS 12 / iOS 15 / Android 12]
- Screen Size: [1920x1080 / Mobile 375x667]
- Device: [Desktop / Laptop / iPhone 12 / iPad Pro]

### REPRODUCIBILITY
[ ] Always (100%)
[ ] Often (75%)
[ ] Sometimes (50%)
[ ] Rarely (25%)
[ ] Once

### WORKAROUND (if any)
[Is there a way to complete the task despite the bug?]

### ADDITIONAL NOTES
[Any other relevant information]

---
```

---

## SEVERITY DEFINITIONS

### Critical ⛔
**Definition:** Prevents core functionality, blocks testing, causes data loss

**Examples:**
- Cannot login (all portals unusable)
- Cannot place orders (primary business function broken)
- Payment fails completely (no revenue)
- Database errors causing crashes
- Security vulnerabilities (exposed PII, no encryption)

**Action:** **STOP TESTING** - Report immediately to development team
**Fix Priority:** Must fix before any launch consideration
**Timeline:** Fix within 24 hours

---

### High ⚠️
**Definition:** Major feature broken but workaround exists

**Examples:**
- Cart items disappear after refresh (can re-add)
- Email notifications not sending (customers confused)
- M-Pesa payment fails but COD works (limits payment options)
- Admin cannot update order status (manual SQL workaround)
- Mobile layout broken (desktop works)

**Action:** Continue testing other areas, document thoroughly
**Fix Priority:** Must fix before production launch
**Timeline:** Fix within 3-5 days

---

### Medium 📋
**Definition:** Non-critical feature issue or usability problem

**Examples:**
- Search filter doesn't persist after navigation
- Product images slow to load (but they do load)
- Wishlist button sometimes needs double-click
- Dashboard metrics update slowly (but eventually load)
- Minor UI alignment issues

**Action:** Continue testing, include in bug report
**Fix Priority:** Should fix, but not blocking launch
**Timeline:** Fix within 1-2 weeks (post-launch OK)

---

### Low 🔹
**Definition:** Cosmetic issues, typos, minor improvements

**Examples:**
- Typo in button text ("Chekout" instead of "Checkout")
- Color contrast slightly off but readable
- Icon misalignment by 2px
- Console warning (not error)
- Missing alt text on decorative image

**Action:** Note in report, low priority
**Fix Priority:** Nice to have
**Timeline:** Fix when time permits (post-launch)

---

## BUG EXAMPLES

### Example 1: Critical Bug

```markdown
## BUG #1: Cannot complete checkout - 500 error on order submission

**Reported:** 2026-01-07 14:35
**Tester:** John Doe
**Affected Area:** [X] Customer Portal  [ ] Admin Portal  [ ] Employee Portal  [ ] POS  [X] Backend API
**Severity:** [X] Critical  [ ] High  [ ] Medium  [ ] Low
**Related Test:** TEST #4 - Checkout Cash on Delivery

### STEPS TO REPRODUCE
1. Navigate to http://localhost:3000
2. Login as customer@example.com
3. Add any product to cart
4. Click "Proceed to Checkout"
5. Fill in shipping address (all valid data)
6. Select "Cash on Delivery"
7. Click "Place Order"
8. Observe error

### EXPECTED RESULT
- Order should be created successfully
- User redirected to /order-confirmation
- Order confirmation email sent
- Order appears in admin panel

### ACTUAL RESULT
- Loading spinner appears for 5 seconds
- Error message: "Failed to create order. Please try again."
- Browser console shows: "POST /api/orders 500 Internal Server Error"
- User stuck on checkout page, order not created

### SCREENSHOTS/LOGS
**Browser Console:**
```
POST http://localhost:5001/api/orders 500 (Internal Server Error)
Error: Request failed with status code 500
```

**Backend Logs:**
```
[ERROR] IntegrityError: null value in column "customer_id" violates not-null constraint
DETAIL:  Failing row contains (null, null, ...)
```

### BROWSER/DEVICE
- Browser: Chrome 120
- OS: macOS 14 Sonoma
- Screen Size: 1920x1080
- Device: MacBook Pro

### REPRODUCIBILITY
[X] Always (100%)

### WORKAROUND
None - cannot complete any orders

### ADDITIONAL NOTES
This is a regression bug - orders were working in Day 5 testing. Possibly related to recent authentication changes (Day 8-10).

---
```

---

### Example 2: High Bug

```markdown
## BUG #2: Email notifications not sending after order placement

**Reported:** 2026-01-07 15:10
**Tester:** Jane Smith
**Affected Area:** [X] Customer Portal  [ ] Admin Portal  [ ] Employee Portal  [ ] POS  [X] Backend API
**Severity:** [ ] Critical  [X] High  [ ] Medium  [ ] Low
**Related Test:** TEST #4 - Checkout Cash on Delivery (Step 23)

### STEPS TO REPRODUCE
1. Complete order checkout (COD or M-Pesa)
2. Check customer email inbox
3. Wait 5 minutes
4. Observe: No email received

### EXPECTED RESULT
Customer should receive order confirmation email within 1-2 minutes containing:
- Order number
- Order items
- Total amount
- Shipping address
- Estimated delivery date

### ACTUAL RESULT
No email received. Order is created successfully (appears in admin portal) but customer never gets confirmation.

### SCREENSHOTS/LOGS
**Backend Logs:**
```
[WARNING] SMTP connection failed: [Errno 61] Connection refused
[INFO] Order created successfully: Order #1001
[ERROR] Failed to send email notification: SMTPConnectError
```

### BROWSER/DEVICE
- Browser: N/A (backend issue)
- OS: Ubuntu Server 22.04
- Backend: Flask development server

### REPRODUCIBILITY
[X] Always (100%)

### WORKAROUND
Manual workaround:
1. Admin can call customer to confirm order
2. Admin can manually send email using third-party service
3. Customer can check order status in their account

### ADDITIONAL NOTES
SMTP service configured in .env but connection failing. Possible causes:
- SMTP credentials incorrect
- Email service (Gmail/SendGrid) blocking connection
- Firewall blocking port 587
- Need to verify backend/.env SMTP settings
```

---

### Example 3: Medium Bug

```markdown
## BUG #3: Product search doesn't handle special characters

**Reported:** 2026-01-07 15:45
**Tester:** Alex Johnson
**Affected Area:** [X] Customer Portal  [ ] Admin Portal  [ ] Employee Portal  [ ] POS  [ ] Backend API
**Severity:** [ ] Critical  [ ] High  [X] Medium  [ ] Low
**Related Test:** TEST #1 - Browse Products (Step 8)

### STEPS TO REPRODUCE
1. Navigate to http://localhost:3000/products
2. In search bar, type: "women's dress"
3. Press Enter
4. Observe results

### EXPECTED RESULT
Search should find all dresses, ignoring apostrophe

### ACTUAL RESULT
No results found. Search appears to be too strict with special characters.

### SCREENSHOTS/LOGS
Screenshot shows search bar with "women's dress" and "No products found" message.

### BROWSER/DEVICE
- Browser: Firefox 120
- OS: Windows 11
- Screen Size: 1366x768

### REPRODUCIBILITY
[X] Always (100%)

### WORKAROUND
Search without apostrophe: "womens dress" - works fine

### ADDITIONAL NOTES
Also tested:
- "dress" → Works ✓
- "women" → Works ✓
- "women's" → No results ✗
- "maternity&wear" → No results ✗

Suggest improving search to strip special characters or use fuzzy matching.
```

---

### Example 4: Low Bug

```markdown
## BUG #4: Typo in checkout button text

**Reported:** 2026-01-07 16:00
**Tester:** Chris Lee
**Affected Area:** [X] Customer Portal  [ ] Admin Portal  [ ] Employee Portal  [ ] POS  [ ] Backend API
**Severity:** [ ] Critical  [ ] High  [ ] Medium  [X] Low
**Related Test:** TEST #4 - Checkout (Step 14)

### STEPS TO REPRODUCE
1. Go to checkout page
2. Observe button text

### EXPECTED RESULT
Button should say: "Place Order"

### ACTUAL RESULT
Button says: "Plase Order" (typo: missing "c")

### SCREENSHOTS/LOGS
[Screenshot of button with typo]

### BROWSER/DEVICE
- Browser: All browsers
- OS: All
- Component: frontend-customer/src/pages/Checkout.js (line 245)

### REPRODUCIBILITY
[X] Always (100%)

### WORKAROUND
N/A - purely cosmetic

### ADDITIONAL NOTES
Easy fix - one character change in component.
```

---

## TESTING SESSIONS - BUG LOG

### Session 1: Core Customer Journey (90 min)
**Tester:** [Name]
**Date/Time:** [Start - End]

**Bugs Found:**
- [ ] None
- [ ] Critical: ___
- [ ] High: ___
- [ ] Medium: ___
- [ ] Low: ___

**Notes:**
[Session summary, overall impression]

---

### Session 2: Admin Portal (60 min)
**Tester:** [Name]
**Date/Time:** [Start - End]

**Bugs Found:**
- [ ] None
- [ ] Critical: ___
- [ ] High: ___
- [ ] Medium: ___
- [ ] Low: ___

**Notes:**
[Session summary]

---

### Session 3: POS & Employee (45 min)
**Tester:** [Name]
**Date/Time:** [Start - End]

**Bugs Found:**
- [ ] None
- [ ] Critical: ___
- [ ] High: ___
- [ ] Medium: ___
- [ ] Low: ___

**Notes:**
[Session summary]

---

### Session 4: Cross-Platform (45 min)
**Tester:** [Name]
**Date/Time:** [Start - End]

**Bugs Found:**
- [ ] None
- [ ] Critical: ___
- [ ] High: ___
- [ ] Medium: ___
- [ ] Low: ___

**Notes:**
[Session summary]

---

## OVERALL UAT SUMMARY

**Total Testing Time:** ___ hours
**Total Bugs Found:** ___

**Breakdown:**
- Critical (⛔): ___ bugs
- High (⚠️): ___ bugs
- Medium (📋): ___ bugs
- Low (🔹): ___ bugs

**Pass/Fail Criteria:**
- [ ] **PASS** - 0 critical bugs, ≤2 high bugs
- [ ] **CONDITIONAL PASS** - 0 critical bugs, 3-5 high bugs (fix before launch)
- [ ] **FAIL** - Any critical bugs OR >5 high bugs

**Recommendation:**
- [ ] Ready for production deployment
- [ ] Ready after fixes (list critical/high bugs)
- [ ] Not ready - major issues need resolution

**Next Steps:**
1. [e.g., Fix BUG #1 and BUG #2]
2. [e.g., Re-test affected areas]
3. [e.g., Schedule regression test]
4. [e.g., Proceed to Week 3 deployment]

---

## ADDITIONAL FEEDBACK

### What Worked Well
-
-
-

### Areas for Improvement
-
-
-

### Performance Observations
-
-
-

### User Experience Notes
-
-
-

---

**Bug Report Template Version:** 1.0
**Created:** January 7, 2026
**For:** Happy Place Boutique Day 13 UAT
**Reference:** UAT_EXECUTION_REPORT_2026-01-07.md, MANUAL_TESTING_GUIDE.md

**Instructions:** Copy bug format above for each issue. Number sequentially. Include all details.
