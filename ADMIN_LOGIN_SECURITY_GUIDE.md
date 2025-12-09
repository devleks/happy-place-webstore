# Admin Login Security Guide
## Happy Place E-commerce Platform

**Version:** 1.0
**Date:** December 3, 2025
**Phase:** 11 - Admin Dashboard

---

## Overview

The Happy Place admin authentication system follows **Security by Design** principles with robust, defense-in-depth security measures protecting administrative access to the platform.

---

## Security Architecture

### Multi-Layer Security Model

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security (HTTPS, CORS, Rate Limiting)    │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Authentication (JWT, Password Hashing, 2FA)      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Authorization (RBAC, Permission Checking)         │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Session Management (Token Rotation, Timeouts)    │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Audit Logging (All admin actions logged)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow

### Employee Login Process

```
1. User navigates to /login
2. Toggles to "Employee Login" tab
3. Enters credentials (email + password)
4. Frontend sends POST to /api/auth/employee/login
5. Backend validates credentials:
   ├─ Check if employee exists
   ├─ Verify password hash (scrypt)
   ├─ Check account status (is_active)
   ├─ Check account locks
   ├─ Verify 2FA if enabled
   └─ Check failed login attempts
6. If successful:
   ├─ Generate JWT access token (30-day expiry)
   ├─ Generate JWT refresh token
   ├─ Log successful authentication
   ├─ Reset failed login counter
   └─ Return tokens + employee data
7. Frontend stores tokens in localStorage
8. Redirect to /admin/dashboard
```

---

## Security Features

### 1. Password Security

**Hashing Algorithm:** Scrypt (werkzeug.security)
- **Parameters:**
  - N=32768 (CPU/memory cost)
  - r=8 (block size)
  - p=1 (parallelization)
- **Salt:** Automatically generated per password
- **Hash Length:** 64 bytes
- **Format:** `scrypt:32768:8:1${salt}${hash}`

**Password Requirements:**
- Minimum 8 characters
- Must contain letters and numbers
- No dictionary words recommended
- Changed passwords logged with timestamp

**Example Hash:**
```
scrypt:32768:8:1$aN3mX4h5lTrT5gK6$7c9f4e2a1b8d3c5f6e9a0b7d4c1e8f2a...
```

### 2. Account Lockout Protection

**Failed Login Threshold:** 5 attempts
**Lockout Duration:** 30 minutes
**Counter Reset:** On successful login

**Lockout Logic:**
```python
if employee.failed_login_attempts >= 5:
    employee.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
    return {'error': 'Account locked for 30 minutes'}
```

**Status Check:**
```sql
SELECT
    email,
    failed_login_attempts,
    account_locked_until,
    CASE
        WHEN account_locked_until > NOW() THEN 'LOCKED'
        WHEN failed_login_attempts >= 3 THEN 'AT RISK'
        ELSE 'ACTIVE'
    END as status
FROM employees;
```

### 3. Two-Factor Authentication (2FA)

**Method:** TOTP (Time-based One-Time Password)
**Standard:** RFC 6238
**Algorithm:** SHA-1
**Digits:** 6
**Period:** 30 seconds

**Setup Flow:**
1. Admin enables 2FA in settings
2. System generates TOTP secret
3. QR code displayed for authenticator app
4. Admin enters verification code
5. Backup codes generated (10 codes)
6. 2FA activated

**Login with 2FA:**
```json
POST /api/auth/employee/login
{
  "email": "admin@happyplace.co.ke",
  "password": "admin123",
  "totp_code": "123456"
}
```

**Security Measures:**
- Backup codes hashed (bcrypt)
- TOTP secret encrypted at rest
- Rate limiting on verification attempts
- Audit logging of all 2FA events

### 4. JWT Token Security

**Access Token:**
- **Expiry:** 30 days
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Claims:** user_id, user_type, role, email, exp, iat, jti
- **Signed with:** SECRET_KEY (256-bit minimum)

**Refresh Token:**
- **Expiry:** 60 days
- **Single use:** Invalidated after refresh
- **Stored:** Database session table
- **Rotation:** New refresh token issued on each use

**Token Payload:**
```json
{
  "sub": "2",  // employee_id
  "user_type": "employee",
  "role": "admin",
  "email": "admin@happyplace.co.ke",
  "exp": 1704067200,  // Expiration timestamp
  "iat": 1701475200,  // Issued at
  "jti": "unique-token-id",  // JWT ID for revocation
  "fresh": true
}
```

**Token Validation:**
```python
1. Check signature (prevents tampering)
2. Check expiration (exp claim)
3. Check not before (nbf claim)
4. Verify token not revoked (jti in blacklist)
5. Validate user still exists and active
6. Verify role/permissions current
```

### 5. Role-Based Access Control (RBAC)

**Roles Hierarchy:**
```
admin (highest privilege)
  └─ Full system access
  └─ System settings management
  └─ Employee management

manager
  └─ Dashboard, inventory, orders
  └─ Customer management
  └─ Reports

cashier
  └─ POS operations
  └─ Sales transactions

staff (lowest privilege)
  └─ Limited inventory access
  └─ Order fulfillment
```

**Permission Decorators:**
```python
@admin_required
def admin_only_endpoint():
    # Only admin role can access
    pass

@manager_required
def manager_or_admin_endpoint():
    # Manager or admin roles
    pass

@employee_required
def all_employees_endpoint():
    # Any authenticated employee
    pass
```

**Permission Check Logic:**
```python
def manager_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('user_type') != 'employee':
            return {'error': 'Employee access required'}, 403
        if claims.get('role') not in ['manager', 'admin']:
            return {'error': 'Manager or admin role required'}, 403
        return fn(*args, **kwargs)
    return wrapper
```

### 6. Session Management

**Session Features:**
- Device tracking (user agent, IP)
- Concurrent session limits
- Active session viewing
- Remote session termination
- Session timeout enforcement

**Session Table Schema:**
```sql
CREATE TABLE employee_sessions (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    access_token_jti VARCHAR(36) UNIQUE,
    refresh_token_jti VARCHAR(36) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_activity TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);
```

**Session Cleanup:**
- Expired sessions deleted daily
- Inactive sessions (30 days) auto-terminated
- Manual logout invalidates all tokens

### 7. Audit Logging

**All Admin Actions Logged:**
- Login/logout events
- Password changes
- 2FA enable/disable
- Permission changes
- Data access (customer PII)
- System configuration changes
- Failed authentication attempts

**ActivityLog Schema:**
```sql
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Log Entry Example:**
```json
{
  "employee_id": 1,
  "action": "customer_data_export",
  "resource_type": "customer",
  "resource_id": 123,
  "details": {
    "export_format": "JSON",
    "reason": "GDPR request",
    "fields_exported": ["profile", "orders", "addresses"]
  },
  "ip_address": "192.168.1.100",
  "created_at": "2025-12-03T10:30:00Z"
}
```

### 8. Rate Limiting

**Endpoints Protected:**
- `/api/auth/employee/login` - 5 attempts per 15 minutes per IP
- `/api/auth/employee/pin-login` - 3 attempts per 5 minutes per IP
- `/api/admin/*` - 100 requests per minute per user

**Implementation:**
- Redis-based rate limiting (production)
- In-memory fallback (development)
- Returns HTTP 429 when limit exceeded
- Includes Retry-After header

### 9. CORS & HTTPS

**CORS Policy:**
```python
CORS(app,
     origins=['https://happyplace.co.ke', 'http://localhost:3000'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
)
```

**HTTPS Enforcement:**
- All production traffic over HTTPS only
- HSTS header: `max-age=31536000; includeSubDomains`
- Secure cookie flags: `Secure; HttpOnly; SameSite=Strict`

### 10. Input Validation

**Backend Validation:**
```python
# Email validation
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Password validation (registration)
- min_length = 8
- requires_uppercase = True
- requires_number = True
- prohibits_common_passwords = True

# SQL injection prevention
- All queries use parameterized statements (SQLAlchemy ORM)
- Never string concatenation for queries
```

**Frontend Validation:**
- Form validation before submission
- XSS prevention (React auto-escapes)
- CSRF token validation (JWT in header, not cookie)

---

## Test Credentials (Development Only)

### Admin Account (Full Access)
```
Email: admin@happyplace.co.ke
Password: admin123
Role: admin
```

### Manager Account (Standard Access)
```
Email: manager@happyplace.co.ke
Password: manager123
Role: manager
```

**⚠️ SECURITY WARNING:**
These are development credentials. In production:
1. Change all default passwords immediately
2. Enforce strong password policy
3. Enable 2FA for all admin accounts
4. Regular password rotation (90 days)
5. Monitor for unauthorized access attempts

---

## Testing the Login System

### Step 1: Access the Login Page

1. Navigate to: `http://localhost:3000/login`
2. You should see two tabs: "Customer Login" and "Employee Login"

### Step 2: Switch to Employee Login

1. Click the "Employee Login" tab
2. The tab should highlight with the gold color (#D4AF37)

### Step 3: Enter Credentials

**For Admin Access:**
```
Email:    admin@happyplace.co.ke
Password: admin123
```

**For Manager Access:**
```
Email:    manager@happyplace.co.ke
Password: manager123
```

### Step 4: Submit

1. Click "Login" button
2. If successful, you should be redirected to `/admin/dashboard`
3. If unsuccessful, check:
   - You're on the "Employee Login" tab (not Customer)
   - Email is exactly: `admin@happyplace.co.ke` (check for typos)
   - Password is exactly: `admin123` (case-sensitive)
   - Backend server is running on port 5001
   - Frontend can reach the backend API

### Step 5: Verify Access

Once logged in, you should see:
- Admin sidebar with navigation menu
- Dashboard with metrics cards
- User profile in top-right showing name and role
- Access to all admin pages

---

## Troubleshooting

### Issue: "Failed to login. Please check your credentials"

**Possible Causes:**
1. Wrong tab selected (Customer instead of Employee)
2. Typo in email or password
3. Account locked due to failed attempts
4. Backend server not running
5. Network/CORS issues

**Diagnostic Steps:**

1. **Verify Password Hashes:**
```bash
cd backend
python scripts/diagnose_login.py
```

Expected output:
```
Testing password verification:
  'admin123': ✅ MATCH
```

2. **Check Account Status:**
```bash
PGPASSWORD='password' psql -U postgres -d happy_place_db -c \
  "SELECT email, is_active, failed_login_attempts, account_locked_until
   FROM employees WHERE email='admin@happyplace.co.ke';"
```

Expected output:
```
is_active: t
failed_login_attempts: 0
account_locked_until: null
```

3. **Reset Passwords:**
```bash
cd backend
python scripts/reset_admin_passwords.py
```

4. **Check Backend Server:**
```bash
# Check if running
lsof -i :5001

# View logs
tail -f logs/app.log
```

5. **Test API Directly:**
```bash
curl -X POST http://localhost:5001/api/auth/employee/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.co.ke","password":"admin123"}'
```

Expected response:
```json
{
  "success": true,
  "access_token": "eyJhbGci...",
  "employee": {
    "id": 1,
    "email": "admin@happyplace.co.ke",
    "role": "admin"
  }
}
```

### Issue: Account Locked

**Clear Account Lock:**
```sql
UPDATE employees
SET failed_login_attempts = 0,
    account_locked_until = NULL
WHERE email IN ('admin@happyplace.co.ke', 'manager@happyplace.co.ke');
```

### Issue: Network/CORS Error

**Check CORS Configuration:**
```python
# backend/app.py
CORS(app, origins=['http://localhost:3000'])
```

**Check API Base URL:**
```javascript
// frontend/src/services/api.js
const API_BASE_URL = 'http://localhost:5001/api';
```

---

## Security Best Practices

### For Development

1. ✅ Use separate admin accounts per developer
2. ✅ Never commit credentials to git
3. ✅ Use environment variables for secrets
4. ✅ Enable debug logging for auth failures
5. ✅ Test with realistic failed login scenarios

### For Production

1. ✅ Change all default passwords before deployment
2. ✅ Enable 2FA for all admin accounts (mandatory)
3. ✅ Use strong, unique passwords (16+ characters)
4. ✅ Implement IP whitelisting for admin access
5. ✅ Enable rate limiting on all auth endpoints
6. ✅ Monitor audit logs daily for suspicious activity
7. ✅ Regular security audits and penetration testing
8. ✅ Automated alerts for failed login spikes
9. ✅ Password rotation every 90 days
10. ✅ Review and revoke unused admin accounts monthly

---

## Compliance & Standards

### OWASP Top 10 Mitigation

✅ **A01:2021 - Broken Access Control**
- Role-based permissions on all admin endpoints
- JWT validation on every request
- Audit logging of all access attempts

✅ **A02:2021 - Cryptographic Failures**
- Scrypt password hashing (32768 rounds)
- JWT token signing (HS256)
- HTTPS enforcement in production
- Encrypted database fields for sensitive data

✅ **A03:2021 - Injection**
- Parameterized SQL queries (SQLAlchemy ORM)
- Input validation on all endpoints
- Output encoding (React auto-escapes)

✅ **A05:2021 - Security Misconfiguration**
- Minimal privilege principle
- Secure defaults
- Regular dependency updates
- Disabled debug mode in production

✅ **A07:2021 - Identification and Authentication Failures**
- Multi-factor authentication (2FA)
- Secure password storage (scrypt)
- Account lockout mechanism
- Session management with timeout

✅ **A09:2021 - Security Logging and Monitoring Failures**
- Comprehensive audit logging
- Failed authentication monitoring
- Admin action tracking
- Anomaly detection ready

### GDPR Compliance

✅ **Data Protection**
- Employee PII encrypted at rest
- Access logs for all data queries
- Data retention policies
- Secure password reset mechanism

✅ **Right of Access**
- Admin audit trail export
- Session history viewing
- Login history available

---

## Incident Response

### Suspected Compromise

**Immediate Actions:**
1. Lock affected account
2. Invalidate all tokens for user
3. Review audit logs
4. Check for unauthorized data access
5. Force password reset
6. Enable 2FA if not already active

**SQL Commands:**
```sql
-- Lock account
UPDATE employees SET
    is_active = FALSE,
    account_locked_until = NOW() + INTERVAL '24 hours'
WHERE email = 'compromised@email.com';

-- Invalidate sessions
DELETE FROM employee_sessions WHERE employee_id = ?;

-- Review recent activity
SELECT * FROM activity_logs
WHERE employee_id = ?
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

---

## Support & Contact

**Security Issues:**
Report to: security@happyplace.co.ke

**Technical Support:**
Contact: support@happyplace.co.ke

**Documentation:**
Location: `/docs/ADMIN_LOGIN_SECURITY_GUIDE.md`

---

**Document Version:** 1.0
**Last Updated:** December 3, 2025
**Next Review:** March 3, 2026

---

## Appendix: Security Checklist

### Pre-Deployment Security Checklist

- [ ] All default passwords changed
- [ ] 2FA enabled for all admin accounts
- [ ] Rate limiting configured
- [ ] HTTPS certificate installed
- [ ] CORS origins restricted to production domain
- [ ] Database credentials rotated
- [ ] JWT secret keys generated (256-bit minimum)
- [ ] Session timeout configured (30 minutes)
- [ ] Account lockout enabled (5 attempts / 30 minutes)
- [ ] Audit logging enabled
- [ ] Log monitoring configured
- [ ] Backup and disaster recovery tested
- [ ] Security scanning completed (OWASP ZAP / Burp Suite)
- [ ] Penetration testing completed
- [ ] Incident response plan documented
- [ ] Security training completed for all admins

### Monthly Security Tasks

- [ ] Review audit logs for anomalies
- [ ] Check for failed login attempts
- [ ] Review active admin sessions
- [ ] Verify 2FA enabled on all accounts
- [ ] Update dependencies (security patches)
- [ ] Test backup restoration
- [ ] Review and update firewall rules
- [ ] Scan for vulnerabilities
- [ ] Review access permissions
- [ ] Test incident response procedures
