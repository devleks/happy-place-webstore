#!/bin/bash
# Stop Happy Place backend server

cd "$(dirname "$0")"

echo "Stopping Gunicorn server..."

# Try to stop using PID file first
if [ -f gunicorn.pid ]; then
    PID=$(cat gunicorn.pid)
    if kill -0 $PID 2>/dev/null; then
        kill -TERM $PID
        echo "✓ Sent TERM signal to Gunicorn (PID: $PID)"
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                echo "✓ Server stopped gracefully"
                rm -f gunicorn.pid
                exit 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        kill -9 $PID 2>/dev/null
        echo "✓ Server force stopped"
        rm -f gunicorn.pid
    else
        echo "⚠ PID file exists but process not running"
        rm -f gunicorn.pid
    fi
fi

# Fallback: kill any process on port 5001
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "Killing processes on port 5001..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    echo "✓ Processes killed"
else
    echo "✓ No server running on port 5001"
fi
