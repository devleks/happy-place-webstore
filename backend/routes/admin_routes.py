"""
Admin Dashboard API Routes

Comprehensive admin panel endpoints for:
- Dashboard metrics and analytics
- Inventory management
- Order management
- Customer management (with GDPR compliance)
- Employee management
- Promotion management
- Reports and analytics
- Store settings

All endpoints require JWT authentication and appropriate role permissions.
"""

from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
import re
import uuid

from services.admin_dashboard_service import AdminDashboardService
from services.inventory_management_service import InventoryManagementService
from services.order_management_service import OrderManagementService
from services.customer_management_service import CustomerManagementService
from services.employee_management_service import EmployeeManagementService
from services.promotion_service import PromotionService
from services.report_service import ReportService
from services.settings_service import SettingsService
from middleware import manager_required, admin_required
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Services will be initialized in each endpoint to avoid app context issues
def get_services():
    """Get service instances (lazy initialization)"""
    return {
        'dashboard': AdminDashboardService(),
        'inventory': InventoryManagementService(),
        'order': OrderManagementService(),
        'customer': CustomerManagementService(),
        'employee': EmployeeManagementService(),
        'promotion': PromotionService(),
        'report': ReportService(),
        'settings': SettingsService()
    }


# =====================================================
# DASHBOARD ENDPOINTS
# =====================================================

@admin_bp.route('/dashboard/metrics', methods=['GET'])
@jwt_required()
@manager_required
def get_dashboard_metrics(current_employee):
    """
    Get key dashboard metrics (sales, orders, customers, inventory).

    GET /api/admin/dashboard/metrics?period=today|week|month|year

    Returns:
        200: Dashboard metrics
        400: Error
    """
    try:
        period = request.args.get('period', 'today')
        _employee_id = int(get_jwt_identity())

        result = get_services()['dashboard'].get_dashboard_metrics(period=period)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/confirm-cod', methods=['POST'])
@jwt_required()
@manager_required
def confirm_cod_order_admin(current_employee, order_id):
    """Confirm a COD order on behalf of the customer."""
    try:
        _employee_id = int(get_jwt_identity())
        result = get_services()['order'].confirm_cod_order(order_id=order_id, employee_id=employee_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Confirm COD (admin) operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None, "order_id": order_id}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/mark-cod-paid', methods=['POST'])
@jwt_required()
@manager_required
def mark_cod_paid_admin(current_employee, order_id):
    """Mark COD payment as received and complete payment (deduct inventory)."""
    try:
        result = get_services()['order'].mark_cod_paid(order_id=order_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Mark COD paid operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None, "order_id": order_id}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/cod/expire', methods=['POST'])
@jwt_required()
@manager_required
def expire_unconfirmed_cod_orders(current_employee):
    """Expire unconfirmed COD orders and release reserved inventory."""
    try:
        data = request.get_json() or {}
        max_orders = data.get('max_orders', 1000)
        result = get_services()['order'].expire_unconfirmed_cod_orders(max_orders=max_orders)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Expire unconfirmed COD orders operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/reports/products', methods=['GET'])
@jwt_required()
@manager_required
def get_products_report(current_employee):
    """
    Get products performance report.

    GET /api/admin/reports/products?start_date=2025-01-01&end_date=2025-01-31

    Returns:
        200: Products report
        400: Error
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, desc
        from models.database_models import db, Order, OrderItem, Product, Category, POSTransaction, POSTransactionItem

        def _parse_date(value, default_dt, is_end=False):
            if not value:
                return default_dt
            raw = str(value).strip()
            is_date_only = ('T' not in raw and ':' not in raw)
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    dt = datetime.strptime(raw, fmt)
                    return dt + timedelta(days=1) if (is_end and is_date_only) else dt
                except ValueError:
                    continue
            try:
                dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
                return dt + timedelta(days=1) if (is_end and is_date_only) else dt
            except ValueError:
                return default_dt

        now = datetime.utcnow()
        default_start = now - timedelta(days=30)
        default_end = now + timedelta(days=1)

        start_dt = _parse_date(request.args.get('start_date'), default_start, is_end=False)
        end_dt = _parse_date(request.args.get('end_date'), default_end, is_end=True)

        base_filter = [
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        ]

        online_orders = db.session.query(func.count(func.distinct(Order.id)))\
            .select_from(Order)\
            .filter(*base_filter)\
            .scalar() or 0

        pos_orders = db.session.query(func.count(func.distinct(POSTransaction.id)))\
            .select_from(POSTransaction)\
            .filter(
                POSTransaction.created_at >= start_dt,
                POSTransaction.created_at < end_dt,
                POSTransaction.status == 'completed'
            )\
            .scalar() or 0

        total_orders = int(online_orders or 0) + int(pos_orders or 0)

        online_units = db.session.query(func.coalesce(func.sum(OrderItem.quantity), 0))\
            .select_from(Order)\
            .join(OrderItem, Order.id == OrderItem.order_id)\
            .filter(*base_filter)\
            .scalar() or 0

        pos_units = db.session.query(func.coalesce(func.sum(POSTransactionItem.quantity), 0))\
            .select_from(POSTransaction)\
            .join(POSTransactionItem, POSTransaction.id == POSTransactionItem.transaction_id)\
            .filter(
                POSTransaction.created_at >= start_dt,
                POSTransaction.created_at < end_dt,
                POSTransaction.status == 'completed'
            )\
            .scalar() or 0

        total_units = int(online_units or 0) + int(pos_units or 0)

        unique_products = db.session.execute(
            db.text(
                """
                SELECT COUNT(DISTINCT t.product_id) AS unique_products
                FROM (
                    SELECT oi.product_id AS product_id
                    FROM orders o
                    JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.created_at >= :start_dt
                      AND o.created_at < :end_dt
                      AND o.status != 'cancelled'
                    UNION
                    SELECT pti.product_id AS product_id
                    FROM pos_transactions pt
                    JOIN pos_transaction_items pti ON pt.id = pti.transaction_id
                    WHERE pt.created_at >= :start_dt
                      AND pt.created_at < :end_dt
                      AND pt.status = 'completed'
                ) t
                """
            ),
            {'start_dt': start_dt, 'end_dt': end_dt}
        ).scalar() or 0

        online_category_rows = db.session.query(
            Category.name.label('category'),
            func.coalesce(func.sum(OrderItem.quantity), 0).label('units_sold'),
            func.coalesce(func.sum(OrderItem.total_price), 0).label('revenue')
        ).select_from(Order)\
         .join(OrderItem, Order.id == OrderItem.order_id)\
         .join(Product, OrderItem.product_id == Product.id)\
         .outerjoin(Category, Product.category_id == Category.id)\
         .filter(*base_filter)\
         .group_by(Category.name)\
         .order_by(desc('revenue'))\
         .all()

        pos_category_rows = db.session.query(
            Category.name.label('category'),
            func.coalesce(func.sum(POSTransactionItem.quantity), 0).label('units_sold'),
            func.coalesce(func.sum(POSTransactionItem.total_price), 0).label('revenue')
        ).select_from(POSTransaction)\
         .join(POSTransactionItem, POSTransaction.id == POSTransactionItem.transaction_id)\
         .join(Product, POSTransactionItem.product_id == Product.id)\
         .outerjoin(Category, Product.category_id == Category.id)\
         .filter(
            POSTransaction.created_at >= start_dt,
            POSTransaction.created_at < end_dt,
            POSTransaction.status == 'completed'
         )\
         .group_by(Category.name)\
         .order_by(desc('revenue'))\
         .all()

        category_totals = {}
        for row in online_category_rows:
            cat = row.category or 'Uncategorized'
            category_totals[cat] = {
                'unitsSold': int(row.units_sold or 0),
                'revenue': float(row.revenue or 0)
            }
        for row in pos_category_rows:
            cat = row.category or 'Uncategorized'
            if cat not in category_totals:
                category_totals[cat] = {'unitsSold': 0, 'revenue': 0.0}
            category_totals[cat]['unitsSold'] += int(row.units_sold or 0)
            category_totals[cat]['revenue'] += float(row.revenue or 0)

        total_revenue = float(sum(v['revenue'] for v in category_totals.values()) or 0)
        category_breakdown = []
        for cat, totals in sorted(category_totals.items(), key=lambda kv: kv[1]['revenue'], reverse=True):
            revenue = float(totals['revenue'] or 0)
            category_breakdown.append({
                'category': cat,
                'unitsSold': int(totals['unitsSold'] or 0),
                'revenue': revenue,
                'percentage': (revenue / total_revenue * 100) if total_revenue > 0 else 0
            })

        return jsonify({
            'totalProductsSold': int(total_units or 0),
            'uniqueProducts': int(unique_products or 0),
            'avgUnitsPerOrder': float(total_units / total_orders) if total_orders else 0,
            'categoryBreakdown': category_breakdown,
        }), 200
    except Exception:
        logger.error(
            "Products report failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/dashboard/activity', methods=['GET'])
@jwt_required()
@manager_required
def get_dashboard_activity(current_employee):
    """
    Get recent activity feed (orders, customers, inventory changes).

    GET /api/admin/dashboard/activity?limit=20

    Returns:
        200: Activity feed
        400: Error
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        _employee_id = int(get_jwt_identity())

        result = get_services()['dashboard'].get_recent_activity(limit=limit)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/dashboard/alerts', methods=['GET'])
@jwt_required()
@manager_required
def get_dashboard_alerts(current_employee):
    """
    Get system alerts (low stock, pending orders, issues).

    GET /api/admin/dashboard/alerts

    Returns:
        200: System alerts
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['dashboard'].get_alerts()
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/dashboard/trends', methods=['GET'])
@jwt_required()
@manager_required
def get_dashboard_trends(current_employee):
    """
    Get trends data for charts (sales, orders, revenue over time).

    GET /api/admin/dashboard/trends?period=week|month|year

    Returns:
        200: Trends data
        400: Error
    """
    try:
        period = request.args.get('period', 'month')
        _employee_id = int(get_jwt_identity())

        result = get_services()['dashboard'].get_trends(period=period)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


# =====================================================
# INVENTORY MANAGEMENT ENDPOINTS
# =====================================================

@admin_bp.route('/inventory', methods=['GET'])
@jwt_required()
@manager_required
def get_inventory(current_employee):
    """
    Get inventory list with filters and pagination.

    GET /api/admin/inventory?category=&status=&search=&page=1&limit=50

    Returns:
        200: Inventory list
        400: Error
    """
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)

        filters = {}
        if category:
            filters['category_id'] = category
        if status:
            filters['status'] = status
        if search:
            filters['search'] = search

        result = get_services()['inventory'].get_inventory_list(
            filters=filters,
            page=page,
            per_page=limit
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/<int:product_id>', methods=['GET'])
@jwt_required()
@manager_required
def get_inventory_details(current_employee, product_id):
    """
    Get detailed inventory information for a product.

    GET /api/admin/inventory/:product_id

    Returns:
        200: Product inventory details
        404: Product not found
        400: Error
    """
    try:
        result = get_services()['inventory'].get_inventory_details(product_id=product_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/<int:product_id>', methods=['PUT'])
@jwt_required()
@manager_required
def update_inventory(current_employee, product_id):
    """
    Update inventory levels for a product.

    PUT /api/admin/inventory/:product_id
    Body: {
        "physical_stock": 100,
        "reserved_stock": 5,
        "reorder_point": 20,
        "reorder_quantity": 50
    }

    Returns:
        200: Inventory updated
        400: Error
    """
    try:
        data = request.get_json() or {}
        employee_id = int(get_jwt_identity())

        result = get_services()['inventory'].update_inventory(
            product_id=product_id,
            employee_id=employee_id,
            **data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/bulk-update', methods=['POST'])
@jwt_required()
@manager_required
def bulk_update_inventory(current_employee):
    """
    Bulk update multiple products' inventory.

    POST /api/admin/inventory/bulk-update
    Body: {
        "updates": [
            {"product_id": 1, "physical_stock": 100},
            {"product_id": 2, "physical_stock": 50}
        ]
    }

    Returns:
        200: Bulk update completed
        400: Error
    """
    try:
        data = request.get_json() or {}
        employee_id = int(get_jwt_identity())

        if 'updates' not in data:
            return jsonify({'error': 'Updates array required'}), 400

        result = get_services()['inventory'].bulk_update_inventory(
            updates=data['updates'],
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/adjust', methods=['POST'])
@jwt_required()
@manager_required
def adjust_inventory(current_employee):
    """
    Adjust inventory (damage, loss, found, correction).

    POST /api/admin/inventory/adjust
    Body: {
        "product_id": 1,
        "quantity": -5,
        "reason": "damaged",
        "notes": "Water damage"
    }

    Returns:
        200: Inventory adjusted
        400: Error
    """
    try:
        data = request.get_json(silent=True) or {}
        employee_id = int(get_jwt_identity())

        variant_id = data.get('variant_id')
        if variant_id is None:
            variant_id = data.get('product_id')

        if variant_id is None:
            return jsonify({'success': False, 'error': 'Missing required field: variant_id'}), 400
        if 'quantity' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: quantity'}), 400
        if 'reason' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: reason'}), 400

        try:
            variant_id = int(variant_id)
            quantity_delta = int(data['quantity'])
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'Invalid variant_id or quantity'}), 400

        if quantity_delta == 0:
            return jsonify({'success': False, 'error': 'Quantity must be non-zero'}), 400

        adjustment = {
            'type': 'remove' if quantity_delta < 0 else 'add',
            'quantity': abs(quantity_delta),
            'reason': data.get('reason') or 'Stock adjustment',
        }

        success = get_services()['inventory'].adjust_stock(
            variant_id=variant_id,
            adjustment=adjustment,
            employee_id=employee_id
        )

        if not success:
            return jsonify({'success': False, 'error': 'Inventory not found'}), 400

        return jsonify({'success': True}), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/transfer', methods=['POST'])
@jwt_required()
@manager_required
def transfer_inventory(current_employee):
    """
    Transfer inventory between locations (if multi-location support).

    POST /api/admin/inventory/transfer
    Body: {
        "product_id": 1,
        "quantity": 10,
        "from_location": "warehouse",
        "to_location": "store",
        "notes": "Restocking"
    }

    Returns:
        200: Transfer completed
        400: Error
    """
    try:
        data = request.get_json()
        _employee_id = int(get_jwt_identity())

        required = ['product_id', 'quantity', 'from_location', 'to_location']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        result = get_services()['inventory'].transfer_inventory(
            product_id=data['product_id'],
            quantity=data['quantity'],
            from_location=data['from_location'],
            to_location=data['to_location'],
            notes=data.get('notes'),
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/<int:product_id>/history', methods=['GET'])
@jwt_required()
@manager_required
def get_inventory_history(current_employee, product_id):
    """
    Get inventory change history for a product.

    GET /api/admin/inventory/:product_id/history?limit=50&offset=0

    Returns:
        200: Inventory history
        400: Error
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        result = get_services()['inventory'].get_inventory_history(
            product_id=product_id,
            limit=limit,
            offset=offset
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/<int:product_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_inventory_item(current_employee, product_id):
    """
    Delete/archive an inventory item (Admin only).

    DELETE /api/admin/inventory/:product_id

    Returns:
        200: Item deleted
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['inventory'].delete_inventory_item(
            product_id=product_id,
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory/alerts', methods=['GET'])
@jwt_required()
@manager_required
def get_inventory_alerts(current_employee):
    """
    Get inventory alerts (low stock, out of stock, overstock).

    GET /api/admin/inventory/alerts

    Returns:
        200: Inventory alerts
        400: Error
    """
    try:
        result = get_services()['inventory'].get_inventory_alerts()
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/inventory', methods=['POST'])
@admin_bp.route('/products', methods=['POST'])  # Alias for backwards compatibility
@jwt_required()
@manager_required
def create_product(current_employee):
    """
    Create a new product.

    POST /api/admin/inventory (or /api/admin/products)
    Body: {
        "name": "Product Name",
        "description": "Description",
        "category_id": 2,
        "price": 29.99,
        "sku": "SKU-001",
        "variants": [optional array of variants]
    }

    Returns:
        201: Product created
        400: Error
    """
    try:
        from extensions import db
        from models.database_models import Product, Inventory
        from models.extended_models import ProductVariant

        data = request.get_json()
        employee_id = int(get_jwt_identity())

        def _slugify(value: str) -> str:
            value = (value or '').strip().lower()
            value = re.sub(r'[^a-z0-9]+', '-', value)
            value = value.strip('-')
            return value or str(uuid.uuid4())

        # Required fields
        required = ['name', 'category_id', 'price']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create product
        product_sku = data.get('sku') or f"SKU-{uuid.uuid4().hex[:8].upper()}"
        product = Product(
            name=data['name'],
            slug=_slugify(data['name']),
            description=data.get('description', ''),
            category_id=data['category_id'],
            price=data['price'],
            sku=product_sku,
            is_active=True
        )
        db.session.add(product)
        db.session.flush()  # Get product ID

        # Handle variants (if provided) or create default variant
        variants_data = data.get('variants', [])
        created_variants = []

        if not variants_data:
            # Create single default variant
            variant = ProductVariant(
                product_id=product.id,
                sku=product_sku,
                size=data.get('size', 'One Size'),
                color=data.get('color', 'Default')
            )
            db.session.add(variant)
            db.session.flush()

            # Create inventory record
            inventory = Inventory(
                variant_id=variant.id,
                quantity=data.get('stock_quantity', 0),
                reserved_quantity=0,
                low_stock_threshold=data.get('low_stock_threshold', 10)
            )
            db.session.add(inventory)
            created_variants.append({'variant_id': variant.id, 'sku': variant.sku})
        else:
            # Create multiple variants
            for variant_data in variants_data:
                variant = ProductVariant(
                    product_id=product.id,
                    sku=variant_data.get('sku', f'SKU-{product.id}-{len(created_variants)+1}'),
                    size=variant_data.get('size', 'One Size'),
                    color=variant_data.get('color', 'Default')
                )
                db.session.add(variant)
                db.session.flush()

                # Create inventory record
                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=variant_data.get('stock_quantity', 0),
                    reserved_quantity=0,
                    low_stock_threshold=variant_data.get('low_stock_threshold', 10)
                )
                db.session.add(inventory)
                created_variants.append({'variant_id': variant.id, 'sku': variant.sku})

        db.session.commit()

        return jsonify({
            'message': 'Product created successfully',
            'product_id': product.id,
            'variants': created_variants
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"ERROR creating product: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/products/<int:product_id>', methods=['PATCH'])
@jwt_required()
@manager_required
def update_product(current_employee, product_id):
    """
    Update an existing product.

    PATCH /api/admin/products/:id
    Body: {
        "name": "Updated Product Name",
        "description": "Updated description",
        "price": 39.99,
        "category_id": 2,
        "is_active": true
    }

    Returns:
        200: Product updated
        404: Product not found
        400: Error
    """
    try:
        from models.database_models import db, Product

        data = request.get_json()
        employee_id = int(get_jwt_identity())

        # Get product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Update fields if provided
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'sale_price' in data:
            product.sale_price = data['sale_price']
        if 'category_id' in data:
            product.category_id = data['category_id']
        if 'is_active' in data:
            product.is_active = data['is_active']
        if 'is_featured' in data:
            product.is_featured = data['is_featured']
        if 'weight' in data:
            product.weight = data['weight']

        db.session.commit()

        return jsonify({
            'message': 'Product updated successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'is_active': product.is_active
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update product failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/inventory/<int:product_id>/images', methods=['POST'])
@jwt_required()
@manager_required
def upload_product_images(current_employee, product_id):
    """
    Upload product images.

    POST /api/admin/inventory/:product_id/images
    Content-Type: multipart/form-data
    Form Data:
        - images: File[] (multiple image files)
        - primary_index: int (index of primary image, default 0)

    Returns:
        200: Images uploaded
        400: Error
    """
    try:
        from models.database_models import db, Product, ProductImage
        import os
        from werkzeug.utils import secure_filename
        from datetime import datetime

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Check if files were uploaded
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400

        files = request.files.getlist('images')
        if len(files) == 0:
            return jsonify({'error': 'No images provided'}), 400

        # Get primary index
        primary_index = int(request.form.get('primary_index', 0))

        # Upload directory
        upload_dir = os.path.join('static', 'uploads', 'products')
        os.makedirs(upload_dir, exist_ok=True)

        uploaded_images = []

        for index, file in enumerate(files):
            if file and file.filename:
                # Secure filename
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"product_{product_id}_{timestamp}_{index}_{filename}"

                # Save file
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)

                # Create database record
                image_url = f"/static/uploads/products/{filename}"
                is_primary = (index == primary_index)

                # If this is the new primary, unset other primary images
                if is_primary:
                    ProductImage.query.filter_by(
                        product_id=product_id,
                        is_primary=True
                    ).update({'is_primary': False})

                product_image = ProductImage(
                    product_id=product_id,
                    image_url=image_url,
                    alt_text=product.name,
                    display_order=index,
                    is_primary=is_primary
                )
                db.session.add(product_image)
                uploaded_images.append({
                    'url': image_url,
                    'is_primary': is_primary
                })

        db.session.commit()

        return jsonify({
            'message': f'{len(uploaded_images)} images uploaded successfully',
            'images': uploaded_images
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"ERROR uploading images: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


# =====================================================
# ORDER MANAGEMENT ENDPOINTS
# =====================================================

@admin_bp.route('/orders', methods=['GET'])
@jwt_required()
@manager_required
def get_orders(current_employee):
    """
    Get orders list with filters and pagination.

    GET /api/admin/orders?status=&channel=&search=&page=1&limit=50

    Returns:
        200: Orders list
        400: Error
    """
    try:
        status = request.args.get('status')
        channel = request.args.get('channel')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)

        filters = {}
        if status:
            filters['status'] = status
        if channel:
            filters['channel'] = channel
        if search:
            filters['search'] = search

        result = get_services()['order'].get_order_list(
            filters=filters,
            page=page,
            per_page=limit
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"ERROR in get_orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
@manager_required
def get_order_details(current_employee, order_id):
    """
    Get detailed order information.

    GET /api/admin/orders/:order_id

    Returns:
        200: Order details
        404: Order not found
        400: Error
    """
    try:
        result = get_services()['order'].get_order_details(order_id=order_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT', 'PATCH'])
@jwt_required()
@manager_required
def update_order_status(current_employee, order_id):
    """
    Update order status.

    PUT/PATCH /api/admin/orders/:order_id/status
    Body: {
        "status": "processing|shipped|delivered|cancelled",
        "notes": "Optional notes"
    }

    Returns:
        200: Status updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        if 'status' not in data:
            return jsonify({'error': 'Status required'}), 400

        result = get_services()['order'].update_order_status(
            order_id=order_id,
            status=data['status'],
            tracking=data.get('tracking'),
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
@manager_required
def cancel_order(current_employee, order_id):
    """
    Cancel an order.

    POST /api/admin/orders/:order_id/cancel
    Body: {
        "reason": "customer_request|out_of_stock|other",
        "notes": "Optional notes"
    }

    Returns:
        200: Order cancelled
        400: Error
    """
    try:
        data = request.get_json() or {}
        employee_id = int(get_jwt_identity())

        if 'reason' not in data:
            return jsonify({'error': 'Cancellation reason required'}), 400

        result = get_services()['order'].cancel_order(
            order_id=order_id,
            reason=data['reason'],
            notes=data.get('notes'),
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/refund', methods=['POST'])
@jwt_required()
@manager_required
def refund_order(current_employee, order_id):
    """
    Process order refund.

    POST /api/admin/orders/:order_id/refund
    Body: {
        "amount": 150.00,
        "reason": "customer_return|damaged|other",
        "notes": "Optional notes"
    }

    Returns:
        200: Refund processed
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        required = ['amount', 'reason']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        result = get_services()['order'].process_refund(
            order_id=order_id,
            amount=data['amount'],
            reason=data['reason'],
            notes=data.get('notes'),
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/notes', methods=['POST'])
@jwt_required()
@manager_required
def add_order_note(current_employee, order_id):
    """
    Add internal note to order.

    POST /api/admin/orders/:order_id/notes
    Body: {
        "note": "Customer called to confirm address",
        "is_internal": true
    }

    Returns:
        200: Note added
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        if 'note' not in data:
            return jsonify({'error': 'Note required'}), 400

        result = get_services()['order'].add_order_note(
            order_id=order_id,
            note=data['note'],
            is_internal=data.get('is_internal', True),
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/timeline', methods=['GET'])
@jwt_required()
@manager_required
def get_order_timeline(current_employee, order_id):
    """
    Get order timeline/history.

    GET /api/admin/orders/:order_id/timeline

    Returns:
        200: Order timeline
        400: Error
    """
    try:
        result = get_services()['order'].get_order_timeline(order_id=order_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/orders/<int:order_id>/notify', methods=['POST'])
@jwt_required()
@manager_required
def send_order_notification(current_employee, order_id):
    """
    Send notification to customer about order.

    POST /api/admin/orders/:order_id/notify
    Body: {
        "type": "shipping_update|delivery_confirmation|other",
        "message": "Your order has been shipped"
    }

    Returns:
        200: Notification sent
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        required = ['type', 'message']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        result = get_services()['order'].send_notification(
            order_id=order_id,
            notification_type=data['type'],
            message=data['message'],
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


# =====================================================
# ORDER TRACKING ENDPOINTS (Phase 1 - Task 1.1.3)
# =====================================================

@admin_bp.route('/orders/<int:order_id>/tracking', methods=['POST'])
@jwt_required()
@manager_required
def add_order_tracking(current_employee, order_id):
    """
    Add tracking information to an order.
    
    POST /api/admin/orders/:order_id/tracking
    Body: {
        "tracking_number": "DHL123456789",
        "carrier": "DHL Express",
        "estimated_delivery": "2025-12-15",
        "notes": "Package dispatched from warehouse"
    }
    
    Returns:
        200: Tracking added successfully
        400: Validation error
        404: Order not found
    """
    try:
        from models import db
        from models.database_models import Order, ShippingCarrier, ShipmentUpdate
        from datetime import datetime
        
        data = request.get_json()
        employee_id = int(get_jwt_identity())
        
        # Validate required fields
        if not data.get('tracking_number'):
            return jsonify({'error': 'Tracking number is required'}), 400
        if not data.get('carrier'):
            return jsonify({'error': 'Carrier is required'}), 400
        
        # Get order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get carrier to generate tracking URL
        carrier = ShippingCarrier.query.filter_by(name=data['carrier']).first()
        tracking_url = None
        if carrier:
            tracking_url = carrier.generate_tracking_url(data['tracking_number'])
        
        # Update order with tracking info
        order.tracking_number = data['tracking_number']
        order.carrier = data['carrier']
        order.tracking_url = tracking_url
        order.shipping_notes = data.get('notes', '')
        
        # Parse estimated delivery date
        if data.get('estimated_delivery'):
            try:
                order.estimated_delivery_date = datetime.strptime(
                    data['estimated_delivery'], '%Y-%m-%d'
                ).date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Update order status to shipped if not already
        if order.status not in ['shipped', 'delivered']:
            order.status = 'shipped'
            order.shipped_at = datetime.utcnow()
        
        # Create shipment update
        shipment_update = ShipmentUpdate(
            order_id=order_id,
            status='shipped',
            location='Warehouse',
            description=data.get('notes', 'Package shipped'),
            timestamp=datetime.utcnow(),
            created_by=employee_id
        )
        db.session.add(shipment_update)
        
        db.session.commit()
        
        logger.info(
            f"Tracking added to order {order_id}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": employee_id, "order_id": order_id}
            )}
        )
        
        return jsonify({
            'message': 'Tracking information added successfully',
            'order': order.to_dict(include_items=False)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to add tracking to order {order_id}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True
        )
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/orders/<int:order_id>/tracking', methods=['GET'])
@jwt_required()
@manager_required
def get_order_tracking(current_employee, order_id):
    """
    Get tracking information for an order.
    
    GET /api/admin/orders/:order_id/tracking
    
    Returns:
        200: Tracking information
        404: Order not found or no tracking info
    """
    try:
        from models.database_models import Order, ShipmentUpdate
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if not order.tracking_number:
            return jsonify({'error': 'No tracking information available'}), 404
        
        # Get shipment updates
        updates = ShipmentUpdate.query.filter_by(order_id=order_id)\
            .order_by(ShipmentUpdate.timestamp.desc()).all()
        
        return jsonify({
            'tracking_number': order.tracking_number,
            'carrier': order.carrier,
            'tracking_url': order.tracking_url,
            'estimated_delivery_date': order.estimated_delivery_date.isoformat() if order.estimated_delivery_date else None,
            'shipping_notes': order.shipping_notes,
            'status': order.status,
            'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
            'updates': [update.to_dict() for update in updates]
        }), 200
        
    except Exception as e:
        logger.error(
            f"Failed to get tracking for order {order_id}",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True
        )
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/shipping/carriers', methods=['GET'])
@jwt_required()
def get_shipping_carriers():
    """
    Get list of available shipping carriers.
    
    GET /api/shipping/carriers
    
    Returns:
        200: List of carriers
    """
    try:
        from models.database_models import ShippingCarrier
        
        carriers = ShippingCarrier.query.filter_by(is_active=True).all()
        
        return jsonify({
            'carriers': [carrier.to_dict() for carrier in carriers]
        }), 200
        
    except Exception as e:
        logger.error(
            "Failed to get shipping carriers",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True
        )
        return jsonify({'error': str(e)}), 400


# =====================================================
# CUSTOMER MANAGEMENT ENDPOINTS
# =====================================================

@admin_bp.route('/customers', methods=['GET'])
@jwt_required()
@manager_required
def get_customers(current_employee):
    """
    Get customers list with filters and pagination.

    GET /api/admin/customers?search=&status=&page=1&limit=50

    Returns:
        200: Customers list
        400: Error
    """
    try:
        search = request.args.get('search')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status

        result = get_services()['customer'].get_customer_list(
            filters=filters,
            page=page,
            per_page=limit
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"ERROR in get_customers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/customers/<int:customer_id>', methods=['GET'])
@jwt_required()
@manager_required
def get_customer_details(current_employee, customer_id):
    """
    Get detailed customer information.

    GET /api/admin/customers/:customer_id

    Returns:
        200: Customer details
        404: Customer not found
        400: Error
    """
    try:
        result = get_services()['customer'].get_customer_details(customer_id=customer_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@jwt_required()
@manager_required
def update_customer(current_employee, customer_id):
    """
    Update customer information.

    PUT /api/admin/customers/:customer_id
    Body: {
        "email": "newemail@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "+254712345678"
    }

    Returns:
        200: Customer updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        result = get_services()['customer'].update_customer(
            customer_id=customer_id,
            employee_id=employee_id,
            **data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_customer(current_employee, customer_id):
    """
    Delete/deactivate customer account (Admin only).

    DELETE /api/admin/customers/:customer_id

    Returns:
        200: Customer deleted
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['customer'].delete_customer(
            customer_id=customer_id,
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/customers/<int:customer_id>/orders', methods=['GET'])
@jwt_required()
@manager_required
def get_customer_orders(current_employee, customer_id):
    """
    Get customer's order history.

    GET /api/admin/customers/:customer_id/orders?limit=50

    Returns:
        200: Customer orders
        400: Error
    """
    try:
        limit = request.args.get('limit', 50, type=int)

        result = get_services()['customer'].get_customer_orders(
            customer_id=customer_id,
            limit=limit
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/customers/<int:customer_id>/activity', methods=['GET'])
@jwt_required()
@manager_required
def get_customer_activity(current_employee, customer_id):
    """
    Get customer activity log.

    GET /api/admin/customers/:customer_id/activity?limit=50

    Returns:
        200: Customer activity
        400: Error
    """
    try:
        limit = request.args.get('limit', 50, type=int)

        result = get_services()['customer'].get_customer_activity(
            customer_id=customer_id,
            limit=limit
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/customers/<int:customer_id>/export', methods=['POST'])
@jwt_required()
@manager_required
def export_customer_data(current_employee, customer_id):
    """
    Export customer data (GDPR compliance).

    POST /api/admin/customers/:customer_id/export

    Returns:
        200: Customer data export
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['customer'].export_customer_data(
            customer_id=customer_id,
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/customers/<int:customer_id>/anonymize', methods=['POST'])
@jwt_required()
@admin_required
def anonymize_customer(current_employee, customer_id):
    """
    Anonymize customer data (GDPR right to be forgotten - Admin only).

    POST /api/admin/customers/:customer_id/anonymize
    Body: {
        "confirmation": "ANONYMIZE"
    }

    Returns:
        200: Customer anonymized
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        if data.get('confirmation') != 'ANONYMIZE':
            return jsonify({'error': 'Confirmation required'}), 400

        reason = data.get('reason', 'Admin requested anonymization')
        success = get_services()['customer'].anonymize_customer(
            customer_id=customer_id,
            reason=reason,
            performed_by=employee_id
        )

        if success:
            return jsonify({'success': True, 'message': 'Customer anonymized successfully'}), 200
        else:
            return jsonify({'error': 'Failed to anonymize customer'}), 400
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/customers/<int:customer_id>/consent-history', methods=['GET'])
@jwt_required()
@manager_required
def get_customer_consent_history(current_employee, customer_id):
    """
    Get customer's GDPR consent history.

    GET /api/admin/customers/:customer_id/consent-history

    Returns:
        200: Consent history
        400: Error
    """
    try:
        result = get_services()['customer'].get_consent_history(customer_id=customer_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


# =====================================================
# EMPLOYEE MANAGEMENT ENDPOINTS
# =====================================================

@admin_bp.route('/employees', methods=['GET'])
@jwt_required()
@manager_required
def get_employees(current_employee):
    """
    Get employees list with filters.

    GET /api/admin/employees?role=&status=&search=

    Returns:
        200: Employees list
        400: Error
    """
    try:
        role = request.args.get('role')
        status = request.args.get('status')
        search = request.args.get('search')

        filters = {}
        if role:
            filters['role'] = role
        if status:
            filters['status'] = status
        if search:
            filters['search'] = search

        result = get_services()['employee'].get_employee_list(
            filters=filters
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees/<int:employee_id>', methods=['GET'])
@jwt_required()
@manager_required
def get_employee_details(current_employee, employee_id):
    """
    Get detailed employee information.

    GET /api/admin/employees/:employee_id

    Returns:
        200: Employee details
        404: Employee not found
        400: Error
    """
    try:
        result = get_services()['employee'].get_employee_details(employee_id=employee_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees', methods=['POST'])
@jwt_required()
@admin_required
def create_employee(current_employee):
    """
    Create new employee account (Admin only).

    POST /api/admin/employees
    Body: {
        "email": "employee@happyplace.com",
        "full_name": "John Smith",
        "role": "cashier|manager|admin",
        "pin": "123456"
    }

    Returns:
        201: Employee created
        400: Error
    """
    try:
        data = request.get_json(silent=True) or {}
        _admin_id = int(get_jwt_identity())

        required = ['email', 'full_name', 'role']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        result = get_services()['employee'].create_employee(data)

        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees/<int:employee_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_employee(current_employee, employee_id):
    """
    Update employee information (Admin only).

    PUT /api/admin/employees/:employee_id
    Body: {
        "email": "newemail@happyplace.com",
        "full_name": "John Smith",
        "role": "cashier|manager|admin"
    }

    Returns:
        200: Employee updated
        400: Error
    """
    try:
        data = request.get_json()
        _admin_id = int(get_jwt_identity())

        result = get_services()['employee'].update_employee(
            employee_id=employee_id,
            data=data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def deactivate_employee(current_employee, employee_id):
    """
    Deactivate employee account (Admin only).

    DELETE /api/admin/employees/:employee_id

    Returns:
        200: Employee deactivated
        400: Error
    """
    try:
        admin_id = int(get_jwt_identity())

        result = get_services()['employee'].deactivate_employee(
            employee_id=employee_id,
            admin_id=admin_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees/<int:employee_id>/reset-password', methods=['POST'])
@jwt_required()
@admin_required
def reset_employee_password(current_employee, employee_id):
    """
    Reset employee password (Admin only).

    POST /api/admin/employees/:employee_id/reset-password
    Body: {
        "new_password": "NewSecurePass123"
    }

    Returns:
        200: Password reset
        400: Error
    """
    try:
        data = request.get_json()
        admin_id = int(get_jwt_identity())

        if 'new_password' not in data:
            return jsonify({'error': 'New password required'}), 400

        result = get_services()['employee'].reset_password(
            employee_id=employee_id,
            new_password=data['new_password'],
            admin_id=admin_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees/<int:employee_id>/disable-2fa', methods=['POST'])
@jwt_required()
@admin_required
def disable_employee_2fa(current_employee, employee_id):
    """
    Disable 2FA for employee (Admin only - for account recovery).

    POST /api/admin/employees/:employee_id/disable-2fa

    Returns:
        200: 2FA disabled
        400: Error
    """
    try:
        admin_id = int(get_jwt_identity())

        result = get_services()['employee'].disable_2fa(
            employee_id=employee_id,
            admin_id=admin_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees/<int:employee_id>/activity', methods=['GET'])
@jwt_required()
@manager_required
def get_employee_activity(current_employee, employee_id):
    """
    Get employee activity log.

    GET /api/admin/employees/:employee_id/activity?limit=50

    Returns:
        200: Employee activity
        400: Error
    """
    try:
        limit = request.args.get('limit', 50, type=int)

        result = get_services()['employee'].get_employee_activity(
            employee_id=employee_id,
            limit=limit
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/employees/<int:employee_id>/performance', methods=['GET'])
@jwt_required()
@manager_required
def get_employee_performance(current_employee, employee_id):
    """
    Get employee performance metrics.

    GET /api/admin/employees/:employee_id/performance?period=month

    Returns:
        200: Employee performance
        400: Error
    """
    try:
        period = request.args.get('period', 'month')

        result = get_services()['employee'].get_employee_performance(
            employee_id=employee_id,
            period=period
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


# =====================================================
# PROMOTION MANAGEMENT ENDPOINTS
# =====================================================

@admin_bp.route('/promotions', methods=['GET'])
@jwt_required()
@manager_required
def get_promotions(current_employee):
    """
    Get promotions list with filters.

    GET /api/admin/promotions?status=active|scheduled|expired

    Returns:
        200: Promotions list
        400: Error
    """
    try:
        status = request.args.get('status')

        filters = {}
        if status:
            filters['status'] = status

        result = get_services()['promotion'].get_promotion_list(filters=filters)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions/<int:promotion_id>', methods=['GET'])
@jwt_required()
@manager_required
def get_promotion_details(current_employee, promotion_id):
    """
    Get detailed promotion information.

    GET /api/admin/promotions/:promotion_id

    Returns:
        200: Promotion details
        404: Promotion not found
        400: Error
    """
    try:
        result = get_services()['promotion'].get_promotion_details(promotion_id=promotion_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions', methods=['POST'])
@jwt_required()
@manager_required
def create_promotion(current_employee):
    """
    Create new promotion.

    POST /api/admin/promotions
    Body: {
        "code": "SUMMER20",
        "name": "Summer Sale",
        "discount_type": "percentage|fixed_amount|free_shipping",
        "discount_value": 20,
        "start_date": "2025-06-01",
        "end_date": "2025-06-30",
        "minimum_order_amount": 100 (optional),
        "maximum_discount_amount": 50 (optional),
        "usage_limit": 100 (optional),
        "usage_per_customer": 1 (optional)
    }

    Returns:
        201: Promotion created
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        # Map 'type' to 'discount_type' and 'value' to 'discount_value' for backwards compatibility
        if 'type' in data and 'discount_type' not in data:
            data['discount_type'] = data.pop('type')
        if 'value' in data and 'discount_value' not in data:
            data['discount_value'] = data.pop('value')

        required = ['code', 'name', 'discount_type', 'discount_value', 'start_date', 'end_date']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        result = get_services()['promotion'].create_promotion(
            data=data,
            created_by=employee_id
        )

        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions/<int:promotion_id>', methods=['PUT'])
@jwt_required()
@manager_required
def update_promotion(current_employee, promotion_id):
    """
    Update promotion.

    PUT /api/admin/promotions/:promotion_id
    Body: {
        "name": "Updated Summer Sale",
        "value": 25
    }

    Returns:
        200: Promotion updated
        400: Error
    """
    try:
        data = request.get_json(silent=True) or {}

        # Backwards compatible field mappings
        if 'type' in data and 'discount_type' not in data:
            data['discount_type'] = data.pop('type')
        if 'value' in data and 'discount_value' not in data:
            data['discount_value'] = data.pop('value')

        # Frontend-admin uses different field names
        if 'min_purchase_amount' in data and 'minimum_order_amount' not in data:
            data['minimum_order_amount'] = data.pop('min_purchase_amount')
        if 'max_uses' in data and 'usage_limit' not in data:
            data['usage_limit'] = data.pop('max_uses')

        # Normalize numeric inputs coming from HTML forms
        if 'usage_limit' in data:
            if data['usage_limit'] == '' or data['usage_limit'] is None:
                data['usage_limit'] = None
            else:
                try:
                    data['usage_limit'] = int(data['usage_limit'])
                except (TypeError, ValueError):
                    return jsonify({'success': False, 'error': 'Invalid usage_limit'}), 400

        if 'usage_per_customer' in data:
            if data['usage_per_customer'] == '' or data['usage_per_customer'] is None:
                data['usage_per_customer'] = None
            else:
                try:
                    data['usage_per_customer'] = int(data['usage_per_customer'])
                except (TypeError, ValueError):
                    return jsonify({'success': False, 'error': 'Invalid usage_per_customer'}), 400

        result = get_services()['promotion'].update_promotion(
            promotion_id=promotion_id,
            data=data
        )

        if result.get('success'):
            return jsonify(result), 200
        return jsonify(result), 400
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions/<int:promotion_id>', methods=['DELETE'])
@jwt_required()
@manager_required
def delete_promotion(current_employee, promotion_id):
    """
    Delete promotion.

    DELETE /api/admin/promotions/:promotion_id

    Returns:
        200: Promotion deleted
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['promotion'].delete_promotion(
            promotion_id=promotion_id,
            employee_id=employee_id
        )
        if isinstance(result, dict) and result.get('success'):
            return jsonify(result), 200
        return jsonify(result if isinstance(result, dict) else {'success': False, 'error': 'Failed to delete promotion'}), 400
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions/<int:promotion_id>/toggle', methods=['PUT'])
@jwt_required()
@manager_required
def toggle_promotion(current_employee, promotion_id):
    """
    Toggle promotion active status.

    PUT /api/admin/promotions/:promotion_id/toggle
    Body: {"isActive": true/false}

    Returns:
        200: Promotion toggled
        400: Error
    """
    try:
        from models.database_models import db
        from models.extended_models import Promotion

        data = request.get_json(silent=True) or {}

        if 'isActive' in data:
            is_active = data.get('isActive')
        elif 'is_active' in data:
            is_active = data.get('is_active')
        else:
            return jsonify({'error': 'Missing required field: isActive'}), 400

        if isinstance(is_active, str):
            is_active = is_active.strip().lower() in ('true', '1', 'yes', 'y', 'on')
        elif isinstance(is_active, (int, float)):
            is_active = bool(is_active)
        elif isinstance(is_active, bool):
            pass
        else:
            is_active = bool(is_active)
        
        promotion = Promotion.query.get(promotion_id)
        if not promotion:
            return jsonify({'error': 'Promotion not found'}), 404
        
        promotion.is_active = is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'promotion': promotion.to_dict(),
            'message': f'Promotion {"activated" if is_active else "deactivated"} successfully'
        }), 200
    except Exception as e:
        logger.error(f"Toggle promotion error: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/promotions/<int:promotion_id>/enable', methods=['POST'])
@jwt_required()
@manager_required
def enable_promotion(current_employee, promotion_id):
    """
    Enable/activate promotion.

    POST /api/admin/promotions/:promotion_id/enable

    Returns:
        200: Promotion enabled
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['promotion'].enable_promotion(
            promotion_id=promotion_id,
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions/<int:promotion_id>/disable', methods=['POST'])
@jwt_required()
@manager_required
def disable_promotion(current_employee, promotion_id):
    """
    Disable/deactivate promotion.

    POST /api/admin/promotions/:promotion_id/disable

    Returns:
        200: Promotion disabled
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['promotion'].disable_promotion(
            promotion_id=promotion_id,
            employee_id=employee_id
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions/<int:promotion_id>/analytics', methods=['GET'])
@jwt_required()
@manager_required
def get_promotion_analytics(current_employee, promotion_id):
    """
    Get promotion performance analytics.

    GET /api/admin/promotions/:promotion_id/analytics

    Returns:
        200: Promotion analytics
        400: Error
    """
    try:
        result = get_services()['promotion'].get_promotion_analytics(promotion_id=promotion_id)
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/promotions/<int:promotion_id>/duplicate', methods=['POST'])
@jwt_required()
@manager_required
def duplicate_promotion(current_employee, promotion_id):
    """
    Duplicate existing promotion.

    POST /api/admin/promotions/:promotion_id/duplicate

    Returns:
        201: Promotion duplicated
        400: Error
    """
    try:
        employee_id = int(get_jwt_identity())

        result = get_services()['promotion'].duplicate_promotion(
            promotion_id=promotion_id,
            employee_id=employee_id
        )

        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


# =====================================================
# REPORT ENDPOINTS
# =====================================================

@admin_bp.route('/reports/sales', methods=['GET'])
@jwt_required()
@manager_required
def get_sales_report(current_employee):
    """
    Get sales report.

    GET /api/admin/reports/sales?start_date=2025-01-01&end_date=2025-01-31&group_by=day

    Returns:
        200: Sales report
        400: Error
    """
    try:
        from datetime import datetime, timedelta

        def _parse_date(value, default_dt, is_end=False):
            if not value:
                return default_dt
            raw = str(value).strip()
            is_date_only = ('T' not in raw and ':' not in raw)
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    dt = datetime.strptime(raw, fmt)
                    return dt + timedelta(days=1) if (is_end and is_date_only) else dt
                except ValueError:
                    continue
            try:
                dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
                return dt + timedelta(days=1) if (is_end and is_date_only) else dt
            except ValueError:
                return default_dt

        now = datetime.utcnow()
        default_start = now - timedelta(days=30)
        default_end = now + timedelta(days=1)

        start_date_raw = request.args.get('start_date')
        end_date_raw = request.args.get('end_date')
        start_dt = _parse_date(start_date_raw, default_start, is_end=False)
        end_dt = _parse_date(end_date_raw, default_end, is_end=True)

        group_by = request.args.get('group_by', 'day')
        channel = request.args.get('channel', 'all')

        filters = {}
        if group_by:
            filters['group_by'] = group_by
        if channel:
            filters['channel'] = channel

        result = get_services()['report'].get_sales_report(
            start_date=start_dt.isoformat(),
            end_date=end_dt.isoformat(),
            filters=filters
        )

        summary = (result.get('summary') or {}).get('combined') or {}
        daily_sales = []
        for day in result.get('by_day') or []:
            daily_sales.append({
                'date': day.get('date'),
                'sales': float(day.get('revenue') or 0)
            })

        top_products = []
        for idx, prod in enumerate(result.get('by_product') or []):
            name = prod.get('product')
            top_products.append({
                'id': name or idx,
                'name': name,
                'unitsSold': int(prod.get('units_sold') or 0),
                'revenue': float(prod.get('revenue') or 0)
            })

        return jsonify({
            'totalRevenue': float(summary.get('total_revenue') or 0),
            'totalOrders': int(summary.get('total_orders') or 0),
            'avgOrderValue': float(summary.get('average_order_value') or 0),
            'totalProfit': 0,
            'dailySales': daily_sales,
            'topProducts': top_products,
        }), 200
    except Exception as e:
        print(f"ERROR in get_sales_report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/reports/inventory', methods=['GET'])
@jwt_required()
@manager_required
def get_inventory_report(current_employee):
    """
    Get inventory report.

    GET /api/admin/reports/inventory?category=&status=&sort_by=

    Returns:
        200: Inventory report
        400: Error
    """
    try:
        # Build filters dict from query parameters
        filters = {}
        if request.args.get('category'):
            filters['category_id'] = request.args.get('category')
        if request.args.get('status'):
            filters['stock_status'] = request.args.get('status')
        if request.args.get('sort_by'):
            filters['sort_by'] = request.args.get('sort_by')

        result = get_services()['report'].get_inventory_report(filters=filters)

        summary = result.get('summary') or {}
        items = result.get('items') or []
        low_stock_products = []
        for item in items:
            stock_qty = int(item.get('stock_quantity') or 0)
            if 0 < stock_qty < 10:
                low_stock_products.append({
                    'id': item.get('variant_id'),
                    'name': item.get('product_name'),
                    'stock': stock_qty,
                    'threshold': 10
                })

        return jsonify({
            'totalProducts': int(summary.get('total_variants') or 0),
            'lowStockItems': int(summary.get('low_stock_count') or 0),
            'outOfStockItems': int(summary.get('out_of_stock_count') or 0),
            'totalInventoryValue': float(summary.get('total_stock_value') or 0),
            'lowStockProducts': low_stock_products,
        }), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/reports/customers', methods=['GET'])
@jwt_required()
@manager_required
def get_customers_report(current_employee):
    """
    Get customers report.

    GET /api/admin/reports/customers?period=month

    Returns:
        200: Customers report
        400: Error
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from models.database_models import db, Order

        start_date_raw = request.args.get('start_date')
        end_date_raw = request.args.get('end_date')
        period = request.args.get('period', 'month')

        now = datetime.utcnow()
        default_start = now - timedelta(days=30)
        default_end = now

        def _parse_date(value, default_dt):
            if not value:
                return default_dt
            raw = str(value).strip()
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(raw.replace('Z', '+00:00'))
            except ValueError:
                return default_dt

        if start_date_raw and end_date_raw:
            start_dt = _parse_date(start_date_raw, default_start)
            end_dt = _parse_date(end_date_raw, default_end)
            days = max(1, (end_dt - start_dt).days)
            if days <= 7:
                period = 'week'
            elif days <= 31:
                period = 'month'
            elif days <= 93:
                period = 'quarter'
            else:
                period = 'year'

        result = get_services()['report'].get_customer_report(period=period)

        summary = result.get('summary') or {}
        top_customers = []
        for c in result.get('top_customers') or []:
            top_customers.append({
                'id': c.get('customer_id'),
                'name': c.get('name'),
                'totalOrders': int(c.get('order_count') or 0),
                'totalSpent': float(c.get('total_spent') or 0),
            })

        total_spent = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(Order.status != 'cancelled').scalar() or 0
        distinct_customers = db.session.query(func.count(func.distinct(Order.customer_id))).filter(Order.status != 'cancelled').scalar() or 0
        avg_lifetime_value = float(total_spent / distinct_customers) if distinct_customers else 0

        return jsonify({
            'totalCustomers': int(summary.get('total_customers') or 0),
            'newCustomers': int(summary.get('new_customers') or 0),
            'activeCustomers': int(summary.get('active_customers') or 0),
            'avgLifetimeValue': avg_lifetime_value,
            'topCustomers': top_customers,
        }), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/reports/employees', methods=['GET'])
@jwt_required()
@manager_required
def get_employees_report(current_employee):
    """
    Get employees performance report.

    GET /api/admin/reports/employees?period=month

    Returns:
        200: Employees report
        400: Error
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, desc
        from models.database_models import db, Employee, POSTransaction

        start_date_raw = request.args.get('start_date')
        end_date_raw = request.args.get('end_date')

        now = datetime.utcnow()
        default_start = now - timedelta(days=30)
        default_end = now

        def _parse_date(value, default_dt, is_end=False):
            if not value:
                return default_dt
            raw = str(value).strip()
            is_date_only = ('T' not in raw and ':' not in raw)
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    dt = datetime.strptime(raw, fmt)
                    return dt + timedelta(days=1) if (is_end and is_date_only) else dt
                except ValueError:
                    continue
            try:
                dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
                return dt + timedelta(days=1) if (is_end and is_date_only) else dt
            except ValueError:
                return default_dt

        start_dt = _parse_date(start_date_raw, default_start, is_end=False)
        end_dt = _parse_date(end_date_raw, default_end, is_end=True)

        total_employees = Employee.query.filter(Employee.is_active.is_(True)).count()

        txn_rows = db.session.query(
            Employee.id.label('employee_id'),
            Employee.full_name.label('name'),
            func.count(POSTransaction.id).label('transaction_count'),
            func.coalesce(func.sum(POSTransaction.total), 0).label('total_sales')
        ).join(POSTransaction, Employee.id == POSTransaction.employee_id)\
         .filter(
            POSTransaction.created_at >= start_dt,
            POSTransaction.created_at < end_dt,
            POSTransaction.status == 'completed'
         )\
         .group_by(Employee.id, Employee.full_name)\
         .order_by(desc('total_sales'))\
         .all()

        hours_by_employee = {}
        try:
            table_exists = db.session.execute(
                db.text(
                    """
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'pos_shifts'
                    LIMIT 1
                    """
                )
            ).fetchone()

            if table_exists:
                shift_rows = db.session.execute(
                    db.text(
                        """
                        SELECT
                            employee_id,
                            SUM(
                                GREATEST(
                                    0,
                                    EXTRACT(EPOCH FROM (
                                        LEAST(COALESCE(end_time, :range_end), :range_end)
                                        - GREATEST(start_time, :range_start)
                                    ))
                                )
                            ) AS seconds
                        FROM pos_shifts
                        WHERE start_time < :range_end
                          AND COALESCE(end_time, :range_end) > :range_start
                        GROUP BY employee_id
                        """
                    ),
                    {'range_start': start_dt, 'range_end': end_dt}
                ).fetchall()

                for row in shift_rows:
                    emp_id = int(row[0])
                    seconds = float(row[1] or 0)
                    hours_by_employee[emp_id] = seconds / 3600.0
        except Exception:
            hours_by_employee = {}

        settings_service = get_services().get('settings')
        hourly_rate = 0
        if settings_service:
            rate = settings_service.get_setting('employee_hourly_rate')
            if rate is None:
                rate = settings_service.get_setting('hourly_rate')
            try:
                hourly_rate = float(rate) if rate is not None else 0
            except Exception:
                hourly_rate = 0

        employee_performance = []
        for row in txn_rows:
            emp_id = int(row.employee_id)
            hours = float(hours_by_employee.get(emp_id, 0))
            revenue = float(row.total_sales or 0)
            employee_performance.append({
                'id': emp_id,
                'name': row.name,
                'hours': hours,
                'salesProcessed': int(row.transaction_count or 0),
                'revenue': revenue
            })

        total_hours = float(sum(hours_by_employee.values()) or 0)
        total_labor_cost = float(total_hours * hourly_rate)

        return jsonify({
            'totalEmployees': int(total_employees or 0),
            'totalHours': total_hours,
            'totalLaborCost': total_labor_cost,
            'employeePerformance': employee_performance,
        }), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


# =====================================================
# SETTINGS ENDPOINTS
# =====================================================

@admin_bp.route('/settings', methods=['GET'])
@jwt_required()
@manager_required
def get_settings(current_employee):
    """
    Get all store settings.

    GET /api/admin/settings

    Returns:
        200: Store settings
        400: Error
    """
    try:
        result = get_services()['settings'].get_all_settings()
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/store', methods=['PUT'])
@jwt_required()
@admin_required
def update_store_settings(current_employee):
    """
    Update store information settings (Admin only).

    PUT /api/admin/settings/store
    Body: {
        "store_name": "Happy Place Boutique",
        "address": "123 Main St",
        "phone": "+254712345678",
        "email": "info@happyplace.com"
    }

    Returns:
        200: Settings updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        result = get_services()['settings'].update_store_settings(
            employee_id=employee_id,
            **data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/business', methods=['GET', 'PUT'])
@jwt_required()
@admin_required
def business_settings(current_employee):
    """
    Get or update business hours settings (Admin only).

    GET /api/admin/settings/business
    Returns: Business hours configuration

    PUT /api/admin/settings/business
    Body: {
        "monday_open": "09:00",
        "monday_close": "17:00",
        etc.
    }

    Returns:
        200: Settings retrieved/updated
        400: Error
    """
    try:
        if request.method == 'GET':
            # Return current business hours
            result = get_services()['settings'].get_hours_settings()
            return jsonify(result), 200
        else:
            # PUT: Update business hours
            data = request.get_json()
            employee_id = int(get_jwt_identity())

            result = get_services()['settings'].update_hours_settings(
                employee_id=employee_id,
                hours=data
            )
            return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/notification', methods=['GET', 'PUT'])
@jwt_required()
@admin_required
def notification_settings(current_employee):
    """
    Get or update notification settings (Admin only).

    GET /api/admin/settings/notification
    Returns: Notification configuration

    PUT /api/admin/settings/notification
    Body: {
        "email_notifications": true,
        "low_stock_alert": true,
        "order_notifications": true,
        "customer_notifications": true
    }

    Returns:
        200: Settings retrieved/updated
        400: Error
    """
    try:
        if request.method == 'GET':
            # Return current notification settings
            result = get_services()['settings'].get_email_settings()
            return jsonify(result), 200
        else:
            # PUT: Update notification settings
            data = request.get_json()
            employee_id = int(get_jwt_identity())

            result = get_services()['settings'].update_email_settings(
                employee_id=employee_id,
                **data
            )
            return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/hours', methods=['PUT'])
@jwt_required()
@admin_required
def update_hours_settings(current_employee):
    """
    Update store hours settings (Admin only).

    PUT /api/admin/settings/hours
    Body: {
        "monday": {"open": "09:00", "close": "18:00"},
        "tuesday": {"open": "09:00", "close": "18:00"}
    }

    Returns:
        200: Settings updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        result = get_services()['settings'].update_hours_settings(
            employee_id=employee_id,
            hours=data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/email', methods=['PUT'])
@jwt_required()
@admin_required
def update_email_settings(current_employee):
    """
    Update email notification settings (Admin only).

    PUT /api/admin/settings/email
    Body: {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "noreply@happyplace.com",
        "order_notifications": true
    }

    Returns:
        200: Settings updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        result = get_services()['settings'].update_email_settings(
            employee_id=employee_id,
            **data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/payments', methods=['PUT'])
@jwt_required()
@admin_required
def update_payment_settings(current_employee):
    """
    Update payment gateway settings (Admin only).

    PUT /api/admin/settings/payments
    Body: {
        "mpesa_enabled": true,
        "mpesa_shortcode": "174379",
        "stripe_enabled": true
    }

    Returns:
        200: Settings updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        result = get_services()['settings'].update_payment_settings(
            employee_id=employee_id,
            **data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/tax', methods=['PUT'])
@jwt_required()
@admin_required
def update_tax_settings(current_employee):
    """
    Update tax settings (Admin only).

    PUT /api/admin/settings/tax
    Body: {
        "vat_rate": 16.0,
        "vat_number": "P051234567A",
        "tax_inclusive": true
    }

    Returns:
        200: Settings updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        result = get_services()['settings'].update_tax_settings(
            employee_id=employee_id,
            **data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/returns', methods=['PUT'])
@jwt_required()
@admin_required
def update_return_settings(current_employee):
    """
    Update return/refund policy settings (Admin only).

    PUT /api/admin/settings/returns
    Body: {
        "return_period_days": 30,
        "return_policy": "Full refund within 30 days with receipt",
        "restocking_fee": 0
    }

    Returns:
        200: Settings updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        result = get_services()['settings'].update_return_settings(
            employee_id=employee_id,
            **data
        )
        return jsonify(result), 200
    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/currency', methods=['PUT'])
@jwt_required()
@admin_required
def update_currency_settings(current_employee):
    """
    Update currency settings (Admin only).

    PUT /api/admin/settings/currency
    Body: {
        "currency": "KSh",
        "currency_code": "KES"
    }

    Supported currencies:
    - KES (Kenyan Shilling): KSh
    - USD (US Dollar): $
    - EUR (Euro): €
    - GBP (British Pound): £

    Returns:
        200: Currency updated
        400: Error
    """
    try:
        data = request.get_json()
        employee_id = int(get_jwt_identity())

        if 'currency' not in data or 'currency_code' not in data:
            return jsonify({'error': 'Currency and currency_code required'}), 400

        # Validate currency code
        valid_currencies = {
            'KES': 'KSh',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'TZS': 'TSh',
            'UGX': 'USh'
        }

        currency_code = data['currency_code'].upper()
        if currency_code not in valid_currencies:
            return jsonify({
                'error': f'Invalid currency code. Supported: {", ".join(valid_currencies.keys())}'
            }), 400

        # Update currency settings
        settings_service = get_services()['settings']

        result1 = settings_service.update_setting('currency_symbol', data['currency'], employee_id)
        result2 = settings_service.update_setting('currency_code', currency_code, employee_id)

        if result1['success'] and result2['success']:
            return jsonify({
                'success': True,
                'message': f'Currency updated to {currency_code} ({data["currency"]})',
                'currency': data['currency'],
                'currency_code': currency_code
            }), 200
        else:
            error_msg = result1.get('error') or result2.get('error') or 'Failed to update currency'
            return jsonify({'error': error_msg}), 400

    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@admin_bp.route('/settings/currency', methods=['GET'])
@jwt_required()
@manager_required
def get_currency_settings(current_employee):
    """
    Get current currency settings.

    GET /api/admin/settings/currency

    Returns:
        200: Current currency settings
        400: Error
    """
    try:
        settings_service = get_services()['settings']

        currency = settings_service.get_setting('currency_symbol')
        currency_code = settings_service.get_setting('currency_code')

        return jsonify({
            'success': True,
            'currency': currency or 'KSh',
            'currency_code': currency_code or 'KES'
        }), 200

    except Exception:
        logger.error(
            "Dashboard metrics operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


# Export blueprint
__all__ = ['admin_bp']
