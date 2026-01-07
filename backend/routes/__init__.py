"""
Routes package for Happy Place Boutique API.
Modular route organization for all endpoints.
"""

from flask import Blueprint
import importlib

# Create main API blueprint
api = Blueprint('api', __name__)

def _register_routes() -> None:
    modules = (
        'products',
        'variants',
        'promotions',
        'returns_api',
        'shipping',
        'categories',
        'admin',
        'cart',
        'wishlist',
        'orders',
        'pos',
        'kiosk',
    )
    for module in modules:
        importlib.import_module(f"{__name__}.{module}")


_register_routes()

__all__ = ['api']
