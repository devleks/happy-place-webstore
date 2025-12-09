"""
Order Management Service
Handles order processing, status updates, cancellations, and refunds
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import and_, or_, desc
from models.database_models import (
    db, Order, OrderItem, Customer, Product, Inventory
)
from models.extended_models import ProductVariant
from decimal import Decimal
import json


class OrderManagementService:
    """Service for managing orders"""

    def get_order_list(self, filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
        """
        Get paginated order list with filters

        Args:
            filters: Dict with status, payment_status, customer_id, search, date_from, date_to
            page: Page number
            per_page: Items per page

        Returns:
            Paginated order data
        """
        filters = filters or {}

        # Base query
        query = Order.query

        # Apply filters
        if filters.get('status'):
            query = query.filter(Order.status == filters['status'])

        if filters.get('payment_status'):
            query = query.filter(Order.payment_status == filters['payment_status'])

        if filters.get('customer_id'):
            query = query.filter(Order.customer_id == filters['customer_id'])

        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.join(Customer).filter(
                or_(
                    Customer.first_name.ilike(search_term),
                    Customer.last_name.ilike(search_term),
                    Customer.email.ilike(search_term)
                )
            )

        if filters.get('date_from'):
            query = query.filter(Order.created_at >= filters['date_from'])

        if filters.get('date_to'):
            query = query.filter(Order.created_at <= filters['date_to'])

        # Order by most recent first
        query = query.order_by(desc(Order.created_at))

        # Pagination
        total_count = query.count()
        orders = query.offset((page - 1) * per_page).limit(per_page).all()

        order_list = []
        for order in orders:
            customer = order.customer
            items_count = len(order.items) if order.items else 0

            # Get payment info from payment relationship
            payment_method = order.payment.payment_method if order.payment else 'unknown'
            payment_status = order.payment.status if order.payment else 'pending'

            order_list.append({
                'id': order.id,
                'order_number': order.order_number,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'customer_id': order.customer_id,
                'customer_name': f"{customer.first_name} {customer.last_name}" if customer else 'Guest',
                'customer_email': customer.email if customer else None,
                'customer_phone': customer.phone if customer else None,
                'items_count': items_count,
                'total_amount': float(order.total) if order.total else 0,
                'subtotal': float(order.subtotal) if order.subtotal else 0,
                'tax': float(order.tax) if order.tax else 0,
                'shipping_cost': float(order.shipping_cost) if order.shipping_cost else 0,
                'payment_method': payment_method,
                'payment_status': payment_status,
                'status': order.status
            })

        return {
            'orders': order_list,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }

    def get_order_details(self, order_id: int) -> Dict:
        """
        Get complete order details

        Args:
            order_id: Order ID

        Returns:
            Order details dictionary
        """
        order = Order.query.get(order_id)
        if not order:
            return {'error': 'Order not found'}

        customer = order.customer
        items = []

        for item in order.items:
            variant = item.variant
            product = variant.product if variant else None

            items.append({
                'id': item.id,
                'product_name': product.name if product else 'Unknown Product',
                'variant_id': item.variant_id,
                'size': variant.size if variant else None,
                'color': variant.color if variant else None,
                'sku': variant.sku if variant else None,
                'quantity': item.quantity,
                'price': float(item.unit_price) if item.unit_price else 0,
                'subtotal': float(item.total_price) if item.total_price else 0
            })

        # Parse addresses
        shipping_address = json.loads(order.shipping_address_encrypted) if order.shipping_address_encrypted else {}
        billing_address = json.loads(order.billing_address_encrypted) if order.billing_address_encrypted else {}

        # Get payment info from payment relationship
        payment_method = order.payment.payment_method if order.payment else 'unknown'
        payment_status = order.payment.status if order.payment else 'pending'

        return {
            'id': order.id,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'status': order.status,
            'payment_status': payment_status,
            'payment_method': payment_method,
            'customer': {
                'id': customer.id if customer else None,
                'name': f"{customer.first_name} {customer.last_name}" if customer else 'Guest',
                'email': customer.email if customer else None,
                'phone': customer.phone if customer else None
            },
            'items': items,
            'subtotal': float(order.subtotal) if order.subtotal else 0,
            'shipping_cost': float(order.shipping_cost) if order.shipping_cost else 0,
            'tax': float(order.tax) if order.tax else 0,
            'total': float(order.total) if order.total else 0,
            'shipping_address': shipping_address,
            'billing_address': billing_address,
            'shipping_method': order.shipping_method.name if order.shipping_method else None,
            'tracking_number': getattr(order, 'tracking_number', None),
            'notes': getattr(order, 'notes', None)
        }

    def update_order_status(self, order_id: int, status: str, tracking: Dict = None, employee_id: int = None) -> bool:
        """
        Update order status and tracking info

        Args:
            order_id: Order ID
            status: New status (pending, processing, shipped, completed, cancelled)
            tracking: Optional tracking info {carrier, number, notes}
            employee_id: Employee making the update

        Returns:
            Success boolean
        """
        try:
            order = Order.query.get(order_id)
            if not order:
                return False

            order.status = status

            if tracking:
                # Note: tracking number and notes not currently in Order model
                # Would need to add these fields to Order model
                if 'notes' in tracking and hasattr(order, 'notes'):
                    order.notes = tracking['notes']

            if status == 'shipped':
                order.shipped_at = datetime.now()
            elif status in ['delivered', 'completed']:
                order.delivered_at = datetime.now()

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error updating order status: {e}")
            return False

    def cancel_order(self, order_id: int, reason: str, refund: bool = True, notify: bool = True) -> bool:
        """
        Cancel order with optional refund

        Args:
            order_id: Order ID
            reason: Cancellation reason
            refund: Whether to refund payment
            notify: Whether to notify customer

        Returns:
            Success boolean
        """
        try:
            order = Order.query.get(order_id)
            if not order:
                return False

            # Update order status
            order.status = 'cancelled'
            order.notes = f"Cancelled: {reason}"

            # Restore inventory
            for item in order.items:
                inventory = Inventory.query.filter_by(variant_id=item.variant_id).first()
                if inventory:
                    inventory.quantity += item.quantity
                    if inventory.reserved_quantity >= item.quantity:
                        inventory.reserved_quantity -= item.quantity

            # Handle refund
            if refund and order.payment and order.payment.status == 'paid':
                order.payment.status = 'refunded'

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error cancelling order: {e}")
            return False

    def process_refund(self, order_id: int, refund_data: Dict) -> Dict:
        """
        Process full or partial refund

        Args:
            order_id: Order ID
            refund_data: {type: 'full'|'partial', amount, reason, method}

        Returns:
            Result dictionary
        """
        try:
            order = Order.query.get(order_id)
            if not order:
                return {'success': False, 'error': 'Order not found'}

            refund_type = refund_data.get('type', 'full')
            reason = refund_data.get('reason', 'Customer request')

            if refund_type == 'full':
                refund_amount = order.total
                # Update payment status
                if order.payment:
                    order.payment.status = 'refunded'
                order.status = 'cancelled'
            else:
                refund_amount = Decimal(str(refund_data.get('amount', 0)))

            order.notes = f"{order.notes or ''}\nRefund: {reason} - Amount: {refund_amount}"

            db.session.commit()

            return {
                'success': True,
                'refund_amount': float(refund_amount),
                'order_id': order_id
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def add_order_note(self, order_id: int, note: str, employee_id: int) -> bool:
        """
        Add internal note to order

        Args:
            order_id: Order ID
            note: Note text
            employee_id: Employee adding note

        Returns:
            Success boolean
        """
        try:
            order = Order.query.get(order_id)
            if not order:
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            order.notes = f"{order.notes or ''}\n[{timestamp}] {note}"

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error adding order note: {e}")
            return False

    def get_order_timeline(self, order_id: int) -> List[Dict]:
        """
        Get order event timeline

        Args:
            order_id: Order ID

        Returns:
            List of timeline events
        """
        order = Order.query.get(order_id)
        if not order:
            return []

        timeline = []

        # Order placed
        timeline.append({
            'event': 'order_placed',
            'title': 'Order Placed',
            'timestamp': order.created_at.isoformat() if order.created_at else None,
            'description': 'Customer placed the order'
        })

        # Payment confirmed
        payment_status = order.payment.status if order.payment else 'pending'
        payment_method = order.payment.payment_method if order.payment else 'unknown'
        if payment_status == 'paid':
            timeline.append({
                'event': 'payment_confirmed',
                'title': 'Payment Confirmed',
                'timestamp': order.created_at.isoformat() if order.created_at else None,
                'description': f'Payment via {payment_method}'
            })

        # Status changes (would need order_status_log table for accurate tracking)
        if order.status == 'processing':
            timeline.append({
                'event': 'processing',
                'title': 'Order Processing',
                'timestamp': order.created_at.isoformat() if order.created_at else None,
                'description': 'Order is being prepared'
            })

        if order.status == 'shipped':
            shipping_method_name = order.shipping_method.name if order.shipping_method else 'Standard'
            timeline.append({
                'event': 'shipped',
                'title': 'Order Shipped',
                'timestamp': order.shipped_at.isoformat() if order.shipped_at else order.created_at.isoformat() if order.created_at else None,
                'description': f'Shipped via {shipping_method_name}',
                'tracking': getattr(order, 'tracking_number', None)
            })

        if order.status in ['delivered', 'completed'] and order.delivered_at:
            timeline.append({
                'event': 'completed',
                'title': 'Order Delivered',
                'timestamp': order.delivered_at.isoformat() if order.delivered_at else None,
                'description': 'Order delivered successfully'
            })

        if order.status == 'cancelled':
            timeline.append({
                'event': 'cancelled',
                'title': 'Order Cancelled',
                'timestamp': order.created_at.isoformat() if order.created_at else None,
                'description': 'Order was cancelled'
            })

        return timeline

    def notify_customer(self, order_id: int, notification_type: str) -> bool:
        """
        Send notification to customer (placeholder for email service)

        Args:
            order_id: Order ID
            notification_type: 'order_confirmation', 'shipped', 'delivered', 'cancelled'

        Returns:
            Success boolean
        """
        # Placeholder for email notification
        # Would integrate with email service in production
        print(f"Notification {notification_type} sent for order {order_id}")
        return True
