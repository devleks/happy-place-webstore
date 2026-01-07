"""
Promotions API routes.
Handles promotion code validation and application to orders.
"""

from flask import request, jsonify
from datetime import datetime
from routes import api
from models import db, Promotion, OrderPromotion, Order
from middleware import customer_required
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)


@api.route('/promotions/validate', methods=['POST'])
def validate_promotion():
    """
    Validate a promotion code.
    Public endpoint for checking if a code is valid before checkout.
    """
    data = request.get_json()

    if not data.get('code'):
        return jsonify({
            'error': 'Promotion code is required',
            'code': 'VALIDATION_ERROR'
        }), 400

    promo = Promotion.query.filter_by(code=data['code'].upper()).first()

    if not promo:
        return jsonify({
            'valid': False,
            'error': 'Promotion code not found or expired',
            'code': 'PROMOTION_INVALID'
        }), 400

    # Check active status
    if not promo.is_active:
        return jsonify({
            'valid': False,
            'error': 'Promotion is not active',
            'code': 'PROMOTION_INVALID'
        }), 400

    # Check dates
    now = datetime.utcnow()
    if now < promo.start_date:
        return jsonify({
            'valid': False,
            'error': 'Promotion has not started yet',
            'code': 'PROMOTION_INVALID'
        }), 400

    if promo.end_date and now > promo.end_date:
        return jsonify({
            'valid': False,
            'error': 'Promotion has expired',
            'code': 'PROMOTION_INVALID'
        }), 400

    # Check usage limit
    if promo.usage_limit and promo.total_usage >= promo.usage_limit:
        return jsonify({
            'valid': False,
            'error': 'Promotion usage limit reached',
            'code': 'PROMOTION_INVALID'
        }), 400

    # Check customer usage (if customer_id provided)
    customer_id = data.get('customer_id')
    if customer_id and promo.usage_per_customer:
        customer_uses = OrderPromotion.query.filter_by(
            promotion_id=promo.id,
            customer_id=customer_id
        ).count()

        if customer_uses >= promo.usage_per_customer:
            return jsonify({
                'valid': False,
                'error': 'You have already used this promotion code',
                'code': 'PROMOTION_INVALID'
            }), 400

    # Check minimum order amount
    order_total = data.get('order_total', 0)
    if promo.minimum_order_amount and order_total < promo.minimum_order_amount:
        return jsonify({
            'valid': False,
            'error': f'Minimum order amount of KSh {promo.minimum_order_amount} required',
            'code': 'PROMOTION_INVALID',
            'minimum_required': float(promo.minimum_order_amount),
            'current_total': float(order_total)
        }), 400

    # Calculate discount
    discount_amount = calculate_discount(promo, order_total)
    final_total = max(0, order_total - discount_amount)

    return jsonify({
        'valid': True,
        'promotion': {
            'id': promo.id,
            'code': promo.code,
            'name': promo.name,
            'description': promo.description,
            'discount_type': promo.discount_type,
            'discount_value': float(promo.discount_value),
            'applies_to': promo.applies_to,
            'minimum_order_amount': float(promo.minimum_order_amount) if promo.minimum_order_amount else None,
            'maximum_discount_amount': float(promo.maximum_discount_amount) if promo.maximum_discount_amount else None
        },
        'discount_amount': float(discount_amount),
        'final_total': float(final_total),
        'message': 'Promotion applied successfully'
    }), 200


@api.route('/orders/<int:order_id>/promotions', methods=['POST'])
@customer_required
def apply_promotion_to_order(current_customer, order_id):
    """
    Apply a promotion code to an order.
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

    # Check if order already has a promotion
    existing_promo = OrderPromotion.query.filter_by(order_id=order_id).first()
    if existing_promo:
        return jsonify({
            'error': 'Order already has a promotion applied',
            'code': 'BUSINESS_RULE_VIOLATION'
        }), 400

    data = request.get_json()
    promo_code = data.get('promotion_code')

    if not promo_code:
        return jsonify({
            'error': 'Promotion code is required',
            'code': 'VALIDATION_ERROR'
        }), 400

    promo = Promotion.query.filter_by(code=promo_code.upper()).first()

    if not promo or not promo.is_active:
        return jsonify({
            'error': 'Invalid promotion code',
            'code': 'PROMOTION_INVALID'
        }), 400

    # Validate promotion (reuse validation logic)
    validation = validate_promotion_for_order(promo, current_customer.id, order.subtotal)
    if not validation['valid']:
        return jsonify({
            'error': validation['error'],
            'code': 'PROMOTION_INVALID'
        }), 400

    # Calculate discount
    discount_amount = calculate_discount(promo, order.subtotal)

    try:
        # Create order promotion record
        order_promo = OrderPromotion(
            order_id=order_id,
            promotion_id=promo.id,
            customer_id=current_customer.id,
            discount_amount=discount_amount
        )
        db.session.add(order_promo)

        # Update promotion usage
        promo.total_usage = (promo.total_usage or 0) + 1

        # Recalculate order total
        order.total = order.subtotal - discount_amount + (order.shipping_cost or 0)

        db.session.commit()

        return jsonify({
            'order_id': order.id,
            'promotion_applied': {
                'code': promo.code,
                'discount_amount': float(discount_amount)
            },
            'order_totals': {
                'subtotal': float(order.subtotal),
                'promotion_discount': float(discount_amount),
                'shipping_cost': float(order.shipping_cost or 0),
                'tax': float(order.tax or 0),
                'total': float(order.total)
            }
        }), 200

    except Exception:
        db.session.rollback()
        logger.error(
            "Apply promotion operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"customer_id": current_customer.id if current_customer else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'error': 'Failed to apply promotion',
            'code': 'INTERNAL_ERROR'
        }), 500


@api.route('/promotions/active', methods=['GET'])
def get_active_promotions():
    """
    Get all active promotions.
    Public endpoint.
    """
    now = datetime.utcnow()

    promotions = Promotion.query.filter(
        Promotion.is_active.is_(True),
        Promotion.start_date <= now,
        (Promotion.end_date.is_(None)) | (Promotion.end_date >= now)
    ).all()

    return jsonify({
        'promotions': [
            {
                'code': promo.code,
                'name': promo.name,
                'description': promo.description,
                'discount_type': promo.discount_type,
                'discount_value': float(promo.discount_value),
                'minimum_order_amount': float(promo.minimum_order_amount) if promo.minimum_order_amount else None,
                'maximum_discount_amount': float(promo.maximum_discount_amount) if promo.maximum_discount_amount else None,
                'end_date': promo.end_date.isoformat() if promo.end_date else None
            }
            for promo in promotions
        ]
    }), 200


# Helper functions

def calculate_discount(promo, order_total):
    """Calculate discount amount based on promotion type."""
    discount = 0

    if promo.discount_type == 'percentage':
        discount = order_total * (promo.discount_value / 100)
    elif promo.discount_type == 'fixed_amount':
        discount = promo.discount_value
    elif promo.discount_type == 'free_shipping':
        return 0  # Handled separately in shipping calculation

    # Apply maximum discount cap
    if promo.maximum_discount_amount:
        discount = min(discount, promo.maximum_discount_amount)

    return discount


def validate_promotion_for_order(promo, customer_id, order_total):
    """Validate promotion for a specific order."""
    now = datetime.utcnow()

    # Check dates
    if now < promo.start_date:
        return {'valid': False, 'error': 'Promotion has not started yet'}

    if promo.end_date and now > promo.end_date:
        return {'valid': False, 'error': 'Promotion has expired'}

    # Check usage limit
    if promo.usage_limit and promo.total_usage >= promo.usage_limit:
        return {'valid': False, 'error': 'Promotion usage limit reached'}

    # Check customer usage
    if promo.usage_per_customer:
        customer_uses = OrderPromotion.query.filter_by(
            promotion_id=promo.id,
            customer_id=customer_id
        ).count()

        if customer_uses >= promo.usage_per_customer:
            return {'valid': False, 'error': 'You have already used this promotion'}

    # Check minimum order
    if promo.minimum_order_amount and order_total < promo.minimum_order_amount:
        return {'valid': False, 'error': f'Minimum order of KSh {promo.minimum_order_amount} required'}

    return {'valid': True}
