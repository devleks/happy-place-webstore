"""
POS API Routes
Handles all Point of Sale endpoints
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from functools import wraps

from routes import api
from services.pos_service import POSService
from services.receipt_service import ReceiptService
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)


def employee_required(fn):
    """Decorator to require employee authentication"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        try:
            claims = get_jwt()
            logger.debug(f"employee_required - user_type: {claims.get('user_type')}")

            # Check if user_type is employee
            if claims.get('user_type') != 'employee':
                return jsonify({
                    'success': False,
                    'error': 'Employee access required'
                }), 403

            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(
                "Employee authentication decorator failed",
                extra={"context": safe_auth_context(
                    user_type='employee',
                    ip=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )},
                exc_info=True,
            )
            return jsonify({
                'success': False,
                'error': 'Authentication error'
            }), 422
    return wrapper


def manager_required(fn):
    """Decorator to require manager or admin role"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()

        # Check if user_type is employee
        if claims.get('user_type') != 'employee':
            return jsonify({
                'success': False,
                'error': 'Employee access required'
            }), 403

        # Check if role is manager or admin
        role = claims.get('role')
        if role not in ['manager', 'admin']:
            return jsonify({
                'success': False,
                'error': 'Manager or admin access required'
            }), 403

        return fn(*args, **kwargs)
    return wrapper


# ============================================================================
# TRANSACTION ENDPOINTS
# ============================================================================

@api.route('/pos/transactions', methods=['POST'])
@employee_required
def create_transaction():
    """
    Create a new POS transaction

    POST /api/pos/transactions
    Body: {
        "shift_id": 1,
        "payment_method": "cash",
        "items": [
            {"variant_id": 21, "quantity": 2},
            {"variant_id": 35, "quantity": 1}
        ],
        "customer_id": 123 (optional),
        "cash_tendered": 10000.00 (required for cash)
    }
    """
    try:
        employee_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate required fields
        if not data.get('shift_id'):
            return jsonify({
                'success': False,
                'error': 'shift_id is required'
            }), 400

        if not data.get('payment_method'):
            return jsonify({
                'success': False,
                'error': 'payment_method is required'
            }), 400

        if not data.get('items') or len(data.get('items')) == 0:
            return jsonify({
                'success': False,
                'error': 'items array is required and must not be empty'
            }), 400

        # Validate cash tendered for cash payments
        if data.get('payment_method') == 'cash' and not data.get('cash_tendered'):
            return jsonify({
                'success': False,
                'error': 'cash_tendered is required for cash payments'
            }), 400

        # Get store location from shift (we'll get this from the shift)
        # For now, use store_location_id from request or default to 1
        store_location_id = data.get('store_location_id', 1)

        result = POSService.create_transaction(
            employee_id=employee_id,
            store_location_id=store_location_id,
            shift_id=data['shift_id'],
            payment_method=data['payment_method'],
            items=data['items'],
            customer_id=data.get('customer_id'),
            cash_tendered=data.get('cash_tendered')
        )

        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/<int:transaction_id>', methods=['GET'])
@employee_required
def get_transaction(transaction_id):
    """
    Get transaction details

    GET /api/pos/transactions/:id
    """
    try:
        transaction = POSService.get_transaction(transaction_id)

        if transaction:
            return jsonify({
                'success': True,
                'transaction': transaction
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/<int:transaction_id>/void', methods=['POST'])
@manager_required
def void_transaction(transaction_id):
    """
    Void a transaction (manager/admin only)

    POST /api/pos/transactions/:id/void
    Body: {
        "void_reason": "Customer returned all items"
    }
    """
    try:
        voided_by = int(get_jwt_identity())
        data = request.get_json()
        void_reason = data.get('void_reason')

        if not void_reason:
            return jsonify({
                'success': False,
                'error': 'void_reason is required'
            }), 400

        result = POSService.void_transaction(
            transaction_id=transaction_id,
            voided_by=voided_by,
            void_reason=void_reason
        )

        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/today', methods=['GET'])
@employee_required
def get_todays_transactions():
    """
    Get all transactions for today

    GET /api/pos/transactions/today?shift_id=1&store_location_id=1
    """
    try:
        shift_id = request.args.get('shift_id', type=int)
        store_location_id = request.args.get('store_location_id', type=int)

        transactions = POSService.get_todays_transactions(
            store_location_id=store_location_id,
            shift_id=shift_id
        )

        return jsonify({
            'success': True,
            'transactions': transactions,
            'count': len(transactions)
        }), 200

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/<int:transaction_id>/receipt/printed', methods=['PUT'])
@employee_required
def mark_receipt_printed(transaction_id):
    """
    Mark receipt as printed

    PUT /api/pos/transactions/:id/receipt/printed
    """
    try:
        POSService.mark_receipt_printed(transaction_id)

        return jsonify({
            'success': True,
            'message': 'Receipt marked as printed'
        }), 200

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/<int:transaction_id>/receipt/emailed', methods=['PUT'])
@employee_required
def mark_receipt_emailed(transaction_id):
    """
    Mark receipt as emailed

    PUT /api/pos/transactions/:id/receipt/emailed
    """
    try:
        POSService.mark_receipt_emailed(transaction_id)

        return jsonify({
            'success': True,
            'message': 'Receipt marked as emailed'
        }), 200

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# SHIFT ENDPOINTS
# ============================================================================

@api.route('/pos/shifts/start', methods=['POST'])
@employee_required
def start_shift():
    """
    Start a new shift

    POST /api/pos/shifts/start
    Body: {
        "store_location_id": 1,
        "opening_float": 5000.00
    }
    """
    try:
        employee_id = int(get_jwt_identity())
        data = request.get_json()

        logger.debug(f"Starting shift for employee_id: {employee_id}")

        # Validate required fields
        if not data.get('store_location_id'):
            return jsonify({
                'success': False,
                'error': 'store_location_id is required'
            }), 400

        if data.get('opening_float') is None:
            return jsonify({
                'success': False,
                'error': 'opening_float is required'
            }), 400

        result = POSService.start_shift(
            employee_id=employee_id,
            store_location_id=data['store_location_id'],
            opening_float=data['opening_float']
        )

        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(
            "Start POS shift failed",
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


@api.route('/pos/shifts/close', methods=['POST'])
@employee_required
def close_shift():
    """
    Close current shift

    POST /api/pos/shifts/close
    Body: {
        "shift_id": 1,
        "closing_cash": 8500.00,
        "notes": "Short KSh 50 - customer gave exact change error"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('shift_id'):
            return jsonify({
                'success': False,
                'error': 'shift_id is required'
            }), 400

        if data.get('closing_cash') is None:
            return jsonify({
                'success': False,
                'error': 'closing_cash is required'
            }), 400

        result = POSService.close_shift(
            shift_id=data['shift_id'],
            closing_cash=data['closing_cash'],
            notes=data.get('notes')
        )

        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/shifts/current', methods=['GET'])
@employee_required
def get_current_shift():
    """
    Get current open shift for logged-in employee

    GET /api/pos/shifts/current
    """
    try:
        employee_id = int(get_jwt_identity())
        logger.debug(f"Getting current shift for employee_id: {employee_id}")

        shift = POSService.get_current_shift(employee_id)

        if shift:
            return jsonify({
                'success': True,
                'shift': shift
            }), 200
        else:
            return jsonify({
                'success': True,
                'shift': None,
                'message': 'No open shift found'
            }), 200

    except Exception as e:
        logger.error(
            "Get current POS shift failed",
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


@api.route('/pos/shifts/<int:shift_id>', methods=['GET'])
@employee_required
def get_shift(shift_id):
    """
    Get shift details by ID

    GET /api/pos/shifts/:id
    """
    try:
        shift = POSService.get_shift_by_id(shift_id)

        if shift:
            return jsonify({
                'success': True,
                'shift': shift
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Shift not found'
            }), 404

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/shifts/<int:shift_id>/transactions', methods=['GET'])
@employee_required
def get_shift_transactions(shift_id):
    """
    Get all transactions for a specific shift

    GET /api/pos/shifts/:id/transactions
    """
    try:
        transactions = POSService.get_shift_transactions(shift_id)

        return jsonify({
            'success': True,
            'shift_id': shift_id,
            'transactions': transactions,
            'count': len(transactions)
        }), 200

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/shifts/<int:shift_id>/close', methods=['POST'])
@employee_required
def close_shift_by_id(shift_id):
    """
    Close a specific shift by ID

    POST /api/pos/shifts/:id/close
    Body: {
        "closing_cash": 8500.00,
        "notes": "Short KSh 50 - customer gave exact change error"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if data.get('closing_cash') is None:
            return jsonify({
                'success': False,
                'error': 'closing_cash is required'
            }), 400

        result = POSService.close_shift(
            shift_id=shift_id,
            closing_cash=data['closing_cash'],
            notes=data.get('notes')
        )

        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/shifts/<int:shift_id>/summary', methods=['GET'])
@employee_required
def get_shift_summary(shift_id):
    """
    Get shift summary/statistics

    GET /api/pos/shifts/:id/summary
    """
    try:
        summary = POSService.get_shift_summary(shift_id)

        if summary.get('success'):
            return jsonify(summary), 200
        else:
            return jsonify(summary), 404

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# CASH MANAGEMENT ENDPOINTS
# ============================================================================

@api.route('/pos/cash-movements', methods=['POST'])
@employee_required
def record_cash_movement():
    """
    Record cash in/out movement

    POST /api/pos/cash-movements
    Body: {
        "shift_id": 1,
        "movement_type": "cash_in" or "cash_out",
        "amount": 1000.00,
        "reason": "Petty cash withdrawal"
    }
    """
    try:
        employee_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate required fields
        if not data.get('shift_id'):
            return jsonify({
                'success': False,
                'error': 'shift_id is required'
            }), 400

        if not data.get('movement_type'):
            return jsonify({
                'success': False,
                'error': 'movement_type is required'
            }), 400

        if data.get('movement_type') not in ['cash_in', 'cash_out']:
            return jsonify({
                'success': False,
                'error': 'movement_type must be cash_in or cash_out'
            }), 400

        if data.get('amount') is None:
            return jsonify({
                'success': False,
                'error': 'amount is required'
            }), 400

        if not data.get('reason'):
            return jsonify({
                'success': False,
                'error': 'reason is required'
            }), 400

        movement_id = POSService.record_cash_movement(
            shift_id=data['shift_id'],
            movement_type=data['movement_type'],
            amount=data['amount'],
            reason=data['reason'],
            performed_by=employee_id
        )

        return jsonify({
            'success': True,
            'movement_id': movement_id,
            'message': 'Cash movement recorded'
        }), 201

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# ============================================================================
# RECEIPT ENDPOINTS
# ============================================================================

@api.route('/pos/transactions/<int:transaction_id>/receipt/thermal', methods=['GET'])
@employee_required
def get_thermal_receipt(transaction_id):
    """
    Get thermal receipt for printing

    GET /api/pos/transactions/:id/receipt/thermal?width=58
    Query params:
        - width: 58 (default) or 80 (for 80mm paper)
    """
    try:
        # Get transaction
        transaction = POSService.get_transaction(transaction_id)

        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404

        # Get width parameter (default 58mm = 32 chars)
        width_mm = request.args.get('width', '58')
        char_width = 32 if width_mm == '58' else 48

        # Generate receipt
        receipt_text = ReceiptService.generate_thermal_receipt(transaction, width=char_width)

        return jsonify({
            'success': True,
            'receipt': receipt_text,
            'width': width_mm
        }), 200

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/<int:transaction_id>/receipt/html', methods=['GET'])
@employee_required
def get_html_receipt(transaction_id):
    """
    Get HTML receipt for display or printing

    GET /api/pos/transactions/:id/receipt/html
    """
    try:
        # Get transaction
        transaction = POSService.get_transaction(transaction_id)

        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404

        # Generate HTML receipt
        receipt_html = ReceiptService.generate_html_receipt(transaction)

        return receipt_html, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/pos/transactions/<int:transaction_id>/receipt/formats', methods=['GET'])
@employee_required
def get_all_receipt_formats(transaction_id):
    """
    Get all receipt formats at once

    GET /api/pos/transactions/:id/receipt/formats
    """
    try:
        # Get transaction
        transaction = POSService.get_transaction(transaction_id)

        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404

        # Generate all formats
        formats = ReceiptService.get_receipt_formats(transaction)

        return jsonify({
            'success': True,
            'transaction_id': transaction_id,
            'transaction_number': transaction['transaction_number'],
            'formats': formats
        }), 200

    except Exception as e:
        logger.error(
            "POS operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
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

@api.route('/pos/health', methods=['GET'])
def health_check():
    """POS API health check"""
    return jsonify({
        'success': True,
        'service': 'POS API',
        'status': 'healthy'
    }), 200
