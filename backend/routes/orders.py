"""
Order Routes
Endpoints for order creation, retrieval, and management.
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from routes import api
from models import db, Order, Cart, CartItem, Customer
from services.order_service import OrderService
from services.shipping_service import ShippingService
from logging_utils import get_logger, safe_auth_context


# =====================================================
# Helper Functions & Logger
# =====================================================

logger = get_logger(__name__)

def validate_shipping_address(address: dict) -> tuple:
    """
    Validate shipping address fields.

    Returns:
        (is_valid: bool, error_message: str or None)
    """
    required_fields = ['street', 'city', 'state', 'zip', 'phone']

    for field in required_fields:
        if field not in address or not address[field]:
            return False, f'Missing required field: {field}'

    # Validate phone format (basic)
    phone = address['phone']
    if not phone.startswith('+254') and not phone.startswith('0'):
        return False, 'Phone must start with +254 or 0'

    return True, None


def get_customer_cart(customer_id: int) -> Cart:
    """Get customer's cart or raise error"""
    cart = Cart.query.filter_by(customer_id=customer_id).first()
    if not cart:
        raise ValueError('Cart not found')
    return cart


# =====================================================
# Order Routes
# =====================================================

@api.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create new order from cart.
    NOTE: M-Pesa payment is not yet implemented (Phase 2).

    POST /api/orders
    Body: {
        "shipping_address": {
            "street": "123 Main St",
            "city": "Nairobi",
            "state": "Nairobi County",
            "zip": "00100",
            "phone": "+254712345678"
        },
        "billing_address": {...},  // Optional
        "payment_method": "cod" | "mpesa"  // Default: cod
    }

    Returns:
        201: Order created successfully
        400: Validation error
        501: M-Pesa not implemented
        500: Server error
    """
    try:
        # Get authenticated customer
        customer_id = int(get_jwt_identity())
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        # Get payment method (default to COD)
        payment_method = data.get('payment_method', 'cod')
        
        # Validate payment method
        if payment_method not in ['cod', 'mpesa']:
            return jsonify({'error': 'Invalid payment method. Must be "cod" or "mpesa"'}), 400
        
        # TEMPORARY: Reject M-Pesa until Phase 2 implementation
        if payment_method == 'mpesa':
            logger.info(
                f"M-Pesa payment attempt blocked - Customer: {customer_id}, "
                f"IP: {request.remote_addr}",
                extra={"context": safe_auth_context(
                    user_type='customer',
                    ip=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    extra={"customer_id": customer_id, "payment_method": "mpesa"}
                )}
            )
            return jsonify({
                'error': 'M-Pesa payment coming soon',
                'message': 'M-Pesa integration will be available in the next release. Please use Cash on Delivery (cod) for now.',
                'status': 'not_implemented',
                'available_methods': ['cod'],
                'documentation': '/api/docs#payment-methods'
            }), 501  # 501 Not Implemented

        # Validate shipping address
        shipping_address = data.get('shipping_address')
        if not shipping_address:
            return jsonify({'error': 'Shipping address required'}), 400

        is_valid, error_msg = validate_shipping_address(shipping_address)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Get billing address (optional, defaults to shipping)
        billing_address = data.get('billing_address')
        if billing_address:
            is_valid, error_msg = validate_shipping_address(billing_address)
            if not is_valid:
                return jsonify({'error': f'Billing address: {error_msg}'}), 400

        # Get customer's cart
        cart = get_customer_cart(customer_id)
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()

        if not cart_items or len(cart_items) == 0:
            return jsonify({'error': 'Cart is empty'}), 400

        # Get client info for audit
        ip_address = request.remote_addr or '0.0.0.0'
        user_agent = request.headers.get('User-Agent', 'Unknown')

        # Create order using service
        result = OrderService.create_order(
            customer_id=customer_id,
            shipping_address=shipping_address,
            billing_address=billing_address,
            cart_items=cart_items,
            payment_method=payment_method,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if result['success']:
            # Get created order
            order = Order.query.get(result['order_id'])
            if not order:
                return jsonify({'error': 'Order created but not found'}), 500

            return jsonify({
                'message': 'Order created successfully',
                'order': order.to_dict(include_items=True)
            }), 201
        else:
            return jsonify({
                'error': result.get('error', 'Order creation failed')
            }), 400

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/orders', methods=['GET'])
@jwt_required()
def get_customer_orders():
    """
    Get all orders for authenticated customer.

    GET /api/orders?page=1&per_page=10

    Returns:
        200: List of orders
        404: Customer not found
    """
    try:
        # Get authenticated customer
        customer_id = int(get_jwt_identity())
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10

        # Get orders
        result = OrderService.get_customer_orders(
            customer_id=customer_id,
            page=page,
            per_page=per_page
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(
            "Get customer orders failed",
            extra={"context": safe_auth_context(user_type='customer',
                                                 ip=request.remote_addr,
                                                 user_agent=request.headers.get('User-Agent'))},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    """
    Get order details by ID.

    GET /api/orders/:order_id

    Returns:
        200: Order details
        404: Order not found
        403: Unauthorized access
    """
    try:
        # Get authenticated customer
        customer_id = int(get_jwt_identity())
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        # Get order (with customer_id check for authorization)
        order = OrderService.get_order(order_id, customer_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        return jsonify({
            'order': order.to_dict(include_items=True)
        }), 200

    except Exception as e:
        logger.error(
            "Get order details failed",
            extra={"context": safe_auth_context(user_type='customer',
                                                 ip=request.remote_addr,
                                                 user_agent=request.headers.get('User-Agent'))},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/orders/number/<string:order_number>', methods=['GET'])
@jwt_required()
def get_order_by_number(order_number):
    """
    Get order details by order number.

    GET /api/orders/number/:order_number

    Returns:
        200: Order details
        404: Order not found
    """
    try:
        # Get authenticated customer
        customer_id = int(get_jwt_identity())
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        # Get order by number
        order = OrderService.get_order_by_number(order_number, customer_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        return jsonify({
            'order': order.to_dict(include_items=True)
        }), 200

    except Exception as e:
        logger.error(
            "Get order by number failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"customer_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/orders/shipping-preview', methods=['POST'])
def preview_shipping():
    """
    Preview shipping cost before checkout.

    POST /api/orders/shipping-preview
    Body: {
        "city": "Nairobi"
    }

    Returns:
        200: Shipping calculation
        400: Validation error
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        city = data.get('city')
        if not city:
            return jsonify({'error': 'City required'}), 400

        # Check if user is authenticated
        try:
            customer_id = int(get_jwt_identity())
            customer = Customer.query.get(customer_id)
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404

            # Get customer's cart
            cart = get_customer_cart(customer_id)
            cart_items = CartItem.query.filter_by(cart_id=cart.id).all()

            if not cart_items or len(cart_items) == 0:
                return jsonify({'error': 'Cart is empty'}), 400

            # Calculate shipping with cart items
            result = OrderService.calculate_shipping_preview(cart_items, city)
        except (RuntimeError, TypeError, AttributeError, ValueError):
            # Unauthenticated user - calculate basic shipping without cart
            result = {
                'is_nairobi': city.lower() in ['nairobi', 'nairobi county'],
                'shipping_cost': 0 if city.lower() in ['nairobi', 'nairobi county'] else 300,
                'estimated_days_min': 1 if city.lower() in ['nairobi', 'nairobi county'] else 2,
                'estimated_days_max': 2 if city.lower() in ['nairobi', 'nairobi county'] else 5,
                'message': 'Basic shipping estimate - login for accurate calculation'
            }

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(
            "Shipping preview failed",
            extra={"context": safe_auth_context(user_type='customer',
                                                 ip=request.remote_addr,
                                                 user_agent=request.headers.get('User-Agent'))},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500
