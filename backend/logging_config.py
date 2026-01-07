"""
Logging Configuration for Happy Place Boutique Backend
Production-grade logging with rotation and structured output
"""

import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(app):
    """
    Configure application logging for production.

    Features:
    - Separate log files for different log levels
    - Automatic log rotation
    - Structured JSON logging (optional)
    - Console output for development
    """

    # Get configuration from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_dir = os.getenv('LOG_DIR', '/var/log/happyplace')

    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            # Fallback to local directory if /var/log is not writable
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    root_logger.handlers = []

    # ========================================
    # Console Handler (Development)
    # ========================================
    if app.config.get('FLASK_ENV') == 'development':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # ========================================
    # File Handler - General Application Log
    # ========================================
    app_log_file = os.path.join(log_dir, 'application.log')
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    app_handler.setLevel(logging.INFO)
    app_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app_handler.setFormatter(app_formatter)
    root_logger.addHandler(app_handler)

    # ========================================
    # File Handler - Error Log
    # ========================================
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

    # ========================================
    # File Handler - Security Log
    # ========================================
    security_log_file = os.path.join(log_dir, 'security.log')
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    security_handler.setLevel(logging.WARNING)
    security_formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    security_handler.setFormatter(security_formatter)

    # Create security logger
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)

    # ========================================
    # File Handler - Access Log (Custom)
    # ========================================
    access_log_file = os.path.join(log_dir, 'access.log')
    access_handler = logging.handlers.RotatingFileHandler(
        access_log_file,
        maxBytes=50 * 1024 * 1024,  # 50 MB (larger for access logs)
        backupCount=30
    )
    access_handler.setLevel(logging.INFO)
    access_formatter = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    access_handler.setFormatter(access_formatter)

    # Create access logger
    access_logger = logging.getLogger('access')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False  # Don't propagate to root logger

    # ========================================
    # Log startup information
    # ========================================
    app.logger.info('=' * 80)
    app.logger.info('Happy Place Boutique Backend Starting')
    app.logger.info(f'Environment: {app.config.get("FLASK_ENV")}')
    app.logger.info(f'Log Level: {log_level}')
    app.logger.info(f'Log Directory: {log_dir}')
    app.logger.info('=' * 80)

    return app


def log_security_event(event_type, details, user_id=None, ip_address=None):
    """
    Log security-related events.

    Args:
        event_type: Type of security event (login_failed, unauthorized_access, etc.)
        details: Additional details about the event
        user_id: User ID if applicable
        ip_address: Client IP address
    """
    security_logger = logging.getLogger('security')
    message = f"{event_type.upper()}"
    if user_id:
        message += f" | User: {user_id}"
    if ip_address:
        message += f" | IP: {ip_address}"
    message += f" | Details: {details}"
    security_logger.warning(message)


def log_access(method, path, status_code, response_time_ms, user_id=None, ip_address=None):
    """
    Log API access events.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        response_time_ms: Response time in milliseconds
        user_id: User ID if authenticated
        ip_address: Client IP address
    """
    access_logger = logging.getLogger('access')
    message = f"{method} {path} {status_code} {response_time_ms}ms"
    if user_id:
        message += f" | User: {user_id}"
    if ip_address:
        message += f" | IP: {ip_address}"
    access_logger.info(message)


# ========================================
# Middleware for request logging
# ========================================
def setup_request_logging(app):
    """
    Add middleware to log all HTTP requests.
    """
    from flask import request, g
    import time

    @app.before_request
    def log_request_start():
        g.start_time = time.time()

    @app.after_request
    def log_request_end(response):
        if hasattr(g, 'start_time'):
            response_time_ms = int((time.time() - g.start_time) * 1000)

            # Get user ID if authenticated
            user_id = None
            if hasattr(g, 'current_user'):
                user_id = getattr(g.current_user, 'id', None)

            # Log access
            log_access(
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                ip_address=request.remote_addr
            )

        return response

    return app
