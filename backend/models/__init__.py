"""
Models package for Happy Place Boutique backend.
Contains database models and encrypted field types.

Total: 29 tables (22 core + 7 extended)
"""

from .encrypted_types import (
    EncryptedCustomerString,
    EncryptedAddressString,
    EncryptedPaymentString
)

from .database_models import (
    db,
    Customer, CustomerAddress, Employee,
    Category, Product, ProductImage, Inventory,
    Cart, CartItem, Wishlist, WishlistItem,
    Order, OrderItem, Payment, Review,
    POSTransaction, POSTransactionItem, StoreLocation,
    GDPRDataRequest, GDPRConsentLog, DataAccessLog, ActivityLog,
    RefreshToken, TokenBlacklist, AuthAuditLog, Permission, RolePermission, EmployeeSession
)

from .extended_models import (
    CategoryClosure,
    ProductVariant,
    Promotion, OrderPromotion,
    ShippingMethod,
    Return, ReturnItem
)

__all__ = [
    # Database instance
    'db',

    # Encrypted types
    'EncryptedCustomerString',
    'EncryptedAddressString',
    'EncryptedPaymentString',

    # Core models (22 tables)
    'Customer', 'CustomerAddress', 'Employee',
    'Category', 'Product', 'ProductImage', 'Inventory',
    'Cart', 'CartItem', 'Wishlist', 'WishlistItem',
    'Order', 'OrderItem', 'Payment', 'Review',
    'POSTransaction', 'POSTransactionItem', 'StoreLocation',
    'GDPRDataRequest', 'GDPRConsentLog', 'DataAccessLog', 'ActivityLog',

    # Authentication models (6 new tables - Migration 007)
    'RefreshToken', 'TokenBlacklist', 'AuthAuditLog',
    'Permission', 'RolePermission', 'EmployeeSession',

    # Extended models (7 tables)
    'CategoryClosure',
    'ProductVariant',
    'Promotion', 'OrderPromotion',
    'ShippingMethod',
    'Return', 'ReturnItem'
]
