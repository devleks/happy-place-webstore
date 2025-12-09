#!/bin/bash

# Happy Place Boutique - Production Startup Script
# Starts the backend using Gunicorn WSGI server

echo "======================================"
echo "Happy Place Boutique - Production Mode"
echo "======================================"
echo ""

# Change to backend directory
cd "$(dirname "$0")"

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "❌ Error: Gunicorn is not installed"
    echo "Install it with: pip install gunicorn"
    exit 1
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found in current directory"
    exit 1
fi

# Check if config file exists
if [ ! -f "gunicorn_config.py" ]; then
    echo "⚠️  Warning: gunicorn_config.py not found, using default settings"
    CONFIG_FLAG=""
else
    CONFIG_FLAG="--config gunicorn_config.py"
fi

echo "🚀 Starting Gunicorn WSGI server..."
echo "📍 Binding to: 0.0.0.0:5001"
echo "👷 Workers: $(python3 -c 'import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)')"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Gunicorn
# The 'app:app' refers to the Flask app object in app.py
exec gunicorn $CONFIG_FLAG app:app
