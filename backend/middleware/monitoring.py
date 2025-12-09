"""
Production Monitoring Integration
Supports New Relic and DataDog APM
"""

import os
import time
from flask import request, g
from functools import wraps
from logging_utils import get_logger

logger = get_logger(__name__)

# Check which monitoring service is configured
NEW_RELIC_ENABLED = os.getenv('NEW_RELIC_LICENSE_KEY') is not None
DATADOG_ENABLED = os.getenv('DD_API_KEY') is not None


def init_monitoring(app):
    """
    Initialize monitoring services for Flask application
    
    Usage in app.py:
        from middleware.monitoring import init_monitoring
        init_monitoring(app)
    """
    
    # New Relic APM
    if NEW_RELIC_ENABLED:
        try:
            import newrelic.agent
            import os
            # Get the correct path to newrelic.ini
            # From backend/middleware/ -> go up to backend/ -> up to project root/ -> into monitoring/
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(backend_dir)
            config_path = os.path.join(project_root, 'monitoring', 'newrelic.ini')
            
            if os.path.exists(config_path):
                newrelic.agent.initialize(config_path)
                logger.info(f"New Relic APM initialized with config: {config_path}")
            else:
                logger.warning(f"New Relic config not found at: {config_path}")
        except ImportError:
            logger.warning("New Relic not installed. Install: pip install newrelic")
        except FileNotFoundError as e:
            logger.error(f"New Relic config file not found: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize New Relic: {e}")
    
    # DataDog APM
    if DATADOG_ENABLED:
        try:
            from ddtrace import patch_all, tracer
            patch_all()
            
            # Configure DataDog tracer
            tracer.configure(
                hostname=os.getenv('DD_AGENT_HOST', 'localhost'),
                port=int(os.getenv('DD_TRACE_AGENT_PORT', 8126)),
                settings={
                    'FILTERS': [],
                }
            )
            logger.info("DataDog APM initialized")
        except ImportError:
            logger.warning("DataDog not installed. Install: pip install ddtrace")
        except Exception as e:
            logger.error(f"Failed to initialize DataDog: {e}")
    
    # Request timing middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', str(time.time()))
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            
            # Add custom headers
            response.headers['X-Request-ID'] = g.request_id
            response.headers['X-Response-Time'] = f'{elapsed:.3f}s'
            
            # Log slow requests
            if elapsed > 1.0:  # > 1 second
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} "
                    f"took {elapsed:.3f}s",
                    extra={
                        'request_id': g.request_id,
                        'method': request.method,
                        'path': request.path,
                        'duration': elapsed,
                        'status_code': response.status_code
                    }
                )
        
        return response
    
    # Custom metrics endpoint for DataDog
    @app.route('/metrics', methods=['GET'])
    def metrics():
        """
        Expose application metrics for DataDog agent
        """
        try:
            from models import db, Customer, Product, Order, Employee
            from sqlalchemy import func
            
            with app.app_context():
                metrics = {
                    'customers': {
                        'total': Customer.query.count(),
                        'active': Customer.query.filter_by(is_active=True).count()
                    },
                    'products': {
                        'total': Product.query.count(),
                        'active': Product.query.filter_by(is_active=True).count()
                    },
                    'orders': {
                        'total': Order.query.count(),
                        'today': Order.query.filter(
                            func.date(Order.created_at) == func.current_date()
                        ).count()
                    },
                    'employees': {
                        'total': Employee.query.count(),
                        'active': Employee.query.filter_by(is_active=True).count()
                    }
                }
                
                return metrics, 200
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return {'error': 'Failed to generate metrics'}, 500
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        """
        Health check endpoint for load balancers and monitoring
        """
        try:
            from models import db
            
            # Check database connectivity
            db.session.execute(db.text('SELECT 1'))
            
            return {
                'status': 'healthy',
                'service': 'happy-place-backend',
                'version': '1.0.0',
                'database': 'connected',
                'timestamp': time.time()
            }, 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }, 503


# Custom monitoring decorators
def monitor_performance(operation_name):
    """
    Decorator to monitor specific operations
    
    Usage:
        @monitor_performance('create_order')
        def create_order():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log performance
                logger.info(
                    f"Operation {operation_name} completed in {duration:.3f}s",
                    extra={
                        'operation': operation_name,
                        'duration': duration,
                        'success': True
                    }
                )
                
                # Send to New Relic
                if NEW_RELIC_ENABLED:
                    try:
                        import newrelic.agent
                        newrelic.agent.record_custom_metric(
                            f'Custom/{operation_name}/Duration',
                            duration
                        )
                    except:
                        pass
                
                # Send to DataDog
                if DATADOG_ENABLED:
                    try:
                        from datadog import statsd
                        statsd.histogram(
                            f'happy_place.operation.{operation_name}.duration',
                            duration,
                            tags=[f'operation:{operation_name}']
                        )
                    except:
                        pass
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Operation {operation_name} failed after {duration:.3f}s",
                    extra={
                        'operation': operation_name,
                        'duration': duration,
                        'success': False,
                        'error': str(e)
                    },
                    exc_info=True
                )
                
                # Record error in New Relic
                if NEW_RELIC_ENABLED:
                    try:
                        import newrelic.agent
                        newrelic.agent.record_exception()
                    except:
                        pass
                
                raise
        
        return wrapped
    return decorator


# Database query monitoring
def log_slow_queries(app):
    """
    Log slow database queries
    """
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        
        # Log queries > 100ms
        if total > 0.1:
            logger.warning(
                f"Slow query detected: {total:.3f}s",
                extra={
                    'query_time': total,
                    'query': statement[:200]  # First 200 chars
                }
            )
            
            # Send to monitoring services
            if NEW_RELIC_ENABLED:
                try:
                    import newrelic.agent
                    newrelic.agent.record_custom_metric('Database/SlowQueryCount', 1)
                    newrelic.agent.record_custom_metric('Database/SlowQueryDuration', total)
                except:
                    pass


# Error tracking
def track_error(error, extra_context=None):
    """
    Track error in monitoring services
    
    Usage:
        track_error(exception, {'user_id': user.id, 'operation': 'checkout'})
    """
    logger.error(f"Error tracked: {error}", extra=extra_context or {}, exc_info=True)
    
    if NEW_RELIC_ENABLED:
        try:
            import newrelic.agent
            newrelic.agent.record_exception()
            if extra_context:
                for key, value in extra_context.items():
                    newrelic.agent.add_custom_parameter(key, value)
        except:
            pass
    
    if DATADOG_ENABLED:
        try:
            from ddtrace import tracer
            span = tracer.current_span()
            if span and extra_context:
                for key, value in extra_context.items():
                    span.set_tag(key, value)
        except:
            pass


# Custom event tracking
def track_event(event_name, properties=None):
    """
    Track custom business events
    
    Usage:
        track_event('order_placed', {'order_id': 123, 'total': 5000})
    """
    logger.info(f"Event: {event_name}", extra=properties or {})
    
    if NEW_RELIC_ENABLED:
        try:
            import newrelic.agent
            newrelic.agent.record_custom_event(event_name, properties or {})
        except:
            pass
    
    if DATADOG_ENABLED:
        try:
            from datadog import statsd
            statsd.increment(
                f'happy_place.event.{event_name}',
                tags=[f'{k}:{v}' for k, v in (properties or {}).items()]
            )
        except:
            pass