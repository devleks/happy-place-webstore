"""
POS Service
Handles all Point of Sale operations including transactions, shifts, and cash management.
"""

from typing import Dict, List, Optional
from extensions import db


class POSService:
    """Service for POS operations"""

    @staticmethod
    def is_shifts_table_enabled() -> bool:
        """Return True if required POS shifts tables exist in the database."""
        try:
            row = db.session.execute(
                db.text(
                    """
                    SELECT EXISTS(
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'pos_shifts'
                    )
                    """
                )
            ).fetchone()
            return bool(row[0]) if row else False
        except Exception:
            return False

    @staticmethod
    def is_shift_enabled() -> bool:
        """Compatibility alias used by routes; shifts are enabled when shifts tables exist."""
        return POSService.is_shifts_table_enabled()

    @staticmethod
    def create_transaction(
        employee_id: int,
        store_location_id: int,
        shift_id: int,
        payment_method: str,
        items: List[Dict],
        customer_id: Optional[int] = None,
        cash_tendered: Optional[float] = None
    ) -> Dict:
        """
        Create a POS transaction with inventory deduction.

        Args:
            employee_id: Employee processing the transaction
            store_location_id: Store where transaction occurs
            shift_id: Current shift ID
            payment_method: 'cash', 'mpesa', or 'card'
            items: List of items [{variant_id, quantity}, ...]
            customer_id: Optional customer ID
            cash_tendered: Amount tendered if cash payment

        Returns:
            dict: {
                'success': bool,
                'transaction_id': int,
                'transaction_number': str,
                'total': float,
                'change_given': float (if cash)
            }

        Example:
            result = POSService.create_transaction(
                employee_id=1,
                store_location_id=1,
                shift_id=5,
                payment_method='cash',
                items=[
                    {'variant_id': 21, 'quantity': 2},
                    {'variant_id': 35, 'quantity': 1}
                ],
                cash_tendered=10000.00
            )
        """
        try:
            # Convert items to JSONB format
            import json
            items_json = json.dumps(items)

            # Call stored procedure
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_create_pos_transaction(
                        :employee_id,
                        :store_location_id,
                        :shift_id,
                        :payment_method,
                        CAST(:items AS jsonb),
                        :customer_id,
                        :cash_tendered
                    )
                """),
                {
                    'employee_id': employee_id,
                    'store_location_id': store_location_id,
                    'shift_id': shift_id,
                    'payment_method': payment_method,
                    'items': items_json,
                    'customer_id': customer_id,
                    'cash_tendered': cash_tendered
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Transaction creation procedure did not return result')

            result_data = row[0]  # JSONB result
            db.session.commit()

            return result_data

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Transaction creation failed: {str(e)}')

    @staticmethod
    def get_transaction(transaction_id: int) -> Optional[Dict]:
        """
        Get transaction details by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            dict: Transaction details including items
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT
                        pt.id,
                        pt.transaction_number,
                        e.id AS employee_id,
                        e.full_name AS employee_name,
                        sl.id AS store_location_id,
                        sl.name AS store_name,
                        pt.shift_id,
                        ps.shift_number,
                        pt.customer_id,
                        pt.payment_method,
                        pt.subtotal,
                        pt.tax,
                        pt.total,
                        pt.cash_tendered,
                        pt.change_given,
                        pt.status,
                        pt.receipt_printed,
                        pt.receipt_emailed,
                        pt.voided_at,
                        pt.voided_by,
                        pt.void_reason,
                        pt.created_at
                    FROM pos_transactions pt
                    JOIN pos_shifts ps ON ps.id = pt.shift_id
                    JOIN employees e ON e.id = ps.employee_id
                    JOIN store_locations sl ON sl.id = ps.store_location_id
                    WHERE pt.id = :transaction_id
                """),
                {'transaction_id': transaction_id}
            )

            row = result.fetchone()
            if not row:
                return None

            # Get transaction items
            items_result = db.session.execute(
                db.text("""
                    SELECT
                        pti.id,
                        pti.product_id,
                        p.name AS product_name,
                        pv.size,
                        pv.color,
                        pv.sku,
                        pti.quantity,
                        pti.unit_price,
                        pti.total_price
                    FROM pos_transaction_items pti
                    JOIN products p ON p.id = pti.product_id
                    JOIN inventory i ON i.id = pti.inventory_id
                    JOIN product_variants pv ON pv.id = i.variant_id
                    WHERE pti.transaction_id = :transaction_id
                """),
                {'transaction_id': transaction_id}
            )

            items = []
            for item_row in items_result:
                items.append({
                    'id': item_row[0],
                    'product_id': item_row[1],
                    'product_name': item_row[2],
                    'size': item_row[3],
                    'color': item_row[4],
                    'sku': item_row[5],
                    'quantity': item_row[6],
                    'unit_price': float(item_row[7]),
                    'total_price': float(item_row[8])
                })

            return {
                'id': row[0],
                'transaction_number': row[1],
                'employee_id': row[2],
                'employee_name': row[3],
                'store_location_id': row[4],
                'store_name': row[5],
                'shift_id': row[6],
                'shift_number': row[7],
                'customer_id': row[8],
                'payment_method': row[9],
                'subtotal': float(row[10]),
                'tax': float(row[11]),
                'total': float(row[12]),
                'cash_tendered': float(row[13]) if row[13] else None,
                'change_given': float(row[14]) if row[14] else None,
                'status': row[15],
                'receipt_printed': row[16],
                'receipt_emailed': row[17],
                'voided_at': row[18],
                'voided_by': row[19],
                'void_reason': row[20],
                'created_at': row[21],
                'items': items
            }

        except Exception as e:
            raise RuntimeError(f'Failed to get transaction: {str(e)}')

    @staticmethod
    def void_transaction(transaction_id: int, voided_by: int, void_reason: str) -> Dict:
        """
        Void a transaction and restore inventory.

        Args:
            transaction_id: Transaction to void
            voided_by: Employee ID (must be manager/admin)
            void_reason: Reason for voiding

        Returns:
            dict: Void result
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_void_pos_transaction(
                        :transaction_id,
                        :voided_by,
                        :void_reason
                    )
                """),
                {
                    'transaction_id': transaction_id,
                    'voided_by': voided_by,
                    'void_reason': void_reason
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Void procedure did not return result')

            result_data = row[0]
            db.session.commit()

            return result_data

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Transaction void failed: {str(e)}')

    @staticmethod
    def get_todays_transactions(
        store_location_id: Optional[int] = None,
        shift_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all transactions for today.

        Args:
            store_location_id: Filter by store (optional)
            shift_id: Filter by shift (optional)

        Returns:
            list: List of transactions
        """
        try:
            query = """
                SELECT
                    pt.id,
                    pt.transaction_number,
                    e.full_name AS employee_name,
                    pt.payment_method,
                    pt.total,
                    pt.status,
                    pt.voided_at,
                    pt.created_at
                FROM pos_transactions pt
                JOIN employees e ON e.id = pt.employee_id
                WHERE DATE(pt.created_at) = CURRENT_DATE
            """

            params = {}

            if store_location_id:
                query += " AND pt.store_location_id = :store_location_id"
                params['store_location_id'] = store_location_id

            if shift_id:
                query += " AND pt.shift_id = :shift_id"
                params['shift_id'] = shift_id

            query += " ORDER BY pt.created_at DESC"

            result = db.session.execute(db.text(query), params)

            transactions = []
            for row in result:
                transactions.append({
                    'id': row[0],
                    'transaction_number': row[1],
                    'employee_name': row[2],
                    'payment_method': row[3],
                    'total': float(row[4]),
                    'status': row[5],
                    'voided_at': row[6],
                    'created_at': row[7]
                })

            return transactions

        except Exception as e:
            raise RuntimeError(f'Failed to get transactions: {str(e)}')

    @staticmethod
    def start_shift(employee_id: int, store_location_id: int, opening_float: float) -> Dict:
        """
        Start a new shift for an employee.

        Args:
            employee_id: Employee starting shift
            store_location_id: Store location
            opening_float: Starting cash amount

        Returns:
            dict: Shift details
        """
        try:
            # Check if employee already has an open shift
            existing_shift = db.session.execute(
                db.text("""
                    SELECT id FROM pos_shifts
                    WHERE employee_id = :employee_id
                    AND end_time IS NULL
                    LIMIT 1
                """),
                {'employee_id': employee_id}
            ).fetchone()

            if existing_shift:
                return {
                    'success': False,
                    'error': 'Employee already has an open shift'
                }

            # Generate smart shift number with key information markers:
            # Format: YYYYMMDD-LOC{location_id}-EMP{employee_id}-{sequence}
            # Example: 20251205-LOC1-EMP2-001
            # This makes it easy to:
            # - Track shifts by date
            # - Filter by location
            # - Track employee performance
            # - Identify shift sequence for the day
            from datetime import datetime
            
            today = datetime.now().strftime('%Y%m%d')
            
            # Get sequence number for this employee at this location today
            sequence_result = db.session.execute(
                db.text("""
                    SELECT COALESCE(COUNT(*), 0) + 1
                    FROM pos_shifts
                    WHERE employee_id = :employee_id
                    AND store_location_id = :store_location_id
                    AND DATE(start_time) = CURRENT_DATE
                """),
                {
                    'employee_id': employee_id,
                    'store_location_id': store_location_id
                }
            ).fetchone()
            
            sequence = str(sequence_result[0]).zfill(3) if sequence_result else '001'
            shift_number = f"{today}-LOC{store_location_id}-EMP{employee_id}-{sequence}"

            # Insert new shift
            result = db.session.execute(
                db.text("""
                    INSERT INTO pos_shifts (
                        employee_id,
                        store_location_id,
                        shift_number,
                        start_time,
                        opening_float
                    ) VALUES (
                        :employee_id,
                        :store_location_id,
                        :shift_number,
                        NOW(),
                        :opening_float
                    )
                    RETURNING id, shift_number, start_time
                """),
                {
                    'employee_id': employee_id,
                    'store_location_id': store_location_id,
                    'shift_number': shift_number,
                    'opening_float': opening_float
                }
            )

            row = result.fetchone()
            db.session.commit()

            return {
                'success': True,
                'shift': {
                    'shift_id': row[0],
                    'shift_number': row[1],
                    'start_time': row[2].isoformat(),
                    'opening_float': float(opening_float),
                    'total_sales': 0.0,
                    'transaction_count': 0,
                    'cash_sales': 0.0,
                    'mpesa_sales': 0.0,
                    'card_sales': 0.0
                }
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Start shift failed: {str(e)}'
            }

    @staticmethod
    def close_shift(shift_id: int, closing_cash: float, notes: Optional[str] = None) -> Dict:
        """
        Close a shift with cash reconciliation.

        Args:
            shift_id: Shift to close
            closing_cash: Actual cash counted
            notes: Optional notes about discrepancies

        Returns:
            dict: Closing summary with variance
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_close_shift(
                        :shift_id,
                        :closing_cash,
                        :notes
                    )
                """),
                {
                    'shift_id': shift_id,
                    'closing_cash': closing_cash,
                    'notes': notes
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Close shift procedure did not return result')

            result_data = row[0]
            db.session.commit()

            return result_data

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Close shift failed: {str(e)}')

    @staticmethod
    def get_shift_summary(shift_id: int) -> Dict:
        """
        Get shift statistics and summary.

        Args:
            shift_id: Shift ID

        Returns:
            dict: Comprehensive shift summary
        """
        try:
            result = db.session.execute(
                db.text("SELECT * FROM sp_get_shift_summary(:shift_id)"),
                {'shift_id': shift_id}
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Get shift summary procedure did not return result')

            return row[0]  # JSONB result

        except Exception as e:
            raise RuntimeError(f'Failed to get shift summary: {str(e)}')

    @staticmethod
    def get_current_shift(employee_id: int) -> Optional[Dict]:
        """
        Get current open shift for an employee.

        Args:
            employee_id: Employee ID

        Returns:
            dict: Shift details or None if no open shift
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT
                        ps.id,
                        ps.shift_number,
                        ps.start_time,
                        ps.opening_float,
                        COALESCE(SUM(CASE WHEN pt.status != 'voided' THEN pt.total ELSE 0 END), 0) as total_sales,
                        COUNT(CASE WHEN pt.status != 'voided' THEN pt.id END) as transaction_count,
                        COALESCE(SUM(CASE WHEN pt.payment_method = 'cash' AND pt.status != 'voided' THEN pt.total ELSE 0 END), 0) as cash_sales,
                        COALESCE(SUM(CASE WHEN pt.payment_method = 'mpesa' AND pt.status != 'voided' THEN pt.total ELSE 0 END), 0) as mpesa_sales,
                        COALESCE(SUM(CASE WHEN pt.payment_method = 'card' AND pt.status != 'voided' THEN pt.total ELSE 0 END), 0) as card_sales
                    FROM pos_shifts ps
                    LEFT JOIN pos_transactions pt ON pt.shift_id = ps.id
                    WHERE ps.employee_id = :employee_id
                      AND ps.end_time IS NULL
                    GROUP BY ps.id, ps.shift_number, ps.start_time, ps.opening_float
                    ORDER BY ps.start_time DESC
                    LIMIT 1
                """),
                {'employee_id': employee_id}
            )

            row = result.fetchone()
            if not row:
                return None

            return {
                'shift_id': row[0],
                'shift_number': row[1],
                'start_time': row[2].isoformat(),
                'opening_float': float(row[3]),
                'total_sales': float(row[4]),
                'transaction_count': row[5],
                'cash_sales': float(row[6]),
                'mpesa_sales': float(row[7]),
                'card_sales': float(row[8])
            }

        except Exception as e:
            print(f"[ERROR] get_current_shift: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_shift_by_id(shift_id: int) -> Optional[Dict]:
        """
        Get shift details by ID.

        Args:
            shift_id: Shift ID

        Returns:
            dict: Shift details or None if not found
        """
        try:
            # Simplified query - get shift data first without aggregations
            result = db.session.execute(
                db.text("""
                    SELECT
                        ps.id,
                        ps.shift_number,
                        ps.employee_id,
                        e.full_name AS employee_name,
                        ps.store_location_id,
                        COALESCE(sl.name, 'Unknown Location') AS store_name,
                        ps.start_time,
                        ps.end_time,
                        ps.opening_float,
                        ps.closing_cash,
                        ps.expected_cash,
                        CASE 
                            WHEN ps.closing_cash IS NOT NULL AND ps.expected_cash IS NOT NULL 
                            THEN ps.closing_cash - ps.expected_cash
                            ELSE NULL
                        END as cash_variance,
                        ps.notes
                    FROM pos_shifts ps
                    JOIN employees e ON e.id = ps.employee_id
                    LEFT JOIN store_locations sl ON sl.id = ps.store_location_id
                    WHERE ps.id = :shift_id
                """),
                {'shift_id': shift_id}
            )

            row = result.fetchone()
            if not row:
                return None

            # Get transaction stats separately to avoid complex GROUP BY
            stats_result = db.session.execute(
                db.text("""
                    SELECT
                        COALESCE(SUM(CASE WHEN status != 'voided' THEN total ELSE 0 END), 0) as total_sales,
                        COUNT(CASE WHEN status != 'voided' THEN id END) as transaction_count,
                        COALESCE(SUM(CASE WHEN payment_method = 'cash' AND status != 'voided' THEN total ELSE 0 END), 0) as cash_sales,
                        COALESCE(SUM(CASE WHEN payment_method = 'mpesa' AND status != 'voided' THEN total ELSE 0 END), 0) as mpesa_sales,
                        COALESCE(SUM(CASE WHEN payment_method = 'card' AND status != 'voided' THEN total ELSE 0 END), 0) as card_sales
                    FROM pos_transactions
                    WHERE shift_id = :shift_id
                """),
                {'shift_id': shift_id}
            )
            
            stats_row = stats_result.fetchone()

            return {
                'shift_id': row[0],
                'shift_number': row[1],
                'employee_id': row[2],
                'employee_name': row[3],
                'store_location_id': row[4],
                'store_name': row[5],
                'start_time': row[6].isoformat() if row[6] else None,
                'end_time': row[7].isoformat() if row[7] else None,
                'opening_float': float(row[8]) if row[8] else 0,
                'closing_cash': float(row[9]) if row[9] else None,
                'expected_cash': float(row[10]) if row[10] else None,
                'cash_variance': float(row[11]) if row[11] else None,
                'notes': row[12],
                'total_sales': float(stats_row[0]) if stats_row else 0,
                'transaction_count': stats_row[1] if stats_row else 0,
                'cash_sales': float(stats_row[2]) if stats_row else 0,
                'mpesa_sales': float(stats_row[3]) if stats_row else 0,
                'card_sales': float(stats_row[4]) if stats_row else 0
            }

        except Exception as e:
            print(f"[ERROR] get_shift_by_id for shift_id={shift_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_shift_transactions(shift_id: int) -> List[Dict]:
        """
        Get all transactions for a specific shift.

        Args:
            shift_id: Shift ID

        Returns:
            list: List of transactions
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT
                        pt.id,
                        pt.transaction_number,
                        e.full_name AS employee_name,
                        pt.payment_method,
                        pt.subtotal,
                        pt.tax,
                        pt.total,
                        pt.status,
                        pt.voided_at,
                        pt.created_at
                    FROM pos_transactions pt
                    JOIN pos_shifts ps ON ps.id = pt.shift_id
                    JOIN employees e ON e.id = ps.employee_id
                    WHERE pt.shift_id = :shift_id
                    ORDER BY pt.created_at DESC
                """),
                {'shift_id': shift_id}
            )

            transactions = []
            for row in result:
                transactions.append({
                    'id': row[0],
                    'transaction_number': row[1],
                    'employee_name': row[2],
                    'payment_method': row[3],
                    'subtotal': float(row[4]),
                    'tax': float(row[5]),
                    'total': float(row[6]),
                    'status': row[7],
                    'voided_at': row[8],
                    'created_at': row[9]
                })

            return transactions

        except Exception as e:
            print(f"[ERROR] get_shift_transactions: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def record_cash_movement(
        shift_id: int,
        movement_type: str,
        amount: float,
        reason: str,
        performed_by: int
    ) -> int:
        """
        Record a cash in/out movement.

        Args:
            shift_id: Current shift
            movement_type: 'cash_in' or 'cash_out'
            amount: Amount
            reason: Reason for movement
            performed_by: Employee ID

        Returns:
            int: Movement ID
        """
        try:
            result = db.session.execute(
                db.text("""
                    INSERT INTO pos_cash_movements (
                        shift_id,
                        movement_type,
                        amount,
                        reason,
                        created_at
                    ) VALUES (
                        :shift_id,
                        :movement_type,
                        :amount,
                        :reason,
                        NOW()
                    ) RETURNING id
                """),
                {
                    'shift_id': shift_id,
                    'movement_type': movement_type,
                    'amount': amount,
                    'reason': reason
                }
            )

            row = result.fetchone()
            movement_id = row[0] if row else None

            db.session.commit()
            return movement_id

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Cash movement recording failed: {str(e)}')

    @staticmethod
    def mark_receipt_printed(transaction_id: int) -> bool:
        """
        Mark a transaction receipt as printed.

        Args:
            transaction_id: Transaction ID

        Returns:
            bool: Success
        """
        try:
            db.session.execute(
                db.text("""
                    UPDATE pos_transactions
                    SET receipt_printed = TRUE
                    WHERE id = :transaction_id
                """),
                {'transaction_id': transaction_id}
            )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Failed to mark receipt printed: {str(e)}')

    @staticmethod
    def mark_receipt_emailed(transaction_id: int) -> bool:
        """
        Mark a transaction receipt as emailed.

        Args:
            transaction_id: Transaction ID

        Returns:
            bool: Success
        """
        try:
            db.session.execute(
                db.text("""
                    UPDATE pos_transactions
                    SET receipt_emailed = TRUE
                    WHERE id = :transaction_id
                """),
                {'transaction_id': transaction_id}
            )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Failed to mark receipt emailed: {str(e)}')
