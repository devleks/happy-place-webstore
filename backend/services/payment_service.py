"""
Payment Service
Handles payment processing using stored procedures for security and atomicity.
"""

from typing import Dict, Optional
from extensions import db
from models.database_models import Payment


class PaymentService:
    """Service for payment processing"""

    @staticmethod
    def complete_payment(
        payment_id: int,
        transaction_id_encrypted: Optional[str] = None,
        mpesa_phone_encrypted: Optional[str] = None
    ) -> Dict:
        """
        Complete payment using stored procedure.

        This atomically:
        1. Updates payment status to 'completed'
        2. Updates order status to 'processing'
        3. Deducts inventory (converts reserved to actual deduction)
        4. Logs the payment completion in audit trail

        Args:
            payment_id: Payment ID
            transaction_id_encrypted: Encrypted M-Pesa transaction ID (optional)
            mpesa_phone_encrypted: Encrypted M-Pesa phone number (optional)

        Returns:
            dict: {
                'success': bool,
                'order_id': int,
                'message': str,
                'error': str (if failed)
            }

        Raises:
            ValueError: If payment not found
            RuntimeError: If payment processing fails
        """
        try:
            # Call stored procedure for atomic payment processing
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_process_payment_secure(
                        :payment_id,
                        :transaction_id_encrypted,
                        :mpesa_phone_encrypted
                    )
                """),
                {
                    'payment_id': payment_id,
                    'transaction_id_encrypted': transaction_id_encrypted,
                    'mpesa_phone_encrypted': mpesa_phone_encrypted
                }
            )

            # Fetch result
            row = result.fetchone()
            if not row:
                raise RuntimeError('Stored procedure did not return result')

            success = row[0]
            order_id = row[1]
            message = row[2]

            # Commit transaction
            db.session.commit()

            if not success:
                return {
                    'success': False,
                    'order_id': order_id,
                    'error': message
                }

            return {
                'success': True,
                'order_id': order_id,
                'message': message
            }

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Payment processing failed: {str(e)}')

    @staticmethod
    def get_payment_by_order(order_id: int) -> Optional[Payment]:
        """
        Get payment record by order ID.

        Args:
            order_id: Order ID

        Returns:
            Payment object or None
        """
        return Payment.query.filter_by(order_id=order_id).first()

    @staticmethod
    def get_payment(payment_id: int) -> Optional[Payment]:
        """
        Get payment by ID.

        Args:
            payment_id: Payment ID

        Returns:
            Payment object or None
        """
        return Payment.query.get(payment_id)

    @staticmethod
    def mark_cod_delivered(payment_id: int) -> Dict:
        """
        Mark COD payment as completed when delivered.
        This is a wrapper around complete_payment for COD orders.

        Args:
            payment_id: Payment ID

        Returns:
            dict: Payment completion result
        """
        # Get payment to verify it's COD
        payment = PaymentService.get_payment(payment_id)
        if not payment:
            raise ValueError(f'Payment not found: {payment_id}')

        if payment.payment_method != 'cod':
            raise ValueError(f'Payment is not COD: {payment.payment_method}')

        if payment.status == 'completed':
            return {
                'success': False,
                'error': 'Payment already completed'
            }

        # Complete payment (this will deduct inventory)
        return PaymentService.complete_payment(payment_id)

    @staticmethod
    def process_mpesa_callback(
        payment_id: int,
        transaction_id_encrypted: str,
        mpesa_phone_encrypted: str,
        callback_data: Dict
    ) -> Dict:
        """
        Process M-Pesa STK Push callback.

        Args:
            payment_id: Payment ID
            transaction_id_encrypted: Encrypted M-Pesa transaction ID
            mpesa_phone_encrypted: Encrypted M-Pesa phone number
            callback_data: Full callback data for logging

        Returns:
            dict: Payment completion result
        """
        # Get payment to verify it's M-Pesa
        payment = PaymentService.get_payment(payment_id)
        if not payment:
            raise ValueError(f'Payment not found: {payment_id}')

        if payment.payment_method != 'mpesa':
            raise ValueError(f'Payment is not M-Pesa: {payment.payment_method}')

        if payment.status == 'completed':
            return {
                'success': False,
                'error': 'Payment already completed'
            }

        # Complete payment with M-Pesa details
        return PaymentService.complete_payment(
            payment_id,
            transaction_id_encrypted,
            mpesa_phone_encrypted
        )
