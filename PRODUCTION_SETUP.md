# Production Setup - Quick Reference
## Happy Place Boutique E-Commerce Platform

**Status**: ✅ Gunicorn Installed & Configured
**Phase**: 6A Complete - Ready for Production Deployment

---

## What's Been Configured

### ✅ Production Server (Gunicorn)

**Installed**:
- Gunicorn 23.0.0 (Production WSGI server)
- Added to `requirements.txt`

**Configuration Files Created**:
1. **`gunicorn_config.py`** - Production server configuration
   - Workers: `(CPU_COUNT × 2) + 1`
   - Timeout: 30 seconds
   - Access logging enabled
   - Process management hooks

2. **`start_production.sh`** - Production startup script
   - Auto-detects configuration
   - Displays worker count
   - Starts Gunicorn with proper settings

3. **`happy-place.service`** - Systemd service file
   - Auto-start on boot
   - Process monitoring
   - Automatic restart on failure
   - Security hardening

4. **`DEPLOYMENT_GUIDE.md`** - Complete deployment documentation
   - Server setup instructions
   - SSL configuration
   - Nginx reverse proxy
   - Database setup
   - Monitoring and backups

---

## Quick Start Guide

### Local Production Testing (Current Machine)

**Test Gunicorn Locally**:

```bash
# Navigate to backend
cd /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend

# Option 1: Use the startup script
./start_production.sh

# Option 2: Run Gunicorn directly
gunicorn --config gunicorn_config.py app:app

# Option 3: Quick test (2 workers)
gunicorn --bind 0.0.0.0:5001 --workers 2 app:app
```

**Test the API**:

```bash
# In another terminal
curl http://localhost:5001/api/products

# Should return JSON with products
```

**Stop Gunicorn**:
- Press `Ctrl+C` in the terminal

---

### Production Server Deployment

**See `DEPLOYMENT_GUIDE.md` for complete instructions.**

Quick overview:

1. **Server Setup**
   ```bash
   # Install dependencies
   sudo apt install python3.11 python3-venv nginx mysql-server

   # Clone repository
   git clone <your-repo> /var/www/happy_place_webstore
   ```

2. **Backend Setup**
   ```bash
   cd /var/www/happy_place_webstore/backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with production values
   ```

4. **Install Systemd Service**
   ```bash
   sudo cp happy-place.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable happy-place
   sudo systemctl start happy-place
   ```

5. **Configure Nginx**
   - See DEPLOYMENT_GUIDE.md for Nginx config
   - Set up SSL with Let's Encrypt
   - Configure reverse proxy

6. **Frontend Build**
   ```bash
   cd /var/www/happy_place_webstore/frontend
   npm install
   npm run build
   sudo cp -r build/* /var/www/html/happy_place/
   ```

---

## Configuration Overview

### Gunicorn Settings (gunicorn_config.py)

```python
bind = "0.0.0.0:5001"
workers = (CPU_COUNT × 2) + 1
worker_class = "sync"
timeout = 30
max_requests = 1000
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
```

**Performance**:
- 2-core CPU → 5 workers
- 4-core CPU → 9 workers
- 8-core CPU → 17 workers

### Systemd Service

**Location**: `/etc/systemd/system/happy-place.service`

**Features**:
- Auto-start on boot
- Restart on failure
- Resource limits
- Security hardening
- Logging to journald

**Management Commands**:
```bash
sudo systemctl start happy-place
sudo systemctl stop happy-place
sudo systemctl restart happy-place
sudo systemctl status happy-place
sudo journalctl -u happy-place -f  # View logs
```

---

## Development vs Production

### Development (Current Setup)

```bash
# Flask development server
python app.py

# Features:
# - Auto-reload on code changes
# - Debug mode enabled
# - Single threaded
# - Not for production use
```

### Production (Gunicorn)

```bash
# Gunicorn WSGI server
gunicorn --config gunicorn_config.py app:app

# Features:
# - Multiple worker processes
# - Production optimized
# - Process management
# - Better performance
# - Handles concurrent requests
```

---

## Environment Variables

### Production .env File

**Required Variables**:

```env
# Flask
FLASK_ENV=production
SECRET_KEY=<64-char-hex-key>
JWT_SECRET_KEY=<64-char-hex-key>

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=happy_place_db
DB_USER=happy_place_user
DB_PASSWORD=<secure-password>

# Security
ENCRYPTION_KEY=<32-byte-hex-key>
CORS_ORIGINS=https://yourdomain.com

# Email (optional, for order notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<email>
MAIL_PASSWORD=<app-password>
```

**Generate Secure Keys**:

```bash
# SECRET_KEY and JWT_SECRET_KEY (64 chars)
python3 -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY (32 chars)
python3 -c "import secrets; print(secrets.token_hex(16))"
```

---

## Testing Gunicorn Locally

### Step 1: Stop Flask Development Server

```bash
# If running in background, find the process
lsof -ti:5001 | xargs kill -9
```

### Step 2: Start Gunicorn

```bash
cd /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend
./start_production.sh
```

### Step 3: Test the API

```bash
# In another terminal

# Test products endpoint
curl http://localhost:5001/api/products

# Test with authentication (if you have a token)
curl -H "Authorization: Bearer <your-token>" http://localhost:5001/api/cart
```

### Step 4: Monitor Performance

```bash
# Check worker processes
ps aux | grep gunicorn

# Monitor resource usage
top -p $(pgrep -d',' -f gunicorn)
```

---

## Troubleshooting

### Gunicorn Won't Start

**Error**: "Address already in use"
```bash
# Find process using port 5001
lsof -i :5001

# Kill it
kill -9 <PID>
```

**Error**: "No module named 'app'"
```bash
# Make sure you're in the backend directory
cd /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend

# Check if app.py exists
ls -la app.py
```

### Workers Timing Out

**Symptom**: 502 Bad Gateway errors

**Fix**: Increase timeout in `gunicorn_config.py`:
```python
timeout = 60  # Increase from 30 to 60 seconds
```

### Too Many/Too Few Workers

**Adjust in `gunicorn_config.py`**:
```python
# More workers (if you have CPU cores available)
workers = multiprocessing.cpu_count() * 3 + 1

# Fewer workers (if memory constrained)
workers = 2
```

### Database Connection Errors

**Check**:
1. MySQL is running: `sudo systemctl status mysql`
2. `.env` credentials are correct
3. Database exists: `mysql -u root -p -e "SHOW DATABASES;"`

---

## Performance Optimization

### Recommended Settings by Traffic Level

**Low Traffic** (< 100 requests/min):
```python
workers = 2
max_requests = 500
```

**Medium Traffic** (100-1000 requests/min):
```python
workers = (CPU_COUNT × 2) + 1
max_requests = 1000
```

**High Traffic** (1000+ requests/min):
```python
workers = (CPU_COUNT × 4) + 1
worker_class = "gevent"  # Async workers
max_requests = 2000
```

### Memory Considerations

**Each worker uses ~50-100 MB RAM**:
- 5 workers = ~500 MB RAM
- 9 workers = ~900 MB RAM
- 17 workers = ~1.7 GB RAM

**Leave headroom for**:
- MySQL database
- Operating system
- Frontend (if on same server)
- Other services

---

## Monitoring & Logs

### View Gunicorn Logs

**If using systemd**:
```bash
sudo journalctl -u happy-place -f
```

**If running manually**:
- Logs output to terminal (stdout/stderr)

### Log Levels

```python
# In gunicorn_config.py
loglevel = "debug"    # Most verbose
loglevel = "info"     # Recommended for production
loglevel = "warning"  # Only warnings and errors
loglevel = "error"    # Only errors
```

---

## Next Steps

### Before Production Deployment

1. **Complete QA Testing**
   - Use `QA_SUMMARY.md` and `QUICK_TEST_GUIDE.md`
   - Test all checkout flows
   - Verify order creation
   - Check responsive design

2. **Security Review**
   - Generate strong secret keys
   - Review `.env` configuration
   - Set up firewall rules
   - Configure SSL certificates

3. **Backup Strategy**
   - Set up automated database backups
   - Configure application backups
   - Test restore procedures

4. **Monitoring Setup**
   - Configure error tracking (Sentry)
   - Set up uptime monitoring
   - Create alerting rules

5. **Load Testing**
   - Test with expected traffic levels
   - Monitor resource usage
   - Adjust worker count if needed

### Deployment

See **`DEPLOYMENT_GUIDE.md`** for complete step-by-step instructions.

---

## Quick Commands

```bash
# Development (Flask)
python app.py

# Production (Gunicorn) - Local
./start_production.sh

# Production (Gunicorn) - Server
sudo systemctl start happy-place
sudo systemctl status happy-place
sudo journalctl -u happy-place -f

# Stop Development Server
lsof -ti:5001 | xargs kill -9

# Check if port is free
lsof -i :5001
```

---

## Files Created for Production

1. ✅ **`gunicorn_config.py`** - Gunicorn configuration
2. ✅ **`start_production.sh`** - Production startup script
3. ✅ **`happy-place.service`** - Systemd service file
4. ✅ **`requirements.txt`** - Updated with gunicorn 23.0.0
5. ✅ **`DEPLOYMENT_GUIDE.md`** - Complete deployment docs
6. ✅ **`PRODUCTION_SETUP.md`** - This quick reference

---

## Summary

**Current Status**:
- ✅ Gunicorn installed (v23.0.0)
- ✅ Production configuration created
- ✅ Systemd service file ready
- ✅ Deployment documentation complete
- 🟡 Ready for local testing
- 🟡 Ready for production deployment

**To Test Locally**:
```bash
cd backend
./start_production.sh
```

**To Deploy to Production**:
Follow `DEPLOYMENT_GUIDE.md`

---

**Last Updated**: November 25, 2025
**Project**: Happy Place Boutique E-Commerce Platform
**Phase**: 6A Complete
