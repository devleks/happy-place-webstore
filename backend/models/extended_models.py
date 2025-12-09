"""
Extended Database Models for Happy Place Boutique
7 New Tables for Enhanced E-commerce Features

Tables:
1. CategoryClosure - Hierarchical category queries
2. ProductVariant - Normalized size/color management
3. Promotion - Discount/coupon management
4. OrderPromotion - Promotion usage tracking
5. ShippingMethod - Shipping options
6. Return - Return request management
7. ReturnItem - Return line items

Business Rules Implemented:
- Return window: 2 days
- Restocking fee: 10%
- Exchange-only: clearance & sale items
- Nairobi shipping: Free
- Referral codes: 5% discount
"""

from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint


# ========================
# CATEGORY HIERARCHY
# ========================

class CategoryClosure(db.Model):
    """
    Closure table for efficient category hierarchy queries.

    Stores all ancestor-descendant paths in the category tree.
    Enables O(1) queries like "all products under Women Clothing".

    Example:
    Category Tree:
    - Women Clothing (id=1)
      - Tops (id=2)
        - Blouses (id=3)

    Closure Table:
    (1, 1, 0) - Women Clothing to itself
    (1, 2, 1) - Women Clothing → Tops
    (1, 3, 2) - Women Clothing → Blouses
    (2, 2, 0) - Tops to itself
    (2, 3, 1) - Tops → Blouses
    (3, 3, 0) - Blouses to itself
    """
    __tablename__ = 'category_closure'

    ancestor_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
    descendant_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
    depth = db.Column(db.Integer, nullable=False)

    # Relationships
    ancestor = db.relationship('Category', foreign_keys=[ancestor_id], backref='descendant_paths')
    descendant = db.relationship('Category', foreign_keys=[descendant_id], backref='ancestor_paths')

    def to_dict(self):
        return {
            'ancestor_id': self.ancestor_id,
            'descendant_id': self.descendant_id,
            'depth': self.depth
        }


# ========================
# PRODUCT VARIANTS
# ========================

class ProductVariant(db.Model):
    """
    Normalized product variants (size/color combinations).

    Replaces storing sizes/colors as JSON in products table.
    Each variant has unique SKU and can be individually tracked in inventory.
    """
    __tablename__ = 'product_variants'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    size = db.Column(db.String(20), nullable=False)  # XS, S, M, L, XL, XXL
    color = db.Column(db.String(50), nullable=False)  # Black, White, Blue, etc.
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint: one variant per product/size/color combination
    __table_args__ = (
        UniqueConstraint('product_id', 'size', 'color', name='unique_product_variant'),
    )

    # Relationships
    product = db.relationship('Product', backref='variants')
    inventory = db.relationship('Inventory', backref='variant', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'sku': self.sku,
            'size': self.size,
            'color': self.color,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

    def to_dict_with_inventory(self):
        """Return variant data with inventory information."""
        inventory_data = {}
        if self.inventory:
            available_qty = self.inventory.quantity - self.inventory.reserved_quantity
            inventory_data = {
                'quantity': self.inventory.quantity,
                'reserved_quantity': self.inventory.reserved_quantity,
                'available_quantity': available_qty,
                'is_low_stock': self.inventory.is_low_stock,
                'is_out_of_stock': available_qty == 0
            }

        return {
            'id': self.id,
            'sku': self.sku,
            'size': self.size,
            'color': self.color,
            'is_active': self.is_active,
            'inventory': inventory_data
        }


# ========================
# PROMOTIONS
# ========================

class Promotion(db.Model):
    """
    Discount codes, sales, and promotional campaigns.

    Business Rules:
    - Referral codes: 5% discount
    - Can apply to all products, specific category, or specific product
    - Usage limits per customer and total
    - Time-bound validity
    """
    __tablename__ = 'promotions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "REFER5", "SUMMER25"
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Discount Configuration
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage', 'fixed_amount', 'free_shipping'
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)  # 5 (for 5%) or 500 (for KSh 500)

    # Conditions
    minimum_order_amount = db.Column(db.Numeric(10, 2))  # Minimum cart total
    maximum_discount_amount = db.Column(db.Numeric(10, 2))  # Cap for percentage discounts

    # Applicability
    applies_to = db.Column(db.String(20), default='all', nullable=False)  # 'all', 'category', 'product'
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    # Usage Limits
    usage_limit = db.Column(db.Integer)  # Total uses allowed (NULL = unlimited)
    usage_per_customer = db.Column(db.Integer, default=1)  # Uses per customer
    current_usage_count = db.Column(db.Integer, default=0)

    # Validity
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('Category')
    product = db.relationship('Product')

    @property
    def is_valid(self):
        """Check if promotion is currently valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            (self.usage_limit is None or self.current_usage_count < self.usage_limit)
        )

    @property
    def is_referral_code(self):
        """Check if this is a referral code (5% discount)"""
        return self.discount_type == 'percentage' and self.discount_value == 5

    def can_use(self, customer_id, order_total):
        """
        Check if customer can use this promotion.

        Args:
            customer_id: Customer attempting to use promotion
            order_total: Current order total

        Returns:
            tuple: (can_use: bool, reason: str)
        """
        if not self.is_valid:
            return False, "Promotion expired or inactive"

        # Check minimum order amount
        if self.minimum_order_amount and order_total < self.minimum_order_amount:
            return False, f"Minimum order amount is KSh {self.minimum_order_amount}"

        # Check customer usage limit
        from models.database_models import OrderPromotion
        customer_usage = OrderPromotion.query.join(Order).filter(
            OrderPromotion.promotion_id == self.id,
            Order.customer_id == customer_id
        ).count()

        if customer_usage >= self.usage_per_customer:
            return False, "You've already used this promotion"

        return True, "Valid"

    def calculate_discount(self, order_total):
        """
        Calculate discount amount for given order total.

        Args:
            order_total: Order subtotal

        Returns:
            Decimal: Discount amount in KSh
        """
        if self.discount_type == 'percentage':
            discount = order_total * (self.discount_value / 100)
            if self.maximum_discount_amount:
                discount = min(discount, self.maximum_discount_amount)
            return discount
        elif self.discount_type == 'fixed_amount':
            return min(self.discount_value, order_total)
        elif self.discount_type == 'free_shipping':
            return 0  # Handled separately in order total calculation

        return 0

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'minimum_order_amount': float(self.minimum_order_amount) if self.minimum_order_amount else None,
            'maximum_discount_amount': float(self.maximum_discount_amount) if self.maximum_discount_amount else None,
            'applies_to': self.applies_to,
            'category_id': self.category_id,
            'product_id': self.product_id,
            'usage_limit': self.usage_limit,
            'usage_per_customer': self.usage_per_customer,
            'current_usage_count': self.current_usage_count,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active,
            'is_valid': self.is_valid
        }


class OrderPromotion(db.Model):
    """
    Track promotions applied to orders.

    Stores which promotion codes were used on which orders
    for analytics and customer service.
    """
    __tablename__ = 'order_promotions'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    promotion_code = db.Column(db.String(50), nullable=False)  # Store code at time of use
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False)  # Actual discount applied
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('order_id', 'promotion_id', name='unique_order_promotion'),
    )

    # Relationships
    order = db.relationship('Order', backref='promotions_applied')
    promotion = db.relationship('Promotion')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'promotion_id': self.promotion_id,
            'promotion_code': self.promotion_code,
            'discount_amount': float(self.discount_amount),
            'applied_at': self.applied_at.isoformat()
        }


# ========================
# SHIPPING
# ========================

class ShippingMethod(db.Model):
    """
    Shipping options and costs.

    Business Rules:
    - Nairobi: Free shipping
    - Outside Nairobi: Variable cost
    """
    __tablename__ = 'shipping_methods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # "Nairobi Free Delivery", "Upcountry Standard"
    description = db.Column(db.Text)

    # Pricing
    base_cost = db.Column(db.Numeric(10, 2), nullable=False)  # Base shipping cost
    cost_per_kg = db.Column(db.Numeric(10, 2), default=0)  # Additional cost per kg

    # Delivery Estimates
    estimated_days_min = db.Column(db.Integer)  # Min delivery days
    estimated_days_max = db.Column(db.Integer)  # Max delivery days

    # Availability
    available_for_nairobi = db.Column(db.Boolean, default=True)
    available_outside_nairobi = db.Column(db.Boolean, default=True)

    # Free Shipping Threshold
    free_shipping_threshold = db.Column(db.Numeric(10, 2))  # Free if order > this amount

    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_cost(self, order_total, weight_kg=0, is_nairobi=True):
        """
        Calculate shipping cost for order.

        Args:
            order_total: Order subtotal
            weight_kg: Total weight in kg
            is_nairobi: Is shipping to Nairobi?

        Returns:
            Decimal: Shipping cost
        """
        # Check availability
        if is_nairobi and not self.available_for_nairobi:
            return None
        if not is_nairobi and not self.available_outside_nairobi:
            return None

        # Check free shipping threshold
        if self.free_shipping_threshold and order_total >= self.free_shipping_threshold:
            return 0

        # Nairobi is always free (business rule)
        if is_nairobi:
            return 0

        # Calculate cost for outside Nairobi
        cost = self.base_cost + (weight_kg * self.cost_per_kg)
        return cost

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'base_cost': float(self.base_cost),
            'cost_per_kg': float(self.cost_per_kg),
            'estimated_days_min': self.estimated_days_min,
            'estimated_days_max': self.estimated_days_max,
            'available_for_nairobi': self.available_for_nairobi,
            'available_outside_nairobi': self.available_outside_nairobi,
            'free_shipping_threshold': float(self.free_shipping_threshold) if self.free_shipping_threshold else None,
            'is_active': self.is_active
        }


# ========================
# RETURNS
# ========================

class Return(db.Model):
    """
    Return request management.

    Business Rules:
    - Return window: 2 days from delivery (regular-priced items only)
    - Restocking fee: 10% of item value (regular-priced items only)
    - FINAL SALE items: Clearance & Sale items (no returns, no exchanges)
    - Regular-priced items: Returns allowed (with 10% restocking fee)
    """
    __tablename__ = 'returns'

    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False)  # RMA-2025-001
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)

    # Return Details
    reason = db.Column(db.String(100), nullable=False)  # wrong_size, defective, not_as_described, changed_mind
    reason_description = db.Column(db.Text)

    # Status Workflow
    status = db.Column(db.String(20), nullable=False, default='pending')
    # pending → approved → received → refunded/exchanged
    # pending → rejected

    # Refund Information
    refund_method = db.Column(db.String(20))  # 'original_payment', 'store_credit', 'exchange'
    refund_amount = db.Column(db.Numeric(10, 2))
    restocking_fee = db.Column(db.Numeric(10, 2), default=0)  # 10% of item price

    # Approval Workflow
    approved_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    approved_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    processed_at = db.Column(db.DateTime)

    # Return Shipping
    return_tracking_number = db.Column(db.String(100))
    received_at = db.Column(db.DateTime)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', backref='returns')
    customer = db.relationship('Customer')
    approver = db.relationship('Employee', foreign_keys=[approved_by])
    processor = db.relationship('Employee', foreign_keys=[processed_by])
    items = db.relationship('ReturnItem', backref='return_request', lazy=True, cascade='all, delete-orphan')

    @property
    def is_within_return_window(self):
        """Check if return request is within 2-day window"""
        if not self.order.delivered_at:
            return False

        return_deadline = self.order.delivered_at + timedelta(days=2)
        return datetime.utcnow() <= return_deadline

    @property
    def can_return(self):
        """
        Check if items can be returned (business rules).

        Returns:
            tuple: (can_return: bool, reason: str)
        """
        # Check return window
        if not self.is_within_return_window:
            return False, "Return window expired (2 days from delivery)"

        # Check if any items are clearance or on sale (FINAL SALE - no returns, no exchanges)
        for item in self.items:
            product = item.variant.product
            if hasattr(product, 'is_clearance') and product.is_clearance:
                return False, "Clearance items are FINAL SALE - no returns or exchanges allowed"
            if hasattr(product, 'sale_price') and product.sale_price:
                return False, "Sale items are FINAL SALE - no returns or exchanges allowed"

        return True, "Return allowed (10% restocking fee applies)"

    def calculate_refund_amount(self):
        """
        Calculate refund amount with 10% restocking fee.

        Returns:
            Decimal: Refund amount
        """
        total_return_value = sum(
            item.quantity_returned * item.order_item.unit_price
            for item in self.items
        )

        # Apply 10% restocking fee
        restocking_fee = total_return_value * 0.10
        refund_amount = total_return_value - restocking_fee

        self.restocking_fee = restocking_fee
        self.refund_amount = refund_amount

        return refund_amount

    def to_dict(self):
        return {
            'id': self.id,
            'return_number': self.return_number,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'reason': self.reason,
            'reason_description': self.reason_description,
            'status': self.status,
            'refund_method': self.refund_method,
            'refund_amount': float(self.refund_amount) if self.refund_amount else None,
            'restocking_fee': float(self.restocking_fee),
            'is_within_return_window': self.is_within_return_window,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }


class ReturnItem(db.Model):
    """
    Individual items in a return request.

    Supports partial returns (customer can return some items from an order).
    """
    __tablename__ = 'return_items'

    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('returns.id', ondelete='CASCADE'), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)

    quantity_returned = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(20))  # 'unopened', 'opened', 'damaged', 'worn'

    # Restocking
    restocked = db.Column(db.Boolean, default=False)
    restocked_at = db.Column(db.DateTime)
    restocked_by = db.Column(db.Integer, db.ForeignKey('employees.id'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Check constraint: quantity_returned must be > 0
    __table_args__ = (
        CheckConstraint('quantity_returned > 0', name='check_return_quantity_positive'),
    )

    # Relationships
    order_item = db.relationship('OrderItem')
    variant = db.relationship('ProductVariant')
    restocker = db.relationship('Employee', foreign_keys=[restocked_by])

    def to_dict(self):
        return {
            'id': self.id,
            'return_id': self.return_id,
            'order_item_id': self.order_item_id,
            'variant_id': self.variant_id,
            'quantity_returned': self.quantity_returned,
            'condition': self.condition,
            'restocked': self.restocked,
            'restocked_at': self.restocked_at.isoformat() if self.restocked_at else None,
            'created_at': self.created_at.isoformat()
        }
