"""
Routes package for Happy Place Boutique API.
Modular route organization for all endpoints.
"""

from flask import Blueprint

# Create main API blueprint
api = Blueprint('api', __name__)

# Import all route modules to register them
from . import auth
from . import products
from . import variants
from . import promotions
from . import returns_api
from . import shipping
from . import categories
from . import admin
from . import cart
from . import wishlist
from . import orders
from . import pos
from . import kiosk

__all__ = ['api']
