# Authentication & Authorization Enhancement Plan

**Status:** 📋 PLANNED
**Priority:** HIGH
**Estimated Effort:** 1 week
**Target Implementation:** Immediate (before Phase 11)

---

## 🎯 Objectives

1. **Separate customer and employee authentication flows**
2. **Implement OAuth 2.0 for customer social login**
3. **Add refresh tokens for better security**
4. **Implement 2FA for employees**
5. **Add token blacklist for proper logout**
6. **Enhance permission system**
7. **Improve user experience with persistent sessions**

---

## 📋 Current State Analysis

### What We Have ✅
- Basic JWT authentication for customers
- Employee authentication with role claims
- Role-based decorators (`@employee_required`, `@manager_required`)
- Password hashing with bcrypt

### What's Missing ❌
- Separate login endpoints/pages
- OAuth 2.0 social login
- Refresh tokens
- 2FA for employees
- Token blacklist (proper logout)
- Permission-based authorization
- Audit logging
- Rate limiting

---

## 🏗️ Implementation Plan

### Phase 1: Separate Authentication Flows (Day 1-2)

#### 1.1 Database Schema Updates

**Migration:** `007_auth_enhancements.sql`

```sql
-- Add OAuth fields to customers table
ALTER TABLE customers ADD COLUMN oauth_provider VARCHAR(20);  -- 'google', 'facebook', null
ALTER TABLE customers ADD COLUMN oauth_id VARCHAR(255);
ALTER TABLE customers ADD COLUMN oauth_access_token TEXT;
ALTER TABLE customers ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN last_login TIMESTAMP;
ALTER TABLE customers ADD COLUMN login_count INTEGER DEFAULT 0;

-- Add 2FA fields to employees table
ALTER TABLE employees ADD COLUMN totp_secret VARCHAR(64);  -- For 2FA
ALTER TABLE employees ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE employees ADD COLUMN backup_codes TEXT[];  -- Array of backup codes
ALTER TABLE employees ADD COLUMN pin VARCHAR(6);  -- For POS quick login
ALTER TABLE employees ADD COLUMN last_login TIMESTAMP;
ALTER TABLE employees ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE employees ADD COLUMN account_locked_until TIMESTAMP;

-- Create refresh tokens table
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL,  -- 'customer' or 'employee'
    token_jti VARCHAR(36) UNIQUE NOT NULL,  -- JWT ID
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_refresh_jti (token_jti),
    INDEX idx_refresh_user (user_id, user_type),
    INDEX idx_refresh_expires (expires_at)
);

-- Create token blacklist (for revoked access tokens)
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(36) UNIQUE NOT NULL,
    token_type VARCHAR(20) NOT NULL,  -- 'access' or 'refresh'
    user_id INTEGER,
    user_type VARCHAR(20),
    revoked_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    reason VARCHAR(100),  -- 'logout', 'password_change', 'admin_revoke'

    INDEX idx_blacklist_jti (jti),
    INDEX idx_blacklist_expires (expires_at)
);

-- Create audit log for authentication events
CREATE TABLE auth_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    user_type VARCHAR(20),
    event_type VARCHAR(50) NOT NULL,  -- 'login', 'logout', 'failed_login', 'password_change', '2fa_enabled'
    ip_address VARCHAR(50),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_audit_user (user_id, user_type),
    INDEX idx_audit_event (event_type),
    INDEX idx_audit_created (created_at DESC)
);

-- Create permissions table
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- 'pos', 'inventory', 'reports', 'admin'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create role_permissions junction table
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Seed permissions
INSERT INTO permissions (name, description, category) VALUES
    -- POS Permissions
    ('pos.create_sale', 'Create new sales transactions', 'pos'),
    ('pos.void_transaction', 'Void existing transactions', 'pos'),
    ('pos.view_transactions', 'View transaction history', 'pos'),
    ('pos.print_receipt', 'Print receipts', 'pos'),

    -- Shift Permissions
    ('shift.open', 'Open a new shift', 'pos'),
    ('shift.close', 'Close a shift', 'pos'),
    ('shift.view_all', 'View all employee shifts', 'pos'),

    -- Inventory Permissions
    ('inventory.view', 'View inventory levels', 'inventory'),
    ('inventory.update', 'Update inventory quantities', 'inventory'),
    ('inventory.transfer', 'Transfer inventory between locations', 'inventory'),

    -- Customer Permissions
    ('customer.view', 'View customer information', 'customers'),
    ('customer.edit', 'Edit customer information', 'customers'),
    ('customer.delete', 'Delete customer accounts', 'customers'),

    -- Report Permissions
    ('reports.sales', 'View sales reports', 'reports'),
    ('reports.inventory', 'View inventory reports', 'reports'),
    ('reports.employee', 'View employee performance reports', 'reports'),
    ('reports.financial', 'View financial reports', 'reports'),

    -- Admin Permissions
    ('admin.employees', 'Manage employees', 'admin'),
    ('admin.roles', 'Manage roles and permissions', 'admin'),
    ('admin.settings', 'Modify system settings', 'admin'),
    ('admin.audit_log', 'View audit logs', 'admin');

-- Create roles if not exists
INSERT INTO roles (name, description) VALUES
    ('admin', 'Full system access'),
    ('manager', 'Store manager with elevated permissions'),
    ('cashier', 'POS cashier with basic permissions'),
    ('staff', 'Store staff with limited permissions')
ON CONFLICT (name) DO NOTHING;

-- Assign permissions to roles
-- Admin: All permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin';

-- Manager: Most permissions except admin functions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'manager'
AND p.category IN ('pos', 'inventory', 'customers', 'reports');

-- Cashier: POS and basic operations
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'cashier'
AND p.name IN (
    'pos.create_sale',
    'pos.view_transactions',
    'pos.print_receipt',
    'shift.open',
    'shift.close',
    'inventory.view',
    'customer.view'
);

-- Staff: Very limited permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'staff'
AND p.name IN (
    'inventory.view',
    'customer.view'
);

-- Create indexes
CREATE INDEX idx_customers_oauth ON customers(oauth_provider, oauth_id);
CREATE INDEX idx_customers_email_verified ON customers(email_verified);
CREATE INDEX idx_employees_totp ON employees(totp_enabled);
CREATE INDEX idx_employees_locked ON employees(account_locked_until);
```

---

#### 1.2 Enhanced Authentication Service

**File:** `backend/services/auth_service.py` (NEW - ~600 lines)

```python
import os
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db
from backend.models import (
    Customer, Employee, RefreshToken, TokenBlacklist,
    AuthAuditLog, Permission, Role
)

class AuthService:
    """Enhanced authentication service"""

    # Token expiration times
    ACCESS_TOKEN_EXPIRES = timedelta(hours=1)      # Short-lived
    REFRESH_TOKEN_EXPIRES = timedelta(days=30)     # Long-lived

    # Account lockout settings
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)

    # ============ CUSTOMER AUTHENTICATION ============

    def register_customer(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: Optional[str] = None
    ) -> Dict:
        """Register new customer account"""
        try:
            # Check if email exists
            if Customer.query.filter_by(email=email).first():
                return {'success': False, 'error': 'Email already registered'}

            # Validate password strength
            if not self._is_strong_password(password):
                return {
                    'success': False,
                    'error': 'Password must be at least 8 characters with uppercase, lowercase, and numbers'
                }

            # Create customer
            customer = Customer(
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                email_verified=False  # Require email verification
            )

            db.session.add(customer)
            db.session.commit()

            # Log event
            self._log_auth_event(
                user_id=customer.id,
                user_type='customer',
                event_type='register',
                success=True
            )

            # TODO: Send verification email

            return {
                'success': True,
                'message': 'Account created. Please verify your email.',
                'customer_id': customer.id
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def login_customer(self, email: str, password: str) -> Dict:
        """Customer login with email/password"""
        try:
            customer = Customer.query.filter_by(email=email).first()

            if not customer:
                self._log_auth_event(
                    user_id=None,
                    user_type='customer',
                    event_type='failed_login',
                    success=False,
                    error_message='Email not found'
                )
                return {'success': False, 'error': 'Invalid email or password'}

            # Check password
            if not check_password_hash(customer.password_hash, password):
                self._log_auth_event(
                    user_id=customer.id,
                    user_type='customer',
                    event_type='failed_login',
                    success=False,
                    error_message='Invalid password'
                )
                return {'success': False, 'error': 'Invalid email or password'}

            # Check if email verified (optional - can be enforced)
            if not customer.email_verified:
                return {
                    'success': False,
                    'error': 'Please verify your email before logging in',
                    'requires_verification': True
                }

            # Generate tokens
            tokens = self._generate_tokens(customer.id, 'customer')

            # Update last login
            customer.last_login = datetime.now()
            customer.login_count += 1
            db.session.commit()

            # Log successful login
            self._log_auth_event(
                user_id=customer.id,
                user_type='customer',
                event_type='login',
                success=True
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'user': {
                    'id': customer.id,
                    'email': customer.email,
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'user_type': 'customer'
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def login_customer_oauth(
        self,
        provider: str,
        oauth_id: str,
        email: str,
        name: str,
        access_token: str
    ) -> Dict:
        """Customer login via OAuth (Google, Facebook)"""
        try:
            # Find or create customer
            customer = Customer.query.filter_by(
                oauth_provider=provider,
                oauth_id=oauth_id
            ).first()

            if not customer:
                # Check if email already exists with different auth method
                existing = Customer.query.filter_by(email=email).first()
                if existing:
                    # Link OAuth to existing account
                    existing.oauth_provider = provider
                    existing.oauth_id = oauth_id
                    existing.oauth_access_token = access_token
                    existing.email_verified = True  # OAuth providers verify email
                    customer = existing
                else:
                    # Create new customer
                    name_parts = name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''

                    customer = Customer(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        oauth_provider=provider,
                        oauth_id=oauth_id,
                        oauth_access_token=access_token,
                        email_verified=True
                    )
                    db.session.add(customer)
            else:
                # Update existing OAuth customer
                customer.oauth_access_token = access_token

            # Generate tokens
            tokens = self._generate_tokens(customer.id, 'customer')

            # Update last login
            customer.last_login = datetime.now()
            customer.login_count += 1
            db.session.commit()

            # Log event
            self._log_auth_event(
                user_id=customer.id,
                user_type='customer',
                event_type='oauth_login',
                success=True,
                metadata={'provider': provider}
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'user': {
                    'id': customer.id,
                    'email': customer.email,
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'user_type': 'customer'
                }
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # ============ EMPLOYEE AUTHENTICATION ============

    def login_employee(
        self,
        email: str,
        password: str,
        totp_code: Optional[str] = None
    ) -> Dict:
        """Employee login with email/password + optional 2FA"""
        try:
            employee = Employee.query.filter_by(email=email).first()

            if not employee:
                self._log_auth_event(
                    user_id=None,
                    user_type='employee',
                    event_type='failed_login',
                    success=False,
                    error_message='Email not found'
                )
                return {'success': False, 'error': 'Invalid credentials'}

            # Check if account is locked
            if self._is_account_locked(employee):
                return {
                    'success': False,
                    'error': 'Account locked due to too many failed attempts. Try again later.',
                    'locked_until': employee.account_locked_until.isoformat()
                }

            # Check password
            if not check_password_hash(employee.password_hash, password):
                employee.failed_login_attempts += 1

                # Lock account if too many failures
                if employee.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                    employee.account_locked_until = datetime.now() + self.LOCKOUT_DURATION

                db.session.commit()

                self._log_auth_event(
                    user_id=employee.id,
                    user_type='employee',
                    event_type='failed_login',
                    success=False,
                    error_message='Invalid password'
                )

                return {'success': False, 'error': 'Invalid credentials'}

            # Check 2FA if enabled
            if employee.totp_enabled:
                if not totp_code:
                    return {
                        'success': False,
                        'requires_2fa': True,
                        'message': 'Please enter your 2FA code',
                        'temp_token': self._generate_temp_token(employee.id)
                    }

                # Verify 2FA code
                if not self._verify_totp(employee.totp_secret, totp_code):
                    self._log_auth_event(
                        user_id=employee.id,
                        user_type='employee',
                        event_type='failed_2fa',
                        success=False
                    )
                    return {'success': False, 'error': 'Invalid 2FA code'}

            # Success - generate tokens
            tokens = self._generate_tokens(
                user_id=employee.id,
                user_type='employee',
                additional_claims={
                    'role': employee.role.name if employee.role else 'staff',
                    'store_location_id': employee.store_location_id
                }
            )

            # Reset failed attempts
            employee.failed_login_attempts = 0
            employee.account_locked_until = None
            employee.last_login = datetime.now()
            db.session.commit()

            # Log successful login
            self._log_auth_event(
                user_id=employee.id,
                user_type='employee',
                event_type='login',
                success=True
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'user': {
                    'id': employee.id,
                    'email': employee.email,
                    'full_name': employee.full_name,
                    'role': employee.role.name if employee.role else 'staff',
                    'user_type': 'employee'
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def login_employee_pin(self, pin: str) -> Dict:
        """Quick POS login with 6-digit PIN"""
        try:
            employee = Employee.query.filter_by(pin=pin).first()

            if not employee:
                self._log_auth_event(
                    user_id=None,
                    user_type='employee',
                    event_type='failed_pin_login',
                    success=False
                )
                return {'success': False, 'error': 'Invalid PIN'}

            # Check if account is locked
            if self._is_account_locked(employee):
                return {'success': False, 'error': 'Account locked'}

            # Generate short-lived token (POS sessions should be shorter)
            tokens = self._generate_tokens(
                user_id=employee.id,
                user_type='employee',
                additional_claims={'role': employee.role.name if employee.role else 'staff'},
                access_expires=timedelta(hours=8)  # Shift duration
            )

            employee.last_login = datetime.now()
            db.session.commit()

            self._log_auth_event(
                user_id=employee.id,
                user_type='employee',
                event_type='pin_login',
                success=True
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'user': {
                    'id': employee.id,
                    'full_name': employee.full_name,
                    'role': employee.role.name if employee.role else 'staff',
                    'user_type': 'employee'
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============ 2FA MANAGEMENT ============

    def enable_2fa(self, employee_id: int) -> Dict:
        """Enable 2FA for employee and return QR code"""
        try:
            employee = Employee.query.get(employee_id)
            if not employee:
                return {'success': False, 'error': 'Employee not found'}

            # Generate secret
            secret = pyotp.random_base32()
            employee.totp_secret = secret

            # Generate backup codes (10 codes)
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
            employee.backup_codes = backup_codes

            # Don't enable yet - wait for verification
            employee.totp_enabled = False
            db.session.commit()

            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=employee.email,
                issuer_name='Happy Place Boutique'
            )

            # Create QR code image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()

            return {
                'success': True,
                'secret': secret,
                'qr_code': f'data:image/png;base64,{qr_base64}',
                'backup_codes': backup_codes,
                'message': 'Scan QR code with Google Authenticator, then verify to enable 2FA'
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def verify_and_enable_2fa(self, employee_id: int, code: str) -> Dict:
        """Verify 2FA code and enable 2FA"""
        try:
            employee = Employee.query.get(employee_id)
            if not employee or not employee.totp_secret:
                return {'success': False, 'error': 'Invalid request'}

            # Verify code
            if self._verify_totp(employee.totp_secret, code):
                employee.totp_enabled = True
                db.session.commit()

                self._log_auth_event(
                    user_id=employee_id,
                    user_type='employee',
                    event_type='2fa_enabled',
                    success=True
                )

                return {
                    'success': True,
                    'message': '2FA enabled successfully'
                }
            else:
                return {'success': False, 'error': 'Invalid code'}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # ============ TOKEN MANAGEMENT ============

    def _generate_tokens(
        self,
        user_id: int,
        user_type: str,
        additional_claims: Optional[Dict] = None,
        access_expires: Optional[timedelta] = None
    ) -> Dict:
        """Generate access and refresh tokens"""

        claims = {
            'user_type': user_type,
            **(additional_claims or {})
        }

        # Create access token
        access_token = create_access_token(
            identity=str(user_id),
            additional_claims=claims,
            expires_delta=access_expires or self.ACCESS_TOKEN_EXPIRES
        )

        # Create refresh token
        refresh_token = create_refresh_token(
            identity=str(user_id),
            additional_claims=claims,
            expires_delta=self.REFRESH_TOKEN_EXPIRES
        )

        # Store refresh token in database
        refresh_jti = get_jti(refresh_token)
        refresh_token_record = RefreshToken(
            user_id=user_id,
            user_type=user_type,
            token_jti=refresh_jti,
            expires_at=datetime.now() + self.REFRESH_TOKEN_EXPIRES,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )

        db.session.add(refresh_token_record)
        db.session.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def refresh_access_token(self, refresh_token_jti: str, user_id: int) -> Dict:
        """Generate new access token using refresh token"""
        try:
            # Check if refresh token is valid and not revoked
            token_record = RefreshToken.query.filter_by(
                token_jti=refresh_token_jti,
                user_id=user_id,
                revoked=False
            ).first()

            if not token_record:
                return {'success': False, 'error': 'Invalid refresh token'}

            # Check if expired
            if datetime.now() > token_record.expires_at:
                return {'success': False, 'error': 'Refresh token expired'}

            # Generate new access token
            if token_record.user_type == 'customer':
                customer = Customer.query.get(user_id)
                additional_claims = {}
            else:
                employee = Employee.query.get(user_id)
                additional_claims = {
                    'role': employee.role.name if employee.role else 'staff'
                }

            access_token = create_access_token(
                identity=str(user_id),
                additional_claims={'user_type': token_record.user_type, **additional_claims},
                expires_delta=self.ACCESS_TOKEN_EXPIRES
            )

            return {
                'success': True,
                'access_token': access_token
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def logout(self, access_jti: str, refresh_jti: str, user_id: int) -> Dict:
        """Logout user by blacklisting tokens"""
        try:
            # Blacklist access token
            access_blacklist = TokenBlacklist(
                jti=access_jti,
                token_type='access',
                user_id=user_id,
                expires_at=datetime.now() + self.ACCESS_TOKEN_EXPIRES,
                reason='logout'
            )

            # Blacklist refresh token
            refresh_blacklist = TokenBlacklist(
                jti=refresh_jti,
                token_type='refresh',
                user_id=user_id,
                expires_at=datetime.now() + self.REFRESH_TOKEN_EXPIRES,
                reason='logout'
            )

            # Mark refresh token as revoked
            refresh_token = RefreshToken.query.filter_by(token_jti=refresh_jti).first()
            if refresh_token:
                refresh_token.revoked = True
                refresh_token.revoked_at = datetime.now()

            db.session.add(access_blacklist)
            db.session.add(refresh_blacklist)
            db.session.commit()

            # Log event
            self._log_auth_event(
                user_id=user_id,
                user_type='customer',  # Will be determined from token
                event_type='logout',
                success=True
            )

            return {'success': True, 'message': 'Logged out successfully'}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # ============ HELPER METHODS ============

    def _is_strong_password(self, password: str) -> bool:
        """Check password strength"""
        import re

        if len(password) < 8:
            return False

        # Must contain uppercase, lowercase, and number
        has_upper = re.search(r'[A-Z]', password)
        has_lower = re.search(r'[a-z]', password)
        has_digit = re.search(r'\d', password)

        return bool(has_upper and has_lower and has_digit)

    def _is_account_locked(self, employee: Employee) -> bool:
        """Check if employee account is locked"""
        if not employee.account_locked_until:
            return False

        if datetime.now() > employee.account_locked_until:
            # Lockout period expired
            employee.account_locked_until = None
            employee.failed_login_attempts = 0
            db.session.commit()
            return False

        return True

    def _verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 30 seconds before/after

    def _generate_temp_token(self, user_id: int) -> str:
        """Generate temporary token for 2FA flow"""
        # Short-lived token (5 minutes) just to pass user_id to 2FA verification
        return create_access_token(
            identity=str(user_id),
            expires_delta=timedelta(minutes=5),
            additional_claims={'temp': True}
        )

    def _log_auth_event(
        self,
        user_id: Optional[int],
        user_type: str,
        event_type: str,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log authentication event"""
        try:
            log = AuthAuditLog(
                user_id=user_id,
                user_type=user_type,
                event_type=event_type,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get('User-Agent') if request else None,
                success=success,
                error_message=error_message,
                metadata=metadata
            )
            db.session.add(log)
            db.session.commit()
        except:
            # Don't fail auth if logging fails
            pass

# Create global instance
auth_service = AuthService()
```

This is getting long! Should I continue with:
1. The authentication routes
2. Frontend components for separate login pages
3. OAuth integration setup
4. JWT blacklist checker

Or would you like me to create a summary document first?