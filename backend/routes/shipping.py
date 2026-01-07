"""
Shipping Methods API routes.
Handles shipping cost calculation and method selection.

Business Rules:
- Nairobi: Free shipping (always)
- Upcountry: KSh 300 base + KSh 50/kg
- Store Pickup: Free
- Free shipping on orders > KSh 5000 (upcountry only)
"""

from flask import request, jsonify
from routes import api
from models import ShippingMethod, Product
from logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)


@api.route('/shipping/methods', methods=['GET'])
def get_shipping_methods():
    """
    Get available shipping methods.
    Query param: is_nairobi (boolean)
    """
    is_nairobi = request.args.get('is_nairobi', 'true').lower() == 'true'

    # Get all active shipping methods
    methods = ShippingMethod.query.filter_by(is_active=True).all()

    # Filter based on location
    if is_nairobi:
        # Nairobi gets free delivery + store pickup
        available_methods = [m for m in methods if m.name in ['Nairobi Free Delivery', 'Store Pickup']]
        location = 'Nairobi'
    else:
        # Upcountry gets standard delivery + store pickup
        available_methods = [m for m in methods if m.name in ['Upcountry Standard Delivery', 'Store Pickup']]
        location = 'Upcountry'

    return jsonify({
        'location': location,
        'is_nairobi': is_nairobi,
        'methods': [
            {
                'id': method.id,
                'name': method.name,
                'description': method.description,
                'base_cost': float(method.base_cost),
                'cost_per_kg': float(method.cost_per_kg),
                'estimated_days_min': method.estimated_days_min,
                'estimated_days_max': method.estimated_days_max,
                'is_free': method.base_cost == 0 and method.cost_per_kg == 0,
                'free_shipping_threshold': float(method.free_shipping_threshold) if method.free_shipping_threshold else None
            }
            for method in available_methods
        ]
    }), 200


@api.route('/shipping/calculate', methods=['POST'])
def calculate_shipping_cost():
    """
    Calculate shipping cost for an order.

    Required fields: shipping_method_id, is_nairobi, order_total
    Optional fields: total_weight_kg, items
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ['shipping_method_id', 'is_nairobi', 'order_total']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'code': 'VALIDATION_ERROR',
            'details': {'missing_fields': missing_fields}
        }), 400

    method = ShippingMethod.query.get(data['shipping_method_id'])

    if not method or not method.is_active:
        return jsonify({
            'error': 'Shipping method not found or inactive',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    is_nairobi = data['is_nairobi']
    order_total = data['order_total']

    # Calculate total weight
    total_weight_kg = data.get('total_weight_kg', 0)

    if not total_weight_kg and data.get('items'):
        # Calculate weight from items
        for item in data['items']:
            product = Product.query.get(item['product_id'])
            if product and product.weight:
                total_weight_kg += float(product.weight) * item.get('quantity', 1)

    # Calculate shipping cost
    if is_nairobi:
        # Nairobi: always free
        final_cost = 0.0
        calculation = {
            'base_cost': 0.0,
            'weight_kg': total_weight_kg,
            'weight_cost': 0.0,
            'total_cost': 0.0,
            'free_shipping_threshold': None,
            'qualifies_for_free_shipping': True
        }
    else:
        # Upcountry: calculate based on weight
        base_cost = float(method.base_cost)
        weight_cost = total_weight_kg * float(method.cost_per_kg)
        total_cost = base_cost + weight_cost

        # Check free shipping threshold
        qualifies_for_free = False
        if method.free_shipping_threshold and order_total >= method.free_shipping_threshold:
            qualifies_for_free = True
            final_cost = 0.0
        else:
            final_cost = total_cost

        calculation = {
            'base_cost': base_cost,
            'weight_kg': total_weight_kg,
            'weight_cost': weight_cost,
            'total_cost': total_cost,
            'free_shipping_threshold': float(method.free_shipping_threshold) if method.free_shipping_threshold else None,
            'qualifies_for_free_shipping': qualifies_for_free
        }

    estimated_delivery = f"{method.estimated_days_min}-{method.estimated_days_max} business days"
    if method.estimated_days_min == 0:
        estimated_delivery = "Same day"

    return jsonify({
        'shipping_method': method.name,
        'is_nairobi': is_nairobi,
        'calculation': calculation,
        'final_cost': final_cost,
        'estimated_delivery': estimated_delivery
    }), 200


@api.route('/shipping/methods/<int:method_id>', methods=['GET'])
def get_shipping_method_details(method_id):
    """
    Get details of a specific shipping method.
    """
    method = ShippingMethod.query.get(method_id)

    if not method:
        return jsonify({
            'error': 'Shipping method not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    return jsonify({
        'id': method.id,
        'name': method.name,
        'description': method.description,
        'base_cost': float(method.base_cost),
        'cost_per_kg': float(method.cost_per_kg),
        'estimated_days_min': method.estimated_days_min,
        'estimated_days_max': method.estimated_days_max,
        'available_for_nairobi': method.name in ['Nairobi Free Delivery', 'Store Pickup'],
        'available_outside_nairobi': method.name in ['Upcountry Standard Delivery', 'Store Pickup'],
        'free_shipping_threshold': float(method.free_shipping_threshold) if method.free_shipping_threshold else None,
        'is_active': method.is_active
    }), 200
