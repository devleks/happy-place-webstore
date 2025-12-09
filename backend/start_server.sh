#!/bin/bash
# Start Happy Place backend server with Gunicorn (production-grade WSGI server)

cd "$(dirname "$0")"

# Kill any existing server on port 5001
echo "Stopping any existing server on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null

# Activate venv
source venv/bin/activate

# Start server with Gunicorn
# --workers 4: Use 4 worker processes (adjust based on CPU cores)
# --bind 127.0.0.1:5001: Bind to localhost port 5001
# --timeout 120: 120 second timeout for requests
# --access-logfile: Log all requests
# --error-logfile: Log all errors
# --daemon: Run in background
echo "Starting Gunicorn server..."
gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5001 \
    --timeout 120 \
    --access-logfile server_access.log \
    --error-logfile server.log \
    --daemon \
    --pid gunicorn.pid \
    'app:create_app()'

# Wait for server to start
sleep 3

# Verify server is running
if curl -s http://127.0.0.1:5001/api/pos/health > /dev/null 2>&1; then
    PID=$(cat gunicorn.pid 2>/dev/null || echo "unknown")
    echo "✓ Gunicorn server started successfully (PID: $PID)"
    echo "✓ Server is healthy and responding"
    echo "  - Access logs: server_access.log"
    echo "  - Error logs: server.log"
    exit 0
else
    echo "✗ Server failed to start properly"
    echo "Recent error logs:"
    tail -20 server.log
    exit 1
fi
