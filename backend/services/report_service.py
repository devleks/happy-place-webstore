"""
Report Service
Generates business reports for sales, inventory, customers, and employees
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy import func, and_, or_, desc, case
from models.database_models import (
    db, Order, OrderItem, POSTransaction, POSTransactionItem,
    Customer, Employee, Product, Category, Payment, Inventory
)
from models.extended_models import ProductVariant, Promotion, OrderPromotion
from decimal import Decimal


class ReportService:
    """Service for generating business reports"""

    def get_sales_report(self, start_date: str, end_date: str, filters: Dict = None) -> Dict:
        """
        Generate comprehensive sales report

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            filters: Optional filters (channel: 'online'|'pos'|'all',
                    category_id, employee_id)

        Returns:
            Sales report data
        """
        try:
            # Parse dates
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return {'error': 'Invalid date format'}

        filters = filters or {}
        channel = filters.get('channel', 'all')

        # Initialize report data
        report = {
            'period': {
                'start_date': start.isoformat(),
                'end_date': end.isoformat()
            },
            'summary': {},
            'by_channel': {},
            'by_category': [],
            'by_product': [],
            'by_day': [],
            'payment_methods': []
        }

        # Online sales
        if channel in ['all', 'online']:
            online_sales = self._get_online_sales(start, end, filters)
            report['summary']['online'] = online_sales['summary']
            if channel == 'online':
                report['by_category'] = online_sales['by_category']
                report['by_product'] = online_sales['by_product']
                report['by_day'] = online_sales['by_day']
                report['payment_methods'] = online_sales['payment_methods']

        # POS sales
        if channel in ['all', 'pos']:
            try:
                pos_sales = self._get_pos_sales(start, end, filters)
                report['summary']['pos'] = pos_sales['summary']
                if channel == 'pos':
                    report['by_category'] = pos_sales['by_category']
                    report['by_product'] = pos_sales['by_product']
                    report['by_day'] = pos_sales['by_day']
                    report['payment_methods'] = pos_sales['payment_methods']
            except Exception as e:
                # POS data might not be available yet
                print(f"POS sales error (non-critical): {str(e)}")
                report['summary']['pos'] = {
                    'total_transactions': 0,
                    'total_revenue': 0,
                    'average_transaction': 0
                }

        # Combined summary
        if channel == 'all':
            online_total = report['summary'].get('online', {}).get('total_revenue', 0)
            pos_total = report['summary'].get('pos', {}).get('total_revenue', 0)
            online_orders = report['summary'].get('online', {}).get('total_orders', 0)
            pos_orders = report['summary'].get('pos', {}).get('total_transactions', 0)

            report['summary']['combined'] = {
                'total_revenue': online_total + pos_total,
                'total_orders': online_orders + pos_orders,
                'average_order_value': (online_total + pos_total) / (online_orders + pos_orders) if (online_orders + pos_orders) > 0 else 0
            }

        return report

    def get_inventory_report(self, filters: Dict = None) -> Dict:
        """
        Generate inventory status report

        Args:
            filters: Optional filters (category_id, stock_status, sort_by)

        Returns:
            Inventory report data
        """
        filters = filters or {}

        # Base query for inventory
        query = db.session.query(
            ProductVariant.id,
            ProductVariant.sku,
            ProductVariant.size,
            ProductVariant.color,
            Product.id.label('product_id'),
            Product.name.label('product_name'),
            Category.name.label('category_name'),
            func.coalesce(Inventory.quantity, 0).label('stock_quantity'),
            func.coalesce(Inventory.reserved_quantity, 0).label('reserved_quantity'),
            func.coalesce(Product.price, 0).label('price')
        ).join(Product, ProductVariant.product_id == Product.id)\
         .outerjoin(Category, Product.category_id == Category.id)\
         .outerjoin(Inventory, ProductVariant.id == Inventory.variant_id)\
         .filter(Product.is_active == True)

        # Apply filters
        if filters.get('category_id'):
            query = query.filter(Product.category_id == filters['category_id'])

        if filters.get('stock_status'):
            if filters['stock_status'] == 'out_of_stock':
                query = query.filter(func.coalesce(Inventory.quantity, 0) <= 0)
            elif filters['stock_status'] == 'low_stock':
                query = query.filter(
                    and_(
                        func.coalesce(Inventory.quantity, 0) > 0,
                        func.coalesce(Inventory.quantity, 0) < 10
                    )
                )
            elif filters['stock_status'] == 'in_stock':
                query = query.filter(func.coalesce(Inventory.quantity, 0) >= 10)

        # Apply sorting
        sort_by = filters.get('sort_by', 'stock_asc')
        if sort_by == 'stock_asc':
            query = query.order_by(func.coalesce(Inventory.quantity, 0).asc())
        elif sort_by == 'stock_desc':
            query = query.order_by(func.coalesce(Inventory.quantity, 0).desc())
        elif sort_by == 'name':
            query = query.order_by(Product.name.asc())
        elif sort_by == 'category':
            query = query.order_by(Category.name.asc(), Product.name.asc())

        items = query.all()

        # Calculate summary statistics
        total_variants = len(items)
        out_of_stock = sum(1 for item in items if item.stock_quantity <= 0)
        low_stock = sum(1 for item in items if 0 < item.stock_quantity < 10)
        total_stock_value = sum(item.stock_quantity * item.price for item in items)
        total_units = sum(item.stock_quantity for item in items)

        # Format inventory items
        inventory_items = []
        for item in items:
            available = item.stock_quantity - item.reserved_quantity
            inventory_items.append({
                'variant_id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'category': item.category_name or 'Uncategorized',
                'sku': item.sku,
                'size': item.size,
                'color': item.color,
                'stock_quantity': item.stock_quantity,
                'reserved_quantity': item.reserved_quantity,
                'available_quantity': available,
                'unit_price': float(item.price),
                'stock_value': float(item.stock_quantity * item.price),
                'stock_status': self._get_stock_status(item.stock_quantity)
            })

        # Group by category
        by_category = db.session.query(
            Category.name,
            func.count(ProductVariant.id).label('variant_count'),
            func.sum(func.coalesce(Inventory.quantity, 0)).label('total_units'),
            func.sum(func.coalesce(Inventory.quantity, 0) * Product.price).label('total_value')
        ).join(Product, ProductVariant.product_id == Product.id)\
         .outerjoin(Category, Product.category_id == Category.id)\
         .outerjoin(Inventory, ProductVariant.id == Inventory.variant_id)\
         .filter(Product.is_active == True)\
         .group_by(Category.name)\
         .all()

        category_summary = []
        for cat in by_category:
            category_summary.append({
                'category': cat.name or 'Uncategorized',
                'variant_count': cat.variant_count,
                'total_units': cat.total_units or 0,
                'total_value': float(cat.total_value or 0)
            })

        return {
            'summary': {
                'total_variants': total_variants,
                'total_units': total_units,
                'total_stock_value': float(total_stock_value),
                'out_of_stock_count': out_of_stock,
                'low_stock_count': low_stock,
                'in_stock_count': total_variants - out_of_stock - low_stock
            },
            'by_category': category_summary,
            'items': inventory_items,
            'generated_at': datetime.utcnow().isoformat()
        }

    def get_customer_report(self, period: str = 'month') -> Dict:
        """
        Generate customer analytics report

        Args:
            period: 'week', 'month', 'quarter', 'year'

        Returns:
            Customer report data
        """
        # Determine date range
        end_date = datetime.utcnow()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        else:  # year
            start_date = end_date - timedelta(days=365)

        # Total customers
        total_customers = Customer.query.filter(Customer.anonymized == False).count()

        # New customers in period
        new_customers = Customer.query.filter(
            and_(
                Customer.created_at >= start_date,
                Customer.anonymized == False
            )
        ).count()

        # Active customers (made purchase in period)
        active_customers = db.session.query(
            func.count(func.distinct(Order.customer_id))
        ).filter(
            and_(
                Order.created_at >= start_date,
                Order.status != 'cancelled'
            )
        ).scalar() or 0

        # Customer lifetime value (top 20)
        top_customers = db.session.query(
            Customer.id,
            Customer.first_name_encrypted,
            Customer.last_name_encrypted,
            Customer.email_encrypted,
            func.count(Order.id).label('order_count'),
            func.sum(Order.total).label('total_spent')
        ).join(Order, Customer.id == Order.customer_id)\
         .filter(
             and_(
                 Customer.anonymized == False,
                 Order.status != 'cancelled'
             )
         )\
         .group_by(Customer.id, Customer.first_name_encrypted, Customer.last_name_encrypted, Customer.email_encrypted)\
         .order_by(desc('total_spent'))\
         .limit(20)\
         .all()

        top_customers_list = []
        for customer in top_customers:
            top_customers_list.append({
                'customer_id': customer.id,
                'name': f"{customer.first_name_encrypted} {customer.last_name_encrypted}",
                'email': customer.email_encrypted,
                'order_count': customer.order_count,
                'total_spent': float(customer.total_spent or 0),
                'average_order_value': float(customer.total_spent / customer.order_count) if customer.order_count > 0 else 0
            })

        # Customer acquisition by month (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        acquisition_by_month = db.session.query(
            func.date_trunc('month', Customer.created_at).label('month'),
            func.count(Customer.id).label('new_customers')
        ).filter(
            and_(
                Customer.created_at >= six_months_ago,
                Customer.anonymized == False
            )
        ).group_by(func.date_trunc('month', Customer.created_at))\
         .order_by(func.date_trunc('month', Customer.created_at))\
         .all()

        acquisition_data = []
        for month_data in acquisition_by_month:
            acquisition_data.append({
                'month': month_data.month.isoformat() if month_data.month else None,
                'new_customers': month_data.new_customers
            })

        # Customer retention (repeat purchase rate)
        customers_with_orders = db.session.query(
            Order.customer_id,
            func.count(Order.id).label('order_count')
        ).filter(Order.status != 'cancelled')\
         .group_by(Order.customer_id)\
         .all()

        repeat_customers = sum(1 for c in customers_with_orders if c.order_count > 1)
        total_with_orders = len(customers_with_orders)
        repeat_rate = (repeat_customers / total_with_orders * 100) if total_with_orders > 0 else 0

        return {
            'period': period,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_customers': total_customers,
                'new_customers': new_customers,
                'active_customers': active_customers,
                'repeat_purchase_rate': round(repeat_rate, 2)
            },
            'top_customers': top_customers_list,
            'acquisition_trend': acquisition_data,
            'generated_at': datetime.utcnow().isoformat()
        }

    def get_employee_performance_report(self, employee_id: int = None, period: str = 'month') -> Dict:
        """
        Generate employee performance report

        Args:
            employee_id: Specific employee ID (None for all employees)
            period: 'week', 'month', 'quarter', 'year'

        Returns:
            Employee performance report
        """
        # Determine date range
        end_date = datetime.utcnow()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        else:  # year
            start_date = end_date - timedelta(days=365)

        # Query POS transactions by employee
        query = db.session.query(
            Employee.id,
            Employee.full_name,
            Employee.role,
            func.count(POSTransaction.id).label('transaction_count'),
            func.sum(POSTransaction.total).label('total_sales'),
            func.avg(POSTransaction.total).label('average_transaction')
        ).join(POSTransaction, Employee.id == POSTransaction.employee_id)\
         .filter(
             and_(
                 POSTransaction.created_at >= start_date,
                 POSTransaction.status == 'completed'
             )
         )

        if employee_id:
            query = query.filter(Employee.id == employee_id)

        query = query.group_by(Employee.id, Employee.full_name, Employee.role)\
                    .order_by(desc('total_sales'))

        employees = query.all()

        employee_performance = []
        for emp in employees:
            employee_performance.append({
                'employee_id': emp.id,
                'name': emp.full_name,
                'role': emp.role,
                'transaction_count': emp.transaction_count,
                'total_sales': float(emp.total_sales or 0),
                'average_transaction': float(emp.average_transaction or 0)
            })

        # Overall statistics
        total_transactions = sum(emp.transaction_count for emp in employees)
        total_sales = sum(emp.total_sales or 0 for emp in employees)

        # If specific employee, get daily breakdown
        daily_breakdown = []
        if employee_id:
            daily_sales = db.session.query(
                func.date(POSTransaction.created_at).label('date'),
                func.count(POSTransaction.id).label('transactions'),
                func.sum(POSTransaction.total).label('sales')
            ).filter(
                and_(
                    POSTransaction.employee_id == employee_id,
                    POSTransaction.created_at >= start_date,
                    POSTransaction.status == 'completed'
                )
            ).group_by(func.date(POSTransaction.created_at))\
             .order_by(func.date(POSTransaction.created_at))\
             .all()

            for day in daily_sales:
                daily_breakdown.append({
                    'date': day.date.isoformat(),
                    'transactions': day.transactions,
                    'sales': float(day.sales or 0)
                })

        return {
            'period': period,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_employees': len(employees),
                'total_transactions': total_transactions,
                'total_sales': float(total_sales),
                'average_per_employee': float(total_sales / len(employees)) if len(employees) > 0 else 0
            },
            'employees': employee_performance,
            'daily_breakdown': daily_breakdown if employee_id else [],
            'generated_at': datetime.utcnow().isoformat()
        }

    # ===== PRIVATE HELPER METHODS =====

    def _get_online_sales(self, start: datetime, end: datetime, filters: Dict) -> Dict:
        """Get online sales data"""
        # Base query
        query = Order.query.filter(
            and_(
                Order.created_at >= start,
                Order.created_at < end,
                Order.status != 'cancelled'
            )
        )

        orders = query.all()

        # Summary
        total_orders = len(orders)
        total_revenue = sum(order.total or 0 for order in orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # By category
        by_category = db.session.query(
            Category.name,
            func.sum(OrderItem.quantity).label('units_sold'),
            func.sum(OrderItem.total_price).label('revenue')
        ).select_from(Order)\
         .join(OrderItem, Order.id == OrderItem.order_id)\
         .join(Product, OrderItem.product_id == Product.id)\
         .join(Category, Product.category_id == Category.id)\
         .filter(
             and_(
                 Order.created_at >= start,
                 Order.created_at < end,
                 Order.status != 'cancelled'
             )
         )\
         .group_by(Category.name)\
         .order_by(desc('revenue'))\
         .all()

        category_data = [{
            'category': cat.name,
            'units_sold': cat.units_sold,
            'revenue': float(cat.revenue or 0)
        } for cat in by_category]

        # By product
        by_product = db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label('units_sold'),
            func.sum(OrderItem.total_price).label('revenue')
        ).select_from(Order)\
         .join(OrderItem, Order.id == OrderItem.order_id)\
         .join(Product, OrderItem.product_id == Product.id)\
         .filter(
             and_(
                 Order.created_at >= start,
                 Order.created_at < end,
                 Order.status != 'cancelled'
             )
         )\
         .group_by(Product.name)\
         .order_by(desc('units_sold'))\
         .limit(20)\
         .all()

        product_data = [{
            'product': prod.name,
            'units_sold': prod.units_sold,
            'revenue': float(prod.revenue or 0)
        } for prod in by_product]

        # By day
        by_day = db.session.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('orders'),
            func.sum(Order.total).label('revenue')
        ).filter(
            and_(
                Order.created_at >= start,
                Order.created_at < end,
                Order.status != 'cancelled'
            )
        ).group_by(func.date(Order.created_at))\
         .order_by(func.date(Order.created_at))\
         .all()

        daily_data = [{
            'date': day.date.isoformat(),
            'orders': day.orders,
            'revenue': float(day.revenue or 0)
        } for day in by_day]

        # Payment methods
        by_payment = db.session.query(
            Payment.payment_method,
            func.count(Order.id).label('count'),
            func.sum(Order.total).label('amount')
        ).join(Payment, Order.id == Payment.order_id)\
         .filter(
             and_(
                 Order.created_at >= start,
                 Order.created_at < end,
                 Order.status != 'cancelled'
             )
         )\
         .group_by(Payment.payment_method)\
         .all()

        payment_data = [{
            'method': payment.payment_method,
            'count': payment.count,
            'amount': float(payment.amount or 0)
        } for payment in by_payment]

        return {
            'summary': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'average_order_value': float(avg_order_value)
            },
            'by_category': category_data,
            'by_product': product_data,
            'by_day': daily_data,
            'payment_methods': payment_data
        }

    def _get_pos_sales(self, start: datetime, end: datetime, filters: Dict) -> Dict:
        """Get POS sales data"""
        # Base query
        query = POSTransaction.query.filter(
            and_(
                POSTransaction.created_at >= start,
                POSTransaction.created_at < end,
                POSTransaction.status == 'completed'
            )
        )

        if filters.get('employee_id'):
            query = query.filter(POSTransaction.employee_id == filters['employee_id'])

        transactions = query.all()

        # Summary
        total_transactions = len(transactions)
        total_revenue = sum(txn.total or 0 for txn in transactions)
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0

        # By category
        by_category = db.session.query(
            Category.name,
            func.sum(POSTransactionItem.quantity).label('units_sold'),
            func.sum(POSTransactionItem.total_price).label('revenue')
        ).select_from(POSTransaction)\
         .join(POSTransactionItem, POSTransaction.id == POSTransactionItem.transaction_id)\
         .join(Product, POSTransactionItem.product_id == Product.id)\
         .join(Category, Product.category_id == Category.id)\
         .filter(
             and_(
                 POSTransaction.created_at >= start,
                 POSTransaction.created_at < end,
                 POSTransaction.status == 'completed'
             )
         )\
         .group_by(Category.name)\
         .order_by(desc('revenue'))\
         .all()

        category_data = [{
            'category': cat.name,
            'units_sold': cat.units_sold,
            'revenue': float(cat.revenue or 0)
        } for cat in by_category]

        # By product
        by_product = db.session.query(
            Product.name,
            func.sum(POSTransactionItem.quantity).label('units_sold'),
            func.sum(POSTransactionItem.total_price).label('revenue')
        ).select_from(POSTransaction)\
         .join(POSTransactionItem, POSTransaction.id == POSTransactionItem.transaction_id)\
         .join(Product, POSTransactionItem.product_id == Product.id)\
         .filter(
             and_(
                 POSTransaction.created_at >= start,
                 POSTransaction.created_at < end,
                 POSTransaction.status == 'completed'
             )
         )\
         .group_by(Product.name)\
         .order_by(desc('units_sold'))\
         .limit(20)\
         .all()

        product_data = [{
            'product': prod.name,
            'units_sold': prod.units_sold,
            'revenue': float(prod.revenue or 0)
        } for prod in by_product]

        # By day
        by_day = db.session.query(
            func.date(POSTransaction.created_at).label('date'),
            func.count(POSTransaction.id).label('transactions'),
            func.sum(POSTransaction.total).label('revenue')
        ).filter(
            and_(
                POSTransaction.created_at >= start,
                POSTransaction.created_at < end,
                POSTransaction.status == 'completed'
            )
        ).group_by(func.date(POSTransaction.created_at))\
         .order_by(func.date(POSTransaction.created_at))\
         .all()

        daily_data = [{
            'date': day.date.isoformat(),
            'transactions': day.transactions,
            'revenue': float(day.revenue or 0)
        } for day in by_day]

        # Payment methods
        by_payment = db.session.query(
            POSTransaction.payment_method,
            func.count(POSTransaction.id).label('count'),
            func.sum(POSTransaction.total).label('amount')
        ).filter(
            and_(
                POSTransaction.created_at >= start,
                POSTransaction.created_at < end,
                POSTransaction.status == 'completed'
            )
        )\
         .group_by(POSTransaction.payment_method)\
         .all()

        payment_data = [{
            'method': payment.payment_method,
            'count': payment.count,
            'amount': float(payment.amount or 0)
        } for payment in by_payment]

        return {
            'summary': {
                'total_transactions': total_transactions,
                'total_revenue': float(total_revenue),
                'average_transaction': float(avg_transaction)
            },
            'by_category': category_data,
            'by_product': product_data,
            'by_day': daily_data,
            'payment_methods': payment_data
        }

    def _get_stock_status(self, quantity: int) -> str:
        """Determine stock status"""
        if quantity <= 0:
            return 'out_of_stock'
        elif quantity < 10:
            return 'low_stock'
        else:
            return 'in_stock'
