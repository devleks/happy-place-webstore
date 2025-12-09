"""
Returns & Refunds API routes.
Handles return eligibility, return requests, and RMA workflow.

Business Rules:
- 2-day return window from delivery (regular-priced items only)
- 10% restocking fee on returns
- Clearance items: FINAL SALE (no returns, no exchanges)
- Sale items: FINAL SALE (no returns, no exchanges)
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from routes import api
from models import db, Order, OrderItem, Return, ReturnItem, Product, ProductVariant
from middleware import customer_required, manager_required
from logging_utils import get_logger, safe_auth_context
from flask_jwt_extended import get_jwt_identity

# Initialize logger
logger = get_logger(__name__)


@api.route('/orders/<int:order_id>/return-eligibility', methods=['GET'])
@customer_required
def check_return_eligibility(current_customer, order_id):
    """
    Check if an order is eligible for return.
    Requires customer authentication.
    """
    order = Order.query.get(order_id)

    if not order:
        return jsonify({
            'error': 'Order not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    # Verify order belongs to customer
    if order.customer_id != current_customer.id:
        return jsonify({
            'error': 'Unauthorized access to order',
            'code': 'INSUFFICIENT_PERMISSIONS'
        }), 403

    # Check if order has been delivered
    if not order.delivered_at:
        return jsonify({
            'order_id': order.id,
            'eligible': False,
            'reason': 'Order not yet delivered'
        }), 200

    # Check return window (2 days from delivery)
    return_deadline = order.delivered_at + timedelta(days=2)
    now = datetime.utcnow()
    within_window = now <= return_deadline

    if not within_window:
        days_since_deadline = (now - return_deadline).days
        return jsonify({
            'order_id': order.id,
            'eligible': False,
            'reason': 'Return window expired',
            'delivered_at': order.delivered_at.isoformat(),
            'return_deadline': return_deadline.isoformat(),
            'days_since_deadline': days_since_deadline
        }), 200

    # Check each item's return eligibility
    items_eligibility = []
    for order_item in order.items:
        product = order_item.product
        can_return, return_type, message = check_item_return_policy(product)

        items_eligibility.append({
            'order_item_id': order_item.id,
            'product_name': product.name,
            'variant': f"{order_item.variant.size} / {order_item.variant.color}" if order_item.variant else None,
            'quantity': order_item.quantity,
            'unit_price': float(order_item.price),
            'can_return': can_return,
            'return_type': return_type,
            'message': message
        })

    hours_remaining = int((return_deadline - now).total_seconds() / 3600)

    return jsonify({
        'order_id': order.id,
        'order_number': order.order_number,
        'delivered_at': order.delivered_at.isoformat(),
        'eligible': within_window,
        'return_deadline': return_deadline.isoformat(),
        'hours_remaining': hours_remaining,
        'items': items_eligibility
    }), 200


@api.route('/returns', methods=['POST'])
@customer_required
def create_return_request(current_customer):
    """
    Create a new return request.
    Requires customer authentication.
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ['order_id', 'reason', 'items', 'refund_method']
    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'code': 'VALIDATION_ERROR',
            'details': {'missing_fields': missing_fields}
        }), 400

    order = Order.query.get(data['order_id'])

    if not order:
        return jsonify({
            'error': 'Order not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    # Verify order belongs to customer
    if order.customer_id != current_customer.id:
        return jsonify({
            'error': 'Unauthorized access to order',
            'code': 'INSUFFICIENT_PERMISSIONS'
        }), 403

    # Check return window
    if not order.delivered_at:
        return jsonify({
            'error': 'Order not yet delivered',
            'code': 'BUSINESS_RULE_VIOLATION'
        }), 400

    return_deadline = order.delivered_at + timedelta(days=2)
    if datetime.utcnow() > return_deadline:
        return jsonify({
            'error': 'Return window expired (2 days from delivery)',
            'code': 'RETURN_WINDOW_EXPIRED'
        }), 400

    try:
        # Generate return number
        return_count = Return.query.count() + 1
        return_number = f"RMA-{datetime.utcnow().year}-{return_count:05d}"

        # Create return request
        return_request = Return(
            return_number=return_number,
            order_id=order.id,
            customer_id=current_customer.id,
            reason=data['reason'],
            reason_description=data.get('reason_description'),
            refund_method=data['refund_method'],
            status='pending'
        )
        db.session.add(return_request)
        db.session.flush()  # Get return ID

        # Add return items
        total_return_value = 0
        return_items_list = []

        for item_data in data['items']:
            order_item = OrderItem.query.get(item_data['order_item_id'])

            if not order_item or order_item.order_id != order.id:
                db.session.rollback()
                return jsonify({
                    'error': 'Invalid order item',
                    'code': 'VALIDATION_ERROR'
                }), 400

            # Check if item can be returned (not clearance/sale)
            product = order_item.product
            can_return, return_type, message = check_item_return_policy(product)

            if not can_return:
                db.session.rollback()
                return jsonify({
                    'error': message,
                    'code': 'BUSINESS_RULE_VIOLATION'
                }), 400

            item_value = order_item.price * item_data['quantity_returned']
            total_return_value += item_value

            return_item = ReturnItem(
                return_id=return_request.id,
                order_item_id=order_item.id,
                variant_id=order_item.variant_id,
                quantity_returned=item_data['quantity_returned'],
                item_value=item_value,
                condition=item_data.get('condition', 'new_with_tags')
            )
            db.session.add(return_item)

            return_items_list.append({
                'product_name': product.name,
                'variant': f"{order_item.variant.size} / {order_item.variant.color}" if order_item.variant else None,
                'quantity_returned': item_data['quantity_returned'],
                'item_value': float(item_value)
            })

        # Calculate restocking fee (10%)
        restocking_fee = total_return_value * 0.10
        refund_amount = total_return_value - restocking_fee

        return_request.restocking_fee = restocking_fee
        return_request.refund_amount = refund_amount

        db.session.commit()

        return jsonify({
            'return_id': return_request.id,
            'return_number': return_number,
            'order_id': order.id,
            'status': 'pending',
            'items': return_items_list,
            'totals': {
                'total_return_value': float(total_return_value),
                'restocking_fee': float(restocking_fee),
                'refund_amount': float(refund_amount)
            },
            'refund_method': data['refund_method'],
            'created_at': return_request.created_at.isoformat(),
            'instructions': 'Please ship items to: Happy Place Boutique, Store No. 22, 1st Floor, Bethel Business Centre, Langata Rd, Nairobi'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(
            "Create return request failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"customer_id": current_customer.id if current_customer else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'error': 'Failed to create return request',
            'code': 'INTERNAL_ERROR'
        }), 500


@api.route('/returns/<int:return_id>', methods=['GET'])
@customer_required
def get_return_status(current_customer, return_id):
    """
    Get return request status and details.
    Requires customer authentication.
    """
    return_request = Return.query.get(return_id)

    if not return_request:
        return jsonify({
            'error': 'Return request not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    # Verify return belongs to customer
    if return_request.customer_id != current_customer.id:
        return jsonify({
            'error': 'Unauthorized access to return',
            'code': 'INSUFFICIENT_PERMISSIONS'
        }), 403

    # Build timeline
    timeline = [
        {
            'status': 'pending',
            'timestamp': return_request.created_at.isoformat()
        }
    ]

    if return_request.approved_at:
        timeline.append({
            'status': 'approved',
            'timestamp': return_request.approved_at.isoformat()
        })

    if return_request.received_at:
        timeline.append({
            'status': 'received',
            'timestamp': return_request.received_at.isoformat()
        })

    if return_request.processed_at:
        timeline.append({
            'status': 'refunded',
            'timestamp': return_request.processed_at.isoformat()
        })

    return jsonify({
        'return_id': return_request.id,
        'return_number': return_request.return_number,
        'order_number': return_request.order.order_number,
        'status': return_request.status,
        'items': [
            {
                'product_name': item.variant.product.name if item.variant else 'Unknown',
                'variant': f"{item.variant.size} / {item.variant.color}" if item.variant else None,
                'quantity_returned': item.quantity_returned,
                'item_value': float(item.item_value),
                'condition': item.condition
            }
            for item in return_request.items
        ],
        'totals': {
            'total_return_value': float(sum(item.item_value for item in return_request.items)),
            'restocking_fee': float(return_request.restocking_fee or 0),
            'refund_amount': float(return_request.refund_amount or 0)
        },
        'refund_method': return_request.refund_method,
        'created_at': return_request.created_at.isoformat(),
        'approved_at': return_request.approved_at.isoformat() if return_request.approved_at else None,
        'timeline': timeline
    }), 200


@api.route('/returns/<int:return_id>/status', methods=['PATCH'])
@manager_required
def update_return_status(current_employee, return_id):
    """
    Update return request status (admin only).
    Requires manager or admin role.
    """
    return_request = Return.query.get(return_id)

    if not return_request:
        return jsonify({
            'error': 'Return request not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    data = request.get_json()
    new_status = data.get('status')

    valid_statuses = ['pending', 'approved', 'received', 'refunded', 'rejected', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({
            'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
            'code': 'VALIDATION_ERROR'
        }), 400

    try:
        return_request.status = new_status

        # Update timestamps based on status
        if new_status == 'approved':
            return_request.approved_by = current_employee.id
            return_request.approved_at = datetime.utcnow()
        elif new_status == 'received':
            return_request.received_at = datetime.utcnow()
        elif new_status == 'refunded':
            return_request.processed_by = current_employee.id
            return_request.processed_at = datetime.utcnow()

        if data.get('notes'):
            return_request.notes = data['notes']

        db.session.commit()

        return jsonify({
            'return_id': return_request.id,
            'status': return_request.status,
            'updated_at': datetime.utcnow().isoformat(),
            'message': 'Return status updated successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(
            "Update return status failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": current_employee.id if current_employee else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'error': 'Failed to update return status',
            'code': 'INTERNAL_ERROR'
        }), 500


# Helper function

def check_item_return_policy(product):
    """
    Check if a product can be returned based on business rules.

    Returns:
        tuple: (can_return: bool, return_type: str, message: str)
    """
    # Clearance items: FINAL SALE
    if hasattr(product, 'is_clearance') and product.is_clearance:
        return False, 'final_sale', 'Clearance items are FINAL SALE - no returns or exchanges allowed'

    # Sale items: FINAL SALE
    if product.sale_price and product.sale_price < product.price:
        return False, 'final_sale', 'Sale items are FINAL SALE - no returns or exchanges allowed'

    # Regular items: returns allowed with restocking fee
    return True, 'refund', 'Full refund available (minus 10% restocking fee)'
