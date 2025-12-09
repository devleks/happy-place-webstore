"""
Fulfillment API Routes (Phase 1, Task 1.2.3)

Endpoints for order fulfillment workflow:
- Order assignment to packers/shippers
- Fulfillment queue management
- Status updates for packing/shipping

All endpoints require employee authentication with appropriate roles.
"""

from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models import db
from models.database_models import Order, OrderAssignment, Employee
from middleware import manager_required, packer_required, shipper_required
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)

# Create blueprint
fulfillment_bp = Blueprint('fulfillment', __name__, url_prefix='/api/fulfillment')


# =====================================================
# ORDER ASSIGNMENT ENDPOINTS (Manager/Admin)
# =====================================================

@fulfillment_bp.route('/assign', methods=['POST'])
@jwt_required()
@manager_required
def assign_order(current_employee):
    """
    Assign an order to a packer or shipper.
    
    POST /api/fulfillment/assign
    Body: {
        "order_id": 123,
        "employee_id": 21,
        "role": "packer"  // or "shipper"
    }
    
    Returns:
        201: Assignment created
        400: Validation error
        404: Order or employee not found
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['order_id', 'employee_id', 'role']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate role
        if data['role'] not in ['packer', 'shipper']:
            return jsonify({'error': 'Role must be either "packer" or "shipper"'}), 400
        
        # Get order
        order = Order.query.get(data['order_id'])
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get employee
        employee = Employee.query.get(data['employee_id'])
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Verify employee has the correct role
        if employee.role not in [data['role'], 'manager', 'admin']:
            return jsonify({
                'error': f'Employee does not have {data["role"]} role',
                'employee_role': employee.role
            }), 400
        
        # Check if assignment already exists
        existing = OrderAssignment.query.filter_by(
            order_id=data['order_id'],
            role=data['role']
        ).first()
        
        if existing:
            # Update existing assignment
            existing.assigned_to = data['employee_id']
            existing.assigned_by = int(get_jwt_identity())
            existing.assigned_at = datetime.utcnow()
            existing.status = 'pending'
            existing.notes = data.get('notes', '')
            assignment = existing
        else:
            # Create new assignment
            assignment = OrderAssignment(
                order_id=data['order_id'],
                assigned_to=data['employee_id'],
                assigned_by=int(get_jwt_identity()),
                role=data['role'],
                status='pending',
                notes=data.get('notes', '')
            )
            db.session.add(assignment)
        
        db.session.commit()
        
        logger.info(
            f"Order {data['order_id']} assigned to {employee.full_name} as {data['role']}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()), "order_id": data['order_id']}
            )}
        )
        
        return jsonify({
            'message': 'Order assigned successfully',
            'assignment': {
                'id': assignment.id,
                'order_id': assignment.order_id,
                'assigned_to': employee.full_name,
                'role': assignment.role,
                'status': assignment.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to assign order",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True
        )
        return jsonify({'error': str(e)}), 400


# =====================================================
# PACKER ENDPOINTS
# =====================================================

@fulfillment_bp.route('/packing/queue', methods=['GET'])
@jwt_required()
@packer_required
def get_packing_queue(current_employee):
    """
    Get orders assigned to current packer or all pending packing orders.
    
    GET /api/fulfillment/packing/queue?status=pending
    
    Returns:
        200: List of orders to pack
    """
    try:
        employee_id = int(get_jwt_identity())
        status = request.args.get('status', 'pending')
        
        # Get assignments for this packer
        query = OrderAssignment.query.filter_by(role='packer')
        
        # Filter by status if provided
        if status != 'all':
            query = query.filter_by(status=status)
        
        # If not admin/manager, only show assigned to this employee
        if current_employee.role not in ['admin', 'manager']:
            query = query.filter_by(assigned_to=employee_id)
        
        assignments = query.order_by(OrderAssignment.assigned_at.desc()).all()
        
        # Get order details
        result = []
        for assignment in assignments:
            order = Order.query.get(assignment.order_id)
            if order:
                result.append({
                    'assignment_id': assignment.id,
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer_name,
                    'items_count': len(order.items) if order.items else 0,
                    'status': assignment.status,
                    'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                    'started_at': assignment.started_at.isoformat() if assignment.started_at else None
                })
        
        return jsonify({'orders': result}), 200
        
    except Exception as e:
        logger.error(
            "Failed to get packing queue",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True
        )
        return jsonify({'error': str(e)}), 400


@fulfillment_bp.route('/packing/<int:assignment_id>/start', methods=['POST'])
@jwt_required()
@packer_required
def start_packing(current_employee, assignment_id):
    """
    Mark packing assignment as started.
    
    POST /api/fulfillment/packing/:assignment_id/start
    
    Returns:
        200: Assignment started
        404: Assignment not found
    """
    try:
        assignment = OrderAssignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        if assignment.role != 'packer':
            return jsonify({'error': 'Not a packing assignment'}), 400
        
        assignment.status = 'in_progress'
        assignment.started_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Packing started',
            'assignment_id': assignment.id,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@fulfillment_bp.route('/packing/<int:assignment_id>/complete', methods=['POST'])
@jwt_required()
@packer_required
def complete_packing(current_employee, assignment_id):
    """
    Mark packing assignment as completed.
    
    POST /api/fulfillment/packing/:assignment_id/complete
    Body: {
        "notes": "Packed and ready for shipping"
    }
    
    Returns:
        200: Packing completed
        404: Assignment not found
    """
    try:
        data = request.get_json() or {}
        
        assignment = OrderAssignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        if assignment.role != 'packer':
            return jsonify({'error': 'Not a packing assignment'}), 400
        
        assignment.status = 'completed'
        assignment.completed_at = datetime.utcnow()
        assignment.notes = data.get('notes', assignment.notes)
        
        # Update order status to ready for shipping
        order = Order.query.get(assignment.order_id)
        if order and order.status == 'processing':
            order.status = 'ready_to_ship'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Packing completed',
            'assignment_id': assignment.id,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# =====================================================
# SHIPPER ENDPOINTS
# =====================================================

@fulfillment_bp.route('/shipping/queue', methods=['GET'])
@jwt_required()
@shipper_required
def get_shipping_queue(current_employee):
    """
    Get orders assigned to current shipper or all pending shipping orders.
    
    GET /api/fulfillment/shipping/queue?status=pending
    
    Returns:
        200: List of orders to ship
    """
    try:
        employee_id = int(get_jwt_identity())
        status = request.args.get('status', 'pending')
        
        # Get assignments for shippers
        query = OrderAssignment.query.filter_by(role='shipper')
        
        # Filter by status if provided
        if status != 'all':
            query = query.filter_by(status=status)
        
        # If not admin/manager, only show assigned to this employee
        if current_employee.role not in ['admin', 'manager']:
            query = query.filter_by(assigned_to=employee_id)
        
        assignments = query.order_by(OrderAssignment.assigned_at.desc()).all()
        
        # Get order details
        result = []
        for assignment in assignments:
            order = Order.query.get(assignment.order_id)
            if order:
                result.append({
                    'assignment_id': assignment.id,
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer_name,
                    'shipping_address': order.shipping_address,
                    'tracking_number': order.tracking_number,
                    'carrier': order.carrier,
                    'status': assignment.status,
                    'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                    'started_at': assignment.started_at.isoformat() if assignment.started_at else None
                })
        
        return jsonify({'orders': result}), 200
        
    except Exception as e:
        logger.error(
            "Failed to get shipping queue",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True
        )
        return jsonify({'error': str(e)}), 400


@fulfillment_bp.route('/shipping/<int:assignment_id>/start', methods=['POST'])
@jwt_required()
@shipper_required
def start_shipping(current_employee, assignment_id):
    """
    Mark shipping assignment as started.
    
    POST /api/fulfillment/shipping/:assignment_id/start
    
    Returns:
        200: Shipping started
        404: Assignment not found
    """
    try:
        assignment = OrderAssignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        if assignment.role != 'shipper':
            return jsonify({'error': 'Not a shipping assignment'}), 400
        
        assignment.status = 'in_progress'
        assignment.started_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Shipping started',
            'assignment_id': assignment.id,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@fulfillment_bp.route('/shipping/<int:assignment_id>/complete', methods=['POST'])
@jwt_required()
@shipper_required
def complete_shipping(current_employee, assignment_id):
    """
    Mark shipping assignment as completed.
    
    POST /api/fulfillment/shipping/:assignment_id/complete
    Body: {
        "notes": "Handed to DHL courier"
    }
    
    Returns:
        200: Shipping completed
        404: Assignment not found
    """
    try:
        data = request.get_json() or {}
        
        assignment = OrderAssignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        if assignment.role != 'shipper':
            return jsonify({'error': 'Not a shipping assignment'}), 400
        
        assignment.status = 'completed'
        assignment.completed_at = datetime.utcnow()
        assignment.notes = data.get('notes', assignment.notes)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Shipping completed',
            'assignment_id': assignment.id,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# =====================================================
# ASSIGNMENT MANAGEMENT
# =====================================================

@fulfillment_bp.route('/assignments/<int:order_id>', methods=['GET'])
@jwt_required()
@manager_required
def get_order_assignments(current_employee, order_id):
    """
    Get all assignments for an order.
    
    GET /api/fulfillment/assignments/:order_id
    
    Returns:
        200: List of assignments
    """
    try:
        assignments = OrderAssignment.query.filter_by(order_id=order_id).all()
        
        result = []
        for assignment in assignments:
            employee = Employee.query.get(assignment.assigned_to) if assignment.assigned_to else None
            assigned_by = Employee.query.get(assignment.assigned_by) if assignment.assigned_by else None
            
            result.append({
                'id': assignment.id,
                'role': assignment.role,
                'status': assignment.status,
                'assigned_to': employee.full_name if employee else None,
                'assigned_by': assigned_by.full_name if assigned_by else None,
                'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                'started_at': assignment.started_at.isoformat() if assignment.started_at else None,
                'completed_at': assignment.completed_at.isoformat() if assignment.completed_at else None,
                'notes': assignment.notes
            })
        
        return jsonify({'assignments': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
