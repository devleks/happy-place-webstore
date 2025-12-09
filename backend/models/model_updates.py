"""
Model Updates for Integration with Extended Tables

This file documents the changes needed to existing models
to work with the 7 new tables.

Apply these changes to database_models.py:
"""

# ========================
# PRODUCT MODEL UPDATES
# ========================

"""
Add to Product model:

1. is_clearance field (for return policy):
   is_clearance = db.Column(db.Boolean, default=False, nullable=False)

2. weight field (for shipping calculation):
   weight = db.Column(db.Numeric(8, 2))  # Weight in kg

3. Remove size/color fields (now in ProductVariant):
   # DELETE: sizes = db.Column(db.String(200))
   # DELETE: colors = db.Column(db.String(200))

Updated Product model snippet:
"""

PRODUCT_UPDATES = """
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2))  # If set, item is "on sale"
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    sku = db.Column(db.String(50), unique=True)

    # NEW: Return policy fields
    is_clearance = db.Column(db.Boolean, default=False, nullable=False)

    # NEW: Shipping calculation
    weight = db.Column(db.Numeric(8, 2))  # Weight in kg

    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (updated)
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all, delete-orphan')  # NEW
    reviews = db.relationship('Review', backref='product', lazy=True)

    @property
    def is_on_sale(self):
        '''Check if product is on sale'''
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def can_be_returned(self):
        '''Check if product can be returned (business rules)'''
        # Clearance items: exchange-only (no returns)
        if self.is_clearance:
            return False
        # Sale items: exchange-only (no returns)
        if self.is_on_sale:
            return False
        # Regular items: returns allowed
        return True
"""

# ========================
# ORDER MODEL UPDATES
# ========================

"""
Add to Order model:

1. shipping_method_id (FK to shipping_methods):
   shipping_method_id = db.Column(db.Integer, db.ForeignKey('shipping_methods.id'))

2. delivered_at (for return window calculation):
   delivered_at = db.Column(db.DateTime)

3. is_nairobi field (for shipping cost calculation):
   is_nairobi = db.Column(db.Boolean, default=True)

Updated Order model snippet:
"""

ORDER_UPDATES = """
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax = db.Column(db.Numeric(10, 2), default=0)
    shipping_cost = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # NEW: Shipping method
    shipping_method_id = db.Column(db.Integer, db.ForeignKey('shipping_methods.id'))
    is_nairobi = db.Column(db.Boolean, default=True)  # For shipping cost calculation

    # Encrypted shipping/billing addresses
    shipping_address_encrypted = db.Column(EncryptedAddressString, nullable=False)
    billing_address_encrypted = db.Column(EncryptedAddressString)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)  # NEW: For return window calculation

    # Relationships (updated)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', lazy=True, uselist=False)
    shipping_method = db.relationship('ShippingMethod')  # NEW
    returns = db.relationship('Return', backref='order', lazy=True)  # NEW

    @property
    def can_request_return(self):
        '''Check if order can be returned (within 2-day window)'''
        if not self.delivered_at:
            return False

        from datetime import timedelta
        return_deadline = self.delivered_at + timedelta(days=2)
        return datetime.utcnow() <= return_deadline
"""

# ========================
# INVENTORY MODEL UPDATES
# ========================

"""
Update Inventory model:

1. Replace product_id + size + color with variant_id:
   variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False, unique=True)

2. Replace online_quantity + store_quantity with single quantity:
   quantity = db.Column(db.Integer, nullable=False, default=0)

3. Remove size and color columns (now in ProductVariant)

Updated Inventory model:
"""

INVENTORY_UPDATES = """
class Inventory(db.Model):
    '''
    Unified inventory tracking.

    Single quantity field for both online and store (as per user requirement).
    References ProductVariant instead of storing size/color directly.
    '''
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=False, unique=True)

    # Single quantity for both store and online (user requirement)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reserved_quantity = db.Column(db.Integer, nullable=False, default=0)  # Pending unpaid orders

    low_stock_threshold = db.Column(db.Integer, default=5)
    last_restocked_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    variant = db.relationship('ProductVariant', backref='inventory')

    @property
    def available_quantity(self):
        '''Quantity available for sale (total - reserved)'''
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def is_low_stock(self):
        '''Check if stock is low'''
        return self.available_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        '''Check if completely out of stock'''
        return self.available_quantity == 0

    def to_dict(self):
        return {
            'id': self.id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'is_low_stock': self.is_low_stock,
            'is_out_of_stock': self.is_out_of_stock,
            'last_restocked_at': self.last_restocked_at.isoformat() if self.last_restocked_at else None,
            'updated_at': self.updated_at.isoformat()
        }
"""

# ========================
# CART_ITEMS MODEL UPDATES
# ========================

"""
Update CartItem model to reference ProductVariant:

OLD:
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)

NEW:
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
"""

CART_ITEM_UPDATES = """
class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)  # UPDATED
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    variant = db.relationship('ProductVariant')  # UPDATED

    def to_dict(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'variant': self.variant.to_dict() if self.variant else None,
            'product': self.variant.product.to_dict() if self.variant else None,
            'added_at': self.added_at.isoformat()
        }
"""

# ========================
# ORDER_ITEMS MODEL UPDATES
# ========================

"""
Update OrderItem model to reference ProductVariant:
"""

ORDER_ITEM_UPDATES = """
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)  # Keep for order history
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)  # NEW
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')  # NEW

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'product': self.product.to_dict(include_images=False) if self.product else None,
            'variant': self.variant.to_dict() if self.variant else None
        }
"""

# ========================
# MODEL IMPORTS UPDATE
# ========================

"""
Update models/__init__.py to include new models:
"""

MODELS_INIT_UPDATE = """
from .encrypted_types import (
    EncryptedCustomerString,
    EncryptedAddressString,
    EncryptedPaymentString
)

from .database_models import (
    Customer, CustomerAddress, Employee,
    Category, Product, ProductImage, Inventory,
    Cart, CartItem, Wishlist, WishlistItem,
    Order, OrderItem, Payment, Review,
    POSTransaction, POSTransactionItem, StoreLocation,
    GDPRDataRequest, GDPRConsentLog, DataAccessLog, ActivityLog
)

from .extended_models import (
    CategoryClosure,
    ProductVariant,
    Promotion, OrderPromotion,
    ShippingMethod,
    Return, ReturnItem
)

__all__ = [
    # Encrypted types
    'EncryptedCustomerString', 'EncryptedAddressString', 'EncryptedPaymentString',

    # Core models
    'Customer', 'CustomerAddress', 'Employee',
    'Category', 'Product', 'ProductImage', 'Inventory',

    # Shopping
    'Cart', 'CartItem', 'Wishlist', 'WishlistItem',

    # Orders
    'Order', 'OrderItem', 'Payment', 'Review',

    # POS
    'POSTransaction', 'POSTransactionItem', 'StoreLocation',

    # GDPR
    'GDPRDataRequest', 'GDPRConsentLog', 'DataAccessLog', 'ActivityLog',

    # Extended models
    'CategoryClosure', 'ProductVariant',
    'Promotion', 'OrderPromotion',
    'ShippingMethod',
    'Return', 'ReturnItem'
]
"""

print("Model updates documented. Apply these changes to database_models.py")
