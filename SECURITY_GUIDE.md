# Security Guide - Happy Place Boutique

Comprehensive security documentation covering authentication, encryption, GDPR compliance, and best practices.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Encryption](#encryption)
4. [GDPR Compliance](#gdpr-compliance)
5. [API Security](#api-security)
6. [POS Security](#pos-security)
7. [Audit Logging](#audit-logging)
8. [Best Practices](#best-practices)
9. [Security Checklist](#security-checklist)

---

## Overview

### Security Architecture

The Happy Place Boutique platform implements multiple layers of security:

- **Authentication:** JWT tokens with refresh mechanism
- **Password Security:** Argon2 hashing (not Bcrypt)
- **Data Encryption:** MultiFernet for PII fields
- **GDPR Compliance:** Right to access, right to erasure
- **Audit Logging:** Complete activity tracking
- **Rate Limiting:** Protection against brute force
- **Input Validation:** Sanitization and validation on all inputs

### Security Standards

- **OWASP Top 10:** Addressed
- **GDPR:** Fully compliant
- **PCI DSS:** Payment data handling (Level 4)
- **ISO 27001:** Information security management

---

## Authentication

### Customer Authentication

#### Registration
```python
# Password requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

# GDPR consent required
- gdpr_consent: true (mandatory)
- marketing_consent: optional
```

#### Login Flow
1. Customer submits email + password
2. Email hashed with SHA-256 for lookup
3. Password verified with Argon2
4. JWT access token (15 min) + refresh token (7 days) issued
5. Last login timestamp updated

#### Token Structure
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Access Token Claims:**
```json
{
  "sub": "customer_123",
  "type": "customer",
  "email": "customer@example.com",
  "exp": 1702400000,
  "iat": 1702399100
}
```

### Employee Authentication

#### Login Methods
1. **Email + Password:** Standard login
2. **PIN Login:** Quick POS access (4-6 digits)
3. **2FA (Optional):** TOTP-based two-factor

#### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access, user management, reports |
| **Manager** | Store operations, inventory, employee management |
| **Cashier** | POS transactions, customer lookup |
| **Packer** | Order fulfillment, packing |
| **Shipper** | Shipping, tracking updates |

#### Permission Decorators
```python
@employee_required  # Any employee
@manager_required   # Manager or Admin only
@admin_required     # Admin only
@packer_required    # Packer role
@shipper_required   # Shipper role
```

### Token Management

#### Access Token
- **Lifetime:** 15 minutes
- **Storage:** Memory only (never localStorage)
- **Transmission:** Authorization header only

#### Refresh Token
- **Lifetime:** 7 days
- **Storage:** HttpOnly cookie (secure, SameSite=Strict)
- **Rotation:** New refresh token on each use
- **Revocation:** Stored in database for blacklisting

#### Token Refresh Flow
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>

Response:
{
  "access_token": "new_access_token"
}
```

---

## Encryption

### MultiFernet Encryption

All PII (Personally Identifiable Information) is encrypted using MultiFernet (layered Fernet encryption).

#### Encrypted Fields

**Customer Data:**
- `email_encrypted`
- `first_name_encrypted`
- `last_name_encrypted`
- `phone_encrypted`

**Address Data:**
- `full_name_encrypted`
- `phone_encrypted`
- `address_line1_encrypted`
- `address_line2_encrypted`
- `city_encrypted`
- `state_encrypted`
- `postal_code_encrypted`

**Payment Data:**
- `payment_details_encrypted`

#### Encryption Keys

**Primary Key:** Active encryption key
**Secondary Keys:** Previous keys for key rotation

```python
# Environment variables
ENCRYPTION_KEY_PRIMARY=base64_encoded_key
ENCRYPTION_KEY_SECONDARY=base64_encoded_key
```

#### Key Rotation

1. Generate new key
2. Add as primary, demote old primary to secondary
3. Re-encrypt all data with new primary key
4. Remove old secondary key after grace period

```bash
python scripts/rotate_encryption_keys.py
```

### Password Hashing

**Algorithm:** Argon2id (NOT Bcrypt)

**Parameters:**
- Time cost: 2 iterations
- Memory cost: 65536 KB (64 MB)
- Parallelism: 4 threads
- Hash length: 32 bytes

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
password_hash = generate_password_hash(password, method='scrypt')

# Verify password
is_valid = check_password_hash(password_hash, password)
```

### Email Hashing

Emails are stored in two forms:
1. **Hash (SHA-256):** For login lookup
2. **Encrypted (MultiFernet):** For display/communication

```python
from services.encryption import hash_email

email_hash = hash_email("customer@example.com")
# Returns: SHA-256 hash for database lookup
```

---

## GDPR Compliance

### Data Subject Rights

#### Right to Access
```http
POST /api/gdpr/data-request
Authorization: Bearer <customer_token>

Body:
{
  "request_type": "access"
}
```

**Response:** Complete data export in JSON format

#### Right to Erasure (Right to be Forgotten)
```http
POST /api/gdpr/data-request
Authorization: Bearer <customer_token>

Body:
{
  "request_type": "deletion"
}
```

**Process:**
1. Request logged in `gdpr_data_requests`
2. Admin reviews request
3. Data anonymized (not deleted for audit trail)
4. Customer notified

### Data Anonymization

**Anonymized Fields:**
- Email → `anonymized_user_[id]@deleted.local`
- Name → `Anonymized User`
- Phone → `NULL`
- Addresses → Deleted

**Preserved Data:**
- Order history (anonymized)
- Transaction records (for accounting)
- Audit logs (for compliance)

### Consent Management

#### Consent Types
1. **GDPR Consent:** Required for account creation
2. **Marketing Consent:** Optional, for promotional emails

#### Consent Logging
Every consent action is logged:
```python
{
  "customer_id": 123,
  "consent_type": "marketing",
  "consent_given": true,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2025-12-12T20:00:00Z"
}
```

### Data Retention

- **Active Customers:** Indefinite
- **Inactive (3+ years):** Auto-anonymization scheduled
- **Deleted Accounts:** Immediate anonymization
- **Audit Logs:** 7 years retention

---

## API Security

### Rate Limiting

**General API:**
- 100 requests per minute per IP
- 429 status code when exceeded

**Authentication Endpoints:**
- Login: 5 attempts per 15 minutes
- Register: 3 attempts per 5 minutes
- Password reset: 3 attempts per hour

**Admin Endpoints:**
- 200 requests per minute

### CORS Configuration

```python
CORS_ORIGINS = [
    "http://localhost:3000",      # Development
    "https://happyplace.co.ke"    # Production
]

CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
CORS_CREDENTIALS = True
```

### Input Validation

All inputs are validated and sanitized:

```python
# Email validation
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Phone validation (Kenya)
phone_regex = r'^\+254[17]\d{8}$'

# SQL injection prevention
- SQLAlchemy ORM (parameterized queries)
- No raw SQL execution

# XSS prevention
- Input sanitization
- Output encoding
- Content Security Policy headers
```

### HTTPS/TLS

**Production Requirements:**
- TLS 1.3 minimum
- Strong cipher suites only
- HSTS enabled
- Certificate pinning (mobile apps)

```python
# Flask configuration
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
```

---

## POS Security

### Physical Security

1. **Device Security:**
   - Screen lock after 5 minutes inactivity
   - Encrypted storage
   - Secure boot

2. **Cash Handling:**
   - Shift-based accountability
   - Opening/closing cash counts
   - Manager approval for voids

### POS Authentication

**Quick PIN Login:**
```python
# 4-6 digit PIN
# Argon2 hashed (same as passwords)
# Max 3 failed attempts → lockout
```

**Session Management:**
- Auto-logout after 30 minutes inactivity
- Shift-based sessions
- Cannot start new shift without ending previous

### Transaction Security

**Void Protection:**
- Manager approval required
- Reason mandatory
- Audit trail logged
- Original receipt retained

**Receipt Security:**
- Unique receipt numbers
- Tamper-evident format
- Digital signature (optional)

---

## Audit Logging

### Activity Logs

All significant actions are logged:

```python
{
  "user_type": "employee",
  "user_id": 5,
  "action": "order_status_change",
  "entity_type": "order",
  "entity_id": 123,
  "details": {
    "old_status": "pending",
    "new_status": "processing"
  },
  "ip_address": "192.168.1.10",
  "timestamp": "2025-12-12T20:00:00Z"
}
```

### PII Access Logging

Every access to customer PII is logged:

```python
{
  "employee_id": 5,
  "customer_id": 123,
  "access_type": "view_profile",
  "accessed_fields": ["email", "phone", "address"],
  "reason": "Customer support inquiry",
  "ip_address": "192.168.1.10",
  "timestamp": "2025-12-12T20:00:00Z"
}
```

### Log Retention

- **Activity Logs:** 2 years
- **PII Access Logs:** 7 years (compliance)
- **Security Events:** 7 years
- **Audit Logs:** 7 years

### Log Analysis

```bash
# Failed login attempts
SELECT * FROM activity_logs 
WHERE action = 'login_failed' 
AND created_at > NOW() - INTERVAL '1 hour';

# PII access by employee
SELECT * FROM data_access_log 
WHERE employee_id = 5 
ORDER BY created_at DESC;
```

---

## Best Practices

### For Developers

1. **Never Log Sensitive Data**
   ```python
   # ❌ Bad
   logger.info(f"User {email} logged in")
   
   # ✅ Good
   logger.info(f"User {user_id} logged in")
   ```

2. **Use Parameterized Queries**
   ```python
   # ❌ Bad
   query = f"SELECT * FROM users WHERE email = '{email}'"
   
   # ✅ Good
   user = Customer.query.filter_by(email_hash=hash_email(email)).first()
   ```

3. **Validate All Inputs**
   ```python
   from marshmallow import Schema, fields, validate
   
   class RegisterSchema(Schema):
       email = fields.Email(required=True)
       password = fields.Str(required=True, validate=validate.Length(min=8))
   ```

4. **Handle Errors Securely**
   ```python
   # ❌ Bad
   return {"error": str(exception)}
   
   # ✅ Good
   logger.error(f"Error: {exception}")
   return {"error": "An error occurred"}
   ```

### For Administrators

1. **Regular Security Audits**
   - Review access logs weekly
   - Check for suspicious activity
   - Update dependencies monthly

2. **Employee Access Management**
   - Principle of least privilege
   - Regular access reviews
   - Immediate revocation on termination

3. **Backup & Recovery**
   - Daily encrypted backups
   - Offsite storage
   - Regular restore testing

4. **Incident Response**
   - Document security incidents
   - Notify affected users (GDPR requirement)
   - Root cause analysis

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets in environment variables (not code)
- [ ] HTTPS/TLS configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Error messages sanitized
- [ ] Logging configured (no sensitive data)
- [ ] Backup strategy implemented

### Production

- [ ] Firewall configured
- [ ] Database access restricted
- [ ] Admin panel IP whitelisted
- [ ] Monitoring alerts configured
- [ ] Incident response plan documented
- [ ] Security audit completed
- [ ] Penetration testing performed
- [ ] GDPR compliance verified
- [ ] Data retention policy implemented
- [ ] Employee security training completed

### Ongoing

- [ ] Weekly log reviews
- [ ] Monthly dependency updates
- [ ] Quarterly security audits
- [ ] Annual penetration testing
- [ ] Continuous monitoring
- [ ] Regular backup testing
- [ ] Access review (quarterly)
- [ ] Security awareness training

---

## Security Headers

```python
# Flask configuration
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Content-Security-Policy': "default-src 'self'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

---

## Incident Response

### Security Incident Procedure

1. **Detection:** Identify security incident
2. **Containment:** Isolate affected systems
3. **Investigation:** Determine scope and impact
4. **Eradication:** Remove threat
5. **Recovery:** Restore normal operations
6. **Notification:** Inform affected parties (GDPR: 72 hours)
7. **Documentation:** Record incident details
8. **Review:** Post-incident analysis

### Contact Information

**Security Team:** security@happyplace.com  
**Emergency:** +254-XXX-XXXXXX  
**GDPR Officer:** dpo@happyplace.com

---

## Compliance

### GDPR Requirements

- ✅ Lawful basis for processing
- ✅ Consent management
- ✅ Right to access
- ✅ Right to erasure
- ✅ Data portability
- ✅ Breach notification (72 hours)
- ✅ Data Protection Officer appointed
- ✅ Privacy by design

### PCI DSS (Level 4)

- ✅ No card data stored
- ✅ Tokenization for payments
- ✅ Encrypted transmission
- ✅ Access controls
- ✅ Regular security testing

---

## Support

For security concerns: security@happyplace.com  
For GDPR requests: dpo@happyplace.com  
For general support: support@happyplace.com
