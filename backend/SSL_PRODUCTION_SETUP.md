# SSL/HTTPS Production Setup Guide - Let's Encrypt

**Date:** January 4, 2026
**Project:** Happy Place Boutique E-Commerce Platform
**Purpose:** Production SSL certificate setup using Let's Encrypt

---

## Overview

This guide covers SSL/HTTPS setup for production deployment using Let's Encrypt free SSL certificates.

**What's Already Done:**
- ✅ Flask app configured for HTTPS support
- ✅ Config.py has SSL settings
- ✅ Self-signed certificates for local development
- ✅ CORS configured for HTTPS origins

**What This Guide Covers:**
- 🔐 Let's Encrypt installation (Ubuntu/Debian server)
- 📜 SSL certificate generation
- ⚙️ Flask production configuration
- 🔄 Auto-renewal setup
- 🌐 Nginx/Gunicorn reverse proxy setup

---

## Prerequisites

**Server Requirements:**
- Ubuntu 20.04+ or Debian 10+ (recommended)
- Root or sudo access
- Domain name pointing to server IP
  - Example: `api.happyplace.co.ke` → `Your Server IP`
  - Verify: `ping api.happyplace.co.ke`

**DNS Setup (REQUIRED before starting):**
```bash
# Verify DNS is correctly configured
dig api.happyplace.co.ke +short
# Should return your server's public IP address
```

---

## Method 1: Certbot with Nginx (RECOMMENDED)

### Step 1: Install Certbot

```bash
# Update package list
sudo apt update

# Install Certbot and Nginx plugin
sudo apt install -y certbot python3-certbot-nginx nginx

# Verify installation
certbot --version
```

### Step 2: Configure Nginx Reverse Proxy

Create Nginx configuration for your domain:

```bash
sudo nano /etc/nginx/sites-available/happyplace-api
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name api.happyplace.co.ke;  # CHANGE THIS to your domain

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
    }
}
```

Enable the site:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/happyplace-api /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 3: Obtain Let's Encrypt Certificate

```bash
# Run Certbot with Nginx plugin
sudo certbot --nginx -d api.happyplace.co.ke

# Follow prompts:
# 1. Enter email address (for renewal notifications)
# 2. Agree to Terms of Service (Y)
# 3. Share email with EFF (optional - Y/N)
# 4. Redirect HTTP to HTTPS? (YES - option 2)
```

**Expected Output:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/api.happyplace.co.ke/fullchain.pem
Key is saved at: /etc/letsencrypt/live/api.happyplace.co.ke/privkey.pem
```

### Step 4: Verify Certificate

```bash
# Check certificate details
sudo certbot certificates

# Test HTTPS endpoint
curl -I https://api.happyplace.co.ke/health

# Should return 200 OK with HTTPS
```

### Step 5: Set Up Auto-Renewal

Certbot automatically creates a systemd timer. Verify it:

```bash
# Check renewal timer status
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run

# Expected output: "Congratulations, all simulated renewals succeeded"
```

**Renewal Schedule:**
- Certificates valid for 90 days
- Auto-renewal runs twice daily
- Renews certificates with <30 days remaining

---

## Method 2: Manual Certificate with Gunicorn

### Step 1: Obtain Certificate (Standalone)

```bash
# Stop any service on port 80
sudo systemctl stop nginx

# Run Certbot standalone
sudo certbot certonly --standalone -d api.happyplace.co.ke

# Certificate saved to:
# /etc/letsencrypt/live/api.happyplace.co.ke/fullchain.pem
# /etc/letsencrypt/live/api.happyplace.co.ke/privkey.pem
```

### Step 2: Configure Gunicorn with SSL

Install Gunicorn:

```bash
cd /path/to/backend
source venv/bin/activate
pip install gunicorn
```

Create Gunicorn configuration:

```bash
nano gunicorn_config.py
```

```python
# gunicorn_config.py
import os

bind = "0.0.0.0:5001"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 5

# SSL Configuration (Production)
certfile = "/etc/letsencrypt/live/api.happyplace.co.ke/fullchain.pem"
keyfile = "/etc/letsencrypt/live/api.happyplace.co.ke/privkey.pem"

# Logging
accesslog = "/var/log/happyplace/access.log"
errorlog = "/var/log/happyplace/error.log"
loglevel = "info"

# Process naming
proc_name = "happyplace_api"

# Server mechanics
daemon = False  # Set to True for background
pidfile = "/var/run/happyplace.pid"
user = "www-data"
group = "www-data"
```

Create log directory:

```bash
sudo mkdir -p /var/log/happyplace
sudo chown www-data:www-data /var/log/happyplace
```

Run Gunicorn:

```bash
gunicorn -c gunicorn_config.py app:app
```

---

## Production Flask Configuration

Update `.env` for production:

```bash
# backend/.env (PRODUCTION)

# SSL/HTTPS
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/api.happyplace.co.ke/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/api.happyplace.co.ke/privkey.pem

# Flask
FLASK_ENV=production
FLASK_DEBUG=false

# Database (Production PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/happy_place_db

# CORS (Production Domains)
CORS_ORIGINS=https://happyplace.co.ke,https://www.happyplace.co.ke,https://admin.happyplace.co.ke

# Secrets (CHANGE THESE)
SECRET_KEY=your-super-secret-production-key-here-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-production-key-here-min-32-chars

# JWT Expiration
JWT_ACCESS_EXPIRES_MINUTES=15
JWT_REFRESH_EXPIRES_DAYS=7

# Encryption Keys (from existing .env - DO NOT CHANGE)
ENCRYPTION_KEY_PRIMARY=your-existing-primary-key
ENCRYPTION_KEY_SECONDARY=your-existing-secondary-key
```

---

## Systemd Service Setup

Create a systemd service for auto-start:

```bash
sudo nano /etc/systemd/system/happyplace-api.service
```

```ini
[Unit]
Description=Happy Place Boutique API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/happy_place_webstore/backend
Environment="PATH=/var/www/happy_place_webstore/backend/venv/bin"
ExecStart=/var/www/happy_place_webstore/backend/venv/bin/gunicorn \
    -c gunicorn_config.py \
    app:app

Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable happyplace-api

# Start service
sudo systemctl start happyplace-api

# Check status
sudo systemctl status happyplace-api

# View logs
sudo journalctl -u happyplace-api -f
```

---

## SSL Certificate Renewal

### Automatic Renewal (Certbot)

Certbot sets up automatic renewal. Verify with:

```bash
# Check renewal timer
sudo systemctl list-timers | grep certbot

# Test renewal (dry run)
sudo certbot renew --dry-run
```

### Manual Renewal

```bash
# Renew all certificates
sudo certbot renew

# Renew specific certificate
sudo certbot renew --cert-name api.happyplace.co.ke

# Force renewal (even if not expiring)
sudo certbot renew --force-renewal
```

### Post-Renewal Hook (Reload Services)

Create renewal hook:

```bash
sudo nano /etc/letsencrypt/renewal-hooks/post/reload-services.sh
```

```bash
#!/bin/bash
# Reload services after certificate renewal

systemctl reload nginx
systemctl restart happyplace-api

echo "$(date): Certificates renewed, services reloaded" >> /var/log/certbot-renew.log
```

Make executable:

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-services.sh
```

---

## Security Best Practices

### 1. Force HTTPS Redirect

Nginx configuration (already done if you chose "redirect" in Certbot):

```nginx
server {
    listen 80;
    server_name api.happyplace.co.ke;
    return 301 https://$server_name$request_uri;
}
```

### 2. HSTS Header

Flask already adds HSTS header in production (see `app.py:111-112`):

```python
if not app.debug:
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
```

### 3. SSL Test

Test your SSL configuration:

```bash
# Command-line test
curl -I https://api.happyplace.co.ke/health

# Online SSL test (after deployment)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.happyplace.co.ke
```

### 4. Certificate Monitoring

Set up monitoring for certificate expiration:

```bash
# Check expiration date
sudo certbot certificates

# Or using openssl
echo | openssl s_client -servername api.happyplace.co.ke -connect api.happyplace.co.ke:443 2>/dev/null | openssl x509 -noout -dates
```

---

## Troubleshooting

### Issue: "Address already in use"

```bash
# Find process on port 5001
sudo lsof -ti:5001

# Kill the process
sudo kill -9 $(sudo lsof -ti:5001)

# Or stop the service
sudo systemctl stop happyplace-api
```

### Issue: "Permission denied" for SSL files

```bash
# Give Gunicorn user access to Let's Encrypt certificates
sudo usermod -aG ssl-cert www-data

# Or use Nginx as reverse proxy (recommended)
# Nginx runs as root and can read /etc/letsencrypt
```

### Issue: Certificate renewal failed

```bash
# Check Certbot logs
sudo cat /var/log/letsencrypt/letsencrypt.log

# Common causes:
# 1. Port 80 blocked (firewall/security group)
# 2. Nginx not configured correctly
# 3. DNS not pointing to server

# Test DNS
dig api.happyplace.co.ke +short
```

### Issue: Mixed content warnings

If frontend shows "mixed content" warnings:

1. Update frontend `.env`:
```bash
# frontend-customer/.env
REACT_APP_API_URL=https://api.happyplace.co.ke
```

2. Rebuild frontend:
```bash
cd frontend-customer
npm run build
```

---

## Verification Checklist

After setup, verify these:

- [ ] Certificate obtained successfully
- [ ] HTTPS endpoint responds: `curl https://api.happyplace.co.ke/health`
- [ ] HTTP redirects to HTTPS
- [ ] Auto-renewal timer active: `sudo systemctl status certbot.timer`
- [ ] Systemd service running: `sudo systemctl status happyplace-api`
- [ ] SSL test passes: https://www.ssllabs.com/ssltest/
- [ ] HSTS header present: `curl -I https://api.happyplace.co.ke | grep Strict`
- [ ] CORS allows production domains
- [ ] Frontend API_URL updated to HTTPS

---

## Quick Commands Reference

```bash
# Check certificate status
sudo certbot certificates

# Renew certificates (manual)
sudo certbot renew

# Test renewal (dry run)
sudo certbot renew --dry-run

# View Nginx logs
sudo tail -f /var/log/nginx/error.log

# View Gunicorn logs
sudo journalctl -u happyplace-api -f

# Restart services
sudo systemctl restart nginx
sudo systemctl restart happyplace-api

# SSL test
curl -kI https://api.happyplace.co.ke/health
```

---

## Cost & Limits

**Let's Encrypt Free Tier:**
- ✅ **Free** forever
- ✅ Unlimited certificates
- ⚠️ Rate limits:
  - 50 certificates per domain per week
  - 5 duplicate certificates per week
  - 300 new orders per account per 3 hours

**These limits are more than sufficient for production use.**

---

## Next Steps After SSL Setup

1. **Update frontend API URLs** (Week 2, Day 9)
   - `frontend-customer/.env`: `REACT_APP_API_URL=https://api.happyplace.co.ke`
   - `frontend-admin/.env`: `REACT_APP_API_URL=https://api.happyplace.co.ke`

2. **Test payment integration with HTTPS**
   - M-Pesa callback URL must be HTTPS in production
   - Update `.env`: `MPESA_CALLBACK_URL=https://api.happyplace.co.ke/api/payments/mpesa/callback`

3. **Security audit** (Week 2, Day 10)
   - Test HTTPS enforcement
   - Verify HSTS headers
   - Check CORS configuration

---

**Created:** January 4, 2026
**Last Updated:** January 4, 2026
**Maintained By:** Happy Place Development Team

**For support:** Refer to Let's Encrypt documentation at https://letsencrypt.org/docs/
