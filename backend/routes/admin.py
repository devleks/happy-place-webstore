"""
Admin API routes.
Dashboard and inventory management endpoints.
"""

from flask import jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func
from routes import api
from models import db, Order, Customer, Inventory, ProductVariant, Return
from middleware import admin_required, manager_required
from services.settings_service import SettingsService
from logging_utils import get_logger, safe_auth_context
from flask_jwt_extended import get_jwt_identity

# Initialize logger
logger = get_logger(__name__)


@api.route('/admin/dashboard', methods=['GET'])
@manager_required
def get_admin_dashboard(current_employee):
    """
    Get admin dashboard statistics.
    Requires manager or admin role.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total orders today
    orders_today = Order.query.filter(Order.created_at >= today).count()

    # Revenue today
    revenue_today = db.session.query(func.sum(Order.total)).filter(
        Order.created_at >= today,
        Order.status.in_(['completed', 'processing'])
    ).scalar() or 0

    # Total customers
    total_customers = Customer.query.filter_by(is_active=True).count()

    # Low stock items (quantity < 10)
    low_stock_query = db.session.query(
        ProductVariant,
        Inventory
    ).join(
        Inventory,
        ProductVariant.id == Inventory.variant_id
    ).filter(
        Inventory.quantity < 10,
        ProductVariant.is_active == True
    ).all()

    low_stock_items = len(low_stock_query)

    # Pending returns
    pending_returns = Return.query.filter_by(status='pending').count()

    # Low stock alerts details
    low_stock_alerts = []
    for variant, inventory in low_stock_query[:10]:  # Limit to 10
        available_qty = inventory.quantity - inventory.reserved_quantity
        low_stock_alerts.append({
            'variant_id': variant.id,
            'sku': variant.sku,
            'product_name': variant.product.name if variant.product else 'Unknown',
            'size': variant.size,
            'color': variant.color,
            'available_quantity': available_qty,
            'threshold': 10
        })

    # Recent orders (last 10)
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_orders_list = [
        {
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': f"{order.customer.first_name} {order.customer.last_name}" if order.customer else 'Unknown',
            'total': float(order.total),
            'status': order.status,
            'created_at': order.created_at.isoformat() if order.created_at else None
        }
        for order in recent_orders
    ]

    return jsonify({
        'summary': {
            'total_orders_today': orders_today,
            'revenue_today': float(revenue_today),
            'total_customers': total_customers,
            'low_stock_items': low_stock_items,
            'pending_returns': pending_returns
        },
        'recent_orders': recent_orders_list,
        'low_stock_alerts': low_stock_alerts
    }), 200


@api.route('/admin/dashboard/metrics', methods=['GET'])
@manager_required
def get_dashboard_metrics(current_employee):
    """
    Get dashboard metrics for a specific period.
    Requires manager or admin role.
    """
    from flask import request
    period = request.args.get('period', 'today')

    # Calculate date range based on period
    now = datetime.utcnow()
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Total orders in period
    total_orders = Order.query.filter(Order.created_at >= start_date).count()

    # Total sales in period
    total_sales = db.session.query(func.sum(Order.total)).filter(
        Order.created_at >= start_date,
        Order.status.in_(['completed', 'processing', 'shipped'])
    ).scalar() or 0

    # Total customers
    total_customers = Customer.query.filter_by(is_active=True).count()

    # Low stock items
    low_stock_items = db.session.query(
        ProductVariant
    ).join(
        Inventory,
        ProductVariant.id == Inventory.variant_id
    ).filter(
        Inventory.quantity < 10,
        ProductVariant.is_active == True
    ).count()

    return jsonify({
        'totalSales': float(total_sales),
        'totalOrders': total_orders,
        'totalCustomers': total_customers,
        'lowStockItems': low_stock_items
    }), 200


@api.route('/admin/dashboard/activity', methods=['GET'])
@manager_required
def get_dashboard_activity(current_employee):
    """
    Get recent activity for the dashboard.
    Requires manager or admin role.
    """
    # Get recent orders (last 10)
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    activity = []
    for order in recent_orders:
        customer_name = 'Guest'
        if order.customer:
            customer_name = f"{order.customer.first_name} {order.customer.last_name}"

        activity.append({
            'id': f"order_{order.id}",
            'icon': '📦',
            'description': f"Order {order.order_number} placed by {customer_name} - ${float(order.total):.2f}",
            'timestamp': order.created_at.isoformat() if order.created_at else None
        })

    return jsonify(activity), 200


@api.route('/admin/dashboard/alerts', methods=['GET'])
@manager_required
def get_dashboard_alerts(current_employee):
    """
    Get critical alerts for the dashboard.
    Requires manager or admin role.
    """
    alerts = []

    # Low stock alerts
    low_stock_query = db.session.query(
        ProductVariant,
        Inventory
    ).join(
        Inventory,
        ProductVariant.id == Inventory.variant_id
    ).filter(
        Inventory.quantity < 10,
        ProductVariant.is_active == True
    ).all()

    for variant, inventory in low_stock_query[:5]:  # Limit to 5 most critical
        available_qty = inventory.quantity - inventory.reserved_quantity
        severity = 'critical' if available_qty == 0 else 'warning'

        alerts.append({
            'id': f"stock_{variant.id}",
            'type': 'low_stock',
            'severity': severity,
            'title': 'Low Stock Alert',
            'message': f"{variant.product.name if variant.product else 'Unknown'} ({variant.sku}) - Only {available_qty} left",
            'timestamp': datetime.utcnow().isoformat()
        })

    # Pending returns
    pending_returns_count = Return.query.filter_by(status='pending').count()
    if pending_returns_count > 0:
        alerts.append({
            'id': 'pending_returns',
            'type': 'pending_returns',
            'severity': 'warning',
            'title': 'Pending Returns',
            'message': f"{pending_returns_count} return request(s) awaiting review",
            'timestamp': datetime.utcnow().isoformat()
        })

    return jsonify(alerts), 200


@api.route('/settings/public', methods=['GET'])
def get_public_settings():
    """
    Get public settings (no authentication required).
    Used by frontend to display currency and other public information.

    GET /api/settings/public

    Returns:
        200: Public settings
        400: Error
    """
    try:
        settings_service = SettingsService()
        result = settings_service.get_public_settings()

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Failed to fetch settings'}), 400

    except Exception as e:
        logger.error(
            "Public settings operation failed",
            extra={"context": safe_auth_context(
                user_type='public',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 400


@api.route('/admin/inventory/alerts', methods=['GET'])
@manager_required
def get_inventory_alerts(current_employee):
    """
    Get all inventory low stock alerts.
    Requires manager or admin role.
    """
    # Get all low stock items
    low_stock_query = db.session.query(
        ProductVariant,
        Inventory
    ).join(
        Inventory,
        ProductVariant.id == Inventory.variant_id
    ).filter(
        Inventory.quantity < 10,
        ProductVariant.is_active == True
    ).all()

    alerts = []
    for variant, inventory in low_stock_query:
        available_qty = inventory.quantity - inventory.reserved_quantity

        alerts.append({
            'variant_id': variant.id,
            'product_id': variant.product_id,
            'product_name': variant.product.name if variant.product else 'Unknown',
            'sku': variant.sku,
            'size': variant.size,
            'color': variant.color,
            'quantity': inventory.quantity,
            'reserved_quantity': inventory.reserved_quantity,
            'available_quantity': available_qty,
            'is_out_of_stock': available_qty == 0,
            'threshold': 10,
            'urgency': 'critical' if available_qty == 0 else 'warning'
        })

    # Sort by urgency (critical first)
    alerts.sort(key=lambda x: (0 if x['urgency'] == 'critical' else 1, x['available_quantity']))

    return jsonify({
        'alerts': alerts,
        'total': len(alerts),
        'critical_count': len([a for a in alerts if a['urgency'] == 'critical']),
        'warning_count': len([a for a in alerts if a['urgency'] == 'warning'])
    }), 200
