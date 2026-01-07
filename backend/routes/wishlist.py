"""
Wishlist API routes for Happy Place Boutique.

Endpoints:
- GET /api/wishlist - Get customer's wishlist
- POST /api/wishlist/items - Add item to wishlist
- DELETE /api/wishlist/items/<item_id> - Remove item from wishlist
- POST /api/wishlist/move-to-cart/<item_id> - Move wishlist item to cart
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Wishlist, WishlistItem, Product, Cart, CartItem, ProductVariant
from . import api
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)


@api.route('/wishlist', methods=['GET'])
@jwt_required()
def get_wishlist():
    """Get customer's wishlist with all items"""
    try:
        customer_id = int(get_jwt_identity())

        # Get or create wishlist
        wishlist = Wishlist.query.filter_by(customer_id=customer_id).first()
        if not wishlist:
            wishlist = Wishlist(customer_id=customer_id)
            db.session.add(wishlist)
            db.session.commit()

        return jsonify(wishlist.to_dict()), 200

    except Exception:
        logger.error(
            "Wishlist operation failed",
            extra={"context": safe_auth_context(
                user_type='customer',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"customer_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500


@api.route('/wishlist/items', methods=['POST'])
@api.route('/wishlist', methods=['POST'])  # Alias for backwards compatibility
@jwt_required()
def add_to_wishlist():
    """
    Add item to wishlist.

    Request body:
    {
        "product_id": 123  (or "variant_id": 456)
    }
    """
    try:
        customer_id = int(get_jwt_identity())
        data = request.get_json()

        # Accept either product_id or variant_id
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')

        if not product_id and not variant_id:
            return jsonify({'error': 'product_id or variant_id is required'}), 400

        # If variant_id provided, get product_id from variant
        if variant_id and not product_id:
            variant = ProductVariant.query.get(variant_id)
            if not variant:
                return jsonify({'error': 'Product variant not found'}), 404
            product_id = variant.product_id

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Get or create wishlist
        wishlist = Wishlist.query.filter_by(customer_id=customer_id).first()
        if not wishlist:
            wishlist = Wishlist(customer_id=customer_id)
            db.session.add(wishlist)
            db.session.flush()

        # Check if item already in wishlist
        existing_item = WishlistItem.query.filter_by(
            wishlist_id=wishlist.id,
            product_id=product_id
        ).first()

        if existing_item:
            return jsonify({
                'message': 'Product already in wishlist',
                'wishlist_item': existing_item.to_dict()
            }), 200

        # Create new wishlist item
        wishlist_item = WishlistItem(
            wishlist_id=wishlist.id,
            product_id=product_id
        )
        db.session.add(wishlist_item)
        db.session.commit()

        return jsonify({
            'message': 'Item added to wishlist',
            'wishlist_item': wishlist_item.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/wishlist/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_wishlist_item(item_id):
    """Remove item from wishlist"""
    try:
        customer_id = int(get_jwt_identity())

        # Get wishlist item
        wishlist_item = WishlistItem.query.get(item_id)
        if not wishlist_item:
            return jsonify({'error': 'Wishlist item not found'}), 404

        # Verify wishlist belongs to customer
        wishlist = Wishlist.query.get(wishlist_item.wishlist_id)
        if wishlist.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized'}), 403

        db.session.delete(wishlist_item)
        db.session.commit()

        return jsonify({'message': 'Item removed from wishlist'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/wishlist/move-to-cart/<int:item_id>', methods=['POST'])
@jwt_required()
def move_to_cart(item_id):
    """
    Move wishlist item to cart.

    Request body (optional):
    {
        "variant_id": 123,
        "quantity": 1
    }
    """
    try:
        customer_id = int(get_jwt_identity())
        data = request.get_json() or {}

        # Get wishlist item
        wishlist_item = WishlistItem.query.get(item_id)
        if not wishlist_item:
            return jsonify({'error': 'Wishlist item not found'}), 404

        # Verify wishlist belongs to customer
        wishlist = Wishlist.query.get(wishlist_item.wishlist_id)
        if wishlist.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Get variant_id from request or use first variant of product
        variant_id = data.get('variant_id')
        if not variant_id:
            # Get first available variant
            variant = ProductVariant.query.filter_by(
                product_id=wishlist_item.product_id
            ).first()
            if not variant:
                return jsonify({'error': 'No variants available for this product'}), 400
            variant_id = variant.id

        quantity = data.get('quantity', 1)

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

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                variant_id=variant_id,
                quantity=quantity
            )
            db.session.add(cart_item)

        # Remove from wishlist
        db.session.delete(wishlist_item)
        db.session.commit()

        return jsonify({
            'message': 'Item moved to cart',
            'cart_item': cart_item.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
