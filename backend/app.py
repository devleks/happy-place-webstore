from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes import api
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.fulfillment_routes import fulfillment_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Validate secrets (especially for production deployments)
    Config.validate_secrets()

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    JWTManager(app)

    # Initialize monitoring
    try:
        from middleware.monitoring import init_monitoring, log_slow_queries
        init_monitoring(app)
        log_slow_queries(app)
    except ImportError:
        print("⚠️  Monitoring middleware not found (optional feature)")
    except Exception as e:
        print(f"⚠️  Monitoring initialization failed: {e}")

    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth_bp)  # Already has /api/auth prefix
    app.register_blueprint(admin_bp)  # Already has /api/admin prefix
    app.register_blueprint(fulfillment_bp)  # Already has /api/fulfillment prefix

    # Create tables
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
