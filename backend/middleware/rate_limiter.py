"""
Rate Limiting Middleware for Happy Place Webstore
Protects authentication and sensitive endpoints from abuse
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """
    Custom rate limiter with storage in memory
    For production, use Redis storage
    """
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()
        
    def is_rate_limited(self, key, max_requests, window_seconds):
        """
        Check if request should be rate limited
        
        Args:
            key: Unique identifier (IP address, user ID, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            tuple: (is_limited: bool, retry_after: int)
        """
        with self.lock:
            now = time.time()
            cutoff = now - window_seconds
            
            # Clean old requests
            self.requests[key] = [req_time for req_time in self.requests[key] 
                                 if req_time > cutoff]
            
            # Check if limit exceeded
            if len(self.requests[key]) >= max_requests:
                # Calculate retry after
                oldest_request = min(self.requests[key])
                retry_after = int((oldest_request + window_seconds) - now) + 1
                return True, retry_after
            
            # Add current request
            self.requests[key].append(now)
            return False, 0
    
    def clear_key(self, key):
        """Clear rate limit for a specific key"""
        with self.lock:
            if key in self.requests:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests=5, window_seconds=60, key_func=None):
    """
    Decorator to rate limit endpoints
    
    Args:
        max_requests: Maximum requests allowed in window (default: 5)
        window_seconds: Time window in seconds (default: 60)
        key_func: Function to generate rate limit key (default: IP address)
    
    Usage:
        @rate_limit(max_requests=5, window_seconds=60)
        @app.route('/login')
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                key = get_remote_address() or request.remote_addr or 'unknown'
            
            # Check rate limit
            is_limited, retry_after = rate_limiter.is_rate_limited(
                key, max_requests, window_seconds
            )
            
            if is_limited:
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {retry_after} seconds.',
                    'retry_after': retry_after
                }), 429
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


# Predefined rate limit decorators
def auth_rate_limit(fn):
    """
    Rate limit for authentication endpoints
    5 requests per minute per IP address
    """
    return rate_limit(max_requests=5, window_seconds=60)(fn)


def admin_rate_limit(fn):
    """
    Rate limit for admin endpoints
    30 requests per minute per IP address
    """
    return rate_limit(max_requests=30, window_seconds=60)(fn)


def api_rate_limit(fn):
    """
    Rate limit for general API endpoints
    60 requests per minute per IP address
    """
    return rate_limit(max_requests=60, window_seconds=60)(fn)


def strict_auth_rate_limit(fn):
    """
    Strict rate limit for sensitive operations
    3 requests per 5 minutes per IP address
    """
    return rate_limit(max_requests=3, window_seconds=300)(fn)


# Flask-Limiter integration (if preferred)
def create_limiter(app):
    """
    Create Flask-Limiter instance with Redis storage (production)
    
    Usage in app.py:
        from middleware.rate_limiter import create_limiter
        limiter = create_limiter(app)
    """
    storage_uri = app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["200 per day", "50 per hour"],
        headers_enabled=True,  # Send X-RateLimit-* headers
        swallow_errors=True     # Don't crash if storage fails
    )
    
    return limiter


# Rate limit strategies
RATE_LIMITS = {
    'auth': {
        'login': (5, 60),           # 5 attempts per minute
        'register': (3, 300),        # 3 registrations per 5 minutes
        'reset_password': (2, 300),  # 2 resets per 5 minutes
        'verify_2fa': (5, 60),       # 5 attempts per minute
    },
    'admin': {
        'create': (10, 60),          # 10 creates per minute
        'update': (20, 60),          # 20 updates per minute
        'delete': (5, 60),           # 5 deletes per minute
        'export': (2, 300),          # 2 exports per 5 minutes
    },
    'api': {
        'read': (60, 60),            # 60 reads per minute
        'write': (30, 60),           # 30 writes per minute
        'search': (20, 60),          # 20 searches per minute
    }
}