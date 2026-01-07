# WEEK 1 EXECUTION CHECKLIST
**Happy Place Boutique - December 26, 2025 to January 1, 2026**

**Print this page. Check boxes with pen. Hang it where you can see it.**

---

## 🎯 WEEK 1 GOAL
By January 1st: One complete test order from browse to payment to email confirmation

---

## DAY 1: Thursday December 26 ☐

### Morning: Backend Debugging
- ☐ Kill backend process: `lsof -ti:5001 | xargs kill -9`
- ☐ Backup: `cp backend/app.py backend/app.py.backup`
- ☐ Comment out middleware: NewRelic, rate limiting, custom monitoring
- ☐ Start backend: `cd backend && python app.py`
- ☐ Test: `curl http://127.0.0.1:5001/api/products`
- ☐ Response < 2 seconds? YES ☐ NO ☐

### Afternoon: Middleware Isolation
- ☐ Re-enable middleware one-by-one
- ☐ Test after each: `curl http://127.0.0.1:5001/api/products`
- ☐ Find the culprit
- ☐ Fix or permanently disable problematic middleware

### Success Criteria
- ☐ Backend responds to 5 endpoints < 2s each
- ☐ No hanging or timeout errors
- ☐ Updated DAILY_LOG.md with findings

---

## DAY 2: Friday December 27 ☐

### Morning: M-Pesa Research
- ☐ Visit https://developer.safaricom.co.ke/
- ☐ Register for sandbox account
- ☐ Get credentials: Consumer Key, Consumer Secret
- ☐ Test authentication with curl
- ☐ Read STK Push documentation

### Afternoon: Payment Abstraction
- ☐ Create `backend/services/payment_service.py`
- ☐ Add methods: `initiate_payment()`, `verify_payment()`, `handle_callback()`
- ☐ Add Payment model to database (if not exists)
- ☐ Add "Cash on Delivery" as payment option

### Success Criteria
- ☐ M-Pesa sandbox credentials working
- ☐ Payment service file created
- ☐ Can create payment record in database

---

## DAY 3: Saturday December 28 ☐

### Morning: M-Pesa Integration
- ☐ Implement STK Push in payment_service.py
- ☐ Add M-Pesa callback endpoint: `/api/payments/mpesa-callback`
- ☐ Test with sandbox phone number
- ☐ Verify payment status updates correctly

### Afternoon: End-to-End Test
- ☐ Create test order in database
- ☐ Initiate M-Pesa payment for test order
- ☐ Receive callback, update order status
- ☐ Handle payment failure gracefully

### Success Criteria
- ☐ One successful M-Pesa sandbox payment
- ☐ Order status changes to "paid" after callback
- ☐ Logged all payment attempts in database

---

## DAY 4: Sunday December 29 ☐

### Morning: Email Service Setup
- ☐ Sign up for SendGrid free tier (or Mailgun)
- ☐ Verify sender email: support@happyplace.co.ke (or use Gmail)
- ☐ Get API key
- ☐ Install: `pip install sendgrid` (or `pip install mailgun`)

### Afternoon: Email Templates
- ☐ Create `backend/templates/emails/order_confirmation.html`
- ☐ Create `backend/templates/emails/tracking_update.html`
- ☐ Create `backend/templates/emails/welcome.html`
- ☐ Create `backend/services/email_service.py`
- ☐ Add trigger: Send email on order creation

### Success Criteria
- ☐ Test email sent to real inbox
- ☐ Order confirmation template looks good
- ☐ Email service function works reliably

---

## DAY 5: Monday December 30 ☐

### Morning: Cart Backend Connection
- ☐ Review `/api/cart` endpoints (should exist per docs)
- ☐ Test endpoints: GET, POST, PUT, DELETE cart items
- ☐ Update `frontend-customer/src/services/api.js` cart methods
- ☐ Wire CartContext to use backend API

### Afternoon: Cart Badge Fix
- ☐ Update Header.js cart badge to use CartContext
- ☐ Remove hardcoded `0`
- ☐ Test: Add item, see badge update
- ☐ Test: Refresh page, badge persists

### Success Criteria
- ☐ Cart persists on page refresh
- ☐ Cart badge shows real count
- ☐ Can add/remove items via frontend

---

## DAY 6: Tuesday December 31 ☐

### Morning: Checkout Flow
- ☐ Review Checkout page: `frontend-customer/src/pages/Checkout.js`
- ☐ Wire payment selection (M-Pesa vs COD)
- ☐ Connect "Place Order" button to backend
- ☐ Add loading states during payment

### Afternoon: End-to-End Test
- ☐ Browse products as customer
- ☐ Add 3 items to cart
- ☐ Go to checkout
- ☐ Enter shipping info
- ☐ Select M-Pesa payment
- ☐ Complete payment (sandbox)
- ☐ Receive order confirmation email

### Success Criteria
- ☐ ONE complete successful test order
- ☐ Order appears in admin panel
- ☐ Email received within 60 seconds

---

## DAY 7: Wednesday January 1 ☐

### Buffer Day Tasks
- ☐ Fix any blockers from previous 6 days
- ☐ Run 5 more test orders to verify stability
- ☐ Set up staging environment (if not done)
- ☐ Deploy backend to staging server
- ☐ Deploy frontend-customer to staging
- ☐ Test staging end-to-end

### Success Criteria
- ☐ Staging environment live
- ☐ 5/5 test orders successful on staging
- ☐ No critical bugs found

---

## WEEK 1 COMPLETION CHECK ✅

### All Must Be TRUE:
- ☐ Backend responds < 2s to all endpoints
- ☐ M-Pesa sandbox integration works
- ☐ Email notifications send reliably
- ☐ Cart persists across sessions
- ☐ Checkout flow completes successfully
- ☐ At least 1 end-to-end test order successful
- ☐ DAILY_LOG.md updated every day

### Week 1 Status:
- ☐ ✅ SUCCESS - All tasks complete, moving to Week 2
- ☐ ⚠️ PARTIAL - Some tasks incomplete, extend to 5-week plan
- ☐ ❌ FAILURE - Major blockers remain, re-assess plan

---

## IF PARTIAL OR FAILURE:

**Stop. Do not proceed to Week 2.**

1. Fill out Week 1 Retrospective in DAILY_LOG.md
2. Identify the blocker that prevented completion
3. Decide:
   - ☐ Extend Week 1 tasks into Week 2 (delay launch 1 week)
   - ☐ Change approach (e.g., skip M-Pesa, launch with COD only)
   - ☐ Get help (hire freelancer for specific blocker)
4. Update RECOVERY_PLAN_2025.md with new timeline
5. Communicate new expected launch date

**Honesty now saves time later.**

---

## WEEK 2 PREVIEW (If Week 1 Successful)

**Week 2 Goal:** Security, Polish, UAT Testing

You'll work on:
- SSL certificate setup
- Security audit (SQL injection, XSS)
- Performance optimization
- Bug fixes
- UAT with real users

**Only start Week 2 if Week 1 is ✅ SUCCESS**

---

## EMERGENCY CONTACTS

**If completely stuck:**
1. Check RECOVERY_PLAN_2025.md Appendix B (Fallback options)
2. Search Stack Overflow / GitHub Issues
3. Ask in relevant Discord/Slack (Flask, React, M-Pesa communities)
4. Consider hiring Upwork freelancer for specific blocker (budget $50-200 for 4-hour fix)

**Mental health check:**
- If 3+ days of low energy (😟), take a full rest day
- If feeling overwhelmed, read Appendix A again (Honest Assessment)
- This is a 4-week plan, not a 4-day sprint

---

**Print Date:** December 26, 2025
**Expected Completion:** January 1, 2026
**Actual Completion:** _______________
