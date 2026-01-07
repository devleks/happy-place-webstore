"""
Authentication API Routes

Endpoints for customer and employee authentication:
- Customer: register, login, Google OAuth, email verification, password reset
- Employee: login, PIN login, 2FA management
- Token: refresh, logout, session management
"""

from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.auth_service import AuthService
from services.email_service import email_service
from middleware import customer_required, employee_required, manager_required
from middleware.rate_limiter import auth_rate_limit, strict_auth_rate_limit
from logging_utils import get_logger, safe_auth_context
import secrets

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize service and logger
auth_service = AuthService()
logger = get_logger(__name__)


@auth_bp.route('/customer/me', methods=['GET'])
@customer_required
def get_customer_profile(current_customer):
    """Get current customer profile."""
    return jsonify({
        'id': current_customer.id,
        'email': current_customer.email,
        'first_name': current_customer.first_name,
        'last_name': current_customer.last_name,
        'phone': current_customer.phone,
        'gdpr_consent': current_customer.gdpr_consent,
        'marketing_consent': current_customer.marketing_consent,
        'is_active': current_customer.is_active,
        'email_verified': getattr(current_customer, 'email_verified', None),
        'created_at': current_customer.created_at.isoformat() if current_customer.created_at else None
    }), 200


@auth_bp.route('/employee/me', methods=['GET'])
@employee_required
def get_employee_profile(current_employee):
    """Get current employee profile."""
    return jsonify({
        'id': current_employee.id,
        'email': current_employee.email,
        'full_name': current_employee.full_name,
        'role': current_employee.role,
        'is_active': current_employee.is_active,
        'created_at': current_employee.created_at.isoformat() if current_employee.created_at else None
    }), 200


# =====================================================
# CUSTOMER AUTHENTICATION ENDPOINTS
# =====================================================

@auth_bp.route('/customer/register', methods=['POST'])
@strict_auth_rate_limit  # 3 requests per 5 minutes
def customer_register():
    """
    Register new customer account.

    POST /api/auth/customer/register
    Body: {
        "email": "customer@example.com",
        "password": "SecurePass123",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "+254712345678",  // optional
        "gdpr_consent": true,
        "marketing_consent": false  // optional
    }

    Returns:
        201: Customer registered successfully
        400: Validation error or email already exists
    """
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid request body (expected JSON object)'}), 400

        # Validate required fields
        required = ['email', 'password', 'first_name', 'last_name', 'gdpr_consent']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # GDPR consent must be explicitly true
        if data.get('gdpr_consent') is not True:
            return jsonify({'error': 'GDPR consent is required'}), 400

        result = auth_service.register_customer(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            gdpr_consent=data['gdpr_consent'],
            marketing_consent=data.get('marketing_consent', False)
        )

        if result['success']:
            # Send verification email (non-blocking - don't fail registration if email fails)
            try:
                # Generate verification token
                verification_token = secrets.token_urlsafe(32)

                # Get customer info from result
                customer_name = f"{data['first_name']} {data['last_name']}"
                customer_email = data['email']

                # Send verification email
                email_result = email_service.send_verification_email(
                    email=customer_email,
                    customer_name=customer_name,
                    verification_token=verification_token
                )

                if email_result.get('success'):
                    logger.info(
                        f"Verification email sent to {customer_email}",
                        extra={"context": safe_auth_context(
                            email=customer_email,
                            user_type='customer',
                            ip=request.remote_addr,
                            user_agent=request.headers.get('User-Agent')
                        )}
                    )
                else:
                    logger.warning(
                        f"Verification email failed for {customer_email}: {email_result.get('error')}",
                        extra={"context": safe_auth_context(
                            email=customer_email,
                            user_type='customer',
                            ip=request.remote_addr,
                            user_agent=request.headers.get('User-Agent')
                        )}
                    )
            except Exception as e:
                # Log email error but don't fail registration
                logger.error(
                    f"Verification email exception for {data.get('email', 'unknown')}",
                    extra={"context": safe_auth_context(
                        user_type='customer',
                        ip=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )},
                    exc_info=True
                )

            # Debug: print to stderr
            import sys
            print(f"DEBUG: Registration result keys: {list(result.keys())}", file=sys.stderr)
            print(f"DEBUG: Has refresh_token: {'refresh_token' in result}", file=sys.stderr)
            if 'refresh_token' in result:
                print(f"DEBUG: refresh_token value type: {type(result['refresh_token'])}", file=sys.stderr)
                print(f"DEBUG: refresh_token length: {len(result['refresh_token']) if result['refresh_token'] else 0}", file=sys.stderr)

            response_data = {
                'success': True,
                'message': result['message']
            }

            # Add tokens if present
            if 'access_token' in result and result['access_token']:
                response_data['access_token'] = result['access_token']
            if 'refresh_token' in result and result['refresh_token']:
                response_data['refresh_token'] = result['refresh_token']
                print("DEBUG: Added refresh_token to response", file=sys.stderr)
            if 'customer' in result and result['customer']:
                response_data['customer'] = result['customer']

            print(f"DEBUG: Response data keys: {list(response_data.keys())}", file=sys.stderr)
            return jsonify(response_data), 201
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Customer registration failed",
            extra={"context": safe_auth_context(email=data.get('email') if 'data' in locals() and data else None,
                                                 user_type='customer',
                                                 ip=request.remote_addr,
                                                 user_agent=request.headers.get('User-Agent'))},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/customer/login', methods=['POST'])
@auth_rate_limit  # 5 requests per minute
def customer_login():
    """
    Customer login with email and password.

    POST /api/auth/customer/login
    Body: {
        "email": "customer@example.com",
        "password": "SecurePass123"
    }

    Returns:
        200: Login successful with tokens
        400: Invalid credentials or account inactive
    """
    try:
        data = request.get_json()

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400

        result = auth_service.login_customer(
            email=data['email'],
            password=data['password']
        )

        if result['success']:
            return jsonify({
                'success': True,
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'customer': result['customer']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Customer login failed (unexpected error)",
            extra={"context": safe_auth_context(email=data.get('email') if 'data' in locals() and data else None,
                                                 user_type='customer',
                                                 ip=request.remote_addr,
                                                 user_agent=request.headers.get('User-Agent'))},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/customer/google-oauth', methods=['POST'])
def customer_google_oauth():
    """
    Customer login/register with Google OAuth.

    POST /api/auth/customer/google-oauth
    Body: {
        "id_token": "google_id_token_from_oauth_flow"
    }

    Returns:
        200: Login successful with tokens
        400: Invalid Google token
    """
    try:
        data = request.get_json()

        if not data or 'id_token' not in data:
            return jsonify({'error': 'Google ID token required'}), 400

        result = auth_service.login_customer_google_oauth(
            id_token_str=data['id_token']
        )

        if result['success']:
            return jsonify({
                'success': True,
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'customer': result['customer'],
                'is_new_user': result['is_new_user']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Google OAuth operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/customer/verify-email', methods=['POST'])
def customer_verify_email():
    """
    Verify customer email with token.

    POST /api/auth/customer/verify-email
    Body: {
        "token": "email_verification_token"
    }

    Returns:
        200: Email verified successfully
        400: Invalid or expired token
    """
    # TODO: Implement email verification
    return jsonify({'message': 'Email verification not yet implemented'}), 501


@auth_bp.route('/customer/forgot-password', methods=['POST'])
def customer_forgot_password():
    """
    Request password reset email.

    POST /api/auth/customer/forgot-password
    Body: {
        "email": "customer@example.com"
    }

    Returns:
        200: Password reset email sent
        404: Email not found
    """
    # TODO: Implement password reset
    return jsonify({'message': 'Password reset not yet implemented'}), 501


@auth_bp.route('/customer/reset-password', methods=['POST'])
def customer_reset_password():
    """
    Reset password with token.

    POST /api/auth/customer/reset-password
    Body: {
        "token": "password_reset_token",
        "new_password": "NewSecurePass123"
    }

    Returns:
        200: Password reset successful
        400: Invalid or expired token
    """
    # TODO: Implement password reset
    return jsonify({'message': 'Password reset not yet implemented'}), 501


# =====================================================
# EMPLOYEE AUTHENTICATION ENDPOINTS
# =====================================================

@auth_bp.route('/employee/login', methods=['POST'])
@auth_rate_limit  # 5 requests per minute
def employee_login():
    """
    Employee login with email, password, and optional 2FA.

    POST /api/auth/employee/login
    Body: {
        "email": "employee@happyplace.com",
        "password": "SecurePass123",
        "totp_code": "123456"  // required if 2FA enabled
    }

    Returns:
        200: Login successful with tokens
        400: Invalid credentials, account locked, or 2FA code required
    """
    try:
        data = request.get_json()

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400

        result = auth_service.login_employee(
            email=data['email'],
            password=data['password'],
            totp_code=data.get('totp_code')
        )

        if result['success']:
            return jsonify({
                'success': True,
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'employee': result['employee']
            }), 200
        elif result.get('requires_2fa'):
            return jsonify({
                'error': '2FA code required',
                'requires_2fa': True
            }), 400
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Employee login failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"email": data.get('email') if 'data' in locals() and data else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/admin/login', methods=['POST'])
@auth_rate_limit  # 5 requests per minute
def admin_login():
    """
    Admin-specific login endpoint with enhanced security logging.

    POST /api/auth/admin/login
    Body: {
        "email": "admin@happyplace.co.ke",
        "password": "Admin@123",
        "totp_code": "123456"  // required if 2FA enabled
    }

    Returns:
        200: Login successful with tokens
        400: Invalid credentials, not admin role, or 2FA required
        403: Access denied (not admin or manager role)
    """
    try:
        data = request.get_json()

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400

        # Use the same employee login service
        result = auth_service.login_employee(
            email=data['email'],
            password=data['password'],
            totp_code=data.get('totp_code')
        )

        if result['success']:
            # Verify that the user has admin role
            employee_role = (result['employee'].get('role') or '').lower()
            if employee_role != 'admin':
                return jsonify({
                    'error': 'Access denied. Admin role required.'
                }), 403

            # Log admin login for security audit (without full email)
            logger.info(
                "Admin login successful",
                extra={"context": safe_auth_context(email=data.get('email') if 'data' in locals() and data else None,
                                                     user_type='employee',
                                                     ip=request.remote_addr,
                                                     user_agent=request.headers.get('User-Agent'),
                                                     extra={"role": employee_role})},
            )

            return jsonify({
                'success': True,
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'employee': result['employee']
            }), 200
        elif result.get('requires_2fa'):
            return jsonify({
                'error': '2FA code required',
                'requires_2fa': True
            }), 400
        else:
            return jsonify({'error': result['error']}), 403

    except Exception:
        logger.error(
            "Admin login failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"email": data.get('email') if 'data' in locals() and data else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/employee/pin-login', methods=['POST'])
@auth_rate_limit  # 5 requests per minute
def employee_pin_login():
    """
    Quick employee login with 6-digit PIN (for POS).

    POST /api/auth/employee/pin-login
    Body: {
        "pin": "123456"
    }

    Returns:
        200: Login successful with tokens (8-hour session)
        400: Invalid PIN
    """
    try:
        data = request.get_json()

        if not data or 'pin' not in data:
            return jsonify({'error': 'PIN required'}), 400

        result = auth_service.login_employee_pin(pin=data['pin'])

        if result['success']:
            return jsonify({
                'success': True,
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'employee': result['employee']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Employee PIN login failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/employee/enable-2fa', methods=['POST'])
@jwt_required()
def employee_enable_2fa():
    """
    Enable 2FA for employee (generates QR code).

    POST /api/auth/employee/enable-2fa
    Headers: Authorization: Bearer <access_token>

    Returns:
        200: QR code and backup codes
        400: Error enabling 2FA
    """
    try:
        # Get employee ID from JWT
        employee_id = int(get_jwt_identity())

        result = auth_service.enable_2fa(employee_id)

        if result['success']:
            return jsonify({
                'success': True,
                'secret': result['secret'],
                'qr_code': result['qr_code'],
                'backup_codes': result['backup_codes'],
                'message': 'Scan QR code with Google Authenticator and verify to enable 2FA'
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Enable 2FA operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/employee/verify-2fa', methods=['POST'])
@jwt_required()
def employee_verify_2fa():
    """
    Verify and activate 2FA with code from authenticator app.

    POST /api/auth/employee/verify-2fa
    Headers: Authorization: Bearer <access_token>
    Body: {
        "totp_code": "123456"
    }

    Returns:
        200: 2FA enabled successfully
        400: Invalid code
    """
    try:
        employee_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'totp_code' not in data:
            return jsonify({'error': 'TOTP code required'}), 400

        result = auth_service.verify_and_enable_2fa(
            employee_id=employee_id,
            totp_code=data['totp_code']
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': '2FA enabled successfully'
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Verify 2FA operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/employee/disable-2fa', methods=['POST'])
@jwt_required()
def employee_disable_2fa():
    """
    Disable 2FA (requires current 2FA code for security).

    POST /api/auth/employee/disable-2fa
    Headers: Authorization: Bearer <access_token>
    Body: {
        "totp_code": "123456"
    }

    Returns:
        200: 2FA disabled successfully
        400: Invalid code or 2FA not enabled
    """
    try:
        employee_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'totp_code' not in data:
            return jsonify({'error': 'TOTP code required'}), 400

        result = auth_service.disable_2fa(
            employee_id=employee_id,
            totp_code=data['totp_code']
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': '2FA disabled successfully'
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Disable 2FA operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


# =====================================================
# TOKEN MANAGEMENT ENDPOINTS
# =====================================================

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_access_token():
    """
    Generate new access token using refresh token.

    POST /api/auth/refresh
    Headers: Authorization: Bearer <refresh_token>

    Returns:
        200: New access token
        401: Invalid or expired refresh token
    """
    try:
        # Get refresh token JTI
        jwt_data = get_jwt()
        refresh_jti = jwt_data.get('jti')

        if not refresh_jti:
            return jsonify({'error': 'Invalid refresh token'}), 401

        result = auth_service.refresh_access_token(refresh_jti)

        if result['success']:
            return jsonify({
                'success': True,
                'access_token': result['access_token']
            }), 200
        else:
            return jsonify({'error': result['error']}), 401

    except Exception:
        logger.error(
            "Refresh token operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (blacklist current tokens).

    POST /api/auth/logout
    Headers: Authorization: Bearer <access_token>
    Body: {
        "refresh_token": "refresh_token_to_revoke"
    }

    Returns:
        200: Logout successful
        400: Error logging out
    """
    try:
        # Get access token JTI
        jwt_data = get_jwt()
        access_jti = jwt_data.get('jti')

        data = request.get_json()
        if not data or 'refresh_token' not in data:
            return jsonify({'error': 'Refresh token required'}), 400

        # TODO: Extract refresh JTI from refresh token
        # For now, we'll need to decode it
        from flask_jwt_extended import decode_token
        refresh_data = decode_token(data['refresh_token'])
        refresh_jti = refresh_data.get('jti')

        result = auth_service.logout(
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Logout operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/logout-all', methods=['POST'])
@jwt_required()
def logout_all_devices():
    """
    Logout user from all devices (revoke all refresh tokens).

    POST /api/auth/logout-all
    Headers: Authorization: Bearer <access_token>

    Returns:
        200: Logged out from all devices
        400: Error logging out
    """
    try:
        # Get user info from JWT
        user_id = int(get_jwt_identity())
        jwt_data = get_jwt()
        user_type = jwt_data.get('user_type')

        result = auth_service.logout_all_devices(
            user_id=user_id,
            user_type=user_type
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400

    except Exception:
        logger.error(
            "Logout all devices operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_sessions():
    """
    Get list of active sessions for current user.

    GET /api/auth/sessions
    Headers: Authorization: Bearer <access_token>

    Returns:
        200: List of active sessions
    """
    try:
        from models import RefreshToken

        user_id = int(get_jwt_identity())
        jwt_data = get_jwt()
        user_type = jwt_data.get('user_type')

        # Get active refresh tokens
        sessions = RefreshToken.query.filter_by(
            user_id=user_id,
            user_type=user_type,
            revoked=False
        ).order_by(RefreshToken.last_used_at.desc()).all()

        return jsonify({
            'success': True,
            'sessions': [session.to_dict() for session in sessions]
        }), 200

    except Exception:
        logger.error(
            "Get user sessions operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def revoke_session(session_id):
    """
    Revoke specific session (logout from one device).

    DELETE /api/auth/sessions/:session_id
    Headers: Authorization: Bearer <access_token>

    Returns:
        200: Session revoked successfully
        404: Session not found
    """
    try:
        from models import RefreshToken, db

        user_id = int(get_jwt_identity())
        jwt_data = get_jwt()
        user_type = jwt_data.get('user_type')

        # Find and revoke session
        session = RefreshToken.query.filter_by(
            id=session_id,
            user_id=user_id,
            user_type=user_type
        ).first()

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        session.revoked = True
        session.revoked_reason = 'user_revoked'
        from datetime import datetime
        session.revoked_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Session revoked successfully'
        }), 200

    except Exception:
        logger.error(
            "Revoke session operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


# =====================================================
# PERMISSION & AUDIT ENDPOINTS (Admin/Manager only)
# =====================================================

@auth_bp.route('/permissions', methods=['GET'])
@jwt_required()
@manager_required
def get_all_permissions(current_employee):
    """
    Get all available permissions (Manager/Admin only).

    GET /api/auth/permissions
    Headers: Authorization: Bearer <access_token>

    Returns:
        200: List of all permissions
    """
    try:
        from models import Permission

        permissions = Permission.query.filter_by(is_active=True).all()

        # Group by category
        grouped = {}
        for perm in permissions:
            category = perm.category or 'other'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(perm.to_dict())

        return jsonify({
            'success': True,
            'permissions': [p.to_dict() for p in permissions],
            'grouped': grouped
        }), 200

    except Exception:
        logger.error(
            "Get permissions operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/audit-log', methods=['GET'])
@jwt_required()
@manager_required
def get_audit_log(current_employee):
    """
    Get authentication audit log (Manager/Admin only).

    GET /api/auth/audit-log?limit=100&offset=0&user_type=employee&success=true
    Headers: Authorization: Bearer <access_token>

    Returns:
        200: List of audit log entries
    """
    try:
        from models import AuthAuditLog

        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_type = request.args.get('user_type')
        success = request.args.get('success')

        # Build query
        query = AuthAuditLog.query

        if user_type:
            query = query.filter_by(user_type=user_type)

        if success is not None:
            query = query.filter_by(success=success.lower() == 'true')

        # Order by most recent first
        query = query.order_by(AuthAuditLog.created_at.desc())

        # Paginate
        total = query.count()
        logs = query.offset(offset).limit(limit).all()

        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception:
        logger.error(
            "Get audit log operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user info.

    GET /api/auth/me
    Headers: Authorization: Bearer <access_token>

    Returns:
        200: User info and permissions
    """
    try:
        from models import Customer, Employee

        user_id = int(get_jwt_identity())
        jwt_data = get_jwt()
        user_type = jwt_data.get('user_type')

        if user_type == 'customer':
            customer = Customer.query.get(user_id)
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404

            return jsonify({
                'success': True,
                'user_type': 'customer',
                'user': customer.to_dict()
            }), 200

        elif user_type == 'employee':
            employee = Employee.query.get(user_id)
            if not employee:
                return jsonify({'error': 'Employee not found'}), 404

            # Get permissions
            permissions = auth_service.get_employee_permissions(employee.id)

            return jsonify({
                'success': True,
                'user_type': 'employee',
                'user': {
                    'id': employee.id,
                    'email': employee.email,
                    'full_name': employee.full_name,
                    'role': employee.role,
                    'totp_enabled': employee.totp_enabled,
                    'pin_enabled': employee.pin_enabled
                },
                'permissions': permissions
            }), 200
        else:
            return jsonify({'error': 'Invalid user type'}), 400

    except Exception:
        logger.error(
            "Get current user operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


# Export blueprint
__all__ = ['auth_bp']
