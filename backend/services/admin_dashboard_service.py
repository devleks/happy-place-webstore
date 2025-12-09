"""
Admin Dashboard Service
Provides metrics, analytics, and alerts for the admin dashboard
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy import func, and_, or_, case
from models.database_models import (
    db, Order, POSTransaction, Customer, Employee, Product, Inventory,
    ActivityLog, AuthAuditLog
)
from models.extended_models import ProductVariant
from decimal import Decimal


class AdminDashboardService:
    """Service for admin dashboard data and metrics"""

    def get_dashboard_metrics(self, date_range: str = 'today') -> Dict:
        """
        Get key metrics for dashboard overview

        Args:
            date_range: 'today', 'yesterday', 'week', 'month'

        Returns:
            Dictionary with metrics including sales, orders, customers, inventory alerts
        """
        start_date, end_date = self._get_date_range(date_range)

        # Sales metrics
        sales_data = self._get_sales_metrics(start_date, end_date)

        # Order metrics
        order_metrics = self._get_order_metrics(start_date, end_date)

        # Customer metrics
        customer_metrics = self._get_customer_metrics(start_date, end_date)

        # Inventory alerts
        inventory_alerts = self._get_inventory_alerts()

        # Comparison with previous period
        prev_start, prev_end = self._get_previous_period(start_date, end_date)
        prev_sales = self._get_sales_metrics(prev_start, prev_end)

        return {
            'sales': {
                'total': float(sales_data['total']),
                'online': float(sales_data['online']),
                'pos': float(sales_data['pos']),
                'previous_total': float(prev_sales['total']),
                'change_percentage': self._calculate_percentage_change(
                    sales_data['total'],
                    prev_sales['total']
                ),
                'trend': 'up' if sales_data['total'] > prev_sales['total'] else 'down'
            },
            'orders': {
                'total': order_metrics['total'],
                'pending': order_metrics['pending'],
                'processing': order_metrics['processing'],
                'completed': order_metrics['completed'],
                'cancelled': order_metrics['cancelled'],
                'change_percentage': self._calculate_percentage_change(
                    order_metrics['total'],
                    self._get_order_metrics(prev_start, prev_end)['total']
                )
            },
            'customers': {
                'total': customer_metrics['total'],
                'new_today': customer_metrics['new_today'],
                'active': customer_metrics['active'],
                'change_percentage': self._calculate_percentage_change(
                    customer_metrics['new_today'],
                    self._get_customer_metrics(prev_start, prev_end)['new_today']
                )
            },
            'inventory': {
                'low_stock_count': inventory_alerts['low_stock_count'],
                'out_of_stock_count': inventory_alerts['out_of_stock_count'],
                'total_products': inventory_alerts['total_products'],
                'critical': inventory_alerts['out_of_stock_count'] > 0
            },
            'period': date_range,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """
        Get recent activity feed (orders, customers, inventory changes)

        Args:
            limit: Maximum number of activities to return

        Returns:
            List of activity records
        """
        activities = []

        # Recent orders
        recent_orders = Order.query\
            .order_by(Order.created_at.desc())\
            .limit(limit // 2)\
            .all()

        for order in recent_orders:
            activities.append({
                'type': 'order',
                'id': order.id,
                'timestamp': order.created_at.isoformat() if order.created_at else None,
                'description': f'Order #{order.id} placed',
                'amount': float(order.total_amount) if order.total_amount else 0,
                'status': order.status,
                'customer_id': order.customer_id,
                'customer_name': f"{order.customer.first_name} {order.customer.last_name}" if order.customer else 'Guest'
            })

        # Recent customer registrations
        recent_customers = Customer.query\
            .filter(Customer.created_at >= datetime.now() - timedelta(days=7))\
            .order_by(Customer.created_at.desc())\
            .limit(limit // 4)\
            .all()

        for customer in recent_customers:
            activities.append({
                'type': 'customer_registration',
                'id': customer.id,
                'timestamp': customer.created_at.isoformat() if customer.created_at else None,
                'description': f'New customer registered: {customer.first_name} {customer.last_name}',
                'customer_id': customer.id,
                'customer_name': f"{customer.first_name} {customer.last_name}"
            })

        # Recent inventory changes (using ActivityLog)
        try:
            recent_inventory = ActivityLog.query\
                .filter(ActivityLog.resource_type == 'inventory')\
                .order_by(ActivityLog.timestamp.desc())\
                .limit(limit // 4)\
                .all()

            for log in recent_inventory:
                activities.append({
                    'type': 'inventory_change',
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'description': f'Inventory {log.action}',
                    'details': log.details,
                    'employee_id': log.employee_id,
                    'employee_name': log.employee.full_name if log.employee else 'System'
                })
        except:
            pass  # ActivityLog table might not exist yet

        # Sort all activities by timestamp
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return activities[:limit]

    def get_critical_alerts(self) -> Dict:
        """
        Get critical alerts requiring immediate attention

        Returns:
            Dictionary with categorized alerts
        """
        alerts = {
            'critical': [],  # Red - immediate action required
            'warning': [],   # Orange - attention needed soon
            'info': []       # Blue - informational
        }

        # Out of stock items (CRITICAL)
        out_of_stock = db.session.query(
            Product.name,
            ProductVariant.id,
            ProductVariant.size,
            ProductVariant.color,
            ProductVariant.sku,
            Inventory.quantity,
            Inventory.reserved_quantity
        ).join(ProductVariant, Product.id == ProductVariant.product_id)\
         .join(Inventory, ProductVariant.id == Inventory.variant_id)\
         .filter(
             and_(
                 (Inventory.quantity - Inventory.reserved_quantity) <= 0,
                 Product.is_active == True
             )
         ).all()

        for item in out_of_stock:
            alerts['critical'].append({
                'type': 'out_of_stock',
                'title': f'Out of Stock: {item.name}',
                'message': f'{item.name} ({item.size}, {item.color}) - SKU: {item.sku}',
                'variant_id': item.id,
                'action_url': f'/admin/inventory/{item.id}'
            })

        # Low stock items (WARNING)
        low_stock = db.session.query(
            Product.name,
            ProductVariant.id,
            ProductVariant.size,
            ProductVariant.color,
            ProductVariant.sku,
            Inventory.quantity,
            Inventory.reserved_quantity
        ).join(ProductVariant, Product.id == ProductVariant.product_id)\
         .join(Inventory, ProductVariant.id == Inventory.variant_id)\
         .filter(
             and_(
                 (Inventory.quantity - Inventory.reserved_quantity) > 0,
                 (Inventory.quantity - Inventory.reserved_quantity) < 10,
                 Product.is_active == True
             )
         ).all()

        for item in low_stock:
            available = item.quantity - item.reserved_quantity
            alerts['warning'].append({
                'type': 'low_stock',
                'title': f'Low Stock: {item.name}',
                'message': f'{item.name} ({item.size}, {item.color}) - Only {available} available',
                'variant_id': item.id,
                'current_stock': available,
                'action_url': f'/admin/inventory/{item.id}'
            })

        # Pending orders older than 24 hours (WARNING)
        old_pending_orders = Order.query\
            .filter(
                and_(
                    Order.status == 'pending',
                    Order.created_at < datetime.now() - timedelta(hours=24)
                )
            ).count()

        if old_pending_orders > 0:
            alerts['warning'].append({
                'type': 'pending_orders',
                'title': f'{old_pending_orders} Pending Orders',
                'message': f'{old_pending_orders} orders pending for more than 24 hours',
                'count': old_pending_orders,
                'action_url': '/admin/orders?status=pending'
            })

        # Unverified orders (INFO)
        unverified_orders = Order.query\
            .filter(Order.payment_status == 'pending')\
            .count()

        if unverified_orders > 0:
            alerts['info'].append({
                'type': 'unverified_orders',
                'title': f'{unverified_orders} Unverified Orders',
                'message': f'{unverified_orders} orders with pending payment verification',
                'count': unverified_orders,
                'action_url': '/admin/orders?payment_status=pending'
            })

        return {
            'critical': alerts['critical'][:5],  # Top 5 critical
            'warning': alerts['warning'][:10],   # Top 10 warnings
            'info': alerts['info'][:5],          # Top 5 info
            'total_critical': len(alerts['critical']),
            'total_warning': len(alerts['warning']),
            'total_info': len(alerts['info'])
        }

    def get_sales_trends(self, period: str = 'week') -> Dict:
        """
        Get sales trends for charts

        Args:
            period: 'week', 'month', 'quarter', 'year'

        Returns:
            Sales data grouped by time period
        """
        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        elif period == 'quarter':
            days = 90
        else:  # year
            days = 365

        start_date = datetime.now() - timedelta(days=days)

        # Get daily sales for the period
        daily_sales = db.session.query(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total_amount).label('total'),
            func.count(Order.id).label('order_count')
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.status != 'cancelled'
            )
        ).group_by(func.date(Order.created_at))\
         .order_by(func.date(Order.created_at))\
         .all()

        # Get daily POS sales
        daily_pos_sales = db.session.query(
            func.date(POSTransaction.created_at).label('date'),
            func.sum(POSTransaction.total_amount).label('total'),
            func.count(POSTransaction.id).label('transaction_count')
        ).filter(
            and_(
                POSTransaction.created_at >= start_date,
                POSTransaction.status == 'completed'
            )
        ).group_by(func.date(POSTransaction.created_at))\
         .order_by(func.date(POSTransaction.created_at))\
         .all()

        # Combine and format data
        sales_by_date = {}

        for sale in daily_sales:
            date_str = sale.date.isoformat()
            sales_by_date[date_str] = {
                'date': date_str,
                'online': float(sale.total or 0),
                'pos': 0,
                'total': float(sale.total or 0),
                'order_count': sale.order_count
            }

        for sale in daily_pos_sales:
            date_str = sale.date.isoformat()
            if date_str in sales_by_date:
                sales_by_date[date_str]['pos'] = float(sale.total or 0)
                sales_by_date[date_str]['total'] += float(sale.total or 0)
            else:
                sales_by_date[date_str] = {
                    'date': date_str,
                    'online': 0,
                    'pos': float(sale.total or 0),
                    'total': float(sale.total or 0),
                    'order_count': sale.transaction_count
                }

        # Fill in missing dates with zero
        current_date = start_date.date()
        end_date = datetime.now().date()

        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str not in sales_by_date:
                sales_by_date[date_str] = {
                    'date': date_str,
                    'online': 0,
                    'pos': 0,
                    'total': 0,
                    'order_count': 0
                }
            current_date += timedelta(days=1)

        # Sort by date
        sorted_sales = sorted(sales_by_date.values(), key=lambda x: x['date'])

        return {
            'period': period,
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.isoformat(),
            'data': sorted_sales,
            'total_revenue': sum(day['total'] for day in sorted_sales),
            'total_orders': sum(day['order_count'] for day in sorted_sales),
            'average_daily': sum(day['total'] for day in sorted_sales) / len(sorted_sales) if sorted_sales else 0
        }

    # ===== PRIVATE HELPER METHODS =====

    def _get_date_range(self, period: str) -> tuple:
        """Get start and end datetime for a period"""
        end = datetime.now()

        if period == 'today':
            start = datetime.combine(date.today(), datetime.min.time())
        elif period == 'yesterday':
            start = datetime.combine(date.today() - timedelta(days=1), datetime.min.time())
            end = datetime.combine(date.today(), datetime.min.time())
        elif period == 'week':
            start = end - timedelta(days=7)
        elif period == 'month':
            start = end - timedelta(days=30)
        else:
            start = datetime.combine(date.today(), datetime.min.time())

        return start, end

    def _get_previous_period(self, start_date: datetime, end_date: datetime) -> tuple:
        """Get the previous period of same length for comparison"""
        period_length = end_date - start_date
        prev_end = start_date
        prev_start = prev_end - period_length
        return prev_start, prev_end

    def _get_sales_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate sales metrics for a period"""
        # Online sales
        online_sales = db.session.query(
            func.coalesce(func.sum(Order.total_amount), 0)
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status != 'cancelled'
            )
        ).scalar() or Decimal(0)

        # POS sales
        pos_sales = db.session.query(
            func.coalesce(func.sum(POSTransaction.total_amount), 0)
        ).filter(
            and_(
                POSTransaction.created_at >= start_date,
                POSTransaction.created_at < end_date,
                POSTransaction.status == 'completed'
            )
        ).scalar() or Decimal(0)

        return {
            'total': online_sales + pos_sales,
            'online': online_sales,
            'pos': pos_sales
        }

    def _get_order_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get order statistics for a period"""
        orders = db.session.query(
            func.count(Order.id).label('total'),
            func.sum(case((Order.status == 'pending', 1), else_=0)).label('pending'),
            func.sum(case((Order.status == 'processing', 1), else_=0)).label('processing'),
            func.sum(case((Order.status == 'completed', 1), else_=0)).label('completed'),
            func.sum(case((Order.status == 'cancelled', 1), else_=0)).label('cancelled')
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.created_at < end_date
            )
        ).first()

        return {
            'total': orders.total or 0,
            'pending': orders.pending or 0,
            'processing': orders.processing or 0,
            'completed': orders.completed or 0,
            'cancelled': orders.cancelled or 0
        }

    def _get_customer_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get customer statistics for a period"""
        # Total customers
        total_customers = Customer.query.count()

        # New customers in period
        new_customers = Customer.query\
            .filter(
                and_(
                    Customer.created_at >= start_date,
                    Customer.created_at < end_date
                )
            ).count()

        # Active customers (placed order in last 30 days)
        active_customers = db.session.query(
            func.count(func.distinct(Order.customer_id))
        ).filter(
            Order.created_at >= datetime.now() - timedelta(days=30)
        ).scalar() or 0

        return {
            'total': total_customers,
            'new_today': new_customers,
            'active': active_customers
        }

    def _get_inventory_alerts(self) -> Dict:
        """Get inventory alert counts"""
        # Out of stock
        out_of_stock_count = db.session.query(ProductVariant)\
            .join(Product)\
            .join(Inventory, ProductVariant.id == Inventory.variant_id)\
            .filter(
                and_(
                    (Inventory.quantity - Inventory.reserved_quantity) <= 0,
                    Product.is_active == True
                )
            ).count()

        # Low stock (1-9 items available)
        low_stock_count = db.session.query(ProductVariant)\
            .join(Product)\
            .join(Inventory, ProductVariant.id == Inventory.variant_id)\
            .filter(
                and_(
                    (Inventory.quantity - Inventory.reserved_quantity) > 0,
                    (Inventory.quantity - Inventory.reserved_quantity) < 10,
                    Product.is_active == True
                )
            ).count()

        # Total active products
        total_products = Product.query\
            .filter(Product.is_active == True)\
            .count()

        return {
            'out_of_stock_count': out_of_stock_count,
            'low_stock_count': low_stock_count,
            'total_products': total_products
        }

    def _calculate_percentage_change(self, current: float, previous: float) -> float:
        """Calculate percentage change between two values"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0

        change = ((current - previous) / previous) * 100
        return round(change, 2)
