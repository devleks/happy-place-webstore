"""
GDPR Service
Handles GDPR compliance operations using stored procedures.
Implements EU General Data Protection Regulation requirements.
"""

from typing import Dict, Optional
from extensions import db
from models.database_models import Customer


class GDPRService:
    """Service for GDPR compliance operations"""

    @staticmethod
    def export_customer_data(
        customer_id: int,
        requested_by: Optional[int] = None,
        reason: str = 'customer_request'
    ) -> Dict:
        """
        Export all customer data (GDPR Right to Access - Article 15).

        Returns complete personal data export in machine-readable format including:
        - Customer profile
        - Addresses
        - Order history
        - Consent history

        Args:
            customer_id: Customer ID to export
            requested_by: Employee ID if admin-requested, None for self-service
            reason: Reason for export request

        Returns:
            dict: Complete data export with all personal information

        Raises:
            ValueError: If customer not found
            RuntimeError: If export fails
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_gdpr_export_customer_data(
                        :customer_id,
                        :requested_by,
                        :reason
                    )
                """),
                {
                    'customer_id': customer_id,
                    'requested_by': requested_by,
                    'reason': reason
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Export procedure did not return result')

            export_data = row[0]  # JSONB result

            db.session.commit()

            return {
                'success': True,
                'export_data': export_data,
                'message': 'Data export completed successfully'
            }

        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            if 'Customer not found' in error_msg:
                raise ValueError(error_msg)
            raise RuntimeError(f'Data export failed: {error_msg}')

    @staticmethod
    def anonymize_customer(
        customer_id: int,
        requested_by: Optional[int] = None,
        reason: str = 'customer_request'
    ) -> Dict:
        """
        Anonymize customer data (GDPR Right to be Forgotten - Article 17).

        Anonymizes personal data while preserving order history for accounting.
        Business rules:
        - Cannot anonymize customers with outstanding orders
        - Addresses are deleted
        - Cart and wishlist are cleared
        - Order addresses are anonymized
        - Customer profile is anonymized

        Args:
            customer_id: Customer ID to anonymize
            requested_by: Employee ID if admin-requested, None for self-service
            reason: Reason for anonymization

        Returns:
            dict: Anonymization result with counts of affected records

        Raises:
            ValueError: If customer not found or has outstanding orders
            RuntimeError: If anonymization fails
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_gdpr_anonymize_customer(
                        :customer_id,
                        :requested_by,
                        :reason
                    )
                """),
                {
                    'customer_id': customer_id,
                    'requested_by': requested_by,
                    'reason': reason
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Anonymization procedure did not return result')

            result_data = row[0]  # JSONB result

            db.session.commit()

            return {
                'success': result_data.get('success', False),
                'customer_id': result_data.get('customer_id'),
                'anonymized_at': result_data.get('anonymized_at'),
                'addresses_deleted': result_data.get('addresses_deleted', 0),
                'cart_items_cleared': result_data.get('cart_items_cleared', 0),
                'wishlist_items_cleared': result_data.get('wishlist_items_cleared', 0),
                'orders_anonymized': result_data.get('orders_anonymized', 0),
                'message': result_data.get('message', 'Customer anonymized successfully')
            }

        except Exception as e:
            db.session.rollback()
            error_msg = str(e)

            # Check for business rule violations
            if 'outstanding orders' in error_msg.lower():
                raise ValueError(error_msg)
            if 'not found' in error_msg.lower() or 'already anonymized' in error_msg.lower():
                raise ValueError(error_msg)

            raise RuntimeError(f'Anonymization failed: {error_msg}')

    @staticmethod
    def delete_customer(
        customer_id: int,
        requested_by: int,
        reason: str,
        confirmation_code: str
    ) -> Dict:
        """
        Completely delete customer and all related data.

        WARNING: This is irreversible and deletes ALL data including order history.
        Use anonymize_customer() instead to preserve order records for accounting.

        Requires:
        - Admin/Super Admin permissions
        - Confirmation code 'DELETE'

        Args:
            customer_id: Customer ID to delete
            requested_by: Employee ID (must be admin)
            reason: Detailed reason for deletion
            confirmation_code: Must be 'DELETE' to proceed

        Returns:
            dict: Deletion result

        Raises:
            ValueError: If permissions insufficient or confirmation invalid
            RuntimeError: If deletion fails
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_gdpr_delete_customer(
                        :customer_id,
                        :requested_by,
                        :reason,
                        :confirmation_code
                    )
                """),
                {
                    'customer_id': customer_id,
                    'requested_by': requested_by,
                    'reason': reason,
                    'confirmation_code': confirmation_code
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Deletion procedure did not return result')

            result_data = row[0]  # JSONB result

            db.session.commit()

            return {
                'success': result_data.get('success', False),
                'customer_id': result_data.get('customer_id'),
                'deleted_at': result_data.get('deleted_at'),
                'email': result_data.get('email'),
                'orders_deleted': result_data.get('orders_deleted', 0),
                'message': result_data.get('message', 'Customer deleted successfully')
            }

        except Exception as e:
            db.session.rollback()
            error_msg = str(e)

            # Check for authorization/validation errors
            if 'insufficient permissions' in error_msg.lower():
                raise ValueError('Insufficient permissions. Only admins can delete customer data.')
            if 'invalid confirmation' in error_msg.lower():
                raise ValueError('Invalid confirmation code. Must be "DELETE" to proceed.')
            if 'not found' in error_msg.lower():
                raise ValueError(error_msg)

            raise RuntimeError(f'Deletion failed: {error_msg}')

    @staticmethod
    def check_request_status(
        customer_id: int,
        request_type: Optional[str] = None
    ) -> Dict:
        """
        Check status of GDPR requests for a customer.

        Args:
            customer_id: Customer ID
            request_type: Optional filter ('export', 'anonymization', 'deletion')

        Returns:
            dict: Request status including pending and recent requests

        Raises:
            RuntimeError: If check fails
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_gdpr_check_request_status(
                        :customer_id,
                        :request_type
                    )
                """),
                {
                    'customer_id': customer_id,
                    'request_type': request_type
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Status check procedure did not return result')

            status_data = row[0]  # JSONB result

            db.session.commit()

            return {
                'success': True,
                'customer_id': status_data.get('customer_id'),
                'pending_requests': status_data.get('pending_requests', 0),
                'recent_requests': status_data.get('recent_requests', []),
                'checked_at': status_data.get('checked_at')
            }

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Status check failed: {str(e)}')

    @staticmethod
    def validate_anonymization_eligibility(customer_id: int) -> Dict:
        """
        Check if customer can be anonymized (no outstanding orders).

        Args:
            customer_id: Customer ID

        Returns:
            dict: {
                'eligible': bool,
                'reason': str,
                'outstanding_orders': int
            }
        """
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'eligible': False,
                'reason': 'Customer not found',
                'outstanding_orders': 0
            }

        if customer.anonymized:
            return {
                'eligible': False,
                'reason': 'Customer already anonymized',
                'outstanding_orders': 0
            }

        # Count outstanding orders
        outstanding = db.session.execute(
            db.text("""
                SELECT COUNT(*)
                FROM orders
                WHERE customer_id = :customer_id
                  AND status IN ('pending', 'processing', 'shipped')
            """),
            {'customer_id': customer_id}
        ).scalar()

        if outstanding > 0:
            return {
                'eligible': False,
                'reason': f'Customer has {outstanding} outstanding orders',
                'outstanding_orders': outstanding
            }

        return {
            'eligible': True,
            'reason': 'Customer eligible for anonymization',
            'outstanding_orders': 0
        }
