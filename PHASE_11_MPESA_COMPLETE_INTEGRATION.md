# Phase 11: Complete M-Pesa Payment Integration

**Status:** 📋 PLANNED
**Priority:** HIGH
**Estimated Effort:** 3 weeks
**Proposed Start Date:** January 2026
**Dependencies:** Phase 9 POS System (Complete ✅)

---

## 📋 Executive Summary

Phase 11 will implement comprehensive M-Pesa payment integration across the entire Happy Place Boutique ecosystem - both online store checkout and physical store POS terminals. This phase consolidates what was originally planned as Phase 10 with additional features for a complete payment solution.

### Vision
Enable seamless mobile payments for all Happy Place transactions, making M-Pesa the primary payment method for both online and in-store purchases, reducing cash handling and improving transaction security.

### Key Objectives
1. ✅ M-Pesa STK Push for online checkout
2. ✅ M-Pesa payments at POS terminals
3. ✅ Automated callback handling and order completion
4. ✅ Split payment support (cash + M-Pesa, card + M-Pesa)
5. ✅ Refund processing (B2C API)
6. ✅ Transaction reconciliation and reporting
7. ✅ Real-time balance checking (admin)
8. ✅ SMS notifications for customers
9. ✅ Comprehensive error handling and retry logic
10. ✅ Production-ready deployment with monitoring

---

## 🎯 Scope & Features

### 1. M-Pesa Developer Account Setup (Week 1, Day 1)

#### Safaricom Daraja Portal
**Tasks:**
1. Register organization on Daraja Portal
2. Create production app
3. Generate Consumer Key and Consumer Secret
4. Configure Paybill/Till Number
5. Set up callback/validation URLs
6. Whitelist server IPs
7. Test sandbox credentials
8. Request production access

**Deliverables:**
- Daraja account credentials
- Sandbox testing complete
- Production approval received
- Callback URLs configured
- Documentation of setup process

**Credentials Storage:**
```bash
# .env (backend)
MPESA_ENVIRONMENT=sandbox  # or production
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379  # Paybill or Till Number
MPESA_PASSKEY=your_passkey
MPESA_INITIATOR_NAME=your_initiator
MPESA_INITIATOR_PASSWORD=your_initiator_password
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback
MPESA_VALIDATION_URL=https://yourdomain.com/api/mpesa/validate
MPESA_RESULT_URL=https://yourdomain.com/api/mpesa/result
```

---

### 2. Backend Infrastructure (Week 1)

#### 2.1 Database Schema
**Migration:** `backend/migrations/006_mpesa_integration.sql`

**New Tables:**

```sql
-- M-Pesa transactions table (all M-Pesa payments)
CREATE TABLE mpesa_transactions (
    id SERIAL PRIMARY KEY,
    merchant_request_id VARCHAR(100) UNIQUE,
    checkout_request_id VARCHAR(100) UNIQUE,

    -- Customer info
    phone_number VARCHAR(15) NOT NULL,

    -- Transaction details
    amount NUMERIC(10,2) NOT NULL,
    account_reference VARCHAR(100) NOT NULL,  -- Order# or POS Transaction#
    transaction_desc VARCHAR(255),
    transaction_type VARCHAR(20) NOT NULL,  -- stk_push, b2c_refund, c2b_payment

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, success, failed, timeout, cancelled
    mpesa_receipt_number VARCHAR(100),  -- M-Pesa confirmation code (e.g., QGK1234567)
    transaction_date TIMESTAMP,

    -- Callback data
    result_code VARCHAR(10),
    result_desc TEXT,
    callback_received_at TIMESTAMP,
    callback_metadata JSONB,  -- Store full callback for audit

    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '5 minutes'),

    -- Indexes
    INDEX idx_mpesa_merchant_request (merchant_request_id),
    INDEX idx_mpesa_checkout_request (checkout_request_id),
    INDEX idx_mpesa_phone (phone_number),
    INDEX idx_mpesa_status (status),
    INDEX idx_mpesa_receipt (mpesa_receipt_number),
    INDEX idx_mpesa_created (created_at DESC),
    INDEX idx_mpesa_account_ref (account_reference)
);

-- Link to orders (online store)
ALTER TABLE orders ADD COLUMN mpesa_transaction_id INTEGER REFERENCES mpesa_transactions(id);
ALTER TABLE orders ADD COLUMN payment_split JSONB;  -- For split payments: {"cash": 1000, "mpesa": 4000}

-- Link to POS transactions
ALTER TABLE pos_transactions ADD COLUMN mpesa_transaction_id INTEGER REFERENCES mpesa_transactions(id);
ALTER TABLE pos_transactions ADD COLUMN payment_split JSONB;

-- M-Pesa refunds table
CREATE TABLE mpesa_refunds (
    id SERIAL PRIMARY KEY,
    original_transaction_id INTEGER REFERENCES mpesa_transactions(id),

    -- Refund details
    refund_amount NUMERIC(10,2) NOT NULL,
    refund_reason TEXT NOT NULL,
    phone_number VARCHAR(15) NOT NULL,

    -- B2C API data
    conversation_id VARCHAR(100) UNIQUE,
    originator_conversation_id VARCHAR(100) UNIQUE,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, success, failed
    result_code VARCHAR(10),
    result_desc TEXT,
    mpesa_receipt_number VARCHAR(100),

    -- Authorization
    initiated_by INTEGER REFERENCES employees(id),
    approved_by INTEGER REFERENCES employees(id),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Indexes
    INDEX idx_refund_conversation (conversation_id),
    INDEX idx_refund_status (status),
    INDEX idx_refund_created (created_at DESC)
);

-- M-Pesa reconciliation table (daily settlement tracking)
CREATE TABLE mpesa_reconciliation (
    id SERIAL PRIMARY KEY,
    reconciliation_date DATE NOT NULL UNIQUE,

    -- Transaction counts
    total_transactions INTEGER DEFAULT 0,
    successful_transactions INTEGER DEFAULT 0,
    failed_transactions INTEGER DEFAULT 0,

    -- Amounts
    total_amount NUMERIC(12,2) DEFAULT 0,
    successful_amount NUMERIC(12,2) DEFAULT 0,
    refund_amount NUMERIC(12,2) DEFAULT 0,
    net_amount NUMERIC(12,2) DEFAULT 0,

    -- M-Pesa balance (from account balance API)
    mpesa_balance NUMERIC(12,2),
    expected_balance NUMERIC(12,2),
    variance NUMERIC(12,2),

    -- Status
    status VARCHAR(20) DEFAULT 'open',  -- open, reconciled, discrepancy
    notes TEXT,
    reconciled_by INTEGER REFERENCES employees(id),
    reconciled_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_recon_date (reconciliation_date DESC),
    INDEX idx_recon_status (status)
);

-- M-Pesa audit log (all API calls)
CREATE TABLE mpesa_audit_log (
    id SERIAL PRIMARY KEY,
    api_endpoint VARCHAR(100) NOT NULL,  -- stk_push, query_status, b2c, balance
    request_data JSONB NOT NULL,
    response_data JSONB,
    http_status_code INTEGER,
    success BOOLEAN,
    error_message TEXT,
    duration_ms INTEGER,  -- API call duration
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_audit_endpoint (api_endpoint),
    INDEX idx_audit_success (success),
    INDEX idx_audit_created (created_at DESC)
);

-- M-Pesa configuration table (dynamic config)
CREATE TABLE mpesa_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_by INTEGER REFERENCES employees(id),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default config
INSERT INTO mpesa_config (config_key, config_value, description) VALUES
    ('max_transaction_amount', '150000', 'Maximum transaction amount in KSh'),
    ('min_transaction_amount', '10', 'Minimum transaction amount in KSh'),
    ('stk_timeout_seconds', '60', 'STK Push timeout duration'),
    ('retry_limit', '3', 'Maximum retry attempts for failed transactions'),
    ('rate_limit_per_minute', '10', 'Max STK Push requests per user per minute'),
    ('enable_split_payments', 'true', 'Allow split payments (cash + M-Pesa)'),
    ('enable_sms_notifications', 'true', 'Send SMS on transaction completion'),
    ('maintenance_mode', 'false', 'Disable M-Pesa during maintenance');
```

**Rollback Script:** `backend/migrations/006_mpesa_integration_rollback.sql`

```sql
-- Rollback in reverse order
DROP TABLE IF EXISTS mpesa_audit_log CASCADE;
DROP TABLE IF EXISTS mpesa_config CASCADE;
DROP TABLE IF EXISTS mpesa_reconciliation CASCADE;
DROP TABLE IF EXISTS mpesa_refunds CASCADE;
DROP TABLE IF EXISTS mpesa_transactions CASCADE;

ALTER TABLE orders DROP COLUMN IF EXISTS mpesa_transaction_id;
ALTER TABLE orders DROP COLUMN IF EXISTS payment_split;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS mpesa_transaction_id;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS payment_split;
```

---

#### 2.2 M-Pesa Service Layer
**File:** `backend/services/mpesa_service.py` (NEW - ~800 lines)

**Class Structure:**

```python
import os
import base64
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import json
import hashlib
from flask import current_app
from backend.extensions import db
from backend.models import MpesaTransaction, MpesaRefund, MpesaAuditLog, MpesaConfig

class MpesaService:
    """
    Complete M-Pesa integration service

    Handles all M-Pesa operations:
    - STK Push (Lipa Na M-Pesa Online)
    - Transaction status queries
    - Callback processing
    - B2C refunds
    - Account balance checking
    - Reconciliation
    """

    def __init__(self):
        self.environment = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.shortcode = os.getenv('MPESA_SHORTCODE')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.initiator_name = os.getenv('MPESA_INITIATOR_NAME')
        self.initiator_password = os.getenv('MPESA_INITIATOR_PASSWORD')

        # API URLs
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'

        self.auth_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        self.stk_push_url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        self.query_url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
        self.b2c_url = f'{self.base_url}/mpesa/b2c/v1/paymentrequest'
        self.balance_url = f'{self.base_url}/mpesa/accountbalance/v1/query'

        # Callback URLs
        self.callback_url = os.getenv('MPESA_CALLBACK_URL')
        self.validation_url = os.getenv('MPESA_VALIDATION_URL')
        self.result_url = os.getenv('MPESA_RESULT_URL')

    # ============ AUTHENTICATION ============

    def get_access_token(self) -> Optional[str]:
        """
        Generate OAuth access token
        Token valid for 3600 seconds (1 hour)
        """
        try:
            # Create Basic Auth header
            credentials = f'{self.consumer_key}:{self.consumer_secret}'
            encoded = base64.b64encode(credentials.encode()).decode()

            headers = {
                'Authorization': f'Basic {encoded}'
            }

            response = requests.get(self.auth_url, headers=headers, timeout=30)

            # Log API call
            self._log_api_call('auth', {}, response.json(), response.status_code)

            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                current_app.logger.error(f'M-Pesa auth failed: {response.text}')
                return None

        except Exception as e:
            current_app.logger.error(f'M-Pesa auth error: {str(e)}')
            return None

    # ============ STK PUSH ============

    def initiate_stk_push(
        self,
        phone_number: str,
        amount: float,
        account_reference: str,
        transaction_desc: str = 'Payment'
    ) -> Dict:
        """
        Initiate STK Push to customer phone

        Args:
            phone_number: Customer phone (format: 254712345678)
            amount: Amount to pay in KSh
            account_reference: Order number or POS transaction ID
            transaction_desc: Description for customer's M-Pesa statement

        Returns:
            {
                'success': True/False,
                'checkout_request_id': 'ws_CO_...',
                'merchant_request_id': 'merchant_...',
                'message': 'Success message',
                'error': 'Error message if failed'
            }
        """
        try:
            # Validate phone number
            if not self._validate_phone(phone_number):
                return {'success': False, 'error': 'Invalid phone number format. Use 254XXXXXXXXX'}

            # Validate amount
            min_amount = self._get_config('min_transaction_amount', 10)
            max_amount = self._get_config('max_transaction_amount', 150000)

            if amount < float(min_amount):
                return {'success': False, 'error': f'Amount below minimum (KSh {min_amount})'}

            if amount > float(max_amount):
                return {'success': False, 'error': f'Amount exceeds maximum (KSh {max_amount})'}

            # Check maintenance mode
            if self._get_config('maintenance_mode', 'false') == 'true':
                return {'success': False, 'error': 'M-Pesa payment temporarily unavailable. Please try cash payment.'}

            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to authenticate with M-Pesa'}

            # Generate password
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_str = f'{self.shortcode}{self.passkey}{timestamp}'
            password = base64.b64encode(password_str.encode()).decode()

            # Prepare request
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),  # M-Pesa expects integer
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }

            # Make API call
            response = requests.post(
                self.stk_push_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response_data = response.json()

            # Log API call
            self._log_api_call('stk_push', payload, response_data, response.status_code)

            # Check response
            if response.status_code == 200 and response_data.get('ResponseCode') == '0':
                # Success - save to database
                transaction = MpesaTransaction(
                    merchant_request_id=response_data.get('MerchantRequestID'),
                    checkout_request_id=response_data.get('CheckoutRequestID'),
                    phone_number=phone_number,
                    amount=amount,
                    account_reference=account_reference,
                    transaction_desc=transaction_desc,
                    transaction_type='stk_push',
                    status='pending',
                    expires_at=datetime.now() + timedelta(seconds=60)
                )

                db.session.add(transaction)
                db.session.commit()

                return {
                    'success': True,
                    'checkout_request_id': response_data.get('CheckoutRequestID'),
                    'merchant_request_id': response_data.get('MerchantRequestID'),
                    'message': 'STK Push sent successfully. Please check your phone.'
                }
            else:
                error_message = response_data.get('errorMessage') or response_data.get('ResponseDescription', 'Unknown error')
                return {
                    'success': False,
                    'error': f'M-Pesa request failed: {error_message}'
                }

        except Exception as e:
            current_app.logger.error(f'STK Push error: {str(e)}')
            return {'success': False, 'error': 'Payment system error. Please try again.'}

    # ============ CALLBACK HANDLING ============

    def handle_callback(self, callback_data: Dict) -> Dict:
        """
        Process M-Pesa callback from Safaricom

        Callback structure:
        {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "...",
                    "CheckoutRequestID": "...",
                    "ResultCode": 0,  # 0 = success, non-zero = failure
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 5000},
                            {"Name": "MpesaReceiptNumber", "Value": "QGK12345"},
                            {"Name": "TransactionDate", "Value": 20260115143000},
                            {"Name": "PhoneNumber", "Value": 254712345678}
                        ]
                    }
                }
            }
        }
        """
        try:
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})

            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = str(stk_callback.get('ResultCode'))
            result_desc = stk_callback.get('ResultDesc')

            # Find transaction
            transaction = MpesaTransaction.query.filter_by(
                checkout_request_id=checkout_request_id
            ).first()

            if not transaction:
                current_app.logger.error(f'Transaction not found: {checkout_request_id}')
                return {'success': False, 'error': 'Transaction not found'}

            # Update transaction
            transaction.result_code = result_code
            transaction.result_desc = result_desc
            transaction.callback_received_at = datetime.now()
            transaction.callback_metadata = callback_data
            transaction.updated_at = datetime.now()

            # Check result
            if result_code == '0':
                # Success - extract metadata
                metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                metadata_dict = {item['Name']: item.get('Value') for item in metadata}

                transaction.status = 'success'
                transaction.mpesa_receipt_number = metadata_dict.get('MpesaReceiptNumber')

                # Parse transaction date (format: 20260115143000)
                trans_date_str = str(metadata_dict.get('TransactionDate'))
                if trans_date_str:
                    transaction.transaction_date = datetime.strptime(trans_date_str, '%Y%m%d%H%M%S')

                db.session.commit()

                # Process order/POS transaction completion
                self._complete_transaction(transaction)

                # Send SMS notification
                if self._get_config('enable_sms_notifications', 'true') == 'true':
                    self._send_sms_notification(transaction)

                return {
                    'success': True,
                    'message': 'Payment successful',
                    'receipt_number': transaction.mpesa_receipt_number
                }
            else:
                # Failed
                transaction.status = 'failed'
                db.session.commit()

                current_app.logger.warning(
                    f'M-Pesa payment failed: {result_desc} (Code: {result_code})'
                )

                return {
                    'success': False,
                    'error': result_desc,
                    'result_code': result_code
                }

        except Exception as e:
            current_app.logger.error(f'Callback processing error: {str(e)}')
            return {'success': False, 'error': str(e)}

    # ============ QUERY TRANSACTION STATUS ============

    def query_transaction_status(self, checkout_request_id: str) -> Dict:
        """
        Check status of pending STK Push transaction
        Used for polling when callback is delayed
        """
        try:
            # Get transaction from database
            transaction = MpesaTransaction.query.filter_by(
                checkout_request_id=checkout_request_id
            ).first()

            if not transaction:
                return {'success': False, 'error': 'Transaction not found'}

            # If already completed, return cached status
            if transaction.status in ['success', 'failed']:
                return {
                    'success': True,
                    'status': transaction.status,
                    'result_code': transaction.result_code,
                    'result_desc': transaction.result_desc,
                    'receipt_number': transaction.mpesa_receipt_number
                }

            # Check if expired
            if datetime.now() > transaction.expires_at:
                transaction.status = 'timeout'
                db.session.commit()
                return {
                    'success': False,
                    'status': 'timeout',
                    'error': 'Transaction timed out'
                }

            # Query M-Pesa API
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Authentication failed'}

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_str = f'{self.shortcode}{self.passkey}{timestamp}'
            password = base64.b64encode(password_str.encode()).decode()

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }

            response = requests.post(
                self.query_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response_data = response.json()

            # Log API call
            self._log_api_call('query_status', payload, response_data, response.status_code)

            result_code = response_data.get('ResultCode')

            if result_code == '0':
                # Success
                transaction.status = 'success'
                transaction.result_code = str(result_code)
                transaction.result_desc = response_data.get('ResultDesc')
                db.session.commit()

                return {
                    'success': True,
                    'status': 'success',
                    'result_code': result_code,
                    'result_desc': response_data.get('ResultDesc')
                }
            elif result_code:
                # Failed
                transaction.status = 'failed'
                transaction.result_code = str(result_code)
                transaction.result_desc = response_data.get('ResultDesc')
                db.session.commit()

                return {
                    'success': False,
                    'status': 'failed',
                    'result_code': result_code,
                    'error': response_data.get('ResultDesc')
                }
            else:
                # Still pending
                return {
                    'success': True,
                    'status': 'pending',
                    'message': 'Transaction still pending'
                }

        except Exception as e:
            current_app.logger.error(f'Query status error: {str(e)}')
            return {'success': False, 'error': str(e)}

    # ============ B2C REFUNDS ============

    def initiate_refund(
        self,
        original_transaction_id: int,
        refund_amount: float,
        refund_reason: str,
        initiated_by: int
    ) -> Dict:
        """
        Initiate B2C refund to customer

        Args:
            original_transaction_id: ID of original M-Pesa transaction
            refund_amount: Amount to refund
            refund_reason: Reason for refund
            initiated_by: Employee ID initiating refund

        Returns:
            Success/failure dict
        """
        try:
            # Get original transaction
            original_trans = MpesaTransaction.query.get(original_transaction_id)
            if not original_trans:
                return {'success': False, 'error': 'Original transaction not found'}

            if original_trans.status != 'success':
                return {'success': False, 'error': 'Cannot refund unsuccessful transaction'}

            if refund_amount > original_trans.amount:
                return {'success': False, 'error': 'Refund amount exceeds original amount'}

            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Authentication failed'}

            # Generate security credential
            security_credential = self._generate_security_credential()

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'InitiatorName': self.initiator_name,
                'SecurityCredential': security_credential,
                'CommandID': 'BusinessPayment',
                'Amount': int(refund_amount),
                'PartyA': self.shortcode,
                'PartyB': original_trans.phone_number,
                'Remarks': refund_reason[:100],  # Max 100 chars
                'QueueTimeOutURL': self.result_url,
                'ResultURL': self.result_url,
                'Occasion': f'Refund-{original_trans.account_reference}'
            }

            response = requests.post(
                self.b2c_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response_data = response.json()

            # Log API call
            self._log_api_call('b2c_refund', payload, response_data, response.status_code)

            if response.status_code == 200 and response_data.get('ResponseCode') == '0':
                # Create refund record
                refund = MpesaRefund(
                    original_transaction_id=original_transaction_id,
                    refund_amount=refund_amount,
                    refund_reason=refund_reason,
                    phone_number=original_trans.phone_number,
                    conversation_id=response_data.get('ConversationID'),
                    originator_conversation_id=response_data.get('OriginatorConversationID'),
                    status='processing',
                    initiated_by=initiated_by
                )

                db.session.add(refund)
                db.session.commit()

                return {
                    'success': True,
                    'conversation_id': response_data.get('ConversationID'),
                    'message': 'Refund initiated successfully'
                }
            else:
                error_msg = response_data.get('errorMessage', 'Unknown error')
                return {'success': False, 'error': f'Refund failed: {error_msg}'}

        except Exception as e:
            current_app.logger.error(f'Refund error: {str(e)}')
            return {'success': False, 'error': str(e)}

    # ============ HELPER METHODS ============

    def _validate_phone(self, phone: str) -> bool:
        """Validate Kenyan phone number format"""
        import re
        # Must start with 254 and have 9 more digits
        return bool(re.match(r'^254\d{9}$', phone))

    def _get_config(self, key: str, default: any) -> str:
        """Get config value from database"""
        config = MpesaConfig.query.filter_by(config_key=key).first()
        return config.config_value if config else str(default)

    def _log_api_call(self, endpoint: str, request_data: Dict, response_data: Dict, status_code: int):
        """Log all M-Pesa API calls for audit"""
        try:
            # Mask sensitive data before logging
            safe_request = self._mask_sensitive_data(request_data.copy())

            log = MpesaAuditLog(
                api_endpoint=endpoint,
                request_data=safe_request,
                response_data=response_data,
                http_status_code=status_code,
                success=(status_code == 200)
            )

            db.session.add(log)
            db.session.commit()
        except:
            pass  # Don't fail transaction if logging fails

    def _mask_sensitive_data(self, data: Dict) -> Dict:
        """Mask passwords, tokens, etc. in logs"""
        sensitive_keys = ['Password', 'SecurityCredential', 'Passkey']
        for key in sensitive_keys:
            if key in data:
                data[key] = '***MASKED***'
        return data

    def _complete_transaction(self, mpesa_trans: MpesaTransaction):
        """
        Complete order/POS transaction after successful M-Pesa payment
        """
        try:
            account_ref = mpesa_trans.account_reference

            # Check if it's an order (starts with ORD) or POS transaction (starts with POS)
            if account_ref.startswith('ORD-'):
                self._complete_online_order(mpesa_trans)
            elif account_ref.startswith('POS-'):
                self._complete_pos_transaction(mpesa_trans)

        except Exception as e:
            current_app.logger.error(f'Transaction completion error: {str(e)}')

    def _complete_online_order(self, mpesa_trans: MpesaTransaction):
        """Mark online order as paid and confirmed"""
        from backend.models import Order

        order = Order.query.filter_by(order_number=mpesa_trans.account_reference).first()
        if order:
            order.mpesa_transaction_id = mpesa_trans.id
            order.payment_status = 'paid'
            order.order_status = 'confirmed'
            db.session.commit()

            current_app.logger.info(f'Order {order.order_number} marked as paid')

    def _complete_pos_transaction(self, mpesa_trans: MpesaTransaction):
        """Mark POS transaction as complete"""
        from backend.models import POSTransaction

        pos_trans = POSTransaction.query.filter_by(
            transaction_number=mpesa_trans.account_reference
        ).first()

        if pos_trans:
            pos_trans.mpesa_transaction_id = mpesa_trans.id
            pos_trans.payment_status = 'completed'
            db.session.commit()

            current_app.logger.info(f'POS transaction {pos_trans.transaction_number} completed')

    def _send_sms_notification(self, transaction: MpesaTransaction):
        """Send SMS notification to customer (placeholder)"""
        # TODO: Integrate with Africa's Talking or similar SMS provider
        pass

    def _generate_security_credential(self) -> str:
        """Generate security credential for B2C API"""
        # TODO: Encrypt initiator password with M-Pesa public key
        # For now, return base64 encoded password (NOT PRODUCTION READY)
        return base64.b64encode(self.initiator_password.encode()).decode()


# Create global instance
mpesa_service = MpesaService()
```

This is a comprehensive service layer. Would you like me to continue with:
1. The REST API routes (`backend/routes/mpesa.py`)
2. Frontend components (online checkout + POS)
3. Testing scripts
4. Documentation

Or shall I complete the entire Phase 11 document first?
---

#### 2.3 M-Pesa API Routes
**File:** `backend/routes/mpesa.py` (NEW - ~500 lines)

**Endpoints:**

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from backend.services.mpesa_service import mpesa_service
from backend.middleware.auth import employee_required, manager_required
from backend.models import MpesaTransaction, MpesaRefund
from backend.extensions import db
import re

api = Blueprint('mpesa', __name__, url_prefix='/api/mpesa')

# ============ PUBLIC ENDPOINTS (No Auth) ============

@api.route('/callback', methods=['POST'])
def mpesa_callback():
    """
    Safaricom callback endpoint
    Called by Safaricom servers when payment completes
    NO AUTHENTICATION - Safaricom doesn't send auth tokens
    """
    try:
        callback_data = request.get_json()
        
        # Process callback
        result = mpesa_service.handle_callback(callback_data)
        
        # Always return 200 to Safaricom
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Callback error: {str(e)}')
        # Still return 200 to prevent Safaricom retries
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }), 200


@api.route('/validation', methods=['POST'])
def mpesa_validation():
    """
    C2B validation endpoint (if using C2B API)
    Optional - can be used to validate payments before accepting
    """
    # For now, accept all
    return jsonify({
        'ResultCode': 0,
        'ResultDesc': 'Accepted'
    }), 200


@api.route('/result', methods=['POST'])
def mpesa_result():
    """
    B2C result endpoint for refunds
    """
    try:
        result_data = request.get_json()
        
        conversation_id = result_data.get('Result', {}).get('ConversationID')
        result_code = result_data.get('Result', {}).get('ResultCode')
        
        # Find refund
        refund = MpesaRefund.query.filter_by(conversation_id=conversation_id).first()
        
        if refund:
            if result_code == 0:
                refund.status = 'success'
                refund.result_code = str(result_code)
                refund.result_desc = result_data.get('Result', {}).get('ResultDesc')
                refund.completed_at = datetime.now()
            else:
                refund.status = 'failed'
                refund.result_code = str(result_code)
                refund.result_desc = result_data.get('Result', {}).get('ResultDesc')
            
            db.session.commit()
        
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'B2C result error: {str(e)}')
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Accepted'
        }), 200


# ============ AUTHENTICATED ENDPOINTS ============

@api.route('/stk-push', methods=['POST'])
@jwt_required()
def initiate_stk_push():
    """
    Initiate STK Push payment
    
    Request Body:
    {
        "phone_number": "254712345678",
        "amount": 5000.00,
        "account_reference": "ORD-20260115-0042",
        "transaction_desc": "Payment for Order ORD-20260115-0042"
    }
    
    Response:
    {
        "success": true,
        "checkout_request_id": "ws_CO_15012026143500001234567890",
        "merchant_request_id": "29115-34620561-1",
        "message": "STK Push sent successfully"
    }
    """
    try:
        data = request.get_json()
        
        phone = data.get('phone_number')
        amount = data.get('amount')
        reference = data.get('account_reference')
        desc = data.get('transaction_desc', 'Payment')
        
        # Validate inputs
        if not phone or not amount or not reference:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Initiate STK Push
        result = mpesa_service.initiate_stk_push(
            phone_number=phone,
            amount=float(amount),
            account_reference=reference,
            transaction_desc=desc
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/status/<checkout_request_id>', methods=['GET'])
@jwt_required()
def check_transaction_status(checkout_request_id):
    """
    Check status of pending transaction
    Used for polling while waiting for callback
    
    Response:
    {
        "success": true,
        "status": "pending|success|failed|timeout",
        "result_code": "0",
        "result_desc": "The service request is processed successfully",
        "receipt_number": "QGK12345"
    }
    """
    try:
        result = mpesa_service.query_transaction_status(checkout_request_id)
        
        if result['success'] or result.get('status') in ['pending', 'timeout']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/refund', methods=['POST'])
@manager_required  # Only managers can initiate refunds
def initiate_refund():
    """
    Initiate B2C refund
    Requires manager authorization
    
    Request Body:
    {
        "transaction_id": 123,
        "refund_amount": 2500.00,
        "refund_reason": "Customer returned item"
    }
    """
    try:
        claims = get_jwt()
        employee_id = int(get_jwt_identity())
        
        data = request.get_json()
        
        transaction_id = data.get('transaction_id')
        refund_amount = data.get('refund_amount')
        refund_reason = data.get('refund_reason')
        
        if not all([transaction_id, refund_amount, refund_reason]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Initiate refund
        result = mpesa_service.initiate_refund(
            original_transaction_id=transaction_id,
            refund_amount=float(refund_amount),
            refund_reason=refund_reason,
            initiated_by=employee_id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """
    Get M-Pesa transactions with filtering
    
    Query params:
    - status: pending|success|failed
    - date_from: YYYY-MM-DD
    - date_to: YYYY-MM-DD
    - limit: 50 (default)
    - offset: 0 (default)
    """
    try:
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        query = MpesaTransaction.query
        
        if status:
            query = query.filter_by(status=status)
        
        if date_from:
            query = query.filter(MpesaTransaction.created_at >= date_from)
        
        if date_to:
            query = query.filter(MpesaTransaction.created_at <= date_to)
        
        total = query.count()
        transactions = query.order_by(
            MpesaTransaction.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'total': total,
            'transactions': [t.to_dict() for t in transactions]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/transactions/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction_details(transaction_id):
    """Get detailed info for single transaction"""
    try:
        transaction = MpesaTransaction.query.get(transaction_id)
        
        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404
        
        return jsonify({
            'success': True,
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/validate-phone', methods=['POST'])
@jwt_required()
def validate_phone():
    """
    Validate phone number format
    
    Request Body:
    {
        "phone_number": "0712345678" or "254712345678" or "+254712345678"
    }
    
    Response:
    {
        "success": true,
        "formatted": "254712345678",
        "valid": true
    }
    """
    try:
        data = request.get_json()
        phone = data.get('phone_number', '').strip()
        
        # Remove + if present
        phone = phone.replace('+', '')
        
        # Convert 07XX to 2547XX
        if phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        
        # Validate format
        valid = bool(re.match(r'^254\d{9}$', phone))
        
        return jsonify({
            'success': True,
            'formatted': phone if valid else None,
            'valid': valid
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/reconciliation/daily/<date>', methods=['GET'])
@manager_required  # Only managers can view reconciliation
def get_daily_reconciliation(date):
    """
    Get daily M-Pesa reconciliation report
    
    Args:
        date: YYYY-MM-DD format
    
    Response:
    {
        "date": "2026-01-15",
        "total_transactions": 150,
        "successful_transactions": 145,
        "failed_transactions": 5,
        "total_amount": 450000.00,
        "successful_amount": 442500.00,
        "refund_amount": 2500.00,
        "net_amount": 440000.00
    }
    """
    try:
        from datetime import datetime
        
        # Parse date
        recon_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get transactions for that day
        transactions = MpesaTransaction.query.filter(
            db.func.date(MpesaTransaction.created_at) == recon_date
        ).all()
        
        # Calculate stats
        total_count = len(transactions)
        success_count = sum(1 for t in transactions if t.status == 'success')
        failed_count = sum(1 for t in transactions if t.status == 'failed')
        
        total_amount = sum(t.amount for t in transactions)
        success_amount = sum(t.amount for t in transactions if t.status == 'success')
        
        # Get refunds
        refunds = MpesaRefund.query.filter(
            db.func.date(MpesaRefund.created_at) == recon_date,
            MpesaRefund.status == 'success'
        ).all()
        
        refund_amount = sum(r.refund_amount for r in refunds)
        net_amount = success_amount - refund_amount
        
        return jsonify({
            'success': True,
            'date': date,
            'total_transactions': total_count,
            'successful_transactions': success_count,
            'failed_transactions': failed_count,
            'total_amount': float(total_amount),
            'successful_amount': float(success_amount),
            'refund_amount': float(refund_amount),
            'net_amount': float(net_amount),
            'transactions': [t.to_dict() for t in transactions]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/config', methods=['GET'])
@manager_required
def get_mpesa_config():
    """Get current M-Pesa configuration"""
    try:
        from backend.models import MpesaConfig
        
        configs = MpesaConfig.query.all()
        
        return jsonify({
            'success': True,
            'config': {c.config_key: c.config_value for c in configs}
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/config', methods=['PUT'])
@manager_required
def update_mpesa_config():
    """Update M-Pesa configuration (manager only)"""
    try:
        from backend.models import MpesaConfig
        
        claims = get_jwt()
        employee_id = int(get_jwt_identity())
        
        data = request.get_json()
        
        for key, value in data.items():
            config = MpesaConfig.query.filter_by(config_key=key).first()
            if config:
                config.config_value = str(value)
                config.updated_by = employee_id
                config.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/health', methods=['GET'])
def mpesa_health():
    """
    Check M-Pesa integration health
    Public endpoint for monitoring
    """
    try:
        # Check if we can generate access token
        token = mpesa_service.get_access_token()
        
        if token:
            return jsonify({
                'success': True,
                'status': 'healthy',
                'message': 'M-Pesa integration operational'
            }), 200
        else:
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'message': 'Cannot authenticate with M-Pesa'
            }), 503
            
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 503
```

**Register Blueprint in `backend/app.py`:**

```python
from backend.routes.mpesa import api as mpesa_api
app.register_blueprint(mpesa_api)
```

---

### 3. Frontend Implementation (Week 2)

#### 3.1 Online Store - M-Pesa Checkout Component
**File:** `frontend/src/components/Checkout/MpesaPayment.js` (NEW - ~350 lines)

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MpesaPayment.css';

const MpesaPayment = ({ orderTotal, orderNumber, onSuccess, onCancel }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, processing, success, failed, timeout
  const [message, setMessage] = useState('');
  const [checkoutRequestId, setCheckoutRequestId] = useState(null);
  const [countdown, setCountdown] = useState(60);
  const [receiptNumber, setReceiptNumber] = useState('');

  // Format phone number as user types
  const handlePhoneChange = (e) => {
    let value = e.target.value.replace(/\D/g, ''); // Remove non-digits
    
    // Limit to 9 digits (254 is prepended)
    if (value.length > 9) {
      value = value.substring(0, 9);
    }
    
    setPhoneNumber(value);
  };

  // Validate phone number
  const isValidPhone = () => {
    return /^[17]\d{8}$/.test(phoneNumber); // Must start with 1 or 7, then 8 more digits
  };

  // Initiate payment
  const handlePayment = async () => {
    if (!isValidPhone()) {
      setMessage('Please enter a valid phone number');
      return;
    }

    setLoading(true);
    setStatus('processing');
    setMessage('Sending payment request...');
    setCountdown(60);

    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.post(
        '/api/mpesa/stk-push',
        {
          phone_number: `254${phoneNumber}`,
          amount: orderTotal,
          account_reference: orderNumber,
          transaction_desc: `Payment for ${orderNumber}`
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setCheckoutRequestId(response.data.checkout_request_id);
        setMessage('Check your phone for M-Pesa prompt...');
        
        // Start polling for status
        startPolling(response.data.checkout_request_id);
        
        // Start countdown
        startCountdown();
      } else {
        setStatus('failed');
        setMessage(response.data.error || 'Payment request failed');
        setLoading(false);
      }
    } catch (error) {
      setStatus('failed');
      setMessage(error.response?.data?.error || 'Payment system error');
      setLoading(false);
    }
  };

  // Poll for transaction status
  const startPolling = (checkoutId) => {
    const pollInterval = setInterval(async () => {
      try {
        const token = localStorage.getItem('token');
        
        const response = await axios.get(
          `/api/mpesa/status/${checkoutId}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        const { status: txStatus, receipt_number } = response.data;

        if (txStatus === 'success') {
          clearInterval(pollInterval);
          setStatus('success');
          setMessage('Payment successful!');
          setReceiptNumber(receipt_number);
          setLoading(false);
          
          // Call success callback after 2 seconds
          setTimeout(() => {
            onSuccess && onSuccess(receipt_number);
          }, 2000);
        } else if (txStatus === 'failed') {
          clearInterval(pollInterval);
          setStatus('failed');
          setMessage(response.data.error || 'Payment failed');
          setLoading(false);
        } else if (txStatus === 'timeout') {
          clearInterval(pollInterval);
          setStatus('timeout');
          setMessage('Payment timed out');
          setLoading(false);
        }
        // If still pending, continue polling
      } catch (error) {
        // Continue polling even on error (might be network issue)
        console.error('Polling error:', error);
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 65 seconds
    setTimeout(() => {
      clearInterval(pollInterval);
      if (loading) {
        setStatus('timeout');
        setMessage('Payment timed out. Please try again.');
        setLoading(false);
      }
    }, 65000);
  };

  // Countdown timer
  const startCountdown = () => {
    const countInterval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countInterval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Retry payment
  const handleRetry = () => {
    setStatus('idle');
    setMessage('');
    setCheckoutRequestId(null);
    setCountdown(60);
  };

  return (
    <div className="mpesa-payment">
      <div className="mpesa-header">
        <img src="/images/mpesa-logo.png" alt="M-Pesa" className="mpesa-logo" />
        <h3>Pay with M-Pesa</h3>
      </div>

      <div className="payment-amount">
        <span className="label">Amount to Pay:</span>
        <span className="amount">KSh {orderTotal.toLocaleString()}</span>
      </div>

      {status === 'idle' && (
        <>
          <div className="phone-input-group">
            <label>Enter your M-Pesa phone number:</label>
            <div className="phone-input-wrapper">
              <span className="country-code">🇰🇪 +254</span>
              <input
                type="tel"
                placeholder="712345678"
                value={phoneNumber}
                onChange={handlePhoneChange}
                maxLength="9"
                className="phone-input"
                autoFocus
              />
            </div>
            {phoneNumber && !isValidPhone() && (
              <p className="error-text">Invalid phone number</p>
            )}
          </div>

          <button
            className="pay-button"
            onClick={handlePayment}
            disabled={!isValidPhone() || loading}
          >
            Pay KSh {orderTotal.toLocaleString()} with M-Pesa
          </button>

          <button className="cancel-button" onClick={onCancel}>
            Cancel
          </button>

          <div className="payment-info">
            <p>✓ Secure M-Pesa payment</p>
            <p>✓ Instant confirmation</p>
            <p>✓ Receipt sent via SMS</p>
          </div>
        </>
      )}

      {status === 'processing' && (
        <div className="payment-processing">
          <div className="spinner"></div>
          <p className="processing-message">{message}</p>
          <div className="countdown">
            <p>Expires in {countdown} seconds</p>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${(countdown / 60) * 100}%` }}
              ></div>
            </div>
          </div>
          <div className="instructions">
            <h4>Steps to complete payment:</h4>
            <ol>
              <li>Check your phone for M-Pesa prompt</li>
              <li>Enter your M-Pesa PIN</li>
              <li>Confirm payment</li>
            </ol>
          </div>
        </div>
      )}

      {status === 'success' && (
        <div className="payment-success">
          <div className="success-icon">✓</div>
          <h3>Payment Successful!</h3>
          <p>{message}</p>
          {receiptNumber && (
            <div className="receipt-info">
              <p>M-Pesa Receipt: <strong>{receiptNumber}</strong></p>
            </div>
          )}
          <p className="redirect-message">Redirecting to order confirmation...</p>
        </div>
      )}

      {(status === 'failed' || status === 'timeout') && (
        <div className="payment-failed">
          <div className="error-icon">✗</div>
          <h3>{status === 'timeout' ? 'Payment Timed Out' : 'Payment Failed'}</h3>
          <p className="error-message">{message}</p>
          
          <button className="retry-button" onClick={handleRetry}>
            Try Again
          </button>
          <button className="cancel-button" onClick={onCancel}>
            Choose Different Payment Method
          </button>

          <div className="help-info">
            <h4>Common Issues:</h4>
            <ul>
              <li>Insufficient M-Pesa balance</li>
              <li>Wrong PIN entered</li>
              <li>Payment cancelled on phone</li>
              <li>Network timeout</li>
            </ul>
            <p>Need help? Call: +254 700 123456</p>
          </div>
        </div>
      )}

      {message && !['success', 'failed', 'timeout'].includes(status) && (
        <p className="status-message">{message}</p>
      )}
    </div>
  );
};

export default MpesaPayment;
```

**Styling:** `frontend/src/components/Checkout/MpesaPayment.css`

```css
.mpesa-payment {
  max-width: 500px;
  margin: 0 auto;
  padding: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.mpesa-header {
  text-align: center;
  margin-bottom: 30px;
}

.mpesa-logo {
  width: 120px;
  height: auto;
  margin-bottom: 15px;
}

.mpesa-header h3 {
  font-size: 24px;
  color: #0A6E33;
  margin: 0;
}

.payment-amount {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 30px;
}

.payment-amount .label {
  font-size: 14px;
  color: #666;
}

.payment-amount .amount {
  font-size: 28px;
  font-weight: 700;
  color: #0A6E33;
}

.phone-input-group {
  margin-bottom: 25px;
}

.phone-input-group label {
  display: block;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.phone-input-wrapper {
  display: flex;
  align-items: center;
  border: 2px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
}

.phone-input-wrapper:focus-within {
  border-color: #0A6E33;
}

.country-code {
  padding: 12px 15px;
  background: #f5f5f5;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  border-right: 2px solid #ddd;
}

.phone-input {
  flex: 1;
  padding: 12px 15px;
  border: none;
  font-size: 18px;
  outline: none;
  font-family: 'Courier New', monospace;
}

.error-text {
  margin-top: 8px;
  font-size: 12px;
  color: #dc2626;
}

.pay-button {
  width: 100%;
  padding: 16px;
  background: #0A6E33;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
  margin-bottom: 15px;
}

.pay-button:hover:not(:disabled) {
  background: #085A29;
}

.pay-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.cancel-button {
  width: 100%;
  padding: 14px;
  background: white;
  color: #666;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-button:hover {
  background: #f5f5f5;
  border-color: #999;
}

.payment-info {
  margin-top: 25px;
  padding: 20px;
  background: #f0f9f4;
  border-radius: 8px;
  border-left: 4px solid #0A6E33;
}

.payment-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #333;
}

.payment-processing {
  text-align: center;
  padding: 20px 0;
}

.spinner {
  margin: 0 auto 20px;
  width: 60px;
  height: 60px;
  border: 6px solid #f3f3f3;
  border-top: 6px solid #0A6E33;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.processing-message {
  font-size: 18px;
  color: #333;
  margin-bottom: 20px;
}

.countdown {
  margin: 20px 0;
}

.countdown p {
  font-size: 16px;
  color: #666;
  margin-bottom: 10px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e5e5;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0A6E33, #0BA848);
  transition: width 1s linear;
}

.instructions {
  margin-top: 30px;
  padding: 20px;
  background: #fef9e7;
  border-radius: 8px;
  text-align: left;
}

.instructions h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.instructions ol {
  margin: 0;
  padding-left: 20px;
}

.instructions li {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.payment-success {
  text-align: center;
  padding: 30px;
}

.success-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: #10b981;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: white;
  animation: scale-in 0.5s ease;
}

@keyframes scale-in {
  0% { transform: scale(0); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.payment-success h3 {
  color: #10b981;
  margin-bottom: 15px;
}

.receipt-info {
  margin: 20px 0;
  padding: 15px;
  background: #f0f9ff;
  border-radius: 8px;
}

.receipt-info p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.receipt-info strong {
  color: #333;
  font-size: 16px;
  font-family: 'Courier New', monospace;
}

.redirect-message {
  margin-top: 20px;
  color: #999;
  font-size: 14px;
  font-style: italic;
}

.payment-failed {
  text-align: center;
  padding: 30px;
}

.error-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: #dc2626;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: white;
}

.payment-failed h3 {
  color: #dc2626;
  margin-bottom: 15px;
}

.error-message {
  color: #666;
  margin-bottom: 25px;
}

.retry-button {
  width: 100%;
  padding: 16px;
  background: #0A6E33;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 15px;
}

.retry-button:hover {
  background: #085A29;
}

.help-info {
  margin-top: 30px;
  padding: 20px;
  background: #fef2f2;
  border-radius: 8px;
  text-align: left;
}

.help-info h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.help-info ul {
  margin: 0 0 15px 0;
  padding-left: 20px;
}

.help-info li {
  margin: 5px 0;
  font-size: 13px;
  color: #666;
}

.help-info p {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #0A6E33;
}

/* Mobile Responsive */
@media (max-width: 600px) {
  .mpesa-payment {
    padding: 20px;
  }

  .payment-amount .amount {
    font-size: 24px;
  }

  .phone-input {
    font-size: 16px;
  }

  .pay-button {
    font-size: 16px;
    padding: 14px;
  }
}
```

Continue to next message for POS M-Pesa component and remaining sections...

