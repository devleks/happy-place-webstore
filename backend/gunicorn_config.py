# Gunicorn Configuration File
# Happy Place Boutique - Production WSGI Server

import multiprocessing

# Server Socket
bind = "0.0.0.0:5001"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended: (2 x $num_cores) + 1
worker_class = "sync"  # Use 'gevent' or 'eventlet' for async if needed
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to max_requests to prevent all workers restarting at once
timeout = 30  # Workers silent for more than this many seconds are killed and restarted
keepalive = 2  # The number of seconds to wait for requests on a Keep-Alive connection

# Server Mechanics
daemon = False  # Run in foreground (for systemd/docker)
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"  # Log to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
errorlog = "-"  # Log to stderr
loglevel = "info"  # debug, info, warning, error, critical
capture_output = True

# Process Naming
proc_name = "happy_place_backend"

# Server Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("🚀 Happy Place Boutique - Starting Gunicorn")
    print(f"📍 Binding to {server.cfg.bind}")
    print(f"👷 Workers: {server.cfg.workers}")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("🔄 Reloading workers...")

def when_ready(server):
    """Called just after the server is started."""
    print("✅ Gunicorn is ready. Listening on http://0.0.0.0:5001")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f"⚠️  Worker {worker.pid} received INT/QUIT signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"🛑 Worker {worker.pid} aborted")

# SSL (uncomment for HTTPS in production)
# keyfile = "/path/to/ssl/key.pem"
# certfile = "/path/to/ssl/cert.pem"
# ssl_version = 2  # TLSv1.2
# cert_reqs = 0  # No client certificate required
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# ciphers = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Development vs Production
# For development, you might want:
# - reload = True (auto-reload on code changes)
# - workers = 1 (easier debugging)
# - loglevel = "debug"

# For production, use the settings above

print("📋 Gunicorn configuration loaded")
