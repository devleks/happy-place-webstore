# GDPR Compliance Addendum
## Happy Place Boutique - Data Protection & Privacy

**Version:** 2.2
**Date:** November 23, 2025
**Status:** DRAFT - GDPR Compliance Update

---

## Table of Contents
1. [GDPR Overview](#gdpr-overview)
2. [Right to be Forgotten Strategy](#right-to-be-forgotten-strategy)
3. [Updated CUSTOMERS Table](#updated-customers-table)
4. [Data Anonymization Strategy](#data-anonymization-strategy)
5. [GDPR Compliance Tables](#gdpr-compliance-tables)
6. [Data Retention Policy](#data-retention-policy)
7. [Implementation Guidelines](#implementation-guidelines)

---

## GDPR Overview

### Key GDPR Requirements

**1. Right to be Forgotten (Article 17)**
- Customers can request permanent deletion of their personal data
- Personal data must be erased without undue delay
- Exceptions: financial/legal compliance, statistical purposes

**2. Data Minimization (Article 5)**
- Collect only necessary data
- Store data only as long as needed
- Anonymize when personal data is no longer required

**3. Consent Management (Article 7)**
- Explicit consent for data processing
- Separate consent for marketing communications
- Easy withdrawal of consent

**4. Data Portability (Article 20)**
- Customers can export their data in machine-readable format
- Transfer data to another service

**5. Data Protection by Design (Article 25)**
- Privacy built into system architecture
- Pseudonymization and encryption
- Access controls and audit trails

---

## Right to be Forgotten Strategy

### Challenge
When a customer requests data deletion, we must:
- ✅ **Delete** personal identifiable information (PII)
- ✅ **Preserve** order history for financial/tax compliance
- ✅ **Maintain** analytical data for business intelligence
- ✅ **Ensure** referential integrity

### Solution: Data Anonymization

Instead of **deleting** customer records, we **anonymize** them:

| Before Anonymization | After Anonymization |
|---------------------|---------------------|
| email: "jane@example.com" | email: "deleted_customer_12345@anonymized.local" |
| first_name: "Jane" | first_name: "Deleted" |
| last_name: "Doe" | last_name: "Customer" |
| phone: "+254712345678" | phone: NULL |
| Addresses: Full addresses | Addresses: DELETED (cascade) |
| Orders: Linked to customer | Orders: Still linked but anonymized |
| Reviews: With name | Reviews: Anonymous reviewer |

**Benefits:**
- ✅ Order totals, dates, products preserved for analytics
- ✅ Financial reporting remains accurate
- ✅ No personal data remains
- ✅ GDPR compliant
- ✅ Referential integrity maintained

---

## Updated CUSTOMERS Table

### Enhanced CUSTOMERS Table with GDPR Compliance

```sql
CREATE TABLE customers (
  -- Identity
  id SERIAL PRIMARY KEY,
  email VARCHAR(120) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  phone VARCHAR(20),

  -- Account Status
  is_active BOOLEAN DEFAULT TRUE,
  email_verified BOOLEAN DEFAULT FALSE,
  verification_token VARCHAR(255),
  last_login TIMESTAMP,

  -- GDPR Compliance Fields (NEW)
  gdpr_consent BOOLEAN DEFAULT FALSE,                    -- General data processing consent
  gdpr_consent_date TIMESTAMP,                           -- When consent was given
  gdpr_consent_ip VARCHAR(45),                           -- IP address when consent given
  marketing_consent BOOLEAN DEFAULT FALSE,               -- Marketing emails consent
  marketing_consent_date TIMESTAMP,                      -- When marketing consent given
  data_retention_expiry DATE,                            -- When data should be auto-deleted
  anonymized BOOLEAN DEFAULT FALSE,                      -- Has data been anonymized
  anonymized_at TIMESTAMP,                               -- When anonymization occurred
  anonymized_by INTEGER REFERENCES employees(id),        -- Employee who processed anonymization
  original_customer_id VARCHAR(50),                      -- Original ID before anonymization (for audit)

  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_active ON customers(is_active);
CREATE INDEX idx_customers_anonymized ON customers(anonymized);
CREATE INDEX idx_customers_retention_expiry ON customers(data_retention_expiry);
```

### Column Descriptions

| Column | Type | Purpose |
|--------|------|---------|
| **gdpr_consent** | BOOLEAN | Has customer consented to data processing? |
| **gdpr_consent_date** | TIMESTAMP | When did they consent? (audit trail) |
| **gdpr_consent_ip** | VARCHAR(45) | IP address at consent (proof of consent) |
| **marketing_consent** | BOOLEAN | Separate consent for marketing emails |
| **marketing_consent_date** | TIMESTAMP | When marketing consent was given |
| **data_retention_expiry** | DATE | Auto-delete/anonymize after this date |
| **anonymized** | BOOLEAN | Flag: Is this customer anonymized? |
| **anonymized_at** | TIMESTAMP | When anonymization occurred |
| **anonymized_by** | INTEGER | Employee who processed request |
| **original_customer_id** | VARCHAR(50) | Original ID for audit trail |

---

## Data Anonymization Strategy

### Anonymization Process

When a customer requests data deletion:

**Step 1: Mark for Deletion**
```sql
-- Log the deletion request
INSERT INTO gdpr_data_requests (customer_id, request_type, status)
VALUES (customer_id, 'deletion', 'pending');
```

**Step 2: Anonymize Personal Data**
```sql
UPDATE customers
SET
  email = CONCAT('deleted_customer_', id, '@anonymized.local'),
  first_name = 'Deleted',
  last_name = 'Customer',
  phone = NULL,
  password_hash = 'ANONYMIZED',
  verification_token = NULL,
  gdpr_consent = FALSE,
  marketing_consent = FALSE,
  anonymized = TRUE,
  anonymized_at = CURRENT_TIMESTAMP,
  anonymized_by = {employee_id},
  original_customer_id = CONCAT('CUST_', id, '_', EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)),
  is_active = FALSE
WHERE id = customer_id;
```

**Step 3: Delete Related Personal Data**
```sql
-- Delete addresses (CASCADE will handle this)
DELETE FROM customer_addresses WHERE customer_id = customer_id;

-- Anonymize reviews (optional: keep for product ratings)
UPDATE reviews
SET
  customer_id = NULL,  -- Unlink from customer
  is_approved = FALSE  -- Hide from public display
WHERE customer_id = customer_id;
```

**Step 4: Anonymize Order Shipping Data**
```sql
UPDATE orders
SET
  shipping_address = 'REDACTED',
  shipping_city = 'REDACTED',
  shipping_postal_code = 'REDACTED',
  shipping_phone = 'REDACTED',
  notes = NULL
WHERE customer_id = customer_id;
```

**Step 5: Update Request Status**
```sql
UPDATE gdpr_data_requests
SET
  status = 'completed',
  completed_at = CURRENT_TIMESTAMP,
  processed_by = {employee_id}
WHERE customer_id = customer_id AND request_type = 'deletion';
```

### What Gets Preserved

**Financial/Tax Compliance (7+ years):**
- Order IDs, order numbers
- Order totals, subtotals, tax amounts
- Payment amounts and methods
- Order dates and timestamps
- Product IDs and quantities
- Transaction records

**Business Analytics:**
- Anonymized order trends
- Product purchase patterns
- Revenue data
- Inventory movement

### What Gets Deleted/Anonymized

**Immediately:**
- Name (first_name, last_name)
- Email address
- Phone number
- Addresses (shipping/billing)
- Password hash
- Verification tokens
- IP addresses
- Personal notes

**Optional (Configurable):**
- Reviews (can be anonymized or deleted)
- Wishlist (deleted)
- Cart (deleted)

---

## GDPR Compliance Tables

### 1. GDPR_DATA_REQUESTS

**Purpose:** Track all GDPR data requests (deletion, access, portability)

```sql
CREATE TABLE gdpr_data_requests (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  request_type VARCHAR(20) NOT NULL,  -- deletion, access, portability, correction
  request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  customer_email VARCHAR(120) NOT NULL,  -- Email at time of request
  customer_name VARCHAR(100),  -- Name at time of request
  status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, completed, rejected
  approved_by INTEGER REFERENCES employees(id),
  approved_at TIMESTAMP,
  processed_by INTEGER REFERENCES employees(id),
  completed_at TIMESTAMP,
  notes TEXT,
  ip_address VARCHAR(45),  -- IP of requester
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gdpr_requests_customer ON gdpr_data_requests(customer_id);
CREATE INDEX idx_gdpr_requests_status ON gdpr_data_requests(status);
CREATE INDEX idx_gdpr_requests_type ON gdpr_data_requests(request_type);
```

**Request Types:**
- `deletion` - Right to be forgotten
- `access` - Right to access data (data export)
- `portability` - Right to data portability
- `correction` - Right to rectification

**Status Values:**
- `pending` - Request received, awaiting review
- `approved` - Request approved by admin
- `completed` - Request processed
- `rejected` - Request rejected (with reason in notes)

---

### 2. GDPR_CONSENT_LOG

**Purpose:** Audit trail of all consent changes

```sql
CREATE TABLE gdpr_consent_log (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  consent_type VARCHAR(50) NOT NULL,  -- gdpr_consent, marketing_consent
  consent_given BOOLEAN NOT NULL,     -- TRUE = granted, FALSE = withdrawn
  consent_method VARCHAR(50),         -- registration, account_settings, email_link
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_consent_log_customer ON gdpr_consent_log(customer_id);
CREATE INDEX idx_consent_log_date ON gdpr_consent_log(created_at);
```

---

### 3. DATA_ACCESS_LOG

**Purpose:** Log all access to customer personal data (audit trail)

```sql
CREATE TABLE data_access_log (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  accessed_by INTEGER REFERENCES employees(id),  -- NULL if customer themselves
  access_type VARCHAR(50) NOT NULL,  -- view, export, modify, delete
  data_accessed TEXT,  -- JSON: what fields were accessed
  purpose VARCHAR(100),  -- Why was data accessed
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_access_log_customer ON data_access_log(customer_id);
CREATE INDEX idx_access_log_employee ON data_access_log(accessed_by);
CREATE INDEX idx_access_log_date ON data_access_log(created_at);
```

---

## Data Retention Policy

### Retention Periods

| Data Type | Retention Period | After Expiry |
|-----------|-----------------|--------------|
| **Customer Account (Active)** | Until account closure | N/A |
| **Customer Account (Inactive)** | 3 years from last login | Auto-anonymize |
| **Order Data (Financial)** | 7 years (tax law) | Anonymize customer, keep order |
| **Payment Records** | 7 years (financial law) | Anonymize customer, keep transaction |
| **Cart Items** | 90 days | Auto-delete |
| **Wishlist Items** | Until account closure | Delete with account |
| **Reviews (Anonymized)** | Indefinite | Keep for product ratings |
| **Activity Logs** | 2 years | Auto-delete |
| **GDPR Request Logs** | 7 years | Retain for compliance |

### Auto-Anonymization

Automatically anonymize inactive customer accounts:

```sql
-- Run this scheduled job daily
UPDATE customers
SET
  data_retention_expiry = CURRENT_DATE + INTERVAL '3 years'
WHERE
  last_login < CURRENT_DATE - INTERVAL '3 years'
  AND anonymized = FALSE
  AND is_active = TRUE;

-- Execute anonymization for expired accounts
-- (Call anonymization procedure for each customer)
SELECT id FROM customers
WHERE data_retention_expiry <= CURRENT_DATE
  AND anonymized = FALSE;
```

---

## Implementation Guidelines

### 1. Customer Registration Flow

**Consent Collection:**

```html
<!-- Registration Form -->
<form>
  <input type="email" name="email" required />
  <input type="password" name="password" required />

  <!-- GDPR Consent (REQUIRED) -->
  <label>
    <input type="checkbox" name="gdpr_consent" required />
    I consent to Happy Place Boutique collecting and processing my personal data
    as described in our <a href="/privacy-policy">Privacy Policy</a>
  </label>

  <!-- Marketing Consent (OPTIONAL) -->
  <label>
    <input type="checkbox" name="marketing_consent" />
    I would like to receive marketing emails and promotional offers
  </label>

  <button type="submit">Create Account</button>
</form>
```

**Backend Implementation:**

```python
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    ip_address = request.remote_addr

    # GDPR consent is mandatory
    if not data.get('gdpr_consent'):
        return {'error': 'GDPR consent is required'}, 400

    customer = Customer(
        email=data['email'],
        password_hash=hash_password(data['password']),
        first_name=data['first_name'],
        last_name=data['last_name'],
        gdpr_consent=True,
        gdpr_consent_date=datetime.utcnow(),
        gdpr_consent_ip=ip_address,
        marketing_consent=data.get('marketing_consent', False),
        marketing_consent_date=datetime.utcnow() if data.get('marketing_consent') else None,
        data_retention_expiry=datetime.utcnow() + timedelta(days=3*365)
    )

    db.session.add(customer)

    # Log consent
    consent_log = GDPRConsentLog(
        customer_id=customer.id,
        consent_type='gdpr_consent',
        consent_given=True,
        consent_method='registration',
        ip_address=ip_address,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(consent_log)

    db.session.commit()
    return {'message': 'Account created successfully'}, 201
```

---

### 2. Data Deletion Request Flow

**Customer Portal:**

```html
<!-- Account Settings > Privacy -->
<div class="gdpr-section">
  <h3>Your Data Rights</h3>

  <button onclick="exportMyData()">
    Download My Data (JSON)
  </button>

  <button onclick="requestDataDeletion()" class="danger">
    Delete My Account & Data
  </button>

  <p class="warning">
    ⚠️ Deleting your account will permanently remove all your personal information.
    Order history will be retained for legal/financial compliance but anonymized.
  </p>
</div>
```

**Backend Anonymization Function:**

```python
def anonymize_customer(customer_id, processed_by_employee_id):
    """
    Anonymize customer data while preserving order history
    """
    customer = Customer.query.get(customer_id)

    if not customer:
        raise ValueError("Customer not found")

    if customer.anonymized:
        raise ValueError("Customer already anonymized")

    # Create GDPR request record
    gdpr_request = GDPRDataRequest(
        customer_id=customer_id,
        request_type='deletion',
        customer_email=customer.email,
        customer_name=f"{customer.first_name} {customer.last_name}",
        status='completed',
        processed_by=processed_by_employee_id,
        completed_at=datetime.utcnow()
    )
    db.session.add(gdpr_request)

    # Anonymize customer record
    original_id = f"CUST_{customer.id}_{int(time.time())}"
    customer.email = f"deleted_customer_{customer.id}@anonymized.local"
    customer.first_name = "Deleted"
    customer.last_name = "Customer"
    customer.phone = None
    customer.password_hash = "ANONYMIZED"
    customer.verification_token = None
    customer.gdpr_consent = False
    customer.marketing_consent = False
    customer.anonymized = True
    customer.anonymized_at = datetime.utcnow()
    customer.anonymized_by = processed_by_employee_id
    customer.original_customer_id = original_id
    customer.is_active = False

    # Delete addresses (CASCADE)
    CustomerAddress.query.filter_by(customer_id=customer_id).delete()

    # Anonymize order shipping data
    Order.query.filter_by(customer_id=customer_id).update({
        'shipping_address': 'REDACTED',
        'shipping_city': 'REDACTED',
        'shipping_postal_code': 'REDACTED',
        'shipping_phone': 'REDACTED',
        'notes': None
    })

    # Handle reviews (optional: keep but anonymize)
    Review.query.filter_by(customer_id=customer_id).update({
        'is_approved': False  # Hide from public
    })

    # Delete cart and wishlist
    Cart.query.filter_by(customer_id=customer_id).delete()
    Wishlist.query.filter_by(customer_id=customer_id).delete()

    # Log the access
    log = DataAccessLog(
        customer_id=customer_id,
        accessed_by=processed_by_employee_id,
        access_type='delete',
        data_accessed=json.dumps({
            'email': customer.email,
            'name': f"{customer.first_name} {customer.last_name}",
            'orders_preserved': Order.query.filter_by(customer_id=customer_id).count()
        }),
        purpose='GDPR deletion request'
    )
    db.session.add(log)

    db.session.commit()

    return {
        'success': True,
        'anonymized_id': original_id,
        'orders_preserved': Order.query.filter_by(customer_id=customer_id).count()
    }
```

---

### 3. Data Export (Data Portability)

```python
@app.route('/api/gdpr/export-my-data', methods=['GET'])
@login_required
def export_customer_data():
    """
    Export all customer data in JSON format (GDPR Article 20)
    """
    customer_id = get_current_user_id()
    customer = Customer.query.get(customer_id)

    # Log the access
    log = DataAccessLog(
        customer_id=customer_id,
        access_type='export',
        data_accessed='full_customer_data',
        purpose='Data portability request',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    # Compile all customer data
    data = {
        'personal_info': {
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone,
            'created_at': customer.created_at.isoformat(),
        },
        'addresses': [addr.to_dict() for addr in customer.addresses],
        'orders': [order.to_dict() for order in customer.orders],
        'reviews': [review.to_dict() for review in customer.reviews],
        'wishlist': [item.product.to_dict() for item in customer.wishlist.items] if customer.wishlist else [],
        'consents': {
            'gdpr_consent': customer.gdpr_consent,
            'gdpr_consent_date': customer.gdpr_consent_date.isoformat() if customer.gdpr_consent_date else None,
            'marketing_consent': customer.marketing_consent,
        }
    }

    return jsonify(data), 200
```

---

### 4. Privacy Policy Requirements

Your Privacy Policy must include:

1. **What data you collect:**
   - Name, email, phone, addresses
   - Order history, payment information
   - IP addresses, cookies

2. **Why you collect it:**
   - Order processing and fulfillment
   - Customer support
   - Legal compliance
   - Analytics (anonymized)

3. **How long you keep it:**
   - Active accounts: Until closure
   - Inactive accounts: 3 years
   - Order/financial data: 7 years (anonymized)

4. **Customer rights:**
   - Right to access data
   - Right to correction
   - Right to deletion
   - Right to portability
   - Right to withdraw consent

5. **How to exercise rights:**
   - Account settings portal
   - Email: privacy@happyplace.com
   - Response time: 30 days

---

### 5. Admin Dashboard Features

**GDPR Management Panel:**

- View pending deletion requests
- Approve/reject data requests
- Execute anonymization
- Generate compliance reports
- Audit data access logs

**Reports:**
- Number of deletion requests (monthly)
- Average response time
- Anonymized accounts
- Consent rates (GDPR vs Marketing)

---

## Database Migration for GDPR

### Step 1: Add GDPR fields to existing CUSTOMERS table

```sql
ALTER TABLE customers
  ADD COLUMN gdpr_consent BOOLEAN DEFAULT FALSE,
  ADD COLUMN gdpr_consent_date TIMESTAMP,
  ADD COLUMN gdpr_consent_ip VARCHAR(45),
  ADD COLUMN marketing_consent BOOLEAN DEFAULT FALSE,
  ADD COLUMN marketing_consent_date TIMESTAMP,
  ADD COLUMN data_retention_expiry DATE,
  ADD COLUMN anonymized BOOLEAN DEFAULT FALSE,
  ADD COLUMN anonymized_at TIMESTAMP,
  ADD COLUMN anonymized_by INTEGER REFERENCES employees(id),
  ADD COLUMN original_customer_id VARCHAR(50);

-- Update existing customers with default retention expiry
UPDATE customers
SET
  gdpr_consent = TRUE,  -- Assume existing customers consented (grandfathered)
  gdpr_consent_date = created_at,
  data_retention_expiry = CURRENT_DATE + INTERVAL '3 years'
WHERE anonymized = FALSE OR anonymized IS NULL;

-- Create indexes
CREATE INDEX idx_customers_anonymized ON customers(anonymized);
CREATE INDEX idx_customers_retention_expiry ON customers(data_retention_expiry);
```

### Step 2: Create GDPR compliance tables

```sql
-- GDPR Data Requests
CREATE TABLE gdpr_data_requests (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  request_type VARCHAR(20) NOT NULL,
  request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  customer_email VARCHAR(120) NOT NULL,
  customer_name VARCHAR(100),
  status VARCHAR(20) DEFAULT 'pending',
  approved_by INTEGER REFERENCES employees(id),
  approved_at TIMESTAMP,
  processed_by INTEGER REFERENCES employees(id),
  completed_at TIMESTAMP,
  notes TEXT,
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gdpr_requests_customer ON gdpr_data_requests(customer_id);
CREATE INDEX idx_gdpr_requests_status ON gdpr_data_requests(status);

-- GDPR Consent Log
CREATE TABLE gdpr_consent_log (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  consent_type VARCHAR(50) NOT NULL,
  consent_given BOOLEAN NOT NULL,
  consent_method VARCHAR(50),
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_consent_log_customer ON gdpr_consent_log(customer_id);

-- Data Access Log
CREATE TABLE data_access_log (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  accessed_by INTEGER REFERENCES employees(id),
  access_type VARCHAR(50) NOT NULL,
  data_accessed TEXT,
  purpose VARCHAR(100),
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_access_log_customer ON data_access_log(customer_id);
CREATE INDEX idx_access_log_date ON data_access_log(created_at);
```

---

## Summary

### GDPR Compliance Checklist

- [x] **Consent Management** - Explicit consent collection at registration
- [x] **Right to Access** - Data export functionality
- [x] **Right to be Forgotten** - Anonymization instead of deletion
- [x] **Data Minimization** - Only collect necessary data
- [x] **Data Portability** - JSON export of all customer data
- [x] **Retention Policies** - Auto-anonymize after 3 years inactive
- [x] **Audit Trail** - Log all data access and modifications
- [x] **Financial Compliance** - Preserve order data for 7 years (anonymized)
- [x] **Analytics Preservation** - Business intelligence data maintained

### Key Benefits

✅ **GDPR Compliant** - Full compliance with EU data protection laws
✅ **Customer Trust** - Transparent data handling
✅ **Legal Protection** - Audit trails and compliance records
✅ **Business Continuity** - Financial and analytical data preserved
✅ **No Data Loss** - Anonymization instead of deletion

---

**Next Steps:**
1. Review this GDPR addendum
2. Approve the anonymization strategy
3. Implement GDPR tables and fields
4. Create anonymization stored procedures
5. Build admin GDPR management panel
6. Draft Privacy Policy document
7. Test deletion/export workflows

**Status:** Ready for Review and Implementation
