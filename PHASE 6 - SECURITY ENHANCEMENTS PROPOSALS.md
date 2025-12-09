#🔒 Phase 6: Security-First Implementation Plan

  Critical Security Principles We'll Implement:

  ---
  1. Database-Level Security (Stored Procedures & Triggers)

  Create Stored Procedures for Critical Operations:

  a) Order Creation Procedure (create_order_secure)
  CREATE OR REPLACE FUNCTION create_order_secure(
      p_customer_id INTEGER,
      p_cart_items JSONB,
      p_shipping_address TEXT,  -- Already encrypted
      p_shipping_method_id INTEGER,
      p_total NUMERIC
  ) RETURNS TABLE(order_id INTEGER, order_number VARCHAR) AS $$
  BEGIN
      -- Start transaction with row-level locking
      -- Validate inventory with FOR UPDATE lock
      -- Create order
      -- Create order items
      -- Deduct inventory atomically
      -- Create audit log entry
      -- Return order details
  END;
  $$ LANGUAGE plpgsql SECURITY DEFINER;

  b) Payment Processing Procedure (process_payment_secure)
  CREATE OR REPLACE FUNCTION process_payment_secure(
      p_order_id INTEGER,
      p_transaction_id TEXT,  -- Encrypted
      p_mpesa_phone TEXT,     -- Encrypted
      p_amount NUMERIC
  ) RETURNS BOOLEAN AS $$
  BEGIN
      -- Verify order exists and is pending
      -- Verify amount matches order total
      -- Update payment status
      -- Update order status
      -- Create audit log
      -- Prevent duplicate processing (idempotency)
  END;
  $$ LANGUAGE plpgsql SECURITY DEFINER;

  c) Inventory Deduction with Rollback (deduct_inventory_atomic)
  CREATE OR REPLACE FUNCTION deduct_inventory_atomic(
      p_variant_id INTEGER,
      p_quantity INTEGER,
      p_order_id INTEGER
  ) RETURNS BOOLEAN AS $$
  BEGIN
      -- Lock row for update
      -- Check sufficient inventory
      -- Deduct from available_quantity
      -- Add to reserved_quantity
      -- Create inventory transaction record
      -- Rollback if insufficient stock
  END;
  $$ LANGUAGE plpgsql SECURITY DEFINER;

  ---
  2. Server-Side Security (Backend Only)

  All Critical Logic Server-Side:

  ✅ NEVER Trust Client Input:
  - All calculations server-side (shipping, tax, total)
  - Re-validate cart items against database
  - Check inventory availability again before order
  - Verify pricing from database (prevent price manipulation)

  ✅ Backend Validation Chain:
  # backend/services/order_service.py
  class OrderService:
      def create_order(self, customer_id, shipping_data):
          # 1. Validate customer exists and is active
          # 2. Re-fetch cart from database (don't trust client)
          # 3. Validate each item still available
          # 4. Recalculate prices from database
          # 5. Recalculate shipping server-side
          # 6. Use stored procedure for atomic operation
          # 7. Create audit log entry
          # 8. Return encrypted order data

  ✅ Payment Callback Verification:
  # backend/services/mpesa_service.py
  class MpesaService:
      def verify_callback(self, callback_data):
          # 1. Verify M-Pesa signature
          # 2. Check callback IP whitelist
          # 3. Validate transaction ID format
          # 4. Check idempotency (prevent duplicate processing)
          # 5. Use stored procedure for payment update
          # 6. Log all callback attempts (successful or failed)

  ---
  3. Privacy by Design Implementation

  Data Minimization:

  # Collect only what's needed
  REQUIRED_CHECKOUT_DATA = {
      'shipping_address': {
          'full_name': True,      # Encrypted
          'phone': True,          # Encrypted  
          'address_line1': True,  # Encrypted
          'city': True,           # Encrypted
          'county': True,         # Encrypted
          # NO: email (already have from customer)
          # NO: ID number (not needed for delivery)
          # NO: date of birth (not needed)
      }
  }

  Immediate Encryption:

  # backend/routes/orders.py
  @api.route('/orders', methods=['POST'])
  @jwt_required()
  def create_order():
      # 1. Encrypt address BEFORE storing
      encrypted_address = address_encryption.encrypt(
          json.dumps(shipping_address)
      )

      # 2. Use stored procedure (server-side only)
      order = db.session.execute(
          'SELECT * FROM create_order_secure(:customer_id, :data)',
          {'customer_id': customer_id, 'data': encrypted_data}
      )

      # 3. Create audit log
      log_order_creation(customer_id, order.id, request.remote_addr)

      # 4. Return minimal data to client
      return jsonify(order.to_dict(minimal=True))

  ---
  4. Audit Trail & Compliance

  Create Audit Log Table:

  CREATE TABLE order_audit_log (
      id SERIAL PRIMARY KEY,
      order_id INTEGER REFERENCES orders(id),
      action VARCHAR(50) NOT NULL,  -- created, payment_initiated, paid, shipped, etc.
      performed_by INTEGER,          -- customer_id or employee_id
      ip_address INET,
      user_agent TEXT,
      metadata JSONB,                -- Additional context
      created_at TIMESTAMP DEFAULT NOW()
  );

  CREATE INDEX idx_order_audit_order ON order_audit_log(order_id);
  CREATE INDEX idx_order_audit_action ON order_audit_log(action);

  Payment Callback Audit:

  CREATE TABLE payment_callback_log (
      id SERIAL PRIMARY KEY,
      order_id INTEGER REFERENCES orders(id),
      callback_data_encrypted TEXT,  -- Full encrypted callback payload
      source_ip INET,
      signature_valid BOOLEAN,
      processed BOOLEAN DEFAULT FALSE,
      processed_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT NOW()
  );

  ---
  5. Rate Limiting & DDoS Protection

  Implement Flask-Limiter:

  # backend/app.py
  from flask_limiter import Limiter
  from flask_limiter.util import get_remote_address

  limiter = Limiter(
      app,
      key_func=get_remote_address,
      default_limits=["200 per day", "50 per hour"]
  )

  # Critical endpoints with stricter limits
  @api.route('/orders', methods=['POST'])
  @limiter.limit("10 per hour")  # Max 10 orders per hour per IP
  @jwt_required()
  def create_order():
      pass

  @api.route('/payments/mpesa/initiate', methods=['POST'])
  @limiter.limit("5 per minute")  # Max 5 payment attempts per minute
  @jwt_required()
  def initiate_mpesa_payment():
      pass

  ---
  6. Idempotency & Race Condition Prevention

  Idempotency Keys:

  # backend/models/database_models.py
  class Order(db.Model):
      # ...
      idempotency_key = db.Column(db.String(255), unique=True, index=True)

  # Client sends idempotency key with request
  # Server checks if order with this key exists
  # Prevents duplicate orders from double-clicks

  Database Locks:

  # backend/services/order_service.py
  def create_order_atomic(customer_id, cart_items):
      with db.session.begin_nested():  # Savepoint
          # Lock inventory rows
          for item in cart_items:
              inventory = Inventory.query.filter_by(
                  variant_id=item['variant_id']
              ).with_for_update().first()

              if inventory.quantity < item['quantity']:
                  raise InsufficientStockError()

              # Deduct atomically
              inventory.quantity -= item['quantity']

          # Create order
          order = Order(...)
          db.session.add(order)
          db.session.flush()

      db.session.commit()

  ---
  7. M-Pesa Security Measures

  Callback Signature Verification:

  # backend/services/mpesa_service.py
  import hmac
  import hashlib

  class MpesaService:
      def verify_callback_signature(self, callback_data, signature):
          """Verify M-Pesa callback authenticity"""
          expected_signature = hmac.new(
              self.callback_secret.encode(),
              json.dumps(callback_data).encode(),
              hashlib.sha256
          ).hexdigest()

          return hmac.compare_digest(expected_signature, signature)

      def verify_callback_ip(self, source_ip):
          """Whitelist M-Pesa callback IPs"""
          MPESA_CALLBACK_IPS = [
              '196.201.214.0/24',  # M-Pesa production IPs
              # Add sandbox IPs
          ]
          return source_ip in MPESA_CALLBACK_IPS

  ---
  📋 Revised Phase 6 Todo List (Security-Enhanced)

  Backend (12 tasks)

  1. ✅ Review database schema
  2. Create stored procedures (NEW)
    - create_order_secure()
    - process_payment_secure()
    - deduct_inventory_atomic()
  3. Create audit log tables (NEW)
    - order_audit_log
    - payment_callback_log
  4. Install Flask-Limiter (NEW)
  5. Create Order models serialization
  6. Create shipping calculation service
  7. Create order routes with server-side validation
  8. Create M-Pesa service with callback verification
  9. Create payment routes with idempotency
  10. Implement inventory locking mechanism
  11. Add audit logging to all critical operations
  12. Test stored procedures and rollback scenarios

  Frontend (6 tasks - unchanged)

  13. Create Checkout page (client only submits data)
  14. Shipping address form (validation client-side, re-validated server-side)
  15. Payment integration UI (displays status, no sensitive logic)
  16. Order confirmation page (read-only display)
  17. Order history page (read-only display)
  18. Cart checkout integration

  Testing & Security Audit (5 tasks)

  19. Security testing (NEW)
    - SQL injection tests
    - XSS prevention tests
    - CSRF token validation
    - Rate limiting tests
  20. M-Pesa sandbox testing
  21. End-to-end checkout testing
  22. Penetration testing (NEW)
    - Attempt price manipulation
    - Attempt inventory bypass
    - Test callback spoofing
  23. Update documentation

  ---
  Total: 23 Tasks (12 backend + 6 frontend + 5 testing)

  Key Security Additions:
  - ✅ Stored procedures for atomic operations
  - ✅ Database-level locking and transactions
  - ✅ Audit logging for compliance
  - ✅ Rate limiting for DDoS protection
  - ✅ Callback signature verification
  - ✅ IP whitelisting for callbacks
  - ✅ Idempotency for payment operations
  - ✅ Server-side recalculation of ALL values
  - ✅ Input validation and sanitization
  - ✅ NEVER trust client data

  ---
  This approach follows:
  - ✅ Privacy by Design (GDPR Article 25)
  - ✅ Security by Design (ISO 27001)
  - ✅ PCI DSS principles (payment security)
  - ✅ Principle of Least Privilege
  - ✅ Defense in Depth

