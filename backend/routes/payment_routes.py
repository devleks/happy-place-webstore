"""
Payment Routes
Handles payment processing for orders (M-Pesa, Cash on Delivery, Card).
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.database_models import Payment, Order
from models import db
from services.mpesa_service import MPesaService
from services.payment_service import PaymentService
from services.encryption import encrypt_payment
import logging

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payments')


@payment_bp.route('/initiate', methods=['POST'])
@jwt_required()
def initiate_payment():
    """
    Initiate a payment for an order.

    Supports:
    - M-Pesa (STK Push)
    - Cash on Delivery (COD)
    - Card (future)

    Request body:
    {
        "order_id": 123,
        "payment_method": "mpesa",  # or "cod", "card"
        "phone_number": "254712345678"  # Required for M-Pesa
    }

    Returns:
        200: Payment initiated successfully
        400: Invalid input
        404: Order not found
        500: Payment initiation failed
    """
    data = request.get_json()

    # Validate input
    if not data or 'order_id' not in data or 'payment_method' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: order_id, payment_method'
        }), 400

    order_id = data.get('order_id')
    payment_method = data.get('payment_method', '').lower()
    phone_number = data.get('phone_number', '')

    # Validate payment method
    if payment_method not in ['mpesa', 'cod', 'card']:
        return jsonify({
            'success': False,
            'error': 'Invalid payment_method. Must be: mpesa, cod, or card'
        }), 400

    # Get user info from JWT
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    user_type = jwt_data.get('user_type', 'customer')

    # Get order
    order = Order.query.get(order_id)
    if not order:
        return jsonify({
            'success': False,
            'error': f'Order not found: {order_id}'
        }), 404

    # Verify order belongs to customer (if customer is making request)
    if user_type == 'customer' and order.customer_id != int(current_user_id):
        return jsonify({
            'success': False,
            'error': 'Unauthorized: Order does not belong to you'
        }), 403

    # Check if payment already exists
    existing_payment = PaymentService.get_payment_by_order(order_id)
    if existing_payment:
        if existing_payment.status == 'completed':
            return jsonify({
                'success': False,
                'error': 'Payment already completed for this order'
            }), 400

        # Update existing pending payment
        payment = existing_payment
        payment.payment_method = payment_method
    else:
        # Create new payment record
        payment = Payment(
            order_id=order_id,
            payment_method=payment_method,
            amount=order.total,
            status='pending'
        )
        db.session.add(payment)
        db.session.flush()  # Get payment ID

    try:
        if payment_method == 'mpesa':
            # Validate phone number for M-Pesa
            if not phone_number:
                return jsonify({
                    'success': False,
                    'error': 'phone_number required for M-Pesa payment'
                }), 400

            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif phone_number.startswith('7') or phone_number.startswith('1'):
                phone_number = '254' + phone_number

            if not phone_number.startswith('254') or len(phone_number) != 12:
                return jsonify({
                    'success': False,
                    'error': 'Invalid phone number format. Use: 254712345678'
                }), 400

            # Encrypt and save phone number
            payment.mpesa_phone_encrypted = encrypt_payment(phone_number)

            # Initiate M-Pesa STK Push
            mpesa_service = MPesaService()
            result = mpesa_service.initiate_stk_push(
                phone_number=phone_number,
                amount=float(order.total),
                account_reference=f"ORD{order.id}",
                transaction_desc=f"Order #{order.id}"
            )

            if result.get('success'):
                # Save STK Push details (we'll get transaction ID in callback)
                payment.status = 'pending'
                db.session.commit()

                logger.info(f"M-Pesa STK Push initiated for order {order_id}")

                return jsonify({
                    'success': True,
                    'payment_id': payment.id,
                    'message': 'Payment request sent to your phone. Enter your M-Pesa PIN to complete.',
                    'CheckoutRequestID': result.get('CheckoutRequestID'),
                    'CustomerMessage': result.get('CustomerMessage')
                }), 200
            else:
                payment.status = 'failed'
                db.session.commit()

                logger.error(f"M-Pesa STK Push failed for order {order_id}: {result.get('error')}")

                return jsonify({
                    'success': False,
                    'error': result.get('error', 'M-Pesa payment initiation failed'),
                    'ResponseDescription': result.get('ResponseDescription')
                }), 500

        elif payment_method == 'cod':
            # Cash on Delivery - no immediate processing needed
            payment.status = 'pending'
            db.session.commit()

            logger.info(f"COD payment created for order {order_id}")

            return jsonify({
                'success': True,
                'payment_id': payment.id,
                'message': 'Order placed successfully. Pay cash on delivery.',
                'payment_method': 'cod'
            }), 200

        elif payment_method == 'card':
            # Card payment - to be implemented (Stripe/PayPal)
            return jsonify({
                'success': False,
                'error': 'Card payment not yet implemented. Use M-Pesa or Cash on Delivery.'
            }), 501

    except Exception as e:
        db.session.rollback()
        logger.error(f"Payment initiation failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Payment initiation failed: {str(e)}'
        }), 500


@payment_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    M-Pesa STK Push callback endpoint.

    Safaricom sends payment confirmation here after customer enters PIN.

    This endpoint is called by Safaricom servers, not authenticated.

    Request body structure:
    {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "...",
                "CheckoutRequestID": "...",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1.00},
                        {"Name": "MpesaReceiptNumber", "Value": "..."},
                        {"Name": "TransactionDate", "Value": 20231225123456},
                        {"Name": "PhoneNumber", "Value": 254712345678}
                    ]
                }
            }
        }
    }

    Returns:
        200: Callback processed (always return 200 to Safaricom)
    """
    try:
        data = request.get_json()
        logger.info(f"M-Pesa callback received: {data}")

        # Extract callback data
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})

        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc', '')
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        # Log callback
        logger.info(f"M-Pesa callback - CheckoutRequestID: {checkout_request_id}, ResultCode: {result_code}")

        # ResultCode 0 = Success
        if result_code == 0:
            # Extract payment details from metadata
            metadata = stk_callback.get('CallbackMetadata', {})
            items = metadata.get('Item', [])

            mpesa_receipt = None
            phone_number = None
            amount = None

            for item in items:
                name = item.get('Name')
                value = item.get('Value')

                if name == 'MpesaReceiptNumber':
                    mpesa_receipt = str(value)
                elif name == 'PhoneNumber':
                    phone_number = str(value)
                elif name == 'Amount':
                    amount = float(value)

            if mpesa_receipt and phone_number:
                # Find payment by phone number (we saved it encrypted)
                # For now, we'll need to match by amount and recent timestamp
                # In production, store CheckoutRequestID during initiation

                # Encrypt transaction details
                transaction_id_encrypted = encrypt_payment(mpesa_receipt)
                phone_encrypted = encrypt_payment(phone_number)

                # Find most recent pending M-Pesa payment with matching amount
                payment = Payment.query.filter_by(
                    payment_method='mpesa',
                    status='pending',
                    amount=amount
                ).order_by(Payment.created_at.desc()).first()

                if payment:
                    # Complete payment
                    result = PaymentService.complete_payment(
                        payment.id,
                        transaction_id_encrypted,
                        phone_encrypted
                    )

                    if result.get('success'):
                        logger.info(f"Payment {payment.id} completed successfully via M-Pesa")
                    else:
                        logger.error(f"Payment completion failed: {result.get('error')}")
                else:
                    logger.warning(f"No matching payment found for M-Pesa receipt: {mpesa_receipt}")

        else:
            # Payment failed or cancelled
            logger.warning(f"M-Pesa payment failed - ResultCode: {result_code}, Description: {result_desc}")

            # Mark payment as failed if we can find it
            # (Would need CheckoutRequestID stored during initiation to match accurately)

        # Always return 200 to acknowledge receipt
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Callback processed successfully'
        }), 200

    except Exception as e:
        logger.error(f"M-Pesa callback processing error: {e}", exc_info=True)

        # Still return 200 to Safaricom to prevent retries
        return jsonify({
            'ResultCode': 0,
            'ResultDesc': 'Callback received'
        }), 200


@payment_bp.route('/<int:payment_id>/status', methods=['GET'])
@jwt_required()
def get_payment_status(payment_id):
    """
    Get status of a payment.

    Returns:
        200: Payment status
        404: Payment not found
    """
    payment = PaymentService.get_payment(payment_id)

    if not payment:
        return jsonify({
            'success': False,
            'error': 'Payment not found'
        }), 404

    # Verify user can access this payment
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    user_type = jwt_data.get('user_type', 'customer')

    order = Order.query.get(payment.order_id)
    if user_type == 'customer' and order.customer_id != int(current_user_id):
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        }), 403

    return jsonify({
        'success': True,
        'payment': payment.to_dict()
    }), 200


@payment_bp.route('/cod/<int:payment_id>/confirm-delivered', methods=['POST'])
@jwt_required()
def confirm_cod_delivered(payment_id):
    """
    Mark COD payment as completed when order is delivered.

    Only employees can mark COD as delivered.

    Returns:
        200: Payment marked as completed
        403: Unauthorized (not an employee)
        404: Payment not found
        400: Invalid payment method or already completed
    """
    # Check if user is employee
    jwt_data = get_jwt()
    user_type = jwt_data.get('user_type')

    if user_type != 'employee':
        return jsonify({
            'success': False,
            'error': 'Only employees can confirm delivery'
        }), 403

    try:
        result = PaymentService.mark_cod_delivered(payment_id)

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'COD payment marked as completed'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 400

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"COD confirmation failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to confirm delivery'
        }), 500
