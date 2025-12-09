"""
Inventory Service
Handles inventory operations with channel tracking and audit trails.
Implements Phase 1 inventory enhancements.
"""

from typing import Dict, List, Optional
from extensions import db
from datetime import datetime, timedelta


class InventoryService:
    """Service for inventory management operations with channel awareness"""

    @staticmethod
    def get_available_inventory(variant_id: int, channel: str = 'online') -> int:
        """
        Get available inventory for a specific channel.

        Takes into account:
        - Total quantity
        - Reserved quantity
        - Store display units (online only)
        - Active reservations

        Args:
            variant_id: Product variant ID
            channel: 'online', 'store', or 'pos'

        Returns:
            int: Available quantity for the channel

        Example:
            available = InventoryService.get_available_inventory(123, 'online')
        """
        try:
            result = db.session.execute(
                db.text("SELECT sp_get_available_inventory(:variant_id, :channel)"),
                {'variant_id': variant_id, 'channel': channel}
            )

            row = result.fetchone()
            return row[0] if row else 0

        except Exception as e:
            raise RuntimeError(f'Failed to get available inventory: {str(e)}')

    @staticmethod
    def deduct_inventory(
        variant_id: int,
        quantity: int,
        channel: str,
        reference_type: str,
        reference_id: int,
        performed_by: Optional[int] = None,
        customer_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Deduct inventory and log the movement.

        Automatically:
        - Checks availability for channel
        - Deducts from inventory
        - Logs movement to inventory_movements
        - Updates inventory timestamp

        Args:
            variant_id: Product variant ID
            quantity: Quantity to deduct
            channel: 'online', 'store', or 'pos'
            reference_type: 'order', 'transaction', 'return'
            reference_id: ID of the reference (order_id, transaction_id)
            performed_by: Employee ID (optional)
            customer_id: Customer ID (optional)
            notes: Additional notes (optional)

        Returns:
            dict: {
                'success': bool,
                'movement_id': int (if successful),
                'new_quantity': int (if successful),
                'error': str (if failed)
            }

        Raises:
            ValueError: If insufficient inventory
            RuntimeError: If operation fails

        Example:
            result = InventoryService.deduct_inventory(
                variant_id=123,
                quantity=2,
                channel='online',
                reference_type='order',
                reference_id=456,
                customer_id=789
            )
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_deduct_inventory(
                        :variant_id,
                        :quantity,
                        :channel,
                        :reference_type,
                        :reference_id,
                        :performed_by,
                        :customer_id,
                        :notes
                    )
                """),
                {
                    'variant_id': variant_id,
                    'quantity': quantity,
                    'channel': channel,
                    'reference_type': reference_type,
                    'reference_id': reference_id,
                    'performed_by': performed_by,
                    'customer_id': customer_id,
                    'notes': notes
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Deduct inventory procedure did not return result')

            result_data = row[0]  # JSONB result
            db.session.commit()

            if not result_data.get('success'):
                raise ValueError(result_data.get('error', 'Insufficient inventory'))

            return {
                'success': True,
                'movement_id': result_data.get('movement_id'),
                'new_quantity': result_data.get('new_quantity'),
                'deducted': result_data.get('deducted')
            }

        except ValueError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Inventory deduction failed: {str(e)}')

    @staticmethod
    def add_inventory(
        variant_id: int,
        quantity: int,
        channel: str = 'admin',
        movement_type: str = 'restock',
        performed_by: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Add inventory and log the movement.

        Use cases:
        - Restocking from supplier
        - Returns from customers
        - Inventory adjustments
        - Stock transfers

        Args:
            variant_id: Product variant ID
            quantity: Quantity to add
            channel: 'admin', 'store', 'online'
            movement_type: 'restock', 'return', 'adjustment', 'transfer'
            performed_by: Employee ID (optional)
            notes: Additional notes (optional)

        Returns:
            dict: {
                'success': bool,
                'movement_id': int,
                'new_quantity': int,
                'added': int
            }

        Raises:
            RuntimeError: If operation fails

        Example:
            result = InventoryService.add_inventory(
                variant_id=123,
                quantity=50,
                movement_type='restock',
                performed_by=1,
                notes='Weekly restock from supplier'
            )
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_add_inventory(
                        :variant_id,
                        :quantity,
                        :channel,
                        :movement_type,
                        :performed_by,
                        :notes
                    )
                """),
                {
                    'variant_id': variant_id,
                    'quantity': quantity,
                    'channel': channel,
                    'movement_type': movement_type,
                    'performed_by': performed_by,
                    'notes': notes
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Add inventory procedure did not return result')

            result_data = row[0]  # JSONB result
            db.session.commit()

            return {
                'success': True,
                'movement_id': result_data.get('movement_id'),
                'new_quantity': result_data.get('new_quantity'),
                'added': result_data.get('added')
            }

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Inventory addition failed: {str(e)}')

    @staticmethod
    def log_movement(
        variant_id: int,
        movement_type: str,
        channel: str,
        quantity: int,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        performed_by: Optional[int] = None,
        customer_id: Optional[int] = None,
        from_location: Optional[str] = None,
        to_location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Log an inventory movement without changing inventory quantity.

        Use for tracking movements that don't affect total quantity,
        such as transfers between locations.

        Args:
            variant_id: Product variant ID
            movement_type: Type of movement
            channel: Channel performing the movement
            quantity: Quantity moved (can be negative)
            reference_type: Optional reference type
            reference_id: Optional reference ID
            performed_by: Employee ID (optional)
            customer_id: Customer ID (optional)
            from_location: Source location
            to_location: Destination location
            notes: Additional notes

        Returns:
            int: Movement ID

        Example:
            movement_id = InventoryService.log_movement(
                variant_id=123,
                movement_type='transfer',
                channel='admin',
                quantity=10,
                from_location='warehouse',
                to_location='store',
                performed_by=1,
                notes='Weekly store transfer'
            )
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT sp_log_inventory_movement(
                        :variant_id,
                        :movement_type,
                        :channel,
                        :quantity,
                        :reference_type,
                        :reference_id,
                        :performed_by,
                        :customer_id,
                        :from_location,
                        :to_location,
                        :notes
                    )
                """),
                {
                    'variant_id': variant_id,
                    'movement_type': movement_type,
                    'channel': channel,
                    'quantity': quantity,
                    'reference_type': reference_type,
                    'reference_id': reference_id,
                    'performed_by': performed_by,
                    'customer_id': customer_id,
                    'from_location': from_location,
                    'to_location': to_location,
                    'notes': notes
                }
            )

            row = result.fetchone()
            movement_id = row[0] if row else None

            db.session.commit()
            return movement_id

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Movement logging failed: {str(e)}')

    @staticmethod
    def get_inventory_summary(variant_id: int) -> Optional[Dict]:
        """
        Get comprehensive inventory summary for a variant.

        Returns:
            dict with keys:
            - total_quantity
            - reserved_quantity
            - store_display_units
            - online_available
            - store_available
            - stock_status
            - product_name, size, color, sku

        Example:
            summary = InventoryService.get_inventory_summary(123)
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM v_inventory_summary
                    WHERE variant_id = :variant_id
                """),
                {'variant_id': variant_id}
            )

            row = result.fetchone()
            if not row:
                return None

            return {
                'variant_id': row.variant_id,
                'product_name': row.product_name,
                'size': row.size,
                'color': row.color,
                'sku': row.sku,
                'total_quantity': row.total_quantity,
                'reserved_quantity': row.reserved_quantity,
                'store_display_units': row.store_display_units,
                'online_reserved': row.online_reserved,
                'store_reserved': row.store_reserved,
                'online_available': row.online_available,
                'store_available': row.store_available,
                'stock_status': row.stock_status,
                'primary_location': row.primary_location,
                'last_restocked_at': row.last_restocked_at,
                'updated_at': row.updated_at
            }

        except Exception as e:
            raise RuntimeError(f'Failed to get inventory summary: {str(e)}')

    @staticmethod
    def get_movement_history(
        variant_id: Optional[int] = None,
        channel: Optional[str] = None,
        movement_type: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get inventory movement history with filters.

        Args:
            variant_id: Filter by variant (optional)
            channel: Filter by channel (optional)
            movement_type: Filter by movement type (optional)
            days: Number of days to look back (default 30)
            limit: Maximum results (default 100)

        Returns:
            List of movement dictionaries

        Example:
            # Get last 30 days of online sales
            movements = InventoryService.get_movement_history(
                channel='online',
                movement_type='sale',
                days=30
            )
        """
        try:
            query = """
                SELECT * FROM v_inventory_movements_summary
                WHERE created_at >= :since
            """

            params = {'since': datetime.now() - timedelta(days=days)}

            if variant_id:
                query += " AND variant_id = :variant_id"
                params['variant_id'] = variant_id

            if channel:
                query += " AND channel = :channel"
                params['channel'] = channel

            if movement_type:
                query += " AND movement_type = :movement_type"
                params['movement_type'] = movement_type

            query += " ORDER BY created_at DESC LIMIT :limit"
            params['limit'] = limit

            result = db.session.execute(db.text(query), params)

            movements = []
            for row in result:
                movements.append({
                    'product_name': row.product_name,
                    'sku': row.sku,
                    'size': row.size,
                    'color': row.color,
                    'movement_type': row.movement_type,
                    'channel': row.channel,
                    'quantity': row.quantity,
                    'quantity_before': row.quantity_before,
                    'quantity_after': row.quantity_after,
                    'reference_type': row.reference_type,
                    'reference_id': row.reference_id,
                    'performed_by': row.performed_by_email,
                    'notes': row.notes,
                    'created_at': row.created_at
                })

            return movements

        except Exception as e:
            raise RuntimeError(f'Failed to get movement history: {str(e)}')

    @staticmethod
    def set_display_units(variant_id: int, quantity: int, performed_by: int) -> Dict:
        """
        Set the number of display units for a variant.

        Display units are reserved for in-store display and cannot be sold online.

        Args:
            variant_id: Product variant ID
            quantity: Number of display units
            performed_by: Employee ID

        Returns:
            dict: Updated inventory info

        Example:
            result = InventoryService.set_display_units(
                variant_id=123,
                quantity=2,
                performed_by=1
            )
        """
        try:
            # Update display units
            result = db.session.execute(
                db.text("""
                    UPDATE inventory
                    SET store_display_units = :quantity,
                        updated_at = NOW()
                    WHERE variant_id = :variant_id
                    RETURNING quantity, store_display_units
                """),
                {'variant_id': variant_id, 'quantity': quantity}
            )

            row = result.fetchone()
            if not row:
                raise ValueError(f'Variant {variant_id} not found in inventory')

            # Log the change
            InventoryService.log_movement(
                variant_id=variant_id,
                movement_type='display_set',
                channel='admin',
                quantity=quantity,
                performed_by=performed_by,
                notes=f'Set display units to {quantity}'
            )

            db.session.commit()

            return {
                'success': True,
                'variant_id': variant_id,
                'total_quantity': row[0],
                'store_display_units': row[1]
            }

        except ValueError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Failed to set display units: {str(e)}')

    @staticmethod
    def cleanup_expired_reservations() -> int:
        """
        Clean up expired reservations.

        Should be run periodically (e.g., every 15 minutes via cron job).

        Returns:
            int: Number of reservations expired

        Example:
            expired_count = InventoryService.cleanup_expired_reservations()
        """
        try:
            result = db.session.execute(
                db.text("SELECT sp_cleanup_expired_reservations()")
            )

            row = result.fetchone()
            expired_count = row[0] if row else 0

            db.session.commit()
            return expired_count

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Cleanup failed: {str(e)}')
