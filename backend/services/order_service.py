"""
Order Service
Business logic for order creation and management.
Wraps stored procedures for secure, atomic order processing.
"""

import json
from typing import Dict, List, Optional
from decimal import Decimal

from extensions import db
from models.database_models import (
    Order, Customer,
    CartItem, Cart
)
from services.shipping_service import ShippingService
from services.encryption import encrypt_address


class OrderService:
    """Service for order creation and management"""

    @staticmethod
    def create_order(
        customer_id: int,
        shipping_address: Dict,
        billing_address: Optional[Dict],
        cart_items: List[CartItem],
        payment_method: str,
        ip_address: str,
        user_agent: str
    ) -> Dict:
        """
        Create order using stored procedure.

        Args:
            customer_id: Customer ID
            shipping_address: Dict with street, city, state, zip, phone
            billing_address: Optional billing address (if different)
            cart_items: List of CartItem objects
            payment_method: Payment method (cod, mpesa)
            ip_address: Client IP address (for audit)
            user_agent: Client user agent (for audit)

        Returns:
            dict: {
                'success': bool,
                'order_id': int,
                'order_number': str,
                'total': float,
                'payment_method': str,
                'error': str (if failed)
            }

        Raises:
            ValueError: If validation fails
            RuntimeError: If order creation fails
        """
        # Validate customer exists
        customer = Customer.query.get(customer_id)
        if not customer:
            raise ValueError(f'Customer not found: {customer_id}')

        # Validate cart not empty
        if not cart_items or len(cart_items) == 0:
            raise ValueError('Cart is empty')

        # Calculate shipping
        city = shipping_address.get('city', '')
        total_weight = ShippingService.get_cart_weight(cart_items)
        shipping_calc = ShippingService.calculate_shipping(city, total_weight)
        shipping_cost = Decimal(str(shipping_calc['cost']))
        is_nairobi = shipping_calc['is_nairobi']

        # Calculate subtotal from cart items
        subtotal = Decimal('0.00')
        cart_items_data = []

        for item in cart_items:
            variant = item.variant
            if not variant or not variant.product:
                raise ValueError('Invalid cart item: variant not found')

            product = variant.product
            if not product.is_active or not variant.is_active:
                raise ValueError(f'Product {product.name} is no longer available')

            # Use sale_price if available, otherwise regular price
            price = product.sale_price if product.sale_price else product.price
            item_total = price * item.quantity
            subtotal += item_total

            cart_items_data.append({
                'variant_id': variant.id,
                'quantity': item.quantity,
                'price': float(price)
            })

        # Calculate tax (0% for now, can be configured later)
        tax = Decimal('0.00')

        # Calculate total
        _total = subtotal + shipping_cost + tax

        # Encrypt addresses
        shipping_address_encrypted = encrypt_address(json.dumps(shipping_address))

        if billing_address:
            billing_address_encrypted = encrypt_address(json.dumps(billing_address))
        else:
            # Use shipping address as billing if not provided
            billing_address_encrypted = shipping_address_encrypted

        try:
            # Prepare cart items for stored procedure
            cart_items_json = []
            for item in cart_items:
                variant = item.variant
                product = variant.product
                price = product.sale_price if product.sale_price else product.price

                cart_items_json.append({
                    'variant_id': variant.id,
                    'quantity': item.quantity,
                    'unit_price': float(price)
                })

            # Convert cart items to JSON string for PostgreSQL
            cart_items_jsonb = json.dumps(cart_items_json)

            # Call stored procedure for atomic order creation
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_create_order_secure(
                        :customer_id,
                        :shipping_address_encrypted,
                        :billing_address_encrypted,
                        :payment_method,
                        CAST(:cart_items AS jsonb),
                        :shipping_method_id,
                        :is_nairobi,
                        :shipping_cost
                    )
                """),
                {
                    'customer_id': customer_id,
                    'shipping_address_encrypted': shipping_address_encrypted,
                    'billing_address_encrypted': billing_address_encrypted,
                    'payment_method': payment_method,
                    'cart_items': cart_items_jsonb,
                    'shipping_method_id': None,
                    'is_nairobi': is_nairobi,
                    'shipping_cost': float(shipping_cost)
                }
            )

            # Fetch result
            row = result.fetchone()
            if not row:
                raise RuntimeError('Stored procedure did not return result')

            order_id = row[0]
            order_number = row[1]
            _payment_id = row[2]
            total_amount = row[3]

            # Commit transaction
            db.session.commit()

            # Clear customer's cart after successful order
            Cart.query.filter_by(customer_id=customer_id).delete()
            db.session.commit()

            return {
                'success': True,
                'order_id': order_id,
                'order_number': order_number,
                'total': float(total_amount),
                'shipping_cost': float(shipping_cost),
                'is_nairobi': is_nairobi,
                'payment_method': payment_method
            }

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Order creation failed: {str(e)}')

    @staticmethod
    def get_order(order_id: int, customer_id: Optional[int] = None) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order ID
            customer_id: Optional customer ID (for authorization)

        Returns:
            Order object or None
        """
        query = Order.query.filter_by(id=order_id)

        if customer_id:
            query = query.filter_by(customer_id=customer_id)

        return query.first()

    @staticmethod
    def get_order_by_number(
        order_number: str,
        customer_id: Optional[int] = None
    ) -> Optional[Order]:
        """
        Get order by order number.

        Args:
            order_number: Order number (HP-YYYYMMDD-XXXX)
            customer_id: Optional customer ID (for authorization)

        Returns:
            Order object or None
        """
        query = Order.query.filter_by(order_number=order_number)

        if customer_id:
            query = query.filter_by(customer_id=customer_id)

        return query.first()

    @staticmethod
    def get_customer_orders(
        customer_id: int,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """
        Get all orders for a customer (paginated).

        Args:
            customer_id: Customer ID
            page: Page number (default: 1)
            per_page: Items per page (default: 10)

        Returns:
            dict: {
                'orders': list of order dicts,
                'pagination': {...}
            }
        """
        query = Order.query.filter_by(customer_id=customer_id).order_by(
            Order.created_at.desc()
        )

        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'orders': [order.to_dict(include_items=True) for order in paginated.items],
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'total_pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }

    @staticmethod
    def calculate_shipping_preview(cart_items: List[CartItem], city: str) -> Dict:
        """
        Preview shipping cost before checkout.

        Args:
            cart_items: List of CartItem objects
            city: Destination city

        Returns:
            dict: Shipping calculation result
        """
        return ShippingService.calculate_shipping_for_cart(cart_items, city)
