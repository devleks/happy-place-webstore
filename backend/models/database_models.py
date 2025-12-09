"""
Database Models for Happy Place Boutique

Complete 22-table schema with:
- GDPR compliance (anonymization, consent tracking)
- MultiFernet encryption for PII fields
- Separate Customer and Employee models
- E-commerce features (cart, wishlist, orders)
- POS system support
- Audit logging

Tables:
- customers, customer_addresses, employees
- categories, products, product_images, inventory
- carts, cart_items, wishlists, wishlist_items
- orders, order_items, payments, reviews
- pos_transactions, pos_transaction_items, store_locations
- gdpr_data_requests, gdpr_consent_log, data_access_log, activity_logs
"""

from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from models.encrypted_types import (
    EncryptedCustomerString,
    EncryptedAddressString,
    EncryptedPaymentString
)
from services.encryption import hash_email


# ========================
# CUSTOMER MANAGEMENT
# ========================

class Customer(db.Model):
    """
    Customer model for online shoppers (GDPR-compliant).

    Features:
    - Dual email storage (hash for search, encrypted for privacy)
    - Encrypted PII fields (name, phone)
    - GDPR fields (consent, anonymization)
    - Data retention tracking
    """
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)

    # Dual email storage: hash for login lookup, encrypted for privacy
    email_hash = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email_encrypted = db.Column(EncryptedCustomerString, nullable=False)

    # Encrypted PII fields
    first_name_encrypted = db.Column(EncryptedCustomerString, nullable=False)
    last_name_encrypted = db.Column(EncryptedCustomerString, nullable=False)
    phone_encrypted = db.Column(EncryptedCustomerString)

    # Password (one-way Argon2 hash, NOT encrypted)
    password_hash = db.Column(db.String(255), nullable=False)

    # GDPR compliance fields
    gdpr_consent = db.Column(db.Boolean, default=False, nullable=False)
    marketing_consent = db.Column(db.Boolean, default=False, nullable=False)
    data_retention_date = db.Column(db.Date)  # When to auto-anonymize (3+ years inactive)
    anonymized = db.Column(db.Boolean, default=False, nullable=False)
    anonymized_at = db.Column(db.DateTime)

    # Account management
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    addresses = db.relationship('CustomerAddress', backref='customer', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='customer', lazy=True)
    cart = db.relationship('Cart', backref='customer', lazy=True, uselist=False)
    wishlist = db.relationship('Wishlist', backref='customer', lazy=True, uselist=False)
    gdpr_requests = db.relationship('GDPRDataRequest', backref='customer', lazy=True)
    consent_logs = db.relationship('GDPRConsentLog', backref='customer', lazy=True)

    @property
    def email(self):
        """Get decrypted email"""
        return self.email_encrypted

    @email.setter
    def email(self, value):
        """Set email (both hash and encrypted)"""
        self.email_hash = hash_email(value)
        self.email_encrypted = value

    @property
    def first_name(self):
        """Get decrypted first name"""
        return self.first_name_encrypted

    @first_name.setter
    def first_name(self, value):
        """Set encrypted first name"""
        self.first_name_encrypted = value

    @property
    def last_name(self):
        """Get decrypted last name"""
        return self.last_name_encrypted

    @last_name.setter
    def last_name(self, value):
        """Set encrypted last name"""
        self.last_name_encrypted = value

    @property
    def phone(self):
        """Get decrypted phone"""
        return self.phone_encrypted

    @phone.setter
    def phone(self, value):
        """Set encrypted phone"""
        self.phone_encrypted = value

    def set_password(self, password):
        """Hash password using Werkzeug (Argon2 compatible)"""
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def anonymize(self, performed_by=None, reason='GDPR Right to be Forgotten request'):
        """
        Anonymize customer data (GDPR Right to be Forgotten).
        Uses comprehensive GDPR stored procedure that handles validation,
        audit logging, and order preservation.
        
        Args:
            performed_by: Employee ID performing the anonymization
            reason: Reason for anonymization (for audit trail)
        """
        from extensions import db
        import sqlalchemy
        
        try:
            # Call existing comprehensive GDPR anonymization stored procedure
            result = db.session.execute(
                sqlalchemy.text("""
                    SELECT sp_gdpr_anonymize_customer(
                        :customer_id,
                        :performed_by,
                        :reason
                    )
                """),
                {
                    'customer_id': self.id,
                    'performed_by': performed_by,
                    'reason': reason
                }
            )
            
            # Get result and commit
            anonymization_result = result.fetchone()[0]
            db.session.commit()
            
            # Refresh this object to get updated values
            db.session.refresh(self)
            
            return anonymization_result
            
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'Anonymization failed: {str(e)}')

    def to_dict(self, include_pii=True):
        """Convert to dictionary (exclude PII if anonymized or not authorized)"""
        data = {
            'id': self.id,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat(),
            'anonymized': self.anonymized
        }

        if include_pii and not self.anonymized:
            data.update({
                'email': self.email,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'phone': self.phone,
                'gdpr_consent': self.gdpr_consent,
                'marketing_consent': self.marketing_consent
            })

        return data


class CustomerAddress(db.Model):
    """
    Customer shipping/billing addresses with encrypted fields.
    Cascade deleted when customer is anonymized (GDPR).
    """
    __tablename__ = 'customer_addresses'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)

    # Encrypted address fields
    address_line1_encrypted = db.Column(EncryptedAddressString, nullable=False)
    address_line2_encrypted = db.Column(EncryptedAddressString)
    city_encrypted = db.Column(EncryptedAddressString, nullable=False)
    postal_code_encrypted = db.Column(EncryptedAddressString)

    # Non-sensitive fields (not encrypted)
    country = db.Column(db.String(100), nullable=False, default='Kenya')
    address_type = db.Column(db.String(20), nullable=False, default='shipping')  # shipping, billing, both
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def address_line1(self):
        return self.address_line1_encrypted

    @address_line1.setter
    def address_line1(self, value):
        self.address_line1_encrypted = value

    @property
    def address_line2(self):
        return self.address_line2_encrypted

    @address_line2.setter
    def address_line2(self, value):
        self.address_line2_encrypted = value

    @property
    def city(self):
        return self.city_encrypted

    @city.setter
    def city(self, value):
        self.city_encrypted = value

    @property
    def postal_code(self):
        return self.postal_code_encrypted

    @postal_code.setter
    def postal_code(self, value):
        self.postal_code_encrypted = value

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'postal_code': self.postal_code,
            'country': self.country,
            'address_type': self.address_type,
            'is_default': self.is_default
        }


class Employee(db.Model):
    """
    Employee model for system users (admin, manager, cashier, staff).
    NOT subject to GDPR anonymization.
    """
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # admin, manager, cashier, staff
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    pos_transactions = db.relationship('POSTransaction', backref='employee', lazy=True)
    activity_logs = db.relationship('ActivityLog', foreign_keys='ActivityLog.employee_id', backref='employee', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


# ========================
# PRODUCT CATALOG
# ========================

class Category(db.Model):
    """Product categories (Women's Clothing, Maternity Wear, etc.)"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'parent_id': self.parent_id,
            'display_order': self.display_order,
            'is_active': self.is_active
        }


class Product(db.Model):
    """Product catalog"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    sku = db.Column(db.String(50), unique=True)

    # NEW: Return policy and shipping fields
    is_clearance = db.Column(db.Boolean, default=False, nullable=False)
    weight = db.Column(db.Numeric(8, 2))  # Weight in kg for shipping calculation

    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    # Note: variants relationship is defined in ProductVariant model with backref='variants'
    reviews = db.relationship('Review', backref='product', lazy=True)

    @property
    def is_on_sale(self):
        """Check if product is on sale"""
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def can_be_returned(self):
        """Check if product can be returned (business rules: clearance and sale items are exchange-only)"""
        if self.is_clearance:
            return False
        if self.is_on_sale:
            return False
        return True

    def to_dict(self, include_images=True, include_variants=False):
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'price': float(self.price),
            'sale_price': float(self.sale_price) if self.sale_price else None,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'sku': self.sku,
            'is_clearance': self.is_clearance,
            'weight': float(self.weight) if self.weight else None,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_images:
            data['images'] = [img.to_dict() for img in self.images]
            data['primary_image'] = next((img.to_dict() for img in self.images if img.is_primary), None)

        if include_variants:
            data['variants'] = [variant.to_dict() for variant in self.variants]

        return data


class ProductImage(db.Model):
    """
    Product images (one-to-many relationship with Product).
    Replaces single image_url string with proper image management.
    """
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(200))
    display_order = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'image_url': self.image_url,
            'alt_text': self.alt_text,
            'display_order': self.display_order,
            'is_primary': self.is_primary
        }


class Inventory(db.Model):
    """
    Unified inventory tracking for both online and physical store.
    Single quantity field for both channels (as per user requirement).
    References ProductVariant instead of storing size/color directly.
    """
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=False, unique=True)

    # Single quantity for both store and online (user requirement: "So it is clear when quantities are low")
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reserved_quantity = db.Column(db.Integer, nullable=False, default=0)  # Pending unpaid orders

    low_stock_threshold = db.Column(db.Integer, default=5)
    last_restocked_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Note: variant relationship is defined in ProductVariant model with backref='variant'

    @property
    def available_quantity(self):
        """Quantity available for sale (total - reserved)"""
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def is_low_stock(self):
        """Check if stock is low"""
        return self.available_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        """Check if completely out of stock"""
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


# ========================
# E-COMMERCE FEATURES
# ========================

class Cart(db.Model):
    """Shopping cart for customers"""
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'items': [item.to_dict() for item in self.items],
            'total_items': len(self.items),
            'updated_at': self.updated_at.isoformat()
        }


class CartItem(db.Model):
    """Items in shopping cart"""
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    variant = db.relationship('ProductVariant')

    def to_dict(self):
        variant_data = None
        product_data = None

        if self.variant:
            variant_data = self.variant.to_dict()
            if self.variant.product:
                product_data = self.variant.product.to_dict()
                # Add product data to variant for easier access
                variant_data['product'] = product_data

        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'variant': variant_data,
            'product': product_data,
            'added_at': self.added_at.isoformat()
        }


class Wishlist(db.Model):
    """Customer wishlist"""
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    items = db.relationship('WishlistItem', backref='wishlist', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'items': [item.to_dict() for item in self.items],
            'total_items': len(self.items)
        }


class WishlistItem(db.Model):
    """Items in wishlist"""
    __tablename__ = 'wishlist_items'

    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlists.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'wishlist_id': self.wishlist_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'added_at': self.added_at.isoformat()
        }


class Order(db.Model):
    """Customer orders"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, shipped, delivered, cancelled
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax = db.Column(db.Numeric(10, 2), default=0)
    shipping_cost = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # NEW: Shipping method and location tracking
    shipping_method_id = db.Column(db.Integer, db.ForeignKey('shipping_methods.id'))
    is_nairobi = db.Column(db.Boolean, default=True)  # For shipping cost calculation

    # Encrypted shipping/billing addresses (stored as JSON for historical preservation)
    shipping_address_encrypted = db.Column(EncryptedAddressString, nullable=False)
    billing_address_encrypted = db.Column(EncryptedAddressString)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)

    # Order Tracking (Phase 1 - Task 1.1.2)
    tracking_number = db.Column(db.String(100))
    carrier = db.Column(db.String(50))
    tracking_url = db.Column(db.Text)
    estimated_delivery_date = db.Column(db.Date)
    shipping_notes = db.Column(db.Text)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', lazy=True, uselist=False)
    shipping_method = db.relationship('ShippingMethod')
    shipment_updates = db.relationship('ShipmentUpdate', backref='order', lazy=True, cascade='all, delete-orphan', order_by='ShipmentUpdate.timestamp.desc()')
    # Note: returns relationship is defined in Return model with backref='order'

    @property
    def can_request_return(self):
        """Check if order can be returned (within 2-day window from delivery)"""
        if not self.delivered_at:
            return False

        from datetime import timedelta
        return_deadline = self.delivered_at + timedelta(days=2)
        return datetime.utcnow() <= return_deadline

    def to_dict(self, include_items=True):
        """Serialize order for API response"""
        import json

        # Decrypt shipping address
        shipping_address = None
        if self.shipping_address_encrypted:
            try:
                shipping_address = json.loads(self.shipping_address_encrypted)
            except:
                shipping_address = None

        data = {
            'id': self.id,
            'customer_id': self.customer_id,
            'order_number': self.order_number,
            'status': self.status,
            'subtotal': float(self.subtotal),
            'tax': float(self.tax) if self.tax else 0,
            'shipping_cost': float(self.shipping_cost) if self.shipping_cost else 0,
            'total': float(self.total),
            'is_nairobi': self.is_nairobi,
            'shipping_address': shipping_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            # Tracking information (Phase 1)
            'tracking_number': self.tracking_number,
            'carrier': self.carrier,
            'tracking_url': self.tracking_url,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            'shipping_notes': self.shipping_notes
        }

        if include_items and self.items:
            data['items'] = [item.to_dict() for item in self.items]
            data['items_count'] = len(self.items)

        return data


class OrderItem(db.Model):
    """Items in an order"""
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
    variant = db.relationship('ProductVariant')

    def to_dict(self):
        """Serialize order item"""
        # Get product data with primary image
        product_data = None
        if self.product:
            # Find primary image from product images
            image_url = None
            if hasattr(self.product, 'images') and self.product.images:
                primary_img = next((img for img in self.product.images if img.is_primary), None)
                if primary_img:
                    image_url = primary_img.image_url
                elif len(self.product.images) > 0:
                    image_url = self.product.images[0].image_url

            product_data = {
                'id': self.product.id,
                'name': self.product.name,
                'slug': self.product.slug,
                'image_url': image_url
            }

        # Get variant data
        variant_data = None
        if self.variant:
            variant_data = {
                'id': self.variant.id,
                'sku': self.variant.sku,
                'size': self.variant.size,
                'color': self.variant.color
            }

        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'price_at_purchase': float(self.unit_price),  # Alias for compatibility
            'total_price': float(self.total_price),
            'product': product_data,
            'variant': variant_data
        }


class Payment(db.Model):
    """Payment records for orders (M-Pesa integration)"""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default='mpesa')  # mpesa, cash, card
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded

    # Encrypted M-Pesa details
    mpesa_phone_encrypted = db.Column(EncryptedPaymentString)
    transaction_id_encrypted = db.Column(EncryptedPaymentString)  # M-Pesa receipt number

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'payment_method': self.payment_method,
            'amount': float(self.amount),
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

        if include_sensitive and self.mpesa_phone_encrypted:
            data['mpesa_phone'] = self.mpesa_phone_encrypted
            data['transaction_id'] = self.transaction_id_encrypted

        return data


class Review(db.Model):
    """Product reviews by customers"""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'customer_id': self.customer_id,
            'rating': self.rating,
            'title': self.title,
            'comment': self.comment,
            'is_verified_purchase': self.is_verified_purchase,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat()
        }


# ========================
# POS SYSTEM
# ========================

class POSTransaction(db.Model):
    """Point of Sale transactions for physical store"""
    __tablename__ = 'pos_transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_number = db.Column(db.String(50), unique=True, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    store_location_id = db.Column(db.Integer, db.ForeignKey('store_locations.id'), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default='cash')  # cash, mpesa, card
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    cash_tendered = db.Column(db.Numeric(10, 2))
    change_given = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), nullable=False, default='completed')  # completed, voided, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    items = db.relationship('POSTransactionItem', backref='transaction', lazy=True, cascade='all, delete-orphan')
    store_location = db.relationship('StoreLocation')

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_number': self.transaction_number,
            'employee_id': self.employee_id,
            'store_location_id': self.store_location_id,
            'payment_method': self.payment_method,
            'subtotal': float(self.subtotal),
            'tax': float(self.tax),
            'total': float(self.total),
            'cash_tendered': float(self.cash_tendered) if self.cash_tendered else None,
            'change_given': float(self.change_given) if self.change_given else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }


class POSTransactionItem(db.Model):
    """Items in a POS transaction"""
    __tablename__ = 'pos_transaction_items'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('pos_transactions.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    product = db.relationship('Product')
    inventory = db.relationship('Inventory')

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'product_name': self.product.name if self.product else None
        }


class StoreLocation(db.Model):
    """Physical store locations"""
    __tablename__ = 'store_locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    hours_of_operation = db.Column(db.Text)  # JSON string
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'email': self.email,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'hours_of_operation': self.hours_of_operation,
            'is_active': self.is_active
        }


# ========================
# GDPR & AUDIT
# ========================

class GDPRDataRequest(db.Model):
    """GDPR data access/deletion requests"""
    __tablename__ = 'gdpr_data_requests'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    request_type = db.Column(db.String(20), nullable=False)  # access, deletion, portability
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, rejected
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'request_type': self.request_type,
            'status': self.status,
            'requested_at': self.requested_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'notes': self.notes
        }


class GDPRConsentLog(db.Model):
    """Audit trail for GDPR consent collection"""
    __tablename__ = 'gdpr_consent_log'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    consent_type = db.Column(db.String(50), nullable=False)  # marketing, analytics, cookies, gdpr
    consent_given = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    consented_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'consent_type': self.consent_type,
            'consent_given': self.consent_given,
            'ip_address': self.ip_address,
            'consented_at': self.consented_at.isoformat()
        }


class DataAccessLog(db.Model):
    """Audit log for all PII data access (decryption operations)"""
    __tablename__ = 'data_access_log'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    accessed_table = db.Column(db.String(50), nullable=False)
    accessed_record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)  # view, decrypt, export
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reason = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'customer_id': self.customer_id,
            'accessed_table': self.accessed_table,
            'accessed_record_id': self.accessed_record_id,
            'action': self.action,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason
        }


class ActivityLog(db.Model):
    """General activity log for critical operations"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'customer_id': self.customer_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat()
        }

# ========================
# AUTHENTICATION MODELS
# (Added in Migration 007)
# ========================

class RefreshToken(db.Model):
    """
    Refresh tokens for maintaining long-lived sessions (30 days).
    Stores refresh tokens for both customers and employees.
    """
    __tablename__ = 'refresh_tokens'

    id = db.Column(db.Integer, primary_key=True)
    
    # User identification
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'customer' or 'employee'
    
    # Token details
    token_jti = db.Column(db.String(36), unique=True, nullable=False)  # JWT ID
    
    # Device/session tracking
    device_name = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    
    # Lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    revoked_at = db.Column(db.DateTime)
    revoked_reason = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'device_name': self.device_name,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'revoked': self.revoked
        }


class TokenBlacklist(db.Model):
    """
    Blacklisted JWTs that should be rejected.
    Used for logout functionality.
    """
    __tablename__ = 'token_blacklist'

    id = db.Column(db.Integer, primary_key=True)
    
    # Token identification
    jti = db.Column(db.String(36), unique=True, nullable=False)  # JWT ID
    token_type = db.Column(db.String(20), nullable=False)  # 'access' or 'refresh'
    
    # Revocation details
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)  # Original token expiration
    reason = db.Column(db.String(100))  # 'logout', 'logout_all', 'security_breach', etc.
    
    # User context (for auditing)
    user_id = db.Column(db.Integer)
    user_type = db.Column(db.String(20))  # 'customer' or 'employee'

    def to_dict(self):
        return {
            'id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'revoked_at': self.revoked_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'reason': self.reason
        }


class AuthAuditLog(db.Model):
    """
    Comprehensive logging of all authentication events.
    Tracks logins, logouts, failed attempts, 2FA events, etc.
    """
    __tablename__ = 'auth_audit_log'

    id = db.Column(db.Integer, primary_key=True)
    
    # User identification
    user_id = db.Column(db.Integer)
    user_type = db.Column(db.String(20))  # 'customer' or 'employee'
    email = db.Column(db.String(255))
    
    # Event details
    event_type = db.Column(db.String(50), nullable=False)  # 'login', 'logout', 'login_failed', '2fa_failed', etc.
    auth_method = db.Column(db.String(50))  # 'password', 'google_oauth', '2fa', 'pin', etc.
    
    # Result
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text)
    
    # Context
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    device_info = db.Column(db.JSON)  # Additional device details
    
    # Metadata
    extra_data = db.Column(db.JSON)  # Flexible field for additional context
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'email': self.email,
            'event_type': self.event_type,
            'auth_method': self.auth_method,
            'success': self.success,
            'error_message': self.error_message,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }


class Permission(db.Model):
    """
    Granular permissions for fine-grained access control.
    Goes beyond basic roles to provide specific action permissions.
    """
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    
    # Permission details
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'pos.create_sale', 'inventory.update'
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'pos', 'inventory', 'reports', 'admin', etc.
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    role_permissions = db.relationship('RolePermission', backref='permission', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'is_active': self.is_active
        }


class RolePermission(db.Model):
    """
    Maps roles to permissions (many-to-many relationship).
    Defines which permissions each role (admin, manager, cashier, staff) has.
    """
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'manager', 'cashier', 'staff'
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)
    
    # Audit
    granted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('employees.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'permission_id': self.permission_id,
            'permission_name': self.permission.name if self.permission else None,
            'granted_at': self.granted_at.isoformat()
        }


class EmployeeSession(db.Model):
    """
    Track active employee sessions for security monitoring.
    Useful for detecting unauthorized access and managing multiple sessions.
    """
    __tablename__ = 'employee_sessions'

    id = db.Column(db.Integer, primary_key=True)
    
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    
    # Session details
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    session_type = db.Column(db.String(20), nullable=False)  # 'web', 'pos', 'mobile'
    
    # Device info
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    device_name = db.Column(db.String(100))
    
    # Lifecycle
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    employee = db.relationship('Employee', backref='sessions')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'session_type': self.session_type,
            'ip_address': self.ip_address,
            'device_name': self.device_name,
            'started_at': self.started_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active
        }


# ============================================================================
# PHASE 1: ORDER TRACKING MODELS (Task 1.1.2)
# ============================================================================

class ShippingCarrier(db.Model):
    """
    Shipping carriers configuration for order tracking.
    Stores carrier information and tracking URL templates.
    """
    __tablename__ = 'shipping_carriers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    tracking_url_template = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def generate_tracking_url(self, tracking_number):
        """Generate tracking URL by replacing placeholder with actual tracking number"""
        if self.tracking_url_template and tracking_number:
            return self.tracking_url_template.replace('{tracking_number}', tracking_number)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tracking_url_template': self.tracking_url_template,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ShipmentUpdate(db.Model):
    """
    Timeline of shipment status updates for order tracking.
    Records each status change with location and timestamp.
    """
    __tablename__ = 'shipment_updates'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # shipped, in_transit, out_for_delivery, delivered, exception
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship('Employee', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'status': self.status,
            'location': self.location,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_by': self.created_by,
            'created_by_name': self.creator.full_name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
