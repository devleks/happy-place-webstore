"""
Flask Extensions

Centralizes initialization of Flask extensions to avoid circular imports.
Extensions are initialized here and then imported into other modules.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize JWT Manager
jwt = JWTManager()


def init_extensions(app):
    """
    Initialize all Flask extensions with the app instance.

    Args:
        app: Flask application instance
    """
    db.init_app(app)
    jwt.init_app(app)
