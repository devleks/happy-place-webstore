# Security Audit Plan - Happy Place Boutique
## Day 10: Comprehensive Security Testing

**Date:** January 4, 2026
**Version:** 1.0
**Auditor:** Security Review Team
**Scope:** Backend API, Authentication, Data Protection, Authorization

---

## 1. SECURITY CONFIGURATION REVIEW

### ✅ Completed - Security Infrastructure Analysis

**Encryption Implementation:**
- **Algorithm:** MultiFernet (AES-128-CBC + HMAC-SHA256)
- **Key Management:** Separate cipher sets for customer, address, and payment data
- **Key Rotation:** Zero-downtime rotation support via MultiFernet
- **Audit Logging:** Decryption operations logged for compliance
- **Implementation:** `backend/services/encryption.py`

**Password Hashing:**
- **Customers:** Werkzeug Scrypt (`models/database_models.py:127`)
- **Employees:** Werkzeug Scrypt (`models/database_models.py:301`)
- **Storage:** 255-character hash field (sufficient for bcrypt/scrypt/argon2)
- **Method:** One-way hash (no reversible encryption)

**JWT Configuration:**
- **Algorithm:** HS256 (HMAC-SHA256)
- **Access Token Expiry:** 15 minutes (configurable via `JWT_ACCESS_EXPIRES_MINUTES`)
- **Refresh Token Expiry:** 7 days (configurable via `JWT_REFRESH_EXPIRES_DAYS`)
- **Identity Claim:** `sub` (standard JWT claim)
- **Secret Key:** Environment variable `JWT_SECRET_KEY` (32+ chars required in production)

**Email Hashing:**
- **Algorithm:** SHA-256
- **Purpose:** Searchable index for login lookup
- **Normalization:** Lowercase + whitespace trimmed
- **Field:** `email_hash` (64-character hex string, indexed)

**Additional Security Features:**
- **Account Lockout:** Employee accounts track `failed_login_attempts` and `account_locked_until`
- **2FA Support:** Employee TOTP fields (`totp_enabled`, `totp_secret`, `backup_codes`)
- **Session Tracking:** `EmployeeSession` table for audit trail
- **GDPR Compliance:** Anonymization support, consent tracking, data access logs

---

## 2. SECURITY TESTING CHECKLIST

### 2.1 SQL Injection Testing

**Critical Endpoints to Test:**

1. **Authentication Endpoints** (`/api/auth`)
   - [ ] POST `/auth/login` - Email parameter
   - [ ] POST `/auth/employee/login` - Email parameter
   - [ ] POST `/auth/register` - All input fields

2. **Product Endpoints** (`/api`)
   - [ ] GET `/products?search=` - Search parameter
   - [ ] GET `/products?category=` - Category filter
   - [ ] GET `/products/:slug` - Slug parameter

3. **Order Endpoints** (`/api/orders`)
   - [ ] GET `/orders?status=` - Status filter
   - [ ] GET `/orders/:id` - Order ID parameter

4. **Admin Endpoints** (`/api/admin`)
   - [ ] GET `/admin/customers?search=` - Search parameter
   - [ ] GET `/admin/orders?status=` - Status filter
   - [ ] GET `/admin/inventory?category=` - Category filter
   - [ ] GET `/admin/reports/sales?start_date=&end_date=` - Date parameters

**Test Payloads:**
```sql
-- Basic injection
' OR '1'='1
1' OR '1'='1' --
admin'--
' UNION SELECT NULL--

-- Time-based blind injection
1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--

-- PostgreSQL-specific
1'; DROP TABLE customers; --
1' UNION SELECT version()--
```

**Expected Result:** All inputs should be properly parameterized via SQLAlchemy. No SQL execution of injected payloads.

---

### 2.2 Cross-Site Scripting (XSS) Testing

**Endpoints to Test:**

1. **User-Generated Content**
   - [ ] POST `/api/reviews` - Review text
   - [ ] PUT `/api/customers/profile` - Name fields
   - [ ] POST `/api/cart/items` - Notes/comments (if any)

2. **Admin Inputs**
   - [ ] POST `/api/admin/products` - Product name, description
   - [ ] POST `/api/admin/categories` - Category name, description
   - [ ] POST `/api/admin/promotions` - Promotion name, description

**Test Payloads:**
```html
<!-- Basic XSS -->
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>

<!-- Event handler injection -->
<div onmouseover="alert('XSS')">hover me</div>

<!-- SVG-based XSS -->
<svg/onload=alert('XSS')>

<!-- Encoded XSS -->
&#60;script&#62;alert('XSS')&#60;/script&#62;
```

**Expected Result:** All outputs should be properly escaped. Check React's JSX automatic escaping.

---

### 2.3 CSRF Protection Testing

**Authentication Flow:**
- [ ] Verify JWT-based auth doesn't require CSRF tokens (stateless)
- [ ] Check for state-changing GET requests (should all be POST/PUT/DELETE)
- [ ] Verify no session cookies are used (localStorage JWT only)

**Critical Actions to Test:**
- [ ] Order creation without valid JWT
- [ ] Password change without valid JWT
- [ ] Admin actions (employee creation, product deletion) without valid JWT

**Expected Result:** All state-changing operations require valid JWT in Authorization header.

---

### 2.4 JWT Token Security Audit

**Token Generation:**
- [ ] Verify secret key strength (32+ characters)
- [ ] Check algorithm (HS256 only, no "none" algorithm)
- [ ] Confirm expiration times (access: 15min, refresh: 7 days)
- [ ] Verify claims structure (`sub`, `user_type`, `role`)

**Token Validation:**
- [ ] Test expired token rejection
- [ ] Test invalid signature rejection
- [ ] Test algorithm confusion attack (swap HS256 to RS256)
- [ ] Test missing/malformed tokens

**Token Storage:**
- [ ] Verify localStorage usage (not sessionStorage for persistence)
- [ ] Check for token leakage in logs
- [ ] Verify no tokens in URL query parameters

**Test Commands:**
```bash
# Test expired token
curl -X GET http://127.0.0.1:5001/api/orders \
  -H "Authorization: Bearer <EXPIRED_TOKEN>"

# Test invalid signature
curl -X GET http://127.0.0.1:5001/api/orders \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"

# Test missing token
curl -X GET http://127.0.0.1:5001/api/orders
```

---

### 2.5 Authentication & Authorization Testing

**Authentication Tests:**
- [ ] Test weak password acceptance (enforce strength requirements)
- [ ] Test account enumeration (login error messages)
- [ ] Test brute-force protection (rate limiting)
- [ ] Test password reset flow (if implemented)

**Authorization Tests:**
- [ ] Customer accessing admin endpoints (`/api/admin/*`)
- [ ] Cashier accessing manager-only endpoints
- [ ] Non-admin creating employees
- [ ] Horizontal privilege escalation (user A accessing user B's data)

**Role-Based Access Control:**
```python
# Middleware decorators to verify:
@customer_required
@employee_required
@admin_required
@manager_required
@packer_required
@shipper_required
```

**Test Cases:**
```bash
# Customer token accessing admin endpoint
curl -X GET http://127.0.0.1:5001/api/admin/dashboard/metrics \
  -H "Authorization: Bearer <CUSTOMER_TOKEN>"

# Expected: 403 Forbidden

# Cashier token accessing admin-only action
curl -X POST http://127.0.0.1:5001/api/admin/employees \
  -H "Authorization: Bearer <CASHIER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test","role":"admin"}'

# Expected: 403 Forbidden
```

---

### 2.6 Password Hashing Verification

**Configuration Check:**
- [x] Customers use Scrypt ✅ (database_models.py:127)
- [x] Employees use Scrypt ✅ (database_models.py:301)
- [ ] Verify no plaintext passwords in database
- [ ] Check password complexity requirements

**Database Inspection:**
```bash
# Connect to database
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -d happy_place_db

# Check password hash format (should start with 'scrypt:')
SELECT id, email_hash, LEFT(password_hash, 20) FROM customers LIMIT 5;
SELECT id, email, LEFT(password_hash, 20) FROM employees LIMIT 5;

# Verify no NULL password hashes
SELECT COUNT(*) FROM customers WHERE password_hash IS NULL;
SELECT COUNT(*) FROM employees WHERE password_hash IS NULL;
```

**Password Strength Testing:**
- [ ] Test weak password rejection (e.g., "password123")
- [ ] Test short password rejection (< 8 characters)
- [ ] Test common passwords (top 10,000 list)

---

### 2.7 Input Validation & Sanitization

**Endpoints to Test:**

1. **Registration/Profile Updates**
   - [ ] Email format validation
   - [ ] Phone number format validation
   - [ ] Address field length limits
   - [ ] Special character handling

2. **Product/Order Operations**
   - [ ] Negative quantity values
   - [ ] Extremely large numbers (integer overflow)
   - [ ] Null/undefined values
   - [ ] Empty strings vs NULL

3. **Payment Fields**
   - [ ] M-Pesa phone format validation (254XXXXXXXXX)
   - [ ] Amount tampering (negative prices)
   - [ ] Currency validation

**Test Payloads:**
```json
{
  "quantity": -1,
  "price": -100.00,
  "email": "not-an-email",
  "phone": "123",
  "mpesa_phone": "999"
}
```

**Expected Result:** All inputs validated at API layer before database operations.

---

### 2.8 Encryption & Data Protection

**MultiFernet Encryption Tests:**
- [ ] Verify customer PII is encrypted at rest (email, name, phone)
- [ ] Verify address fields are encrypted (street, city, postal code)
- [ ] Verify payment fields are encrypted (M-Pesa phone)
- [ ] Test decryption with invalid keys (should fail gracefully)
- [ ] Verify key rotation works without data loss

**Database Inspection:**
```bash
# Check encrypted fields (should be base64-encoded gibberish)
SELECT id, email_encrypted, first_name_encrypted FROM customers LIMIT 1;

# Should NOT contain plaintext
# Should look like: "gAAAAABf..."
```

**Key Management:**
- [ ] Verify encryption keys in environment variables (not hardcoded)
- [ ] Check `.env` is in `.gitignore`
- [ ] Verify production validation in `config.py:validate_secrets()`

---

### 2.9 HTTPS/TLS Configuration (Production)

**Certificate Validation:**
- [ ] Verify SSL certificate is valid (not self-signed in production)
- [ ] Check certificate expiration date
- [ ] Verify certificate chain is complete
- [ ] Test HTTPS enforcement (HTTP redirects to HTTPS)

**TLS Configuration:**
- [ ] Verify TLS 1.2 minimum (disable SSLv3, TLS 1.0, TLS 1.1)
- [ ] Check cipher suite strength (no weak ciphers)
- [ ] Test HTTP Strict Transport Security (HSTS) header
- [ ] Verify secure cookie flags (Secure, HttpOnly, SameSite)

**Test Commands:**
```bash
# Check TLS version
openssl s_client -connect yourdomain.com:443 -tls1_2

# Check certificate
openssl s_client -connect yourdomain.com:443 -showcerts

# Test SSL Labs
# https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

---

### 2.10 API Rate Limiting

**Configuration:**
- Default: `200 per day, 50 per hour` (config.py:60)
- Storage: Redis or in-memory (development)

**Endpoints to Test:**
- [ ] Login endpoint (prevent brute-force)
- [ ] Registration endpoint (prevent spam)
- [ ] Password reset (prevent abuse)
- [ ] Payment initiation (prevent fraud)

**Test:**
```bash
# Rapid-fire requests
for i in {1..60}; do
  curl -X POST http://127.0.0.1:5001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' &
done

# Expected: 429 Too Many Requests after 50 requests
```

---

## 3. SECURITY AUDIT TOOLS

**Automated Tools:**
- **SQLMap:** SQL injection testing
- **OWASP ZAP:** Full security scan
- **Burp Suite:** Manual testing and interception
- **jwt.io:** JWT token inspection

**Manual Testing:**
- **Postman:** API endpoint testing
- **curl:** Command-line requests
- **psql:** Database inspection

---

## 4. FINDINGS TEMPLATE

For each discovered vulnerability:

```
## FINDING: [Vulnerability Name]

**Severity:** Critical / High / Medium / Low
**Category:** SQL Injection / XSS / Auth Bypass / etc.
**Endpoint:** /api/path/to/endpoint
**Method:** GET / POST / PUT / DELETE

**Description:**
[Detailed description of the vulnerability]

**Proof of Concept:**
[Step-by-step reproduction]

**Impact:**
[What could an attacker do with this?]

**Recommendation:**
[How to fix it]

**Status:** Open / In Progress / Fixed
```

---

## 5. COMPLIANCE CHECKLIST

**OWASP Top 10 (2021):**
- [ ] A01:2021 - Broken Access Control
- [ ] A02:2021 - Cryptographic Failures
- [ ] A03:2021 - Injection
- [ ] A04:2021 - Insecure Design
- [ ] A05:2021 - Security Misconfiguration
- [ ] A06:2021 - Vulnerable Components
- [ ] A07:2021 - Authentication Failures
- [ ] A08:2021 - Software and Data Integrity Failures
- [ ] A09:2021 - Security Logging and Monitoring Failures
- [ ] A10:2021 - Server-Side Request Forgery (SSRF)

**GDPR Requirements:**
- [x] PII encryption at rest ✅
- [x] Right to be forgotten (anonymization) ✅
- [x] Consent tracking ✅
- [x] Data access logging ✅

---

## 6. NEXT STEPS

1. ✅ **Complete security configuration review** (this document)
2. ⏳ **Execute SQL injection tests** (section 2.1)
3. ⏳ **Execute XSS tests** (section 2.2)
4. ⏳ **Execute CSRF tests** (section 2.3)
5. ⏳ **Execute JWT audit** (section 2.4)
6. ⏳ **Execute auth/authz tests** (section 2.5)
7. ⏳ **Execute password audit** (section 2.6)
8. ⏳ **Execute input validation tests** (section 2.7)
9. ⏳ **Document all findings**
10. ⏳ **Create DAY_10_COMPLETE.md**

---

**Document Version:** 1.0
**Last Updated:** January 4, 2026
**Next Review:** After each test phase completion
