"""
Return Service
Handles product returns using stored procedures for business rule enforcement.
"""

import json
from typing import Dict, List, Optional
from extensions import db
from models.database_models import Order


class ReturnService:
    """Service for return processing"""

    @staticmethod
    def create_return(
        order_id: int,
        customer_id: int,
        reason: str,
        reason_description: str,
        return_items: List[Dict],
        approved_by: Optional[int] = None
    ) -> Dict:
        """
        Create product return using stored procedure.

        Business rules enforced by stored procedure:
        - 30-day return window
        - Cannot return cancelled/returned orders
        - Validates return quantities don't exceed purchased
        - Applies 15% restocking fee for used/damaged items
        - Restores inventory for items in 'new' condition (if approved)

        Args:
            order_id: Order ID
            customer_id: Customer ID (for authorization)
            reason: Return reason code
            reason_description: Detailed reason description
            return_items: List of dicts with:
                - order_item_id: int
                - quantity: int
                - condition: str ('new', 'used', 'damaged')
            approved_by: Optional employee ID (auto-approves if provided)

        Returns:
            dict: {
                'success': bool,
                'return_id': int,
                'return_number': str,
                'refund_amount': float,
                'restocking_fee': float,
                'message': str,
                'error': str (if failed)
            }

        Raises:
            ValueError: If validation fails
            RuntimeError: If return processing fails
        """
        try:
            # Convert return items to JSON string for PostgreSQL
            return_items_jsonb = json.dumps(return_items)

            # Call stored procedure for atomic return processing
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_process_return_secure(
                        :order_id,
                        :customer_id,
                        :reason,
                        :reason_description,
                        CAST(:return_items AS jsonb),
                        :approved_by
                    )
                """),
                {
                    'order_id': order_id,
                    'customer_id': customer_id,
                    'reason': reason,
                    'reason_description': reason_description,
                    'return_items': return_items_jsonb,
                    'approved_by': approved_by
                }
            )

            # Fetch result
            row = result.fetchone()
            if not row:
                raise RuntimeError('Stored procedure did not return result')

            return_id = row[0]
            return_number = row[1]
            refund_amount = row[2]
            restocking_fee = row[3]
            message = row[4]

            # Commit transaction
            db.session.commit()

            return {
                'success': True,
                'return_id': return_id,
                'return_number': return_number,
                'refund_amount': float(refund_amount),
                'restocking_fee': float(restocking_fee),
                'message': message
            }

        except Exception as e:
            db.session.rollback()
            # Check if it's a business rule violation
            error_msg = str(e)
            if 'expired' in error_msg.lower() or 'window' in error_msg.lower():
                return {
                    'success': False,
                    'error': error_msg
                }
            elif 'cannot return' in error_msg.lower():
                return {
                    'success': False,
                    'error': error_msg
                }
            else:
                raise RuntimeError(f'Return processing failed: {error_msg}')

    @staticmethod
    def validate_return_eligibility(order_id: int, customer_id: int) -> Dict:
        """
        Check if an order is eligible for return.

        Args:
            order_id: Order ID
            customer_id: Customer ID

        Returns:
            dict: {
                'eligible': bool,
                'message': str,
                'days_remaining': int (if eligible)
            }
        """
        # Get order
        order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()

        if not order:
            return {
                'eligible': False,
                'message': 'Order not found or does not belong to customer'
            }

        # Check status
        if order.status in ('cancelled', 'returned'):
            return {
                'eligible': False,
                'message': f'Cannot return order with status: {order.status}'
            }

        # Check return window (30 days)
        from datetime import datetime
        order_date = order.created_at
        today = datetime.utcnow()
        days_since_order = (today - order_date).days

        if days_since_order > 30:
            return {
                'eligible': False,
                'message': f'Return window expired. Order is {days_since_order} days old (max 30 days)'
            }

        return {
            'eligible': True,
            'message': 'Order is eligible for return',
            'days_remaining': 30 - days_since_order
        }
