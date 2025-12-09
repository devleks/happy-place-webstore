"""
Kiosk Service
Handles cashier kiosk operations including hold/recall, quick access, barcodes, and metrics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db
from sqlalchemy import text


class KioskService:
    """Service for cashier kiosk operations"""

    # ============================================================================
    # BARCODE / QUICK LOOKUP
    # ============================================================================

    @staticmethod
    def scan_barcode(barcode: str) -> Optional[Dict]:
        """
        Scan barcode and return product/variant information

        Args:
            barcode: Barcode string

        Returns:
            Product variant details or None
        """
        try:
            result = db.session.execute(
                text("""
                    SELECT
                        pb.barcode,
                        pb.barcode_type,
                        pv.id as variant_id,
                        pv.sku,
                        pv.size,
                        pv.color,
                        p.id as product_id,
                        p.name as product_name,
                        p.slug,
                        p.price,
                        p.sale_price,
                        COALESCE(p.sale_price, p.price) as effective_price,
                        i.quantity as stock_quantity,
                        i.quantity - i.reserved_quantity as available_quantity,
                        (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = TRUE LIMIT 1) as image_url
                    FROM product_barcodes pb
                    JOIN product_variants pv ON pv.id = pb.variant_id
                    JOIN products p ON p.id = pv.product_id
                    LEFT JOIN inventory i ON i.variant_id = pv.id
                    WHERE pb.barcode = :barcode
                      AND p.is_active = TRUE
                      AND pv.is_active = TRUE
                    LIMIT 1
                """),
                {'barcode': barcode}
            ).fetchone()

            if result:
                return {
                    'variant_id': result[2],
                    'sku': result[3],
                    'size': result[4],
                    'color': result[5],
                    'product_id': result[6],
                    'product_name': result[7],
                    'slug': result[8],
                    'price': float(result[9]),
                    'sale_price': float(result[10]) if result[10] else None,
                    'effective_price': float(result[11]),
                    'stock_quantity': result[12] if result[12] else 0,
                    'available_quantity': result[13] if result[13] else 0,
                    'image_url': result[14],
                    'in_stock': (result[13] or 0) > 0
                }

            return None

        except Exception as e:
            print(f"[ERROR] scan_barcode: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def quick_product_lookup(sku: str) -> Optional[Dict]:
        """
        Quick product lookup by SKU

        Args:
            sku: Product SKU

        Returns:
            Product variant details or None
        """
        try:
            result = db.session.execute(
                text("""
                    SELECT
                        pv.id as variant_id,
                        pv.sku,
                        pv.size,
                        pv.color,
                        p.id as product_id,
                        p.name as product_name,
                        p.slug,
                        p.price,
                        p.sale_price,
                        COALESCE(p.sale_price, p.price) as effective_price,
                        i.quantity as stock_quantity,
                        i.quantity - i.reserved_quantity as available_quantity,
                        (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = TRUE LIMIT 1) as image_url
                    FROM product_variants pv
                    JOIN products p ON p.id = pv.product_id
                    LEFT JOIN inventory i ON i.variant_id = pv.id
                    WHERE pv.sku = :sku
                      AND p.is_active = TRUE
                      AND pv.is_active = TRUE
                    LIMIT 1
                """),
                {'sku': sku}
            ).fetchone()

            if result:
                return {
                    'variant_id': result[0],
                    'sku': result[1],
                    'size': result[2],
                    'color': result[3],
                    'product_id': result[4],
                    'product_name': result[5],
                    'slug': result[6],
                    'price': float(result[7]),
                    'sale_price': float(result[8]) if result[8] else None,
                    'effective_price': float(result[9]),
                    'stock_quantity': result[10] if result[10] else 0,
                    'available_quantity': result[11] if result[11] else 0,
                    'image_url': result[12],
                    'in_stock': (result[11] or 0) > 0
                }

            return None

        except Exception as e:
            print(f"[ERROR] quick_product_lookup: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    # ============================================================================
    # HOLD / RECALL TRANSACTIONS
    # ============================================================================

    @staticmethod
    def hold_transaction(
        employee_id: int,
        shift_id: int,
        items: List[Dict],
        subtotal: float,
        tax: float,
        total: float,
        customer_note: str = None
    ) -> Dict:
        """
        Hold current transaction to serve another customer

        Args:
            employee_id: Employee holding the transaction
            shift_id: Current shift ID
            items: List of cart items
            subtotal: Subtotal amount
            tax: Tax amount
            total: Total amount
            customer_note: Optional note

        Returns:
            Success status and hold reference
        """
        try:
            import json

            # Insert held transaction (trigger will generate hold_reference)
            result = db.session.execute(
                text("""
                    INSERT INTO held_transactions (
                        employee_id, shift_id, items, subtotal, tax, total, customer_note, hold_reference
                    )
                    VALUES (
                        :employee_id, :shift_id, CAST(:items AS jsonb), :subtotal, :tax, :total, :customer_note,
                        (SELECT generate_hold_reference())
                    )
                    RETURNING id, hold_reference
                """),
                {
                    'employee_id': employee_id,
                    'shift_id': shift_id,
                    'items': json.dumps(items),
                    'subtotal': subtotal,
                    'tax': tax,
                    'total': total,
                    'customer_note': customer_note
                }
            ).fetchone()

            db.session.commit()

            return {
                'success': True,
                'hold_id': result[0],
                'hold_reference': result[1],
                'message': f'Transaction held. Reference: {result[1]}'
            }

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] hold_transaction: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_held_transactions(employee_id: int = None, shift_id: int = None) -> List[Dict]:
        """
        Get list of held transactions

        Args:
            employee_id: Filter by employee (optional)
            shift_id: Filter by shift (optional)

        Returns:
            List of held transactions
        """
        try:
            query = """
                SELECT
                    ht.id,
                    ht.hold_reference,
                    ht.employee_id,
                    e.full_name as employee_name,
                    ht.shift_id,
                    ht.items,
                    ht.subtotal,
                    ht.tax,
                    ht.total,
                    ht.customer_note,
                    ht.held_at,
                    ht.expires_at,
                    ht.status
                FROM held_transactions ht
                JOIN employees e ON e.id = ht.employee_id
                WHERE ht.status = 'held'
            """

            params = {}

            if employee_id:
                query += " AND ht.employee_id = :employee_id"
                params['employee_id'] = employee_id

            if shift_id:
                query += " AND ht.shift_id = :shift_id"
                params['shift_id'] = shift_id

            query += " ORDER BY ht.held_at DESC"

            results = db.session.execute(text(query), params).fetchall()

            import json
            held_list = []
            for row in results:
                held_list.append({
                    'id': row[0],
                    'hold_reference': row[1],
                    'employee_id': row[2],
                    'employee_name': row[3],
                    'shift_id': row[4],
                    'items': json.loads(row[5]) if row[5] else [],
                    'subtotal': float(row[6]),
                    'tax': float(row[7]),
                    'total': float(row[8]),
                    'customer_note': row[9],
                    'held_at': row[10].isoformat() if row[10] else None,
                    'expires_at': row[11].isoformat() if row[11] else None,
                    'status': row[12],
                    'item_count': len(json.loads(row[5])) if row[5] else 0
                })

            return held_list

        except Exception as e:
            print(f"[ERROR] get_held_transactions: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def recall_transaction(hold_id: int, employee_id: int) -> Dict:
        """
        Recall a held transaction

        Args:
            hold_id: Held transaction ID
            employee_id: Employee recalling

        Returns:
            Transaction details or error
        """
        try:
            # Get held transaction
            result = db.session.execute(
                text("""
                    SELECT
                        id, hold_reference, items, subtotal, tax, total, customer_note, status
                    FROM held_transactions
                    WHERE id = :hold_id
                      AND status = 'held'
                """),
                {'hold_id': hold_id}
            ).fetchone()

            if not result:
                return {
                    'success': False,
                    'error': 'Held transaction not found or already recalled'
                }

            import json

            # Mark as recalled
            db.session.execute(
                text("""
                    UPDATE held_transactions
                    SET status = 'recalled'
                    WHERE id = :hold_id
                """),
                {'hold_id': hold_id}
            )

            db.session.commit()

            return {
                'success': True,
                'hold_reference': result[1],
                'items': json.loads(result[2]) if result[2] else [],
                'subtotal': float(result[3]),
                'tax': float(result[4]),
                'total': float(result[5]),
                'customer_note': result[6]
            }

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] recall_transaction: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def cancel_held_transaction(hold_id: int) -> Dict:
        """
        Cancel a held transaction

        Args:
            hold_id: Held transaction ID

        Returns:
            Success status
        """
        try:
            db.session.execute(
                text("""
                    UPDATE held_transactions
                    SET status = 'cancelled'
                    WHERE id = :hold_id
                      AND status = 'held'
                """),
                {'hold_id': hold_id}
            )

            db.session.commit()

            return {
                'success': True,
                'message': 'Held transaction cancelled'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    # ============================================================================
    # QUICK ACCESS PRODUCTS
    # ============================================================================

    @staticmethod
    def get_quick_access_products(
        employee_id: int = None,
        store_location_id: int = 1,
        access_type: str = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get quick access products for cashier

        Args:
            employee_id: Employee ID (None for store-wide)
            store_location_id: Store location
            access_type: favorite, frequent, recent (None for all)
            limit: Maximum number of items

        Returns:
            List of quick access products
        """
        try:
            query = """
                SELECT DISTINCT
                    qa.id,
                    qa.variant_id,
                    pv.sku,
                    pv.size,
                    pv.color,
                    p.id as product_id,
                    p.name as product_name,
                    p.price,
                    p.sale_price,
                    COALESCE(p.sale_price, p.price) as effective_price,
                    qa.access_type,
                    qa.access_count,
                    qa.sort_order,
                    (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = TRUE LIMIT 1) as image_url
                FROM pos_quick_access qa
                JOIN product_variants pv ON pv.id = qa.variant_id
                JOIN products p ON p.id = pv.product_id
                WHERE qa.store_location_id = :store_location_id
                  AND p.is_active = TRUE
                  AND pv.is_active = TRUE
            """

            params = {
                'store_location_id': store_location_id,
                'limit': limit
            }

            if employee_id:
                query += " AND (qa.employee_id = :employee_id OR qa.employee_id IS NULL)"
                params['employee_id'] = employee_id

            if access_type:
                query += " AND qa.access_type = :access_type"
                params['access_type'] = access_type

            query += " ORDER BY qa.sort_order ASC, qa.access_count DESC, p.name ASC LIMIT :limit"

            results = db.session.execute(text(query), params).fetchall()

            quick_list = []
            for row in results:
                quick_list.append({
                    'id': row[0],
                    'variant_id': row[1],
                    'sku': row[2],
                    'size': row[3],
                    'color': row[4],
                    'product_id': row[5],
                    'product_name': row[6],
                    'price': float(row[7]),
                    'sale_price': float(row[8]) if row[8] else None,
                    'effective_price': float(row[9]),
                    'access_type': row[10],
                    'access_count': row[11],
                    'image_url': row[13]
                })

            return quick_list

        except Exception as e:
            print(f"[ERROR] get_quick_access_products: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    # ============================================================================
    # CASHIER METRICS
    # ============================================================================

    @staticmethod
    def record_transaction_metrics(
        employee_id: int,
        shift_id: int,
        transaction_seconds: int,
        items_count: int,
        transaction_total: float
    ) -> None:
        """
        Record cashier performance metrics

        Args:
            employee_id: Employee ID
            shift_id: Shift ID
            transaction_seconds: Time taken for transaction
            items_count: Number of items in transaction
            transaction_total: Total sale amount
        """
        try:
            # Calculate items per minute
            items_per_minute = (items_count / transaction_seconds * 60) if transaction_seconds > 0 else 0

            # Update or insert metrics
            db.session.execute(
                text("""
                    INSERT INTO cashier_metrics (
                        employee_id, shift_id, metric_date,
                        transactions_count, items_scanned, items_per_minute,
                        average_transaction_seconds, fastest_transaction_seconds,
                        total_sales
                    )
                    VALUES (
                        :employee_id, :shift_id, CURRENT_DATE,
                        1, :items_count, :items_per_minute,
                        :transaction_seconds, :transaction_seconds,
                        :transaction_total
                    )
                    ON CONFLICT (employee_id, shift_id, metric_date)
                    DO UPDATE SET
                        transactions_count = cashier_metrics.transactions_count + 1,
                        items_scanned = cashier_metrics.items_scanned + :items_count,
                        items_per_minute = (
                            (cashier_metrics.items_scanned + :items_count) /
                            ((cashier_metrics.average_transaction_seconds * cashier_metrics.transactions_count + :transaction_seconds) / 60.0)
                        ),
                        average_transaction_seconds = (
                            (cashier_metrics.average_transaction_seconds * cashier_metrics.transactions_count + :transaction_seconds) /
                            (cashier_metrics.transactions_count + 1)
                        ),
                        fastest_transaction_seconds = LEAST(cashier_metrics.fastest_transaction_seconds, :transaction_seconds),
                        total_sales = cashier_metrics.total_sales + :transaction_total,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    'employee_id': employee_id,
                    'shift_id': shift_id,
                    'items_count': items_count,
                    'items_per_minute': items_per_minute,
                    'transaction_seconds': transaction_seconds,
                    'transaction_total': transaction_total
                }
            )

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] record_transaction_metrics: {str(e)}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def get_cashier_metrics(employee_id: int, shift_id: int = None) -> Optional[Dict]:
        """
        Get cashier performance metrics

        Args:
            employee_id: Employee ID
            shift_id: Shift ID (optional, uses current date if None)

        Returns:
            Metrics dictionary or None
        """
        try:
            query = """
                SELECT
                    transactions_count,
                    items_scanned,
                    items_per_minute,
                    average_transaction_seconds,
                    fastest_transaction_seconds,
                    total_sales,
                    void_count,
                    discount_count
                FROM cashier_metrics
                WHERE employee_id = :employee_id
            """

            params = {'employee_id': employee_id}

            if shift_id:
                query += " AND shift_id = :shift_id"
                params['shift_id'] = shift_id
            else:
                query += " AND metric_date = CURRENT_DATE"

            result = db.session.execute(text(query), params).fetchone()

            if result:
                return {
                    'transactions_count': result[0],
                    'items_scanned': result[1],
                    'items_per_minute': float(result[2]) if result[2] else 0,
                    'average_transaction_seconds': result[3],
                    'fastest_transaction_seconds': result[4],
                    'total_sales': float(result[5]),
                    'void_count': result[6],
                    'discount_count': result[7]
                }

            return None

        except Exception as e:
            print(f"[ERROR] get_cashier_metrics: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
