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
    Get all orders that need packing (status: processing or packing).
    All paid orders automatically appear here - no manual assignment needed.
    
    GET /api/fulfillment/packing/queue?status=pending
    
    Returns:
        200: List of orders to pack
    """
    try:
        # Get all orders with status 'processing', 'packing', or recently 'packed'
        # Include packed orders so completed tab shows recent completions
        orders = Order.query.filter(
            Order.status.in_(['processing', 'packing', 'packed'])
        ).order_by(Order.created_at.asc()).all()
        
        result = []
        for order in orders:
            # Check if there's an assignment for tracking status
            assignment = OrderAssignment.query.filter_by(
                order_id=order.id,
                role='packer'
            ).first()
            
            # Determine the packing status
            if assignment:
                packing_status = assignment.status
                started_at = assignment.started_at.isoformat() if assignment.started_at else None
                assignment_id = assignment.id
            else:
                packing_status = 'pending'
                started_at = None
                assignment_id = None
            
            # Get customer name
            customer_name = "Unknown Customer"
            if order.customer:
                customer_name = f"{order.customer.first_name} {order.customer.last_name}"
            
            result.append({
                'assignment_id': assignment_id,
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_name': customer_name,
                'items_count': len(order.items) if order.items else 0,
                'total': float(order.total),
                'status': packing_status,
                'assigned_at': order.created_at.isoformat(),
                'started_at': started_at
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


@fulfillment_bp.route('/packing/<int:order_id>/start', methods=['POST'])
@jwt_required()
@packer_required
def start_packing(current_employee, order_id):
    """
    Start packing an order. Creates assignment if it doesn't exist.
    
    POST /api/fulfillment/packing/:order_id/start
    
    Returns:
        200: Packing started
        404: Order not found
    """
    try:
        employee_id = int(get_jwt_identity())
        
        # Get the order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check or create assignment
        assignment = OrderAssignment.query.filter_by(
            order_id=order_id,
            role='packer'
        ).first()
        
        if not assignment:
            # Create new assignment
            assignment = OrderAssignment(
                order_id=order_id,
                assigned_to=employee_id,
                assigned_by=employee_id,
                role='packer',
                status='in_progress',
                assigned_at=datetime.utcnow(),
                started_at=datetime.utcnow()
            )
            db.session.add(assignment)
        else:
            # Update existing assignment
            assignment.assigned_to = employee_id
            assignment.status = 'in_progress'
            assignment.started_at = datetime.utcnow()
        
        # Update order status
        order.status = 'packing'
        
        db.session.commit()
        
        logger.info(
            f"Packing started for order {order.order_number}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": employee_id, "order_id": order_id}
            )}
        )
        
        return jsonify({
            'message': 'Packing started',
            'assignment_id': assignment.id,
            'order_id': order_id,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to start packing: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


@fulfillment_bp.route('/packing/<int:assignment_id>/complete', methods=['POST'])
@jwt_required()
@packer_required
def complete_packing(current_employee, assignment_id):
    """
    Mark packing assignment as completed.
    Order automatically moves to shipping queue.
    
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
        
        # Update order status to 'packed' - will automatically appear in shipping queue
        order = Order.query.get(assignment.order_id)
        if order:
            order.status = 'packed'
        
        db.session.commit()
        
        logger.info(
            f"Packing completed for order {order.order_number}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()), "order_id": order.id}
            )}
        )
        
        return jsonify({
            'message': 'Packing completed - order moved to shipping queue',
            'assignment_id': assignment.id,
            'order_id': order.id,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to complete packing: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


# =====================================================
# SHIPPER ENDPOINTS
# =====================================================

@fulfillment_bp.route('/shipping/queue', methods=['GET'])
@jwt_required()
@shipper_required
def get_shipping_queue(current_employee):
    """
    Get all packed orders ready for shipping.
    Only orders with status 'packed' or 'shipping' appear here.
    
    GET /api/fulfillment/shipping/queue?status=pending
    
    Returns:
        200: List of orders to ship
    """
    try:
        # Get all orders with status 'packed' or 'shipping'
        # These are orders that have been packed and need to be shipped
        orders = Order.query.filter(
            Order.status.in_(['packed', 'shipping'])
        ).order_by(Order.created_at.asc()).all()
        
        result = []
        for order in orders:
            # Check if there's a shipping assignment for tracking status
            assignment = OrderAssignment.query.filter_by(
                order_id=order.id,
                role='shipper'
            ).first()
            
            # Determine the shipping status
            if assignment:
                shipping_status = assignment.status
                started_at = assignment.started_at.isoformat() if assignment.started_at else None
                assignment_id = assignment.id
            else:
                shipping_status = 'pending'
                started_at = None
                assignment_id = None
            
            # Get packer info
            packer_assignment = OrderAssignment.query.filter_by(
                order_id=order.id,
                role='packer'
            ).first()
            
            packer_name = None
            packed_at = None
            if packer_assignment:
                packer = Employee.query.get(packer_assignment.assigned_to)
                packer_name = packer.full_name if packer else None
                packed_at = packer_assignment.completed_at.isoformat() if packer_assignment.completed_at else None
            
            # Get customer name
            customer_name = "Unknown Customer"
            if order.customer:
                customer_name = f"{order.customer.first_name} {order.customer.last_name}"
            
            # Get shipping address (decrypt from encrypted field)
            shipping_address = None
            if order.shipping_address_encrypted:
                try:
                    import json
                    shipping_address = json.loads(order.shipping_address_encrypted)
                except:
                    shipping_address = None
            
            result.append({
                'assignment_id': assignment_id,
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_name': customer_name,
                'shipping_address': shipping_address,
                'items_count': len(order.items) if order.items else 0,
                'total': float(order.total),
                'tracking_number': order.tracking_number,
                'carrier': order.carrier,
                'status': shipping_status,
                'packed_by': packer_name,
                'packed_at': packed_at,
                'assigned_at': packed_at or order.created_at.isoformat(),
                'started_at': started_at
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


@fulfillment_bp.route('/shipping/<int:order_id>/start', methods=['POST'])
@jwt_required()
@shipper_required
def start_shipping(current_employee, order_id):
    """
    Start shipping an order. Creates assignment if it doesn't exist.
    
    POST /api/fulfillment/shipping/:order_id/start
    
    Returns:
        200: Shipping started
        404: Order not found
    """
    try:
        employee_id = int(get_jwt_identity())
        
        # Get the order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check or create assignment
        assignment = OrderAssignment.query.filter_by(
            order_id=order_id,
            role='shipper'
        ).first()
        
        if not assignment:
            # Create new assignment
            assignment = OrderAssignment(
                order_id=order_id,
                assigned_to=employee_id,
                assigned_by=employee_id,
                role='shipper',
                status='in_progress',
                assigned_at=datetime.utcnow(),
                started_at=datetime.utcnow()
            )
            db.session.add(assignment)
        else:
            # Update existing assignment
            assignment.assigned_to = employee_id
            assignment.status = 'in_progress'
            assignment.started_at = datetime.utcnow()
        
        # Update order status
        order.status = 'shipping'
        
        db.session.commit()
        
        logger.info(
            f"Shipping started for order {order.order_number}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": employee_id, "order_id": order_id}
            )}
        )
        
        return jsonify({
            'message': 'Shipping started',
            'assignment_id': assignment.id,
            'order_id': order_id,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to start shipping: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400


@fulfillment_bp.route('/shipping/<int:assignment_id>/complete', methods=['POST'])
@jwt_required()
@shipper_required
def complete_shipping(current_employee, assignment_id):
    """
    Mark shipping assignment as completed.
    Order status changes to 'shipped'.
    
    POST /api/fulfillment/shipping/:assignment_id/complete
    Body: {
        "tracking_number": "TRACK123456",
        "carrier": "DHL",
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
        
        # Update order with tracking info and mark as shipped
        order = Order.query.get(assignment.order_id)
        if order:
            order.status = 'shipped'
            order.tracking_number = data.get('tracking_number')
            order.carrier = data.get('carrier')
            order.shipped_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(
            f"Shipping completed for order {order.order_number}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()), "order_id": order.id}
            )}
        )
        
        return jsonify({
            'message': 'Shipping completed - order marked as shipped',
            'assignment_id': assignment.id,
            'order_id': order.id,
            'tracking_number': order.tracking_number,
            'status': assignment.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to complete shipping: {str(e)}", exc_info=True)
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
