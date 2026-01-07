"""
Health Check Endpoint
Provides system health and status information for monitoring
"""

from flask import Blueprint, jsonify
from models.database_models import db
import psutil
import os
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        JSON response with health status and metrics
    """
    try:
        # Check database connectivity
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'

    # Get system metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        system_metrics = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available // (1024 * 1024),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free // (1024 * 1024 * 1024)
        }
    except Exception:
        system_metrics = None

    # Build response
    health_data = {
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'version': os.getenv('APP_VERSION', '1.0.0'),
        'environment': os.getenv('FLASK_ENV', 'unknown')
    }

    if system_metrics:
        health_data['metrics'] = system_metrics

    status_code = 200 if db_status == 'connected' else 503

    return jsonify(health_data), status_code


@health_bp.route('/ping', methods=['GET'])
def ping():
    """
    Simple ping endpoint for basic uptime monitoring.
    """
    return jsonify({'status': 'ok', 'message': 'pong'}), 200


@health_bp.route('/ready', methods=['GET'])
def ready():
    """
    Readiness probe for Kubernetes/container orchestration.
    Checks if the application is ready to receive traffic.
    """
    try:
        # Check database connectivity
        db.session.execute(db.text('SELECT 1'))

        # Add other readiness checks here (Redis, external APIs, etc.)

        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/live', methods=['GET'])
def liveness():
    """
    Liveness probe for Kubernetes/container orchestration.
    Checks if the application is alive and should not be restarted.
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
