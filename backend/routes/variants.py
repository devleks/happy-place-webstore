"""
Product Variants API routes.
Handles variant CRUD operations and inventory management.
"""

from flask import request, jsonify
from routes import api
from models import db, Product, ProductVariant, Inventory
from middleware import manager_required
from logging_utils import get_logger, safe_auth_context
from services.inventory_service import InventoryService

# Initialize logger
logger = get_logger(__name__)


@api.route('/products/<int:product_id>/variants', methods=['GET'])
def get_product_variants(product_id):
    """
    Get all variants for a product.
    Public endpoint.
    """
    product = Product.query.get(product_id)

    if not product:
        return jsonify({
            'error': 'Product not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    variants = ProductVariant.query.filter_by(product_id=product_id, is_active=True).all()

    return jsonify({
        'product_id': product.id,
        'product_name': product.name,
        'variants': [variant.to_dict_with_inventory() for variant in variants]
    }), 200


@api.route('/products/<int:product_id>/variants', methods=['POST'])
@manager_required
def create_product_variant(current_employee, product_id):
    """
    Create a new product variant.
    Requires manager or admin role.
    """
    product = Product.query.get(product_id)

    if not product:
        return jsonify({
            'error': 'Product not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    data = request.get_json()

    # Validate required fields
    required_fields = ['sku', 'size', 'color']
    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'code': 'VALIDATION_ERROR',
            'details': {'missing_fields': missing_fields}
        }), 400

    # Check if SKU already exists
    existing_variant = ProductVariant.query.filter_by(sku=data['sku']).first()
    if existing_variant:
        return jsonify({
            'error': 'SKU already exists',
            'code': 'DUPLICATE_RESOURCE'
        }), 409

    try:
        # Create variant
        variant = ProductVariant(
            product_id=product_id,
            sku=data['sku'],
            size=data['size'],
            color=data['color'],
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()  # Get variant ID

        # Create inventory record
        inventory = Inventory(
            variant_id=variant.id,
            quantity=data.get('initial_quantity', 0),
            reserved_quantity=0
        )
        db.session.add(inventory)
        db.session.commit()

        return jsonify({
            'id': variant.id,
            'product_id': variant.product_id,
            'sku': variant.sku,
            'size': variant.size,
            'color': variant.color,
            'is_active': variant.is_active,
            'created_at': variant.created_at.isoformat() if variant.created_at else None,
            'inventory': {
                'quantity': inventory.quantity,
                'available_quantity': inventory.quantity,
                'is_low_stock': inventory.is_low_stock
            }
        }), 201

    except Exception:
        db.session.rollback()
        logger.error(
            "Create product variant failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": current_employee.id if current_employee else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'error': 'Failed to create variant',
            'code': 'INTERNAL_ERROR'
        }), 500


@api.route('/variants/<int:variant_id>/inventory', methods=['PATCH'])
@manager_required
def update_variant_inventory(current_employee, variant_id):
    """
    Update variant inventory quantity.
    Requires manager or admin role.

    Actions: set, add, subtract
    """
    variant = ProductVariant.query.get(variant_id)

    if not variant:
        return jsonify({
            'error': 'Variant not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    data = request.get_json()

    if 'quantity' not in data or 'action' not in data:
        return jsonify({
            'error': 'Missing required fields: quantity, action',
            'code': 'VALIDATION_ERROR'
        }), 400

    action = data['action']
    quantity_change = data['quantity']

    if action not in ['set', 'add', 'subtract']:
        return jsonify({
            'error': 'Invalid action. Must be: set, add, or subtract',
            'code': 'VALIDATION_ERROR'
        }), 400

    inventory = Inventory.query.filter_by(variant_id=variant_id).first()

    if not inventory:
        return jsonify({
            'error': 'Inventory record not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    try:
        previous_quantity = inventory.quantity

        if action == 'set':
            inventory.quantity = quantity_change
        elif action == 'add':
            inventory.quantity += quantity_change
        elif action == 'subtract':
            inventory.quantity = max(0, inventory.quantity - quantity_change)

        db.session.commit()

        return jsonify({
            'variant_id': variant.id,
            'sku': variant.sku,
            'previous_quantity': previous_quantity,
            'new_quantity': inventory.quantity,
            'available_quantity': inventory.quantity - inventory.reserved_quantity,
            'updated_at': inventory.updated_at.isoformat() if inventory.updated_at else None
        }), 200

    except Exception:
        db.session.rollback()
        logger.error(
            "Update variant inventory failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": current_employee.id if current_employee else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'error': 'Failed to update inventory',
            'code': 'INTERNAL_ERROR'
        }), 500


@api.route('/variants/<int:variant_id>/availability', methods=['GET'])
def check_variant_availability(variant_id):
    """
    Check if a variant is available for purchase.
    Public endpoint.
    """
    variant = ProductVariant.query.get(variant_id)

    if not variant:
        return jsonify({
            'error': 'Variant not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    inventory = Inventory.query.filter_by(variant_id=variant_id).first()

    if not inventory:
        return jsonify({
            'error': 'Inventory record not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    channel = request.args.get('channel', 'online')
    if channel not in ['online', 'store', 'pos']:
        channel = 'online'

    available_quantity = InventoryService.get_available_inventory(variant_id, channel)

    return jsonify({
        'variant_id': variant.id,
        'sku': variant.sku,
        'size': variant.size,
        'color': variant.color,
        'available': variant.is_active and available_quantity > 0,
        'quantity': inventory.quantity,
        'reserved_quantity': inventory.reserved_quantity,
        'available_quantity': available_quantity,
        'is_low_stock': inventory.is_low_stock,
        'is_out_of_stock': available_quantity == 0,
        'can_purchase': variant.is_active and available_quantity > 0
    }), 200
