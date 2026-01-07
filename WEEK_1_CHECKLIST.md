# WEEK 1 CHECKLIST - UNBLOCKING PHASE
**Period:** December 26, 2025 - January 1, 2026
**Goal:** Remove ALL Technical Blockers
**Success Criteria:** Backend stable + Payment working + Emails sending + Cart persisting

---

## 🎯 WEEK 1 OBJECTIVES

- [ ] **Backend HTTP Hanging FIXED** - API responds < 2s
- [ ] **Payment Integration COMPLETE** - M-Pesa sandbox OR Cash-on-Delivery working
- [ ] **Email Service LIVE** - Order confirmations sending automatically
- [ ] **Cart Backend CONNECTED** - Cart persists across sessions
- [ ] **End-to-End Test Order** - One complete purchase flow working

---

## DAY 1: THURSDAY, DECEMBER 26, 2025

### Morning: Backend Debugging Blitz (3-4 hours)

- [ ] **Backup current codebase**
  ```bash
  cd backend
  cp app.py app.py.backup
  git add . && git commit -m "Backup before Week 1 debugging"
  ```

- [ ] **Kill any running processes on port 5001**
  ```bash
  lsof -ti:5001 | xargs kill -9
  ```

- [ ] **Create minimal middleware version**
  - [ ] Comment out `flask_limiter` (rate limiting)
  - [ ] Comment out `newrelic` monitoring
  - [ ] Comment out custom activity logging middleware
  - [ ] Keep only: CORS, JWT, basic error handling

- [ ] **Test minimal backend**
  ```bash
  python app.py
  # In another terminal:
  curl http://127.0.0.1:5001/api/products
  ```

- [ ] **Measure response times**
  - [ ] `/api/products` - Target: < 2s
  - [ ] `/api/categories` - Target: < 2s
  - [ ] `/api/auth/me` - Target: < 1s
  - [ ] `/api/cart` - Target: < 1s
  - [ ] `/api/orders` - Target: < 2s

### Afternoon: Fix HTTP Hanging Issue (3-4 hours)

- [ ] **If minimal version works:**
  - [ ] Re-enable middleware ONE at a time
  - [ ] Test after each re-enable
  - [ ] Identify the culprit
  - [ ] Fix or permanently disable problematic middleware

- [ ] **If minimal version still hangs:**
  - [ ] Check database connection pooling settings
  - [ ] Review SQLAlchemy session management
  - [ ] Check for blocking I/O operations
  - [ ] Review imports for circular dependencies

- [ ] **Database connection audit**
  - [ ] Test PostgreSQL connection directly
  ```bash
  PGPASSWORD='Alway$ B3l13ving' psql -U postgres -d happy_place_db -c "SELECT COUNT(*) FROM products;"
  ```
  - [ ] Check connection pool configuration in `config.py`
  - [ ] Verify no connection leaks

### Evening: Comprehensive API Testing (1-2 hours)

- [ ] **Test all critical endpoints with curl**
  - [ ] GET `/api/products`
  - [ ] GET `/api/products/[slug]`
  - [ ] GET `/api/categories`
  - [ ] POST `/api/auth/login` (with test credentials)
  - [ ] GET `/api/auth/me` (with token)
  - [ ] GET `/api/cart` (with token)
  - [ ] POST `/api/cart/items` (with token)
  - [ ] GET `/api/orders` (with token)
  - [ ] GET `/api/admin/dashboard/metrics` (with admin token)

- [ ] **Document response times**
  - [ ] Create `backend_performance_day1.txt` with results
  - [ ] Note any endpoints still slow (> 2s)

### Day 1 Success Criteria
- [x] **DELIVERABLE:** Backend responds to all routes < 2 seconds
- [ ] Daily log updated in `DAILY_LOG.md`

---

## DAY 2: FRIDAY, DECEMBER 27, 2025

### Morning: M-Pesa API Research (2-3 hours)

- [ ] **Sign up for M-Pesa Daraja API sandbox**
  - [ ] Visit https://developer.safaricom.co.ke/
  - [ ] Create account
  - [ ] Get sandbox credentials (Consumer Key, Consumer Secret)
  - [ ] Save credentials to `.env` file
  ```bash
  MPESA_CONSUMER_KEY=your_key
  MPESA_CONSUMER_SECRET=your_secret
  MPESA_SHORTCODE=174379
  MPESA_PASSKEY=your_passkey
  ```

- [ ] **Read M-Pesa API documentation**
  - [ ] STK Push (Lipa Na M-Pesa Online)
  - [ ] Payment confirmation callbacks
  - [ ] Error handling

- [ ] **Install required packages**
  ```bash
  pip install requests python-dotenv
  pip freeze > requirements.txt
  ```

### Afternoon: Payment Abstraction Layer (3-4 hours)

- [ ] **Create payment service file**
  - [ ] Create `backend/services/payment_service.py`
  - [ ] Design payment interface (supports multiple providers)
  ```python
  class PaymentProvider:
      def initiate_payment(amount, phone, order_id)
      def verify_payment(transaction_id)
      def get_payment_status(transaction_id)
  ```

- [ ] **Update database models**
  - [ ] Verify `payments` table has these fields:
    - `payment_method` (mpesa, cash_on_delivery, card)
    - `transaction_id`
    - `payment_status` (pending, completed, failed)
    - `phone_number_encrypted`
  - [ ] Add migration if needed

- [ ] **Create payment routes**
  - [ ] Create `backend/routes/payment_routes.py`
  - [ ] Add blueprint to `app.py`
  - [ ] Endpoints:
    - POST `/api/payments/initiate` (start payment)
    - GET `/api/payments/:id/status` (check status)
    - POST `/api/payments/callback` (M-Pesa callback handler)

### Evening: Cash on Delivery Fallback (1-2 hours)

- [ ] **Implement COD payment option**
  - [ ] Add COD handling in `payment_service.py`
  - [ ] COD orders automatically marked as "pending payment"
  - [ ] Admin can mark as "paid" when cash received

- [ ] **Test COD flow**
  ```bash
  curl -X POST http://127.0.0.1:5001/api/payments/initiate \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer TOKEN" \
    -d '{"order_id":1,"payment_method":"cash_on_delivery"}'
  ```

### Day 2 Success Criteria
- [x] **DELIVERABLE:** Payment model in database working
- [ ] M-Pesa sandbox credentials obtained
- [ ] COD option functional
- [ ] Daily log updated

---

## DAY 3: SATURDAY, DECEMBER 28, 2025

### Morning: M-Pesa Integration Implementation (3-4 hours)

- [ ] **Implement M-Pesa STK Push**
  - [ ] Add M-Pesa provider class to `payment_service.py`
  - [ ] Implement OAuth token generation
  - [ ] Implement STK Push request
  - [ ] Handle M-Pesa API errors gracefully

- [ ] **Create callback handler**
  - [ ] Implement `/api/payments/callback` endpoint
  - [ ] Parse M-Pesa callback data
  - [ ] Update payment status in database
  - [ ] Update order status based on payment

- [ ] **Add logging**
  - [ ] Log all M-Pesa API requests
  - [ ] Log all callback responses
  - [ ] Create `logs/mpesa.log`

### Afternoon: End-to-End Payment Testing (3-4 hours)

- [ ] **Test M-Pesa sandbox flow**
  - [ ] Create test order
  - [ ] Initiate M-Pesa payment
  - [ ] Use sandbox phone number: 254708374149
  - [ ] Enter sandbox PIN: 1234
  - [ ] Verify callback received
  - [ ] Check payment status updated
  - [ ] Check order status updated

- [ ] **Test error scenarios**
  - [ ] Payment timeout
  - [ ] User cancels payment
  - [ ] Insufficient funds
  - [ ] Invalid phone number

- [ ] **Integration with order creation**
  - [ ] Update `orders_routes.py`
  - [ ] Order creation triggers payment initiation
  - [ ] Order status linked to payment status

### Day 3 Success Criteria
- [x] **DELIVERABLE:** Test payment creates order successfully
- [ ] M-Pesa sandbox payment completes
- [ ] Order status updates correctly
- [ ] Daily log updated

---

## DAY 4: SUNDAY, DECEMBER 29, 2025

### Morning: Email Service Setup (2-3 hours)

- [ ] **Choose email provider**
  - [ ] Option 1: SendGrid (free tier: 100 emails/day)
  - [ ] Option 2: Mailgun (free tier: 5,000 emails/month)
  - [ ] Option 3: AWS SES (pay as you go, cheap)

- [ ] **Sign up and get API key**
  - [ ] Create account
  - [ ] Verify domain (or use sandbox for testing)
  - [ ] Get API key
  - [ ] Add to `.env`:
  ```bash
  SENDGRID_API_KEY=your_key
  # OR
  MAILGUN_API_KEY=your_key
  MAILGUN_DOMAIN=sandbox123.mailgun.org
  ```

- [ ] **Install email package**
  ```bash
  pip install sendgrid
  # OR
  pip install mailgun2
  pip freeze > requirements.txt
  ```

### Afternoon: Email Templates Creation (2-3 hours)

- [ ] **Create email service file**
  - [ ] Create `backend/services/email_service.py`
  - [ ] Functions:
    - `send_order_confirmation(order_id, customer_email)`
    - `send_tracking_update(order_id, tracking_number)`
    - `send_welcome_email(customer_email, name)`

- [ ] **Design HTML email templates**
  - [ ] Create `backend/templates/emails/`
  - [ ] `order_confirmation.html` - Order details, total, payment status
  - [ ] `tracking_update.html` - Tracking number, carrier link
  - [ ] `welcome.html` - Welcome message, shop link

- [ ] **Template variables**
  - [ ] Order confirmation: `{customer_name}`, `{order_id}`, `{total}`, `{items}`
  - [ ] Tracking: `{tracking_number}`, `{carrier}`, `{tracking_url}`
  - [ ] Welcome: `{customer_name}`, `{shop_url}`

### Evening: Wire Email Triggers (1-2 hours)

- [ ] **Integrate with order creation**
  - [ ] Update `orders_routes.py`
  - [ ] After order created, call `send_order_confirmation()`
  - [ ] Handle email send failures gracefully (don't block order)

- [ ] **Integrate with tracking updates**
  - [ ] Update admin order update endpoint
  - [ ] When tracking number added, call `send_tracking_update()`

- [ ] **Test email sending**
  ```bash
  # Create test order
  curl -X POST http://127.0.0.1:5001/api/orders \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer TOKEN" \
    -d '{"items":[...],"payment_method":"cash_on_delivery"}'

  # Check your inbox
  ```

### Day 4 Success Criteria
- [x] **DELIVERABLE:** Order confirmation email sends
- [ ] Email service configured
- [ ] 3 templates created
- [ ] Test email received successfully
- [ ] Daily log updated

---

## DAY 5: MONDAY, DECEMBER 30, 2025

### Morning: Cart Backend Connection (2-3 hours)

- [ ] **Audit existing cart API**
  - [ ] Review `backend/routes/cart.py`
  - [ ] Test endpoints:
    - GET `/api/cart` (get current user's cart)
    - POST `/api/cart/items` (add item)
    - PUT `/api/cart/items/:id` (update quantity)
    - DELETE `/api/cart/items/:id` (remove item)
    - DELETE `/api/cart` (clear cart)

- [ ] **Fix any backend cart issues**
  - [ ] Ensure cart items include product details
  - [ ] Ensure variant information returned
  - [ ] Ensure price calculations correct
  - [ ] Ensure cart total calculated server-side

### Afternoon: Frontend Cart Integration (3-4 hours)

- [ ] **Update CartContext.js**
  - [ ] Replace localStorage-only cart with API calls
  - [ ] `addToCart()` → POST to backend
  - [ ] `updateQuantity()` → PUT to backend
  - [ ] `removeFromCart()` → DELETE to backend
  - [ ] `clearCart()` → DELETE to backend
  - [ ] Keep localStorage as fallback for logged-out users

- [ ] **Add authentication check**
  - [ ] If user logged in: use backend cart
  - [ ] If user logged out: use localStorage cart
  - [ ] On login: merge localStorage cart to backend

- [ ] **Update cart badge counter**
  - [ ] Fetch cart count from backend on app load
  - [ ] Update badge when items added/removed
  - [ ] Show correct count across page refreshes

### Evening: Cart Persistence Testing (1-2 hours)

- [ ] **Test cart functionality**
  - [ ] Add item to cart → refresh page → item still there
  - [ ] Update quantity → refresh → quantity correct
  - [ ] Remove item → refresh → item gone
  - [ ] Badge count accurate

- [ ] **Test logged-in vs logged-out**
  - [ ] Add items while logged out (localStorage)
  - [ ] Login → items merge to backend
  - [ ] Logout → items remain in localStorage

### Day 5 Success Criteria
- [x] **DELIVERABLE:** Cart works end-to-end
- [ ] Cart persists on page refresh
- [ ] Cart badge shows correct count
- [ ] Daily log updated

---

## DAY 6: TUESDAY, DECEMBER 31, 2025

### Morning: Checkout Flow Integration (2-3 hours)

- [ ] **Update Checkout.js**
  - [ ] Fetch cart from backend (not just context)
  - [ ] Display accurate totals from backend
  - [ ] Show shipping cost (if applicable)
  - [ ] Show tax calculations (VAT if required)

- [ ] **Payment method selection**
  - [ ] Radio buttons: M-Pesa, Cash on Delivery
  - [ ] Show phone input for M-Pesa
  - [ ] Validate phone number format (254XXXXXXXXX)

- [ ] **Order submission**
  - [ ] POST to `/api/orders` with:
    - Cart items
    - Shipping address
    - Payment method
    - Phone number (if M-Pesa)
  - [ ] Handle order creation response
  - [ ] Redirect to order confirmation page

### Afternoon: End-to-End Testing (3-4 hours)

- [ ] **Complete purchase flow test**
  1. [ ] Browse products page
  2. [ ] Click "Add to Cart" on 2-3 products
  3. [ ] View cart page
  4. [ ] Update quantity of one item
  5. [ ] Remove one item
  6. [ ] Click "Proceed to Checkout"
  7. [ ] Fill shipping address
  8. [ ] Select "Cash on Delivery"
  9. [ ] Click "Place Order"
  10. [ ] Verify order confirmation page
  11. [ ] Check email inbox
  12. [ ] Verify order in admin portal

- [ ] **Test M-Pesa flow**
  1. [ ] Repeat above steps
  2. [ ] Select "M-Pesa" payment
  3. [ ] Enter sandbox phone: 254708374149
  4. [ ] Complete STK push on phone
  5. [ ] Verify payment callback received
  6. [ ] Verify order status updated

- [ ] **Test error scenarios**
  - [ ] Empty cart checkout attempt
  - [ ] Missing shipping address
  - [ ] Invalid phone number
  - [ ] Payment timeout
  - [ ] Payment failure

### Evening: Bug Fixes (1-2 hours)

- [ ] **Fix any issues found during testing**
- [ ] **Verify all success criteria met**
- [ ] **Document known issues for Week 2**

### Day 6 Success Criteria
- [x] **DELIVERABLE:** One successful test order from scratch
- [ ] End-to-end flow works
- [ ] Email received
- [ ] Admin sees order
- [ ] Daily log updated

---

## DAY 7: WEDNESDAY, JANUARY 1, 2026

### Morning: Catch-Up on Blockers (2-3 hours)

- [ ] **Review Week 1 checklist**
  - [ ] Identify any incomplete tasks
  - [ ] Prioritize critical blockers
  - [ ] Complete essential missing items

- [ ] **Fix high-priority bugs**
  - [ ] Review bug list from Day 6 testing
  - [ ] Fix critical bugs only
  - [ ] Document minor bugs for Week 2

### Afternoon: Staging Environment Setup (3-4 hours)

- [ ] **Set up staging server** (if not already done)
  - [ ] Option 1: Heroku (easiest)
  - [ ] Option 2: DigitalOcean droplet
  - [ ] Option 3: AWS EC2 free tier

- [ ] **Deploy backend to staging**
  ```bash
  # Configure environment variables
  # Set up PostgreSQL database
  # Deploy Flask app
  # Test API endpoints
  ```

- [ ] **Deploy frontend to staging**
  ```bash
  # Build React app
  npm run build
  # Deploy to hosting (Netlify, Vercel, or same server)
  ```

- [ ] **Configure environment variables**
  - [ ] Staging database credentials
  - [ ] M-Pesa sandbox keys (not production)
  - [ ] Email service keys
  - [ ] JWT secret keys
  - [ ] Encryption keys

### Evening: Staging Verification (1-2 hours)

- [ ] **Test staging environment**
  - [ ] Visit staging URL
  - [ ] Complete one full purchase flow
  - [ ] Verify email sent from staging
  - [ ] Check admin portal on staging

- [ ] **Document staging URLs**
  - [ ] Customer frontend: https://staging.happyplace.com
  - [ ] Admin frontend: https://staging-admin.happyplace.com
  - [ ] API backend: https://staging-api.happyplace.com

### Day 7 Success Criteria
- [x] **DELIVERABLE:** Staging environment live
- [ ] Full purchase flow works on staging
- [ ] Environment documented
- [ ] Daily log updated

---

## 📊 WEEK 1 FINAL REVIEW

### End of Week Checklist

- [ ] **Backend Performance**
  - [ ] All API endpoints respond < 2 seconds
  - [ ] No HTTP hanging issues
  - [ ] Database connections stable

- [ ] **Payment Integration**
  - [ ] M-Pesa sandbox working OR
  - [ ] Cash on Delivery working
  - [ ] Payment status updates order status

- [ ] **Email Service**
  - [ ] Order confirmation emails sending
  - [ ] Tracking update emails working
  - [ ] Email delivery < 60 seconds

- [ ] **Cart Functionality**
  - [ ] Cart persists across sessions
  - [ ] Cart badge shows correct count
  - [ ] Cart backend API connected

- [ ] **End-to-End Flow**
  - [ ] Browse → Add to Cart → Checkout → Pay → Email
  - [ ] At least 1 successful test order completed
  - [ ] Order visible in admin portal

### Week 1 Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| API Response Time | < 2s | ___ |
| Test Orders Successful | 1+ | ___ |
| Email Delivery Time | < 60s | ___ |
| Backend Uptime | 99%+ | ___ |
| Critical Bugs Fixed | All P0 | ___ |

### Week 1 Retrospective

**What Worked:**
- _______________________________________________
- _______________________________________________
- _______________________________________________

**What Didn't Work:**
- _______________________________________________
- _______________________________________________
- _______________________________________________

**Blockers for Week 2:**
- _______________________________________________
- _______________________________________________
- _______________________________________________

**Adjustments Needed:**
- _______________________________________________
- _______________________________________________
- _______________________________________________

---

## 🚨 FAILURE TRIGGERS

**If ANY of these are FALSE by Jan 1, trigger re-planning:**

- [ ] Backend responds to all endpoints < 2s
- [ ] At least ONE payment method works (M-Pesa OR COD)
- [ ] Order confirmation email sends successfully
- [ ] Cart persists in database
- [ ] End-to-end test order completes

**If failure triggered:**
1. Stop all work Friday afternoon
2. Write honest retrospective
3. Revise plan with new timeline
4. Communicate delay immediately
5. Resume Monday with revised plan

---

## 📝 DAILY LOG TEMPLATE

**Add to `DAILY_LOG.md` each day:**

```markdown
## [Date] - Day X of Week 1

**Goal:** [Main objective for today]

**Start Time:** ___
**End Time:** ___
**Productive Hours:** ___

### Completed:
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### In Progress:
- [ ] Task that needs more time

### Blocked:
- [ ] Issue preventing progress

### Notes:
- Key learnings
- Decisions made
- Questions for tomorrow

### Tomorrow's Focus:
- Primary goal for next day
```

---

## 🎯 NEXT STEPS

**After completing Week 1:**

1. [ ] Review this checklist and mark completion %
2. [ ] Write Week 1 retrospective
3. [ ] Create Week 2 checklist (Security & Polish phase)
4. [ ] Demo Week 1 work to stakeholders (if applicable)
5. [ ] Commit and push all code to git

**Week 2 Preview (Jan 2-8):**
- SSL/HTTPS setup
- Security audit
- Bug fixes
- Performance optimization
- User acceptance testing

---

**Document Created:** [Date]
**Last Updated:** [Date]
**Owner:** [Your Name]
**Status:** 📋 READY FOR EXECUTION
