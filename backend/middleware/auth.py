"""
Authentication and authorization middleware.
Provides decorators for protecting routes based on user type and role.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models import Customer, Employee


def customer_required(fn):
    """
    Decorator to require customer authentication.

    Usage:
        @api.route('/profile')
        @customer_required
        def get_profile(current_customer):
            return jsonify(current_customer.to_dict())
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        # Check if user type is customer
        if claims.get('user_type') != 'customer':
            return jsonify({'error': 'Customer authentication required'}), 403

        customer_id = get_jwt_identity()
        customer = Customer.query.get(customer_id)

        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        if not customer.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Pass customer to route handler
        return fn(current_customer=customer, *args, **kwargs)

    return wrapper


def employee_required(fn):
    """
    Decorator to require employee authentication.

    Usage:
        @api.route('/admin/dashboard')
        @employee_required
        def get_dashboard(current_employee):
            return jsonify({'employee': current_employee.full_name})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        # Check if user type is employee
        if claims.get('user_type') != 'employee':
            return jsonify({'error': 'Employee authentication required'}), 403

        employee_id = get_jwt_identity()
        employee = Employee.query.get(employee_id)

        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        if not employee.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Pass employee to route handler
        return fn(current_employee=employee, *args, **kwargs)

    return wrapper


def admin_required(fn):
    """
    Decorator to require admin role.

    Usage:
        @api.route('/admin/users')
        @admin_required
        def list_users(current_employee):
            return jsonify({'users': [...]})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        # Check if user type is employee
        if claims.get('user_type') != 'employee':
            return jsonify({'error': 'Employee authentication required'}), 403

        employee_id = get_jwt_identity()
        employee = Employee.query.get(employee_id)

        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        if not employee.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Check if employee has admin role
        if employee.role != 'admin':
            return jsonify({
                'error': 'Insufficient permissions',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'details': {'required_role': 'admin', 'current_role': employee.role}
            }), 403

        # Pass employee to route handler
        return fn(current_employee=employee, *args, **kwargs)

    return wrapper


def manager_required(fn):
    """
    Decorator to require manager or admin role.

    Usage:
        @api.route('/inventory/update')
        @manager_required
        def update_inventory(current_employee):
            return jsonify({'success': True})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        # Check if user type is employee
        if claims.get('user_type') != 'employee':
            return jsonify({'error': 'Employee authentication required'}), 403

        employee_id = get_jwt_identity()
        employee = Employee.query.get(employee_id)

        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        if not employee.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Check if employee has manager or admin role
        if employee.role not in ['admin', 'manager']:
            return jsonify({
                'error': 'Insufficient permissions',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'details': {'required_role': 'admin or manager', 'current_role': employee.role}
            }), 403

        # Pass employee to route handler
        return fn(current_employee=employee, *args, **kwargs)

    return wrapper


def packer_required(fn):
    """
    Decorator to require packer role (Phase 1 - Fulfillment).
    
    Usage:
        @api.route('/fulfillment/packing')
        @packer_required
        def get_packing_queue(current_employee):
            return jsonify({'orders': [...]})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        # Check if user type is employee
        if claims.get('user_type') != 'employee':
            return jsonify({'error': 'Employee authentication required'}), 403

        employee_id = get_jwt_identity()
        employee = Employee.query.get(employee_id)

        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        if not employee.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Check if employee has packer, manager, or admin role
        if employee.role not in ['packer', 'manager', 'admin']:
            return jsonify({
                'error': 'Insufficient permissions',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'details': {'required_role': 'packer, manager, or admin', 'current_role': employee.role}
            }), 403

        # Pass employee to route handler
        return fn(current_employee=employee, *args, **kwargs)

    return wrapper


def shipper_required(fn):
    """
    Decorator to require shipper role (Phase 1 - Fulfillment).
    
    Usage:
        @api.route('/fulfillment/shipping')
        @shipper_required
        def get_shipping_queue(current_employee):
            return jsonify({'orders': [...]})
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        # Check if user type is employee
        if claims.get('user_type') != 'employee':
            return jsonify({'error': 'Employee authentication required'}), 403

        employee_id = get_jwt_identity()
        employee = Employee.query.get(employee_id)

        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        if not employee.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Check if employee has shipper, manager, or admin role
        if employee.role not in ['shipper', 'manager', 'admin']:
            return jsonify({
                'error': 'Insufficient permissions',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'details': {'required_role': 'shipper, manager, or admin', 'current_role': employee.role}
            }), 403

        # Pass employee to route handler
        return fn(current_employee=employee, *args, **kwargs)

    return wrapper


def get_current_customer():
    """
    Helper function to get current customer from JWT.
    Returns None if not authenticated or not a customer.
    """
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()

        if claims.get('user_type') != 'customer':
            return None

        customer_id = get_jwt_identity()
        return Customer.query.get(customer_id)
    except Exception:
        return None


def get_current_employee():
    """
    Helper function to get current employee from JWT.
    Returns None if not authenticated or not an employee.
    """
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()

        if claims.get('user_type') != 'employee':
            return None

        employee_id = get_jwt_identity()
        return Employee.query.get(employee_id)
    except Exception:
        return None
