"""
Cart API routes for Happy Place Boutique.

Endpoints:
- GET /api/cart - Get customer's cart
- POST /api/cart/items - Add item to cart
- PUT /api/cart/items/<item_id> - Update cart item quantity
- DELETE /api/cart/items/<item_id> - Remove item from cart
- DELETE /api/cart - Clear entire cart
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Cart, CartItem, Customer, ProductVariant, Inventory
from . import api
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)

# Configuration constants
# Business rule: Maximum 99 units per cart item to prevent:
# 1. Inventory hoarding by single customer
# 2. DoS attacks via excessive quantities
# 3. Unrealistic bulk orders (use wholesale portal instead)
MAX_CART_QUANTITY = 99


def validate_cart_quantity(quantity, variant_id, current_cart_quantity=0):
    """
    Validate cart quantity against business rules.
    
    Args:
        quantity: TOTAL desired quantity (not delta)
        variant_id: Product variant ID
        current_cart_quantity: Current quantity already in cart (for updates)
        
    Returns:
        (is_valid: bool, error_response: dict or None, status_code: int)
    """
    # Check minimum quantity
    if quantity < 1:
        return False, {'error': 'Quantity must be at least 1'}, 400
    
    # Check maximum quantity
    if quantity > MAX_CART_QUANTITY:
        return False, {
            'error': f'Quantity cannot exceed {MAX_CART_QUANTITY}',
            'max_allowed': MAX_CART_QUANTITY
        }, 400
    
    # Check inventory availability
    inventory = Inventory.query.filter_by(variant_id=variant_id).first()
    if not inventory:
        return False, {'error': 'Product variant not found in inventory'}, 404
    
    # Calculate truly available quantity (total - reserved)
    # For updates: we're replacing current_cart_quantity, so add it back to available pool
    # For new adds: current_cart_quantity is 0, so this is just available stock
    available = (inventory.quantity - inventory.reserved_quantity) + current_cart_quantity
    
    if quantity > available:
        return False, {
            'error': f'Only {available} units available',
            'available_quantity': available,
            'requested': quantity
        }, 400
    
    return True, None, 200


@api.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    """Get customer's cart with all items"""
    try:
        customer_id = int(get_jwt_identity())

        # Get or create cart
        cart = Cart.query.filter_by(customer_id=customer_id).first()
        if not cart:
            cart = Cart(customer_id=customer_id)
            db.session.add(cart)
            db.session.commit()

        # Calculate cart totals
        cart_data = cart.to_dict()
        subtotal = 0

        for item in cart_data['items']:
            if item['variant'] and item['variant']['product']:
                product = item['variant']['product']
                # Use sale_price if available, otherwise use regular price
                sale_price = product.get('sale_price')
                regular_price = product.get('price', 0)
                price = float(sale_price if sale_price is not None else regular_price)
                quantity = item['quantity']
                subtotal += price * quantity

        cart_data['subtotal'] = subtotal

        return jsonify(cart_data), 200

    except Exception as e:
        logger.error(
            "Cart operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"customer_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/cart/items', methods=['POST'])
@jwt_required()
def add_to_cart():
    """
    Add item to cart with comprehensive validation.

    Request body:
    {
        "variant_id": 123,
        "quantity": 2
    }
    """
    try:
        customer_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'variant_id' not in data:
            return jsonify({'error': 'variant_id is required'}), 400

        variant_id = data['variant_id']
        quantity = data.get('quantity', 1)

        # Check if variant exists
        variant = ProductVariant.query.get(variant_id)
        if not variant:
            return jsonify({'error': 'Product variant not found'}), 404

        # Get or create cart
        cart = Cart.query.filter_by(customer_id=customer_id).first()
        if not cart:
            cart = Cart(customer_id=customer_id)
            db.session.add(cart)
            db.session.flush()

        # Check if item already in cart
        cart_item = CartItem.query.filter_by(
            cart_id=cart.id,
            variant_id=variant_id
        ).first()

        # Calculate desired final quantity (current + delta)
        current_quantity = cart_item.quantity if cart_item else 0
        desired_quantity = current_quantity + quantity

        # Validate desired final quantity
        is_valid, error_response, status_code = validate_cart_quantity(
            quantity=desired_quantity,
            variant_id=variant_id,
            current_cart_quantity=current_quantity
        )
        
        if not is_valid:
            # Add current cart context to error for better UX
            if cart_item:
                error_response['current_in_cart'] = current_quantity
            return jsonify(error_response), status_code

        # Update or create cart item
        if cart_item:
            cart_item.quantity = desired_quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                variant_id=variant_id,
                quantity=desired_quantity
            )
            db.session.add(cart_item)

        db.session.commit()

        return jsonify({
            'message': 'Item added to cart',
            'cart_item': cart_item.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Add to cart failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/cart/items/<int:item_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_cart_item(item_id):
    """
    Update cart item quantity with comprehensive validation.

    Request body:
    {
        "quantity": 3
    }
    """
    try:
        customer_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'quantity' not in data:
            return jsonify({'error': 'quantity is required'}), 400

        quantity = data['quantity']

        # Get cart for this customer
        cart = Cart.query.filter_by(customer_id=customer_id).first()
        if not cart:
            return jsonify({'error': 'Cart not found'}), 404

        # Try to find cart item by ID first, then by variant_id
        cart_item = CartItem.query.get(item_id)
        if not cart_item:
            cart_item = CartItem.query.filter_by(
                cart_id=cart.id,
                variant_id=item_id
            ).first()
        
        if not cart_item:
            return jsonify({'error': 'Cart item not found'}), 404

        # Verify cart belongs to customer
        if cart_item.cart_id != cart.id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Validate new quantity
        is_valid, error_response, status_code = validate_cart_quantity(
            quantity=quantity,
            variant_id=cart_item.variant_id,
            current_cart_quantity=cart_item.quantity
        )
        
        if not is_valid:
            return jsonify(error_response), status_code

        # Update quantity
        cart_item.quantity = quantity
        db.session.commit()

        return jsonify({
            'message': 'Cart item updated',
            'cart_item': cart_item.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update cart item failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/cart/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_cart_item(item_id):
    """Remove item from cart"""
    try:
        customer_id = int(get_jwt_identity())

        # Get cart item
        cart_item = CartItem.query.get(item_id)
        if not cart_item:
            return jsonify({'error': 'Cart item not found'}), 404

        # Verify cart belongs to customer
        cart = Cart.query.get(cart_item.cart_id)
        if cart.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized'}), 403

        db.session.delete(cart_item)
        db.session.commit()

        return jsonify({'message': 'Item removed from cart'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/cart', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Clear all items from cart"""
    try:
        customer_id = int(get_jwt_identity())

        cart = Cart.query.filter_by(customer_id=customer_id).first()
        if not cart:
            return jsonify({'message': 'Cart is already empty'}), 200

        # Delete all cart items
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

        return jsonify({'message': 'Cart cleared'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
