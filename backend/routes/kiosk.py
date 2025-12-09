"""
Kiosk API Routes
Cashier kiosk features: barcode scanning, hold/recall, quick access, metrics
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from routes import api
from routes.pos import employee_required
from services.kiosk_service import KioskService
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)


# ============================================================================
# BARCODE / QUICK LOOKUP ENDPOINTS
# ============================================================================

@api.route('/pos/scan', methods=['POST'])
@employee_required
def scan_barcode():
    """
    Scan barcode and return product information

    POST /api/pos/scan
    Body: {
        "barcode": "HP0000000021"
    }
    """
    try:
        data = request.get_json()

        if not data.get('barcode'):
            return jsonify({
                'success': False,
                'error': 'barcode is required'
            }), 400

        product = KioskService.scan_barcode(data['barcode'])

        if product:
            return jsonify({
                'success': True,
                'product': product
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Product not found for this barcode'
            }), 404

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/product/quick/<sku>', methods=['GET'])
@employee_required
def quick_product_lookup(sku):
    """
    Quick product lookup by SKU

    GET /api/pos/product/quick/:sku
    """
    try:
        product = KioskService.quick_product_lookup(sku)

        if product:
            return jsonify({
                'success': True,
                'product': product
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# HOLD / RECALL ENDPOINTS
# ============================================================================

@api.route('/pos/transactions/hold', methods=['POST'])
@employee_required
def hold_transaction():
    """
    Hold current transaction

    POST /api/pos/transactions/hold
    Body: {
        "shift_id": 1,
        "items": [...],
        "subtotal": 9797.00,
        "tax": 1567.52,
        "total": 11364.52,
        "customer_note": "Customer went to get wallet"
    }
    """
    try:
        employee_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate required fields
        required = ['shift_id', 'items', 'subtotal', 'tax', 'total']
        for field in required:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400

        result = KioskService.hold_transaction(
            employee_id=employee_id,
            shift_id=data['shift_id'],
            items=data['items'],
            subtotal=data['subtotal'],
            tax=data['tax'],
            total=data['total'],
            customer_note=data.get('customer_note')
        )

        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/held', methods=['GET'])
@employee_required
def get_held_transactions():
    """
    Get held transactions

    GET /api/pos/transactions/held?shift_id=1
    """
    try:
        employee_id = int(get_jwt_identity())
        shift_id = request.args.get('shift_id', type=int)

        held = KioskService.get_held_transactions(
            employee_id=employee_id,
            shift_id=shift_id
        )

        return jsonify({
            'success': True,
            'held_transactions': held,
            'count': len(held)
        }), 200

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/recall/<int:hold_id>', methods=['POST'])
@employee_required
def recall_transaction(hold_id):
    """
    Recall a held transaction

    POST /api/pos/transactions/recall/:hold_id
    """
    try:
        employee_id = int(get_jwt_identity())

        result = KioskService.recall_transaction(hold_id, employee_id)

        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 404

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/held/<int:hold_id>', methods=['DELETE'])
@employee_required
def cancel_held_transaction(hold_id):
    """
    Cancel a held transaction

    DELETE /api/pos/transactions/held/:hold_id
    """
    try:
        result = KioskService.cancel_held_transaction(hold_id)

        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# QUICK ACCESS ENDPOINTS
# ============================================================================

@api.route('/pos/quick-access', methods=['GET'])
@employee_required
def get_quick_access():
    """
    Get quick access products

    GET /api/pos/quick-access?type=favorite&limit=20
    """
    try:
        employee_id = int(get_jwt_identity())
        access_type = request.args.get('type')
        limit = request.args.get('limit', 20, type=int)

        products = KioskService.get_quick_access_products(
            employee_id=employee_id,
            store_location_id=1,  # TODO: Get from employee's store
            access_type=access_type,
            limit=limit
        )

        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        }), 200

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@api.route('/pos/metrics/current', methods=['GET'])
@employee_required
def get_current_metrics():
    """
    Get current cashier metrics

    GET /api/pos/metrics/current?shift_id=1
    """
    try:
        employee_id = int(get_jwt_identity())
        shift_id = request.args.get('shift_id', type=int)

        metrics = KioskService.get_cashier_metrics(employee_id, shift_id)

        if metrics:
            return jsonify({
                'success': True,
                'metrics': metrics
            }), 200
        else:
            return jsonify({
                'success': True,
                'metrics': {
                    'transactions_count': 0,
                    'items_scanned': 0,
                    'items_per_minute': 0,
                    'average_transaction_seconds': 0,
                    'fastest_transaction_seconds': 0,
                    'total_sales': 0,
                    'void_count': 0,
                    'discount_count': 0
                }
            }), 200

    except Exception as e:
        logger.error(
            "Kiosk operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# HELPER ENDPOINTS
# ============================================================================

@api.route('/pos/kiosk/health', methods=['GET'])
def kiosk_health_check():
    """Kiosk API health check"""
    return jsonify({
        'success': True,
        'service': 'Kiosk API',
        'status': 'healthy',
        'features': [
            'barcode_scanning',
            'hold_recall',
            'quick_access',
            'metrics'
        ]
    }), 200
