"""
Authentication Service

Handles all authentication operations:
- Customer authentication (email/password + Google OAuth)
- Employee authentication (email/password + 2FA + PIN)
- Refresh token management
- Token blacklist/logout
- Session tracking
- Permission checks
- Audit logging
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64

from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token
)
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from extensions import db
from models import Customer, Employee
from logging_utils import get_logger

logger = get_logger(__name__)

ACCESS_TYPE = "access"

class AuthService:
    """Authentication service for customers and employees"""

    # Token expiration times
    ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    POS_SESSION_EXPIRES = timedelta(hours=8)

    # Security settings
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    PASSWORD_MIN_LENGTH = 8

    def __init__(self):
        pass
    
    def _is_test_account(self, email: str) -> bool:
        """Check if email is a test account that should be auto-verified."""
        return (
            email.startswith('uat.') or 
            email.startswith('test') or 
            '@test.com' in email or
            '@example.com' in email
        )

    # =============================
    # CUSTOMER AUTHENTICATION
    # =============================

    def register_customer(self, email: str, password: str, first_name: str,
                         last_name: str, phone: str = None,
                         gdpr_consent: bool = False,
                         marketing_consent: bool = False) -> Dict:
        """
        Register new customer account.

        Returns:
            {
                'success': True,
                'customer_id': int,
                'message': str
            }
        """
        try:
            # Validate password strength
            if not self._validate_password_strength(password):
                return {
                    'success': False,
                    'error': f'Password must be at least {self.PASSWORD_MIN_LENGTH} characters with uppercase, lowercase, and numbers'
                }

            # Check if email already exists
            existing = Customer.query.filter_by(email_hash=self._hash_email(email)).first()
            if existing:
                return {
                    'success': False,
                    'error': 'Email already registered'
                }

            # Create customer
            customer = Customer()
            customer.email = email  # Uses property setter (hash + encrypt)
            customer.first_name = first_name
            customer.last_name = last_name
            customer.phone = phone
            customer.set_password(password)
            customer.gdpr_consent = gdpr_consent
            customer.marketing_consent = marketing_consent
            
            # Auto-verify test accounts (UAT testing)
            is_test_account = self._is_test_account(email)
            customer.email_verified = is_test_account  # Auto-verify test accounts
            customer.data_retention_date = datetime.utcnow() + timedelta(days=3*365)  # 3 years

            # Generate email verification token (only for non-test accounts)
            if not is_test_account:
                customer.email_verification_token = secrets.token_urlsafe(32)
                customer.email_verification_sent_at = datetime.utcnow()

            db.session.add(customer)
            db.session.commit()

            # Log event
            self._log_auth_event(
                user_id=customer.id,
                user_type='customer',
                email=email,
                event_type='register',
                auth_method='password',
                success=True
            )

            # Generate tokens for test accounts (auto-verified)
            result = {
                'success': True,
                'customer_id': customer.id,
                'customer': customer.to_dict(),
                'message': 'Customer registered successfully.'
            }
            
            if is_test_account:
                try:
                    # Generate tokens for immediate use
                    tokens = self._generate_tokens(
                        user_id=customer.id,
                        user_type='customer',
                        additional_claims={}
                    )
                    # Store refresh token
                    self._store_refresh_token(
                        user_id=customer.id,
                        user_type='customer',
                        token_jti=tokens['refresh_jti'],
                        expires_at=datetime.utcnow() + self.REFRESH_TOKEN_EXPIRES
                    )
                    result['access_token'] = tokens['access_token']
                    result['refresh_token'] = tokens['refresh_token']
                except Exception as token_error:
                    # If token generation fails, log but don't fail registration
                    import sys
                    print(f"WARNING: Token generation failed: {str(token_error)}", file=sys.stderr)
            else:
                if not is_test_account:
                    result['verification_token'] = customer.email_verification_token
                    result['message'] += ' Please verify email.'
            
            return result

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Registration failed: {str(e)}'
            }

    def login_customer(self, email: str, password: str) -> Dict:
        """
        Customer login with email/password.

        Returns:
            {
                'success': True,
                'access_token': str,
                'refresh_token': str,
                'customer': {...}
            }
        """
        try:
            # Find customer by email hash
            customer = Customer.query.filter_by(
                email_hash=self._hash_email(email)
            ).first()

            if not customer or not customer.check_password(password):
                self._log_auth_event(
                    user_id=None,
                    user_type='customer',
                    email=email,
                    event_type='login_failed',
                    auth_method='password',
                    success=False,
                    error_message='Invalid credentials'
                )
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }

            # Check if customer is active
            if not customer.is_active:
                return {
                    'success': False,
                    'error': 'Account is inactive'
                }

            # Check if email is verified
            if not customer.email_verified:
                return {
                    'success': False,
                    'error': 'Email not verified. Please check your email.'
                }

            # Generate tokens
            tokens = self._generate_tokens(
                user_id=customer.id,
                user_type='customer',
                additional_claims={}
            )

            # Store refresh token
            self._store_refresh_token(
                user_id=customer.id,
                user_type='customer',
                token_jti=tokens['refresh_jti'],
                expires_at=datetime.utcnow() + self.REFRESH_TOKEN_EXPIRES
            )

            # Update login tracking
            try:
                if hasattr(customer, 'login_count'):
                    current_count = getattr(customer, 'login_count', 0) or 0
                    setattr(customer, 'login_count', current_count + 1)
                if hasattr(customer, 'last_login'):
                    customer.last_login = datetime.utcnow()
                if hasattr(customer, 'last_login_ip'):
                    customer.last_login_ip = self._get_client_ip()
                if hasattr(customer, 'last_login_user_agent'):
                    customer.last_login_user_agent = request.headers.get('User-Agent', '')
                db.session.commit()
            except Exception:
                # Login should still succeed even if optional tracking fields are not present
                db.session.rollback()

            # Log successful login
            self._log_auth_event(
                user_id=customer.id,
                user_type='customer',
                email=email,
                event_type='login',
                auth_method='password',
                success=True
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'customer': customer.to_dict()
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Login failed: {str(e)}'
            }

    def login_customer_google_oauth(self, id_token_str: str) -> Dict:
        """
        Customer login with Google OAuth.

        Args:
            id_token_str: Google ID token from OAuth flow

        Returns:
            {
                'success': True,
                'access_token': str,
                'refresh_token': str,
                'customer': {...},
                'is_new_user': bool
            }
        """
        try:
            # Verify Google ID token
            google_client_id = self._get_google_client_id()
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                google_client_id
            )

            # Extract user info
            google_id = idinfo['sub']
            email = idinfo['email']
            email_verified = idinfo.get('email_verified', False)
            given_name = idinfo.get('given_name', '')
            family_name = idinfo.get('family_name', '')

            # Check if customer exists with this OAuth provider
            customer = Customer.query.filter_by(
                oauth_provider='google',
                oauth_id=google_id
            ).first()

            is_new_user = False

            if not customer:
                # Check if email already exists (link to existing account)
                customer = Customer.query.filter_by(
                    email_hash=self._hash_email(email)
                ).first()

                if customer:
                    # Link OAuth to existing account
                    customer.oauth_provider = 'google'
                    customer.oauth_id = google_id
                    customer.email_verified = bool(customer.email_verified) or bool(email_verified)
                else:
                    # Create new customer
                    customer = Customer()
                    customer.email = email
                    customer.first_name = given_name
                    customer.last_name = family_name
                    customer.oauth_provider = 'google'
                    customer.oauth_id = google_id
                    customer.email_verified = bool(email_verified)
                    customer.gdpr_consent = True  # Implicit via Google login
                    customer.is_active = True
                    customer.password_hash = generate_password_hash(secrets.token_urlsafe(32))  # Random password
                    customer.data_retention_date = datetime.utcnow() + timedelta(days=3*365)

                    db.session.add(customer)
                    is_new_user = True

            # Update OAuth tokens
            customer.oauth_access_token = id_token_str
            db.session.commit()

            # Generate JWT tokens
            tokens = self._generate_tokens(
                user_id=customer.id,
                user_type='customer',
                additional_claims={'oauth_provider': 'google'}
            )

            # Store refresh token
            self._store_refresh_token(
                user_id=customer.id,
                user_type='customer',
                token_jti=tokens['refresh_jti'],
                expires_at=datetime.utcnow() + self.REFRESH_TOKEN_EXPIRES
            )

            # Update login tracking
            customer.login_count += 1
            customer.last_login = datetime.utcnow()
            customer.last_login_ip = self._get_client_ip()
            customer.last_login_user_agent = request.headers.get('User-Agent', '')
            db.session.commit()

            # Log event
            self._log_auth_event(
                user_id=customer.id,
                user_type='customer',
                email=email,
                event_type='login' if not is_new_user else 'register',
                auth_method='google_oauth',
                success=True
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'customer': customer.to_dict(),
                'is_new_user': is_new_user
            }

        except ValueError as e:
            # Invalid token
            self._log_auth_event(
                user_id=None,
                user_type='customer',
                email=None,
                event_type='login_failed',
                auth_method='google_oauth',
                success=False,
                error_message=f'Invalid Google token: {str(e)}'
            )
            return {
                'success': False,
                'error': 'Invalid Google authentication token'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'OAuth login failed: {str(e)}'
            }

    # =============================
    # EMPLOYEE AUTHENTICATION
    # =============================

    def login_employee(self, email: str, password: str, totp_code: str = None) -> Dict:
        """
        Employee login with email/password and optional 2FA.

        Args:
            email: Employee email
            password: Employee password
            totp_code: 6-digit TOTP code (required if 2FA enabled)

        Returns:
            {
                'success': True,
                'access_token': str,
                'refresh_token': str,
                'employee': {...},
                'requires_2fa': bool  # If 2FA enabled but code not provided
            }
        """
        try:
            employee = Employee.query.filter_by(email=email).first()

            if not employee or not check_password_hash(employee.password_hash, password):
                # Log failed attempt
                if employee:
                    employee.failed_login_attempts += 1
                    if employee.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                        employee.account_locked_until = datetime.utcnow() + self.LOCKOUT_DURATION
                    db.session.commit()

                self._log_auth_event(
                    user_id=employee.id if employee else None,
                    user_type='employee',
                    email=email,
                    event_type='login_failed',
                    auth_method='password',
                    success=False,
                    error_message='Invalid credentials'
                )
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }

            # Check if account is locked
            if employee.account_locked_until and employee.account_locked_until > datetime.utcnow():
                return {
                    'success': False,
                    'error': f'Account locked until {employee.account_locked_until.strftime("%H:%M:%S")} due to failed login attempts'
                }

            # Check if account is active
            if not employee.is_active:
                return {
                    'success': False,
                    'error': 'Account is inactive'
                }

            # Check 2FA
            if employee.totp_enabled:
                if not totp_code:
                    return {
                        'success': False,
                        'requires_2fa': True,
                        'message': 'Please provide 2FA code'
                    }

                if not self._verify_totp(employee.totp_secret, totp_code):
                    # Check backup codes
                    if not self._verify_backup_code(employee, totp_code):
                        employee.failed_login_attempts += 1
                        db.session.commit()

                        self._log_auth_event(
                            user_id=employee.id,
                            user_type='employee',
                            email=email,
                            event_type='2fa_failed',
                            auth_method='totp',
                            success=False,
                            error_message='Invalid 2FA code'
                        )
                        return {
                            'success': False,
                            'error': 'Invalid 2FA code'
                        }

            # Generate tokens
            tokens = self._generate_tokens(
                user_id=employee.id,
                user_type='employee',
                additional_claims={
                    'role': employee.role
                }
            )

            # Store refresh token
            self._store_refresh_token(
                user_id=employee.id,
                user_type='employee',
                token_jti=tokens['refresh_jti'],
                expires_at=datetime.utcnow() + self.REFRESH_TOKEN_EXPIRES
            )

            # Reset failed attempts
            employee.failed_login_attempts = 0
            employee.account_locked_until = None

            # Update login tracking
            employee.login_count += 1
            employee.last_login = datetime.utcnow()
            employee.last_login_ip = self._get_client_ip()
            employee.last_login_user_agent = request.headers.get('User-Agent', '')
            db.session.commit()

            # Log successful login
            self._log_auth_event(
                user_id=employee.id,
                user_type='employee',
                email=email,
                event_type='login',
                auth_method='password_2fa' if employee.totp_enabled else 'password',
                success=True
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'employee': {
                    'id': employee.id,
                    'email': employee.email,
                    'full_name': employee.full_name,
                    'role': employee.role
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Login failed: {str(e)}'
            }

    def login_employee_pin(self, pin: str) -> Dict:
        """
        Quick employee login with 6-digit PIN (for POS terminals).

        Args:
            pin: 6-digit PIN

        Returns:
            {
                'success': True,
                'access_token': str,
                'refresh_token': str (8-hour POS session),
                'employee': {...}
            }
        """
        try:
            # Find employee with matching PIN
            employees = Employee.query.filter_by(pin_enabled=True, is_active=True).all()

            employee = None
            for emp in employees:
                if emp.pin_hash and check_password_hash(emp.pin_hash, pin):
                    employee = emp
                    break

            if not employee:
                self._log_auth_event(
                    user_id=None,
                    user_type='employee',
                    email=None,
                    event_type='pin_login_failed',
                    auth_method='pin',
                    success=False,
                    error_message='Invalid PIN'
                )
                return {
                    'success': False,
                    'error': 'Invalid PIN'
                }

            # Check if account is locked
            if employee.account_locked_until and employee.account_locked_until > datetime.utcnow():
                return {
                    'success': False,
                    'error': 'Account is locked'
                }

            # Generate tokens with shorter expiration for POS
            tokens = self._generate_tokens(
                user_id=employee.id,
                user_type='employee',
                additional_claims={'role': employee.role, 'session_type': 'pos'},
                expires_delta=self.POS_SESSION_EXPIRES
            )

            # Store refresh token
            self._store_refresh_token(
                user_id=employee.id,
                user_type='employee',
                token_jti=tokens['refresh_jti'],
                expires_at=datetime.utcnow() + self.POS_SESSION_EXPIRES
            )

            # Update login tracking
            employee.login_count += 1
            employee.last_login = datetime.utcnow()
            employee.last_login_ip = self._get_client_ip()
            db.session.commit()

            # Log PIN login
            self._log_auth_event(
                user_id=employee.id,
                user_type='employee',
                email=employee.email,
                event_type='pin_login',
                auth_method='pin',
                success=True
            )

            return {
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'employee': {
                    'id': employee.id,
                    'email': employee.email,
                    'full_name': employee.full_name,
                    'role': employee.role
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'PIN login failed: {str(e)}'
            }

    # =============================
    # 2FA (TOTP) MANAGEMENT
    # =============================

    def enable_2fa(self, employee_id: int) -> Dict:
        """
        Enable 2FA for employee and generate QR code.

        Returns:
            {
                'success': True,
                'secret': str,  # Base32 secret
                'qr_code': str,  # Base64-encoded PNG
                'backup_codes': List[str]  # 10 backup codes
            }
        """
        try:
            employee = Employee.query.get(employee_id)
            if not employee:
                return {'success': False, 'error': 'Employee not found'}

            # Generate TOTP secret
            secret = pyotp.random_base32()

            # Generate backup codes (10 codes, 8 characters each)
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

            # Hash backup codes for storage
            hashed_backup_codes = [generate_password_hash(code) for code in backup_codes]

            # Store in database
            employee.totp_secret = secret
            employee.backup_codes = hashed_backup_codes  # Store hashed versions
            # Don't enable yet - wait for verification

            db.session.commit()

            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=employee.email,
                issuer_name='Happy Place Boutique'
            )

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

            return {
                'success': True,
                'secret': secret,
                'qr_code': qr_code_base64,
                'backup_codes': backup_codes,  # Return plain text to user (only time they'll see them),
                'provisioning_uri': provisioning_uri
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Failed to enable 2FA: {str(e)}'
            }

    def verify_and_enable_2fa(self, employee_id: int, totp_code: str) -> Dict:
        """
        Verify 2FA setup and enable it.

        Args:
            employee_id: Employee ID
            totp_code: 6-digit code from authenticator app

        Returns:
            {'success': True/False}
        """
        try:
            employee = Employee.query.get(employee_id)
            if not employee or not employee.totp_secret:
                return {'success': False, 'error': 'No 2FA setup found'}

            # Verify code
            if not self._verify_totp(employee.totp_secret, totp_code):
                return {'success': False, 'error': 'Invalid code'}

            # Enable 2FA
            employee.totp_enabled = True
            employee.totp_enabled_at = datetime.utcnow()
            db.session.commit()

            # Log event
            self._log_auth_event(
                user_id=employee.id,
                user_type='employee',
                email=employee.email,
                event_type='2fa_enabled',
                auth_method='totp',
                success=True
            )

            return {'success': True, 'message': '2FA enabled successfully'}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def disable_2fa(self, employee_id: int, totp_code: str) -> Dict:
        """
        Disable 2FA (requires current code for security).
        """
        try:
            employee = Employee.query.get(employee_id)
            if not employee or not employee.totp_enabled:
                return {'success': False, 'error': '2FA not enabled'}

            # Verify code before disabling
            if not self._verify_totp(employee.totp_secret, totp_code):
                return {'success': False, 'error': 'Invalid code'}

            # Disable 2FA
            employee.totp_enabled = False
            employee.totp_secret = None
            employee.backup_codes = None
            db.session.commit()

            # Log event
            self._log_auth_event(
                user_id=employee.id,
                user_type='employee',
                email=employee.email,
                event_type='2fa_disabled',
                auth_method='totp',
                success=True
            )

            return {'success': True, 'message': '2FA disabled successfully'}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # =============================
    # TOKEN MANAGEMENT
    # =============================

    def refresh_access_token(self, refresh_token_jti: str) -> Dict:
        """
        Generate new access token using refresh token.

        Returns:
            {
                'success': True,
                'access_token': str
            }
        """
        try:
            # Check if refresh token is blacklisted
            if self._is_token_blacklisted(refresh_token_jti):
                return {'success': False, 'error': 'Token has been revoked'}

            # Get refresh token from database
            from models.database_models import RefreshToken
            refresh_token = RefreshToken.query.filter_by(token_jti=refresh_token_jti).first()

            if not refresh_token or refresh_token.revoked:
                return {'success': False, 'error': 'Invalid refresh token'}

            if refresh_token.expires_at < datetime.utcnow():
                return {'success': False, 'error': 'Refresh token expired'}

            # Generate new access token
            access_token = create_access_token(
                identity=str(refresh_token.user_id),
                additional_claims={'user_type': refresh_token.user_type},
                expires_delta=self.ACCESS_TOKEN_EXPIRES
            )

            # Update last used
            refresh_token.last_used_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'access_token': access_token
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def logout(self, access_token_jti: str, refresh_token_jti: str) -> Dict:
        """
        Logout user by blacklisting tokens.

        Args:
            access_token_jti: Access token JTI
            refresh_token_jti: Refresh token JTI

        Returns:
            {'success': True}
        """
        try:
            from models.database_models import TokenBlacklist, RefreshToken

            # Blacklist access token
            blacklist_entry = TokenBlacklist(
                jti=access_token_jti,
                token_type=ACCESS_TYPE,
                expires_at=datetime.utcnow() + self.ACCESS_TOKEN_EXPIRES,
                reason='logout'
            )
            db.session.add(blacklist_entry)

            # Revoke refresh token
            refresh_token = RefreshToken.query.filter_by(token_jti=refresh_token_jti).first()
            if refresh_token:
                refresh_token.revoked = True
                refresh_token.revoked_at = datetime.utcnow()
                refresh_token.revoked_reason = 'logout'

            db.session.commit()

            return {'success': True, 'message': 'Logged out successfully'}

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def logout_all_devices(self, user_id: int, user_type: str) -> Dict:
        """
        Logout user from all devices by revoking all refresh tokens.
        """
        try:
            from models.database_models import RefreshToken

            # Revoke all refresh tokens for user
            tokens = RefreshToken.query.filter_by(
                user_id=user_id,
                user_type=user_type,
                revoked=False
            ).all()

            for token in tokens:
                token.revoked = True
                token.revoked_at = datetime.utcnow()
                token.revoked_reason = 'logout_all'

            db.session.commit()

            return {
                'success': True,
                'message': f'Logged out from {len(tokens)} devices'
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # =============================
    # PERMISSION CHECKS
    # =============================

    def has_permission(self, employee_id: int, permission_name: str) -> bool:
        """
        Check if employee has a specific permission.

        Args:
            employee_id: Employee ID
            permission_name: Permission name (e.g., 'pos.create_sale')

        Returns:
            True if employee has permission, False otherwise
        """
        try:
            from models.database_models import Permission, RolePermission

            employee = Employee.query.get(employee_id)
            if not employee or not employee.is_active:
                return False

            # Check if role has permission
            permission = Permission.query.filter_by(name=permission_name, is_active=True).first()
            if not permission:
                return False

            role_perm = RolePermission.query.filter_by(
                role=employee.role,
                permission_id=permission.id
            ).first()

            return role_perm is not None

        except Exception:
            return False

    def get_employee_permissions(self, employee_id: int) -> List[str]:
        """
        Get all permissions for an employee.

        Returns:
            List of permission names
        """
        try:
            from models.database_models import Permission, RolePermission

            employee = Employee.query.get(employee_id)
            if not employee or not employee.is_active:
                return []

            permissions = db.session.query(Permission.name).join(
                RolePermission, Permission.id == RolePermission.permission_id
            ).filter(
                RolePermission.role == employee.role,
                Permission.is_active.is_(True)
            ).all()

            return [perm[0] for perm in permissions]

        except Exception:
            return []

    # =============================
    # HELPER METHODS
    # =============================

    def _generate_tokens(self, user_id: int, user_type: str,
                        additional_claims: Dict = None,
                        expires_delta: timedelta = None) -> Dict:
        """Generate access and refresh tokens."""
        import uuid

        claims = additional_claims or {}
        claims['user_type'] = user_type

        # Generate JTIs
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())

        claims['jti'] = access_jti

        access_token = create_access_token(
            identity=str(user_id),
            additional_claims=claims,
            expires_delta=expires_delta or self.ACCESS_TOKEN_EXPIRES
        )

        refresh_token = create_refresh_token(
            identity=str(user_id),
            additional_claims={'jti': refresh_jti, 'user_type': user_type},
            expires_delta=self.REFRESH_TOKEN_EXPIRES
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_jti': access_jti,
            'refresh_jti': refresh_jti
        }

    def _store_refresh_token(self, user_id: int, user_type: str,
                            token_jti: str, expires_at: datetime) -> None:
        """Store refresh token in database."""
        from models.database_models import RefreshToken

        refresh_token = RefreshToken(
            user_id=user_id,
            user_type=user_type,
            token_jti=token_jti,
            ip_address=self._get_client_ip(),
            user_agent=request.headers.get('User-Agent', ''),
            expires_at=expires_at
        )
        db.session.add(refresh_token)
        db.session.commit()

    def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        from models.database_models import TokenBlacklist

        blacklisted = TokenBlacklist.query.filter_by(jti=jti).first()
        return blacklisted is not None and blacklisted.expires_at > datetime.utcnow()

    def _verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 1 time step before/after

    def _verify_backup_code(self, employee: Employee, code: str) -> bool:
        """Verify and consume backup code."""
        if not employee.backup_codes:
            return False

        for idx, hashed_code in enumerate(employee.backup_codes):
            if check_password_hash(hashed_code, code):
                # Remove used backup code
                employee.backup_codes.pop(idx)
                db.session.commit()
                return True

        return False

    def _hash_email(self, email: str) -> str:
        """Hash email for lookup (uses services.encryption.hash_email)."""
        from services.encryption import hash_email
        return hash_email(email)

    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements."""
        if len(password) < self.PASSWORD_MIN_LENGTH:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        return has_upper and has_lower and has_digit

    def _get_client_ip(self) -> str:
        """Get client IP address."""
        return request.remote_addr or 'unknown'

    def _get_google_client_id(self) -> str:
        """Get Google OAuth client ID from config."""
        from flask import current_app
        return current_app.config.get('GOOGLE_CLIENT_ID', '')

    def _log_auth_event(self, user_id: Optional[int], user_type: str, email: Optional[str],
                       event_type: str, auth_method: str, success: bool,
                       error_message: str = None, extra_data: Dict = None) -> None:
        """Log authentication event to audit log."""
        from models.database_models import AuthAuditLog

        log_entry = AuthAuditLog(
            user_id=user_id,
            user_type=user_type,
            email=email,
            event_type=event_type,
            auth_method=auth_method,
            success=success,
            error_message=error_message,
            ip_address=self._get_client_ip(),
            user_agent=request.headers.get('User-Agent', ''),
            extra_data=extra_data
        )
        db.session.add(log_entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
