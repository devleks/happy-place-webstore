# Phase 10: M-Pesa Payment Integration - Implementation Plan

**Status:** 📋 PLANNED (Deferred from Phase 9)
**Priority:** High
**Estimated Effort:** 2 weeks
**Proposed Start Date:** January 2026
**Dependencies:** Phase 9 POS System (Complete ✅)

---

## 📋 Executive Summary

Phase 10 will integrate M-Pesa payment processing into both the online store checkout and physical store POS system. This will enable customers to pay via M-Pesa STK Push (Lipa Na M-Pesa Online) for a seamless mobile payment experience.

### Key Objectives
1. Enable M-Pesa payments for online orders
2. Enable M-Pesa payments at POS terminals
3. Support split payments (cash + M-Pesa, future: card + M-Pesa)
4. Handle M-Pesa callbacks and webhooks
5. Refund processing for voided/returned orders
6. Transaction reconciliation
7. Error handling and retry logic

---

## 🎯 Scope & Features

### 1. M-Pesa STK Push Integration (Core)

#### Online Store Checkout
**User Flow:**
1. Customer reaches checkout
2. Selects "M-Pesa" payment method
3. Enters phone number (format: 254XXXXXXXXX)
4. Clicks "Pay with M-Pesa"
5. Receives STK Push prompt on phone
6. Enters M-Pesa PIN
7. Order confirmed automatically

#### POS Terminal Checkout
**Staff Flow:**
1. Cashier completes transaction
2. Selects "M-Pesa" payment method
3. Enters customer phone number
4. Triggers STK Push
5. Customer receives prompt
6. Customer enters PIN
7. Receipt printed upon confirmation

### 2. Payment Processing

#### STK Push Request
**Features:**
- Generate unique transaction reference
- Calculate amount (order total)
- Send push to customer phone
- Store transaction in pending state
- Set 60-second timeout

#### Callback Handling
**Features:**
- Receive Safaricom callback
- Verify transaction signature
- Update order/transaction status
- Trigger inventory deduction (online)
- Send confirmation email/SMS
- Handle success/failure/timeout

### 3. Split Payment Support (Future Enhancement)

**Scenarios:**
- Cash + M-Pesa (e.g., KSh 3,000 cash + KSh 2,000 M-Pesa)
- Card + M-Pesa (future)
- Multiple M-Pesa transactions (rare)

### 4. Refund Processing

**Use Cases:**
- Voided POS transactions
- Online order returns
- Failed deliveries
- Customer disputes

**Flow:**
1. Manager initiates refund
2. System calls M-Pesa B2C API
3. Customer receives refund notification
4. Transaction recorded in database
5. Email confirmation sent

### 5. Error Handling

**Scenarios:**
- Customer cancels payment
- Insufficient funds
- Wrong PIN entered
- Timeout (no response)
- Network errors
- M-Pesa downtime

**Handling:**
- Clear error messages
- Retry option
- Fallback to cash/card
- Admin notification for failures

---

## 🗂️ Implementation Breakdown

### Week 1: M-Pesa Setup & Backend

#### Day 1: M-Pesa Developer Account Setup
**Tasks:**
- Register on Safaricom Daraja Portal
- Create app in sandbox
- Obtain Consumer Key and Consumer Secret
- Set up callback URLs
- Configure shortcode
- Test credentials

**Deliverables:**
- Sandbox credentials stored in `.env`
- Callback URL configured
- Documentation of setup process

#### Day 2: Backend Service - M-Pesa Integration
**File:** `backend/services/mpesa_service.py` (NEW)

**Methods:**
1. `get_access_token()` - OAuth token generation
2. `stk_push()` - Initiate STK Push
3. `query_transaction()` - Check transaction status
4. `handle_callback()` - Process Safaricom callback
5. `verify_signature()` - Security validation
6. `initiate_refund()` - B2C refund request
7. `check_account_balance()` - Balance inquiry (admin)

**Configuration:**
```python
MPESA_CONFIG = {
    'consumer_key': os.getenv('MPESA_CONSUMER_KEY'),
    'consumer_secret': os.getenv('MPESA_CONSUMER_SECRET'),
    'shortcode': os.getenv('MPESA_SHORTCODE'),
    'passkey': os.getenv('MPESA_PASSKEY'),
    'callback_url': os.getenv('MPESA_CALLBACK_URL'),
    'environment': os.getenv('MPESA_ENVIRONMENT', 'sandbox')  # sandbox | production
}
```

#### Day 3: Database Schema Updates
**Migration:** `006_mpesa_integration.sql`

**New Tables:**
```sql
-- M-Pesa transactions table
CREATE TABLE mpesa_transactions (
    id SERIAL PRIMARY KEY,
    merchant_request_id VARCHAR(100) UNIQUE,
    checkout_request_id VARCHAR(100) UNIQUE,
    phone_number VARCHAR(15) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    account_reference VARCHAR(100),  -- Order number or transaction ID
    transaction_type VARCHAR(20) NOT NULL,  -- stk_push, refund
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, success, failed, timeout
    mpesa_receipt_number VARCHAR(100),
    transaction_date TIMESTAMP,
    result_code VARCHAR(10),
    result_desc TEXT,
    callback_received_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Link to orders (online)
ALTER TABLE orders ADD COLUMN mpesa_transaction_id INTEGER REFERENCES mpesa_transactions(id);

-- Link to POS transactions
ALTER TABLE pos_transactions ADD COLUMN mpesa_transaction_id INTEGER REFERENCES mpesa_transactions(id);

-- Refunds table
CREATE TABLE mpesa_refunds (
    id SERIAL PRIMARY KEY,
    original_transaction_id INTEGER REFERENCES mpesa_transactions(id),
    refund_amount NUMERIC(10,2) NOT NULL,
    refund_reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    conversation_id VARCHAR(100),
    originator_conversation_id VARCHAR(100),
    result_code VARCHAR(10),
    result_desc TEXT,
    initiated_by INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_mpesa_merchant_request ON mpesa_transactions(merchant_request_id);
CREATE INDEX idx_mpesa_checkout_request ON mpesa_transactions(checkout_request_id);
CREATE INDEX idx_mpesa_phone ON mpesa_transactions(phone_number);
CREATE INDEX idx_mpesa_status ON mpesa_transactions(status);
CREATE INDEX idx_mpesa_created ON mpesa_transactions(created_at DESC);
```

#### Day 4-5: API Routes
**File:** `backend/routes/mpesa.py` (NEW)

**Endpoints:**
```
POST   /api/mpesa/stk-push              - Initiate payment
POST   /api/mpesa/callback              - Safaricom callback (public)
GET    /api/mpesa/status/:checkout_id   - Check transaction status
POST   /api/mpesa/refund                - Initiate refund (manager only)
GET    /api/mpesa/transactions/today    - Today's transactions
GET    /api/mpesa/transactions/:id      - Transaction details
POST   /api/mpesa/verify                - Verify phone number format
```

**STK Push Endpoint:**
```python
@api.route('/mpesa/stk-push', methods=['POST'])
@jwt_required()
def initiate_stk_push():
    """
    Initiate M-Pesa STK Push

    Request Body:
    {
        "phone_number": "254712345678",
        "amount": 5000.00,
        "account_reference": "ORD-20260115-0042",
        "transaction_type": "order"  # order | pos_transaction
    }
    """
    data = request.get_json()
    phone = data.get('phone_number')
    amount = data.get('amount')
    reference = data.get('account_reference')

    # Validate phone number
    if not re.match(r'^254\d{9}$', phone):
        return jsonify({'error': 'Invalid phone number format'}), 400

    # Initiate STK Push
    result = mpesa_service.stk_push(
        phone_number=phone,
        amount=amount,
        account_reference=reference
    )

    if result['success']:
        return jsonify({
            'success': True,
            'checkout_request_id': result['checkout_request_id'],
            'message': 'STK Push sent. Please check your phone.'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 400
```

**Callback Endpoint:**
```python
@api.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    Safaricom callback endpoint (no authentication required)

    This is called by Safaricom servers when payment completes
    """
    callback_data = request.get_json()

    # Process callback asynchronously (use Celery in production)
    result = mpesa_service.handle_callback(callback_data)

    # Always return success to Safaricom
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
```

---

### Week 2: Frontend & Testing

#### Day 1-2: Online Store - Checkout M-Pesa Component
**File:** `frontend/src/components/Checkout/MpesaPayment.js` (NEW)

**Features:**
- Phone number input with Kenya flag icon
- Format validation (254XXXXXXXXX)
- "Pay with M-Pesa" button
- Loading spinner during STK Push
- Payment status polling (every 2 seconds)
- Success/failure messages
- Timeout handling (60 seconds)
- Retry option

**UI Flow:**
```jsx
<MpesaPayment orderTotal={9999.00} orderNumber="ORD-20260115-0042">
  <div className="mpesa-payment">
    <div className="phone-input-group">
      <span className="country-code">🇰🇪 +254</span>
      <input
        type="tel"
        placeholder="712345678"
        maxLength="9"
        value={phoneNumber}
        onChange={handlePhoneChange}
      />
    </div>

    <button onClick={handlePayment} disabled={!isValidPhone || loading}>
      {loading ? 'Sending...' : 'Pay KSh 9,999 with M-Pesa'}
    </button>

    {loading && (
      <div className="payment-status">
        <Spinner />
        <p>Check your phone for M-Pesa prompt...</p>
        <p className="timeout-countdown">Expires in {countdown}s</p>
      </div>
    )}

    {status === 'success' && (
      <div className="payment-success">
        ✓ Payment successful! Receipt: {receiptNumber}
      </div>
    )}

    {status === 'failed' && (
      <div className="payment-failed">
        ✗ Payment failed: {errorMessage}
        <button onClick={retry}>Try Again</button>
      </div>
    )}
  </div>
</MpesaPayment>
```

#### Day 3: POS - M-Pesa Payment Component
**File:** `frontend/src/components/POS/MpesaPayment.js` (NEW)

**Features:**
- Large numeric keypad for phone entry
- Clear display of amount to pay
- "Send Payment Request" button
- Real-time status updates
- Audio feedback on success/failure
- Print receipt after successful payment
- Manager override for failed payments

**Staff Flow:**
1. Click "M-Pesa" payment method
2. Enter customer phone (254712345678)
3. Click "Send Payment Request"
4. Wait for customer to enter PIN
5. System beeps on success
6. Receipt prints automatically
7. Cart clears

#### Day 4: Testing & Error Scenarios

**Test Cases:**
1. ✅ Successful payment (online)
2. ✅ Successful payment (POS)
3. ❌ Customer cancels payment
4. ❌ Insufficient funds
5. ❌ Wrong PIN (3 attempts)
6. ❌ Timeout (customer doesn't respond)
7. ❌ Network error during STK Push
8. ❌ Callback not received
9. ✅ Refund processing
10. ✅ Split payment (cash + M-Pesa)

**Testing Script:**
```bash
#!/bin/bash
# test_mpesa_integration.sh

TOKEN="your_jwt_token"
BASE_URL="http://127.0.0.1:5001/api"

echo "=== Test 1: STK Push ==="
curl -X POST "$BASE_URL/mpesa/stk-push" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "254712345678",
    "amount": 100.00,
    "account_reference": "TEST-001",
    "transaction_type": "order"
  }'

echo -e "\n\n=== Test 2: Check Status ==="
CHECKOUT_ID="ws_CO_15012026143500001234567890"
curl -X GET "$BASE_URL/mpesa/status/$CHECKOUT_ID" \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Test 3: Simulate Callback ==="
curl -X POST "$BASE_URL/mpesa/callback" \
  -H "Content-Type: application/json" \
  -d @callback_sample.json
```

#### Day 5: Documentation & Go-Live Prep

**Documentation:**
1. M-Pesa Integration Guide
2. Error handling documentation
3. Refund process guide
4. Testing checklist
5. Production deployment steps

**Deliverables:**
- `MPESA_INTEGRATION_GUIDE.md`
- `MPESA_TESTING_GUIDE.md`
- `MPESA_ERROR_CODES.md`
- Admin training materials

---

## 🔧 Technical Stack

### APIs
- **Safaricom Daraja API** - M-Pesa integration
- **OAuth 2.0** - Authentication
- **STK Push API** - Payment initiation
- **B2C API** - Refunds

### Backend
- **Python Requests** - HTTP client
- **APScheduler** - Transaction status polling (optional)
- **Celery** - Async callback processing (production)
- **Redis** - Task queue (production)

### Frontend
- **Axios** - API calls
- **React Hooks** - State management
- **SetInterval** - Status polling
- **Web Audio API** - POS audio feedback

---

## 🔐 Security Considerations

### Authentication
- OAuth token refreshes every 60 minutes
- Store tokens in memory (never database)
- Validate callback signatures
- Whitelist Safaricom IPs for callbacks

### Data Protection
- Encrypt M-Pesa credentials in `.env`
- Never log full phone numbers
- Mask phone in receipts (254***45678)
- PCI DSS not required (M-Pesa handles card data)

### Fraud Prevention
- Rate limiting (max 5 STK Push per minute per user)
- Phone number verification
- Amount limits (max KSh 150,000)
- Duplicate transaction prevention
- Transaction expiry (60 seconds)

---

## 📊 Database Schema

### M-Pesa Transactions Table
```sql
mpesa_transactions
├─ id (PK)
├─ merchant_request_id (unique)
├─ checkout_request_id (unique)
├─ phone_number
├─ amount
├─ account_reference (order number)
├─ transaction_type (stk_push | refund)
├─ status (pending | success | failed | timeout)
├─ mpesa_receipt_number
├─ transaction_date
├─ result_code
├─ result_desc
├─ callback_received_at
├─ created_at
└─ updated_at
```

### M-Pesa Refunds Table
```sql
mpesa_refunds
├─ id (PK)
├─ original_transaction_id (FK → mpesa_transactions)
├─ refund_amount
├─ refund_reason
├─ status (pending | success | failed)
├─ conversation_id
├─ originator_conversation_id
├─ result_code
├─ result_desc
├─ initiated_by (FK → employees)
├─ created_at
└─ completed_at
```

---

## 🎨 UI/UX Design

### Online Checkout
**Color Scheme:**
- M-Pesa Green: `#0A6E33`
- Success: `#10b981`
- Error: `#dc2626`
- Loading: `#f59e0b`

### POS Terminal
**Large Touch-Friendly Design:**
- Phone input: 60px height
- Payment button: 80px height
- Status messages: 24px font
- Countdown timer: 32px font

---

## 🧪 Testing Strategy

### Unit Tests
- M-Pesa service methods
- Phone number validation
- Amount validation
- Signature verification

### Integration Tests
- STK Push end-to-end
- Callback handling
- Refund processing
- Status polling

### E2E Tests
- Online checkout with M-Pesa
- POS transaction with M-Pesa
- Failed payment handling
- Refund flow

### Load Tests
- 100 concurrent STK Push requests
- Callback processing under load
- Database performance

---

## 📈 Success Metrics

### Functional Metrics
- [ ] STK Push success rate > 95%
- [ ] Average payment time < 30 seconds
- [ ] Callback processing < 2 seconds
- [ ] Refund success rate > 98%

### Business Metrics
- [ ] 50% of online orders paid via M-Pesa
- [ ] 30% of POS transactions via M-Pesa
- [ ] Reduced cash handling
- [ ] Increased transaction volume

---

## 🚧 Risks & Mitigation

### Risk 1: M-Pesa Downtime
**Mitigation:** Fallback to cash/card, status page monitoring, customer notifications

### Risk 2: Callback Delays
**Mitigation:** Active polling as backup, 60-second timeout, retry logic

### Risk 3: Wrong Phone Numbers
**Mitigation:** Format validation, confirmation step, clear error messages

### Risk 4: Refund Delays
**Mitigation:** B2C API typically instant, but warn customers 24-48 hours

---

## 💰 Cost Estimate

### Safaricom Fees
- **STK Push:** No transaction fee (customer pays standard M-Pesa charges)
- **B2C (Refunds):** ~KSh 25-30 per transaction
- **Till Number:** KSh 550/month (if using till) or Free (if using paybill)

### Development
- **Week 1:** Backend (40 hours)
- **Week 2:** Frontend + Testing (40 hours)
- **Total:** 80 hours

---

## 🗓️ Timeline

```
Week 1: Backend & M-Pesa Setup
├─ Day 1: Developer account setup
├─ Day 2: M-Pesa service layer
├─ Day 3: Database migration
└─ Day 4-5: API routes

Week 2: Frontend & Testing
├─ Day 1-2: Online checkout component
├─ Day 3: POS payment component
├─ Day 4: Testing & error scenarios
└─ Day 5: Documentation & deployment
```

---

## ✅ Acceptance Criteria

### Must-Have for Go-Live
- [ ] STK Push works (online)
- [ ] STK Push works (POS)
- [ ] Callback handling works
- [ ] Success/failure detection
- [ ] Timeout handling
- [ ] Phone validation
- [ ] Refunds working
- [ ] Error messages clear
- [ ] Documentation complete

### Nice-to-Have
- [ ] Split payments
- [ ] Transaction reconciliation report
- [ ] M-Pesa balance check (admin)
- [ ] SMS notifications

---

## 📚 Deliverables

### Backend
- [ ] MpesaService (7 methods)
- [ ] M-Pesa API routes (7 endpoints)
- [ ] Database migration
- [ ] Callback webhook

### Frontend
- [ ] Online M-Pesa component
- [ ] POS M-Pesa component
- [ ] Loading states
- [ ] Error handling

### Documentation
- [ ] M-Pesa integration guide
- [ ] Testing guide
- [ ] Error codes reference
- [ ] Refund process guide

---

## 🎯 Next Steps After Approval

1. **Register Daraja Developer Account** (Day 1)
2. **Obtain Sandbox Credentials** (Day 1)
3. **Set Up Callback URL** (Day 1)
4. **Start Backend Development** (Day 2)

---

## 📞 References

- [Safaricom Daraja Portal](https://developer.safaricom.co.ke/)
- [STK Push API Documentation](https://developer.safaricom.co.ke/docs?shell#lipa-na-m-pesa-online-payment)
- [M-Pesa Error Codes](https://developer.safaricom.co.ke/docs#response-codes)
- [OAuth API](https://developer.safaricom.co.ke/docs?shell#authentication)

---

**Status:** 📋 PLANNED (Deferred from Phase 9)
**Created:** November 27, 2025
**Proposed Start:** January 2026
**Estimated Duration:** 2 weeks
**Dependencies:** Phase 9 Complete ✅
