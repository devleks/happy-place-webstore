"""
Authentication routes for Happy Place Boutique API.
Handles customer and employee registration/login.
"""

from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
import hashlib

from routes import api
from models import db, Customer, Employee
from middleware import customer_required, employee_required
from logging_utils import get_logger, safe_auth_context
from services.encryption import encrypt_customer

# Initialize logger
logger = get_logger(__name__)


@api.route('/auth/customer/register', methods=['POST'])
def customer_register():
    """
    Register a new customer account.

    Required fields: email, password, first_name, last_name, gdpr_consent
    Optional fields: phone, marketing_consent
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name', 'gdpr_consent']
    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'code': 'VALIDATION_ERROR',
            'details': {'missing_fields': missing_fields}
        }), 400

    # Validate GDPR consent
    if not data.get('gdpr_consent'):
        return jsonify({
            'error': 'GDPR consent is required',
            'code': 'GDPR_CONSENT_REQUIRED'
        }), 400

    # Validate password length
    if len(data['password']) < 8:
        return jsonify({
            'error': 'Password must be at least 8 characters',
            'code': 'VALIDATION_ERROR'
        }), 400

    # Create new customer using stored procedure
    try:
        # Generate email hash and encrypt PII
        email_hash = hashlib.sha256(data['email'].lower().encode()).hexdigest()
        password_hash = generate_password_hash(data['password'])
        
        # Encrypt customer PII fields
        email_encrypted = encrypt_customer(data['email'])
        first_name_encrypted = encrypt_customer(data['first_name'])
        last_name_encrypted = encrypt_customer(data['last_name'])
        phone_encrypted = encrypt_customer(data.get('phone')) if data.get('phone') else None

        # Call stored procedure for atomic customer registration
        result = db.session.execute(
            db.text("""
                SELECT * FROM sp_register_customer_secure(
                    :email_hash,
                    :email_encrypted,
                    :password_hash,
                    :first_name_encrypted,
                    :last_name_encrypted,
                    :gdpr_consent,
                    :ip_address,
                    :user_agent,
                    :phone_encrypted,
                    :marketing_consent
                )
            """),
            {
                'email_hash': email_hash,
                'email_encrypted': email_encrypted,
                'password_hash': password_hash,
                'first_name_encrypted': first_name_encrypted,
                'last_name_encrypted': last_name_encrypted,
                'gdpr_consent': data['gdpr_consent'],
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'phone_encrypted': phone_encrypted,
                'marketing_consent': data.get('marketing_consent', False)
            }
        )

        # Fetch result
        row = result.fetchone()
        if not row:
            raise RuntimeError('Stored procedure did not return result')

        customer_id = row[0]
        registration_success = row[1]
        error_message = row[2]

        if not registration_success:
            return jsonify({
                'error': error_message or 'Registration failed',
                'code': 'REGISTRATION_ERROR'
            }), 400

        # Get the created customer for response
        customer = Customer.query.get(customer_id)
        if not customer:
            raise RuntimeError('Customer not found after registration')

        # Commit transaction
        db.session.commit()

        # Create access token
        access_token = create_access_token(
            identity=str(customer.id),
            additional_claims={'user_type': 'customer'},
            expires_delta=timedelta(days=30)
        )

        return jsonify({
            'message': 'Customer registered successfully',
            'access_token': access_token,
            'customer': {
                'id': customer.id,
                'email': customer.email,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone': customer.phone,
                'gdpr_consent': customer.gdpr_consent,
                'marketing_consent': customer.marketing_consent,
                'is_active': customer.is_active,
                'created_at': customer.created_at.isoformat() if customer.created_at else None
            }
        }), 201

    except Exception:
        db.session.rollback()
        logger.error(
            "Customer registration failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"email": data.get('email')}
            )},
            exc_info=True,
        )
        return jsonify({
            'error': 'Registration failed',
            'code': 'INTERNAL_ERROR'
        }), 500


@api.route('/auth/customer/login', methods=['POST'])
def customer_login():
    """
    Customer login endpoint.

    Required fields: email, password
    """
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    # Find customer by email hash
    email_hash = hashlib.sha256(data['email'].lower().encode()).hexdigest()
    customer = Customer.query.filter_by(email_hash=email_hash).first()

    if not customer or not check_password_hash(customer.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    if not customer.is_active:
        return jsonify({'error': 'Account is inactive'}), 403

    # Create access token
    access_token = create_access_token(
        identity=str(customer.id),
        additional_claims={'user_type': 'customer'},
        expires_delta=timedelta(days=30)
    )

    return jsonify({
        'access_token': access_token,
        'customer': {
            'id': customer.id,
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'is_active': customer.is_active
        }
    }), 200


@api.route('/auth/employee/login', methods=['POST'])
def employee_login():
    """
    Employee login endpoint.

    Required fields: email, password
    """
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    # Find employee by email (not encrypted)
    employee = Employee.query.filter_by(email=data['email'].lower()).first()

    if not employee or not check_password_hash(employee.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    if not employee.is_active:
        return jsonify({'error': 'Account is inactive'}), 403

    # Create access token
    access_token = create_access_token(
        identity=str(employee.id),
        additional_claims={'user_type': 'employee', 'role': employee.role},
        expires_delta=timedelta(hours=8)
    )

    return jsonify({
        'access_token': access_token,
        'employee': {
            'id': employee.id,
            'email': employee.email,
            'full_name': employee.full_name,
            'role': employee.role,
            'is_active': employee.is_active
        }
    }), 200


@api.route('/auth/customer/me', methods=['GET'])
@customer_required
def get_customer_profile(current_customer):
    """
    Get current customer profile.
    Requires customer authentication.
    """
    return jsonify({
        'id': current_customer.id,
        'email': current_customer.email,
        'first_name': current_customer.first_name,
        'last_name': current_customer.last_name,
        'phone': current_customer.phone,
        'gdpr_consent': current_customer.gdpr_consent,
        'marketing_consent': current_customer.marketing_consent,
        'is_active': current_customer.is_active,
        'email_verified': current_customer.email_verified,
        'created_at': current_customer.created_at.isoformat() if current_customer.created_at else None
    }), 200


@api.route('/auth/employee/me', methods=['GET'])
@employee_required
def get_employee_profile(current_employee):
    """
    Get current employee profile.
    Requires employee authentication.
    """
    return jsonify({
        'id': current_employee.id,
        'email': current_employee.email,
        'full_name': current_employee.full_name,
        'role': current_employee.role,
        'is_active': current_employee.is_active,
        'created_at': current_employee.created_at.isoformat() if current_employee.created_at else None
    }), 200
