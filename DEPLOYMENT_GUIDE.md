# Production Deployment Guide
## Happy Place Boutique - E-Commerce Platform

**Version**: 1.0
**Date**: November 25, 2025
**Status**: Production-Ready (Phase 6A Complete)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Requirements](#server-requirements)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Database Setup](#database-setup)
6. [SSL/HTTPS Configuration](#ssl-https-configuration)
7. [Environment Variables](#environment-variables)
8. [Nginx Reverse Proxy](#nginx-reverse-proxy)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup Strategy](#backup-strategy)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

**Server (Ubuntu 20.04+ / RHEL 8+ / Debian 11+)**:
- Python 3.11+
- Node.js 18+ & npm
- MySQL 8.0+
- Nginx 1.18+
- Git
- SSL certificates (Let's Encrypt recommended)

**Local Development**:
- Same as above for local testing
- Gunicorn (installed: `pip install gunicorn`)

---

## Server Requirements

### Minimum Specs (Small-Medium Traffic)

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 40 GB SSD
- **Bandwidth**: 100 GB/month

### Recommended Specs (Production)

- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Bandwidth**: 500 GB/month
- **Backup**: Daily automated backups

### Ports to Open

- `80` - HTTP (redirects to HTTPS)
- `443` - HTTPS
- `3306` - MySQL (internal only, not exposed)
- `22` - SSH (restrict to known IPs)

---

## Backend Deployment

### Step 1: Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip nginx mysql-server git -y

# Install certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

### Step 2: Create Application User

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash happyplace
sudo usermod -aG www-data happyplace

# Create application directory
sudo mkdir -p /var/www/happy_place_webstore
sudo chown -R happyplace:www-data /var/www/happy_place_webstore
```

### Step 3: Clone Repository

```bash
# Switch to application user
sudo su - happyplace

# Clone repository
cd /var/www
git clone <your-repo-url> happy_place_webstore
cd happy_place_webstore
```

### Step 4: Set Up Python Virtual Environment

```bash
# Navigate to backend
cd /var/www/happy_place_webstore/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

```bash
# Create .env file
nano /var/www/happy_place_webstore/backend/.env
```

Add the following (update with your actual values):

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-secure-random-key-here>
JWT_SECRET_KEY=<generate-another-secure-key-here>

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=happy_place_db
DB_USER=happy_place_user
DB_PASSWORD=<secure-database-password>

# Encryption Keys (32-byte hex strings)
ENCRYPTION_KEY=<generate-32-byte-hex-key>

# CORS Origins (your frontend domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email Configuration (for order notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<your-app-password>
MAIL_DEFAULT_SENDER=<your-email>

# Payment Gateway (M-Pesa - Phase 6B)
# MPESA_CONSUMER_KEY=
# MPESA_CONSUMER_SECRET=
# MPESA_SHORTCODE=
# MPESA_PASSKEY=
```

**Generate Secure Keys:**

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY
python3 -c "import secrets; print(secrets.token_hex(16))"
```

### Step 6: Install Gunicorn Systemd Service

```bash
# Copy service file
sudo cp /var/www/happy_place_webstore/backend/happy-place.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/happy-place.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable happy-place

# Start service
sudo systemctl start happy-place

# Check status
sudo systemctl status happy-place
```

### Step 7: Make Scripts Executable

```bash
cd /var/www/happy_place_webstore/backend
chmod +x start_production.sh
```

### Step 8: Test Backend

```bash
# Check if backend is running
curl http://localhost:5001/api/products

# Should return JSON with products
```

---

## Frontend Deployment

### Step 1: Configure Frontend Environment

```bash
# Navigate to frontend
cd /var/www/happy_place_webstore/frontend

# Create production .env
nano .env.production
```

Add:

```env
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENV=production
```

### Step 2: Build Production Bundle

```bash
# Install dependencies
npm install

# Build for production
npm run build

# This creates a 'build' folder with optimized static files
```

### Step 3: Deploy Static Files

```bash
# Create web root
sudo mkdir -p /var/www/html/happy_place

# Copy build files
sudo cp -r build/* /var/www/html/happy_place/

# Set permissions
sudo chown -R www-data:www-data /var/www/html/happy_place
sudo chmod -R 755 /var/www/html/happy_place
```

---

## Database Setup

### Step 1: Secure MySQL Installation

```bash
sudo mysql_secure_installation
```

Answer:
- Set root password: **Yes**
- Remove anonymous users: **Yes**
- Disallow root login remotely: **Yes**
- Remove test database: **Yes**
- Reload privilege tables: **Yes**

### Step 2: Create Database and User

```bash
# Login to MySQL
sudo mysql -u root -p

# Create database
CREATE DATABASE happy_place_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user
CREATE USER 'happy_place_user'@'localhost' IDENTIFIED BY '<secure-password>';

# Grant privileges
GRANT ALL PRIVILEGES ON happy_place_db.* TO 'happy_place_user'@'localhost';
FLUSH PRIVILEGES;

# Exit
EXIT;
```

### Step 3: Import Database Schema

```bash
# Import schema
mysql -u happy_place_user -p happy_place_db < /var/www/happy_place_webstore/backend/database_schema.sql

# Import seed data (if available)
mysql -u happy_place_user -p happy_place_db < /var/www/happy_place_webstore/backend/seed_data.sql
```

### Step 4: Test Database Connection

```bash
cd /var/www/happy_place_webstore/backend
source venv/bin/activate
python3 -c "from extensions import db; from app import app; app.app_context().push(); print('✅ Database connected')"
```

---

## SSL/HTTPS Configuration

### Step 1: Install SSL Certificate (Let's Encrypt)

```bash
# Get certificate for main domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Get certificate for API subdomain
sudo certbot --nginx -d api.yourdomain.com

# Certificates auto-renew. Test renewal:
sudo certbot renew --dry-run
```

### Step 2: Update Gunicorn Config for SSL (Optional)

If terminating SSL at Gunicorn instead of Nginx:

```python
# Edit gunicorn_config.py
keyfile = "/etc/letsencrypt/live/yourdomain.com/privkey.pem"
certfile = "/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
```

**Note**: Recommended to terminate SSL at Nginx (reverse proxy) instead.

---

## Environment Variables

### Production Environment File

**Location**: `/var/www/happy_place_webstore/backend/.env`

```env
# Application
FLASK_ENV=production
DEBUG=False
SECRET_KEY=<64-char-hex>
JWT_SECRET_KEY=<64-char-hex>

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=happy_place_db
DB_USER=happy_place_user
DB_PASSWORD=<secure-password>

# Security
ENCRYPTION_KEY=<32-byte-hex>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# JWT
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=<app-specific-password>
MAIL_DEFAULT_SENDER=Happy Place <noreply@yourdomain.com>

# Storage (for product images)
UPLOAD_FOLDER=/var/www/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# Admin
ADMIN_EMAIL=admin@yourdomain.com
SUPPORT_EMAIL=support@yourdomain.com
```

**Security Note**: Never commit `.env` files to version control!

---

## Nginx Reverse Proxy

### Step 1: Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/happy_place
```

Add configuration:

```nginx
# Happy Place Boutique - Nginx Configuration

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Frontend (Main Website)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Root directory (React build)
    root /var/www/html/happy_place;
    index index.html;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:; connect-src 'self' https://api.yourdomain.com;" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;

    # Serve React App
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Access and error logs
    access_log /var/log/nginx/happy_place_access.log;
    error_log /var/log/nginx/happy_place_error.log;
}

# Backend API (api.yourdomain.com)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Access and error logs
    access_log /var/log/nginx/api_access.log;
    error_log /var/log/nginx/api_error.log;
}
```

### Step 2: Enable Configuration

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/happy_place /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# If OK, reload Nginx
sudo systemctl reload nginx
```

### Step 3: Verify

```bash
# Check frontend
curl -I https://yourdomain.com

# Check backend API
curl https://api.yourdomain.com/api/products
```

---

## Monitoring & Logging

### Backend Logs

```bash
# View Gunicorn logs
sudo journalctl -u happy-place -f

# View access logs
sudo tail -f /var/log/nginx/api_access.log

# View error logs
sudo tail -f /var/log/nginx/api_error.log
```

### Frontend Logs

```bash
# Nginx access logs
sudo tail -f /var/log/nginx/happy_place_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/happy_place_error.log
```

### Application Monitoring (Optional)

Consider implementing:
- **Sentry** - Error tracking
- **Prometheus + Grafana** - Metrics and dashboards
- **Uptime Robot** - Uptime monitoring
- **CloudWatch / DataDog** - Full observability

---

## Backup Strategy

### Database Backups

**Automated Daily Backup Script:**

```bash
sudo nano /usr/local/bin/backup_happy_place.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/happy_place"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="happy_place_db"
DB_USER="happy_place_user"
DB_PASS="<your-password>"

mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup_happy_place.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
```

Add:
```
0 2 * * * /usr/local/bin/backup_happy_place.sh >> /var/log/backups.log 2>&1
```

### Application Backups

```bash
# Backup application code weekly
sudo rsync -avz /var/www/happy_place_webstore /var/backups/app_$(date +%Y%m%d)
```

---

## Troubleshooting

### Backend Not Starting

```bash
# Check service status
sudo systemctl status happy-place

# Check logs
sudo journalctl -u happy-place -n 50

# Common issues:
# 1. Database connection failed - Check .env DB credentials
# 2. Port already in use - Check: sudo lsof -i :5001
# 3. Permission denied - Check file ownership
```

### Frontend 404 Errors

```bash
# Ensure index.html exists
ls -la /var/www/html/happy_place/index.html

# Check Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Database Connection Errors

```bash
# Test MySQL connection
mysql -u happy_place_user -p happy_place_db

# Check MySQL is running
sudo systemctl status mysql

# Check .env database credentials
```

### SSL Certificate Issues

```bash
# Renew certificates
sudo certbot renew

# Check certificate expiration
sudo certbot certificates
```

### Performance Issues

```bash
# Check server resources
htop

# Check Gunicorn workers
sudo systemctl status happy-place

# Increase workers in gunicorn_config.py
# workers = (CPU_COUNT * 2) + 1
```

---

## Production Checklist

Before going live:

### Security
- [ ] All `.env` files configured with strong secrets
- [ ] Database user has limited privileges
- [ ] SSH key-based authentication only
- [ ] Firewall configured (ufw/iptables)
- [ ] SSL certificates installed and auto-renewing
- [ ] Security headers configured in Nginx
- [ ] CORS origins restricted to your domain
- [ ] Debug mode disabled (`FLASK_ENV=production`)

### Performance
- [ ] Gunicorn workers optimized for CPU count
- [ ] Nginx gzip compression enabled
- [ ] Static assets cached (1 year)
- [ ] Database indexes created
- [ ] Query optimization done

### Reliability
- [ ] Systemd service enabled (auto-start on boot)
- [ ] Daily database backups configured
- [ ] Weekly application backups configured
- [ ] Monitoring and alerting set up
- [ ] Error logging configured

### Testing
- [ ] Full end-to-end testing in staging
- [ ] Load testing completed
- [ ] Security scan performed
- [ ] Mobile responsiveness verified
- [ ] Cross-browser testing done

---

## Quick Commands Reference

```bash
# Backend Management
sudo systemctl start happy-place      # Start backend
sudo systemctl stop happy-place       # Stop backend
sudo systemctl restart happy-place    # Restart backend
sudo systemctl status happy-place     # Check status
sudo journalctl -u happy-place -f     # View logs

# Nginx Management
sudo nginx -t                         # Test config
sudo systemctl reload nginx           # Reload config
sudo systemctl restart nginx          # Restart Nginx

# Database Management
sudo systemctl status mysql           # Check MySQL
mysql -u happy_place_user -p          # Connect to DB

# SSL Certificates
sudo certbot renew                    # Renew all certs
sudo certbot certificates             # List certs

# View Logs
sudo tail -f /var/log/nginx/api_access.log
sudo tail -f /var/log/nginx/api_error.log
sudo journalctl -u happy-place -f
```

---

## Support & Resources

- **Documentation**: See project README.md
- **API Docs**: `API_SPECIFICATION_V3.2.md`
- **Database Schema**: `DATABASE_SCHEMA_COMPLETE_V3.2.md`
- **QA Testing**: `QA_TEST_PLAN.md`, `QA_SUMMARY.md`

---

**Deployment Guide Version**: 1.0
**Last Updated**: November 25, 2025
**Project Status**: Phase 6A Complete, Ready for Production
