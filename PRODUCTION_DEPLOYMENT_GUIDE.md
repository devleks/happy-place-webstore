# Production Deployment Guide - Happy Place Boutique

**Complete guide for deploying Happy Place Boutique to production**

**Last Updated:** January 7, 2026
**Target Environment:** Ubuntu 22.04 LTS
**Estimated Setup Time:** 4-6 hours

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Configuration](#database-configuration)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup Configuration](#backup-configuration)
10. [Production Checklist](#production-checklist)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements

**Minimum Specifications:**
- **CPU:** 2 cores (4+ recommended)
- **RAM:** 4GB (8GB+ recommended)
- **Disk:** 40GB SSD
- **OS:** Ubuntu 22.04 LTS (or similar)
- **Network:** Static IP address, domain name configured

**Software Requirements:**
- Python 3.11+
- PostgreSQL 14+
- Node.js 16+
- Nginx 1.18+
- Certbot (for Let's Encrypt SSL)

### Domain Configuration

Before deployment, ensure:
- ✅ Domain purchased and DNS configured
- ✅ A records pointing to server IP:
  - `happyplace.com` → Server IP
  - `www.happyplace.com` → Server IP
  - `admin.happyplace.com` → Server IP
- ✅ DNS propagation complete (check with `dig` or `nslookup`)

---

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    build-essential \
    libpq-dev

# Install Node.js 18.x LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
python3.11 --version
node --version
npm --version
psql --version
nginx -v
```

### 2. Create Deployment User

```bash
# Create deployment user (recommended: www-data or deploy)
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy

# Set up SSH key authentication for deploy user
sudo mkdir -p /home/deploy/.ssh
# Add your public key to /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

### 3. Create Directory Structure

```bash
# Create application directory
sudo mkdir -p /var/www/happyplace
sudo chown -R deploy:deploy /var/www/happyplace

# Create log directory
sudo mkdir -p /var/log/happyplace
sudo chown -R deploy:deploy /var/log/happyplace

# Create backup directory
sudo mkdir -p /var/backups/happy_place
sudo chown -R deploy:deploy /var/backups/happy_place
```

---

## Database Configuration

### 1. PostgreSQL Setup

```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user
sudo -u postgres psql -c "CREATE USER happy_place_user WITH PASSWORD 'STRONG_PASSWORD_HERE';"

# Create production database
sudo -u postgres psql -c "CREATE DATABASE happy_place_production OWNER happy_place_user;"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE happy_place_production TO happy_place_user;"

# Enable UUID extension (required)
sudo -u postgres psql -d happy_place_production -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### 2. PostgreSQL Security Configuration

Edit `/etc/postgresql/14/main/pg_hba.conf`:

```conf
# Add this line for local application access
host    happy_place_production    happy_place_user    127.0.0.1/32    scram-sha-256
```

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Performance tuning (adjust based on server resources)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'ddl'
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 3. Initialize Database Schema

```bash
# Clone repository to deployment directory
cd /var/www/happyplace
git clone https://github.com/devleks/happy-place-webstore.git .

# Set up Python virtual environment
cd /var/www/happyplace/backend
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database (run migrations)
python scripts/migrate_database.py

# Seed initial data (optional - use for testing)
# python seed.py
```

---

## Backend Deployment

### 1. Environment Configuration

```bash
cd /var/www/happyplace/backend

# Copy production environment template
cp .env.production.template .env.production

# Edit production environment file
nano .env.production
```

**Critical values to update in `.env.production`:**

```bash
# Database (use strong password)
DATABASE_URL=postgresql://happy_place_user:YOUR_STRONG_PASSWORD@localhost:5432/happy_place_production

# Security keys (generate new ones!)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Encryption keys (generate new ones!)
# Run: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
CUSTOMER_ENCRYPTION_KEYS=<key1>,<key2>
ADDRESS_ENCRYPTION_KEYS=<key1>,<key2>
PAYMENT_ENCRYPTION_KEYS=<key1>,<key2>

# M-Pesa Production credentials
MPESA_CONSUMER_KEY=your_production_key
MPESA_CONSUMER_SECRET=your_production_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://happyplace.com/api/payments/mpesa/callback

# Email configuration
SMTP_HOST=your_smtp_host
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_email_password
EMAIL_FROM=noreply@happyplace.com

# CORS origins
CORS_ORIGINS=https://happyplace.com,https://www.happyplace.com,https://admin.happyplace.com

# SSL/HTTPS
SSL_ENABLED=true
```

**Secure the environment file:**

```bash
chmod 600 .env.production
```

### 2. Systemd Service Configuration

```bash
# Copy systemd service file
sudo cp /var/www/happyplace/backend/systemd/happyplace-backend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable happyplace-backend

# Start the service
sudo systemctl start happyplace-backend

# Check status
sudo systemctl status happyplace-backend

# View logs
sudo journalctl -u happyplace-backend -f
```

### 3. Test Backend

```bash
# Health check
curl http://127.0.0.1:5001/api/health

# Should return:
# {"status":"healthy","database":"connected",...}

# Test API endpoint
curl http://127.0.0.1:5001/api/products

# Should return product list (may be empty initially)
```

---

## Frontend Deployment

### 1. Build Customer Frontend

```bash
cd /var/www/happyplace/frontend-customer

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
REACT_APP_API_URL=https://happyplace.com
REACT_APP_ENVIRONMENT=production
EOF

# Build for production
npm run build

# Verify build
ls -lh build/
```

### 2. Build Admin Frontend

```bash
cd /var/www/happyplace/frontend-admin

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
REACT_APP_API_URL=https://admin.happyplace.com
REACT_APP_ENVIRONMENT=production
EOF

# Build for production
npm run build

# Verify build
ls -lh build/
```

### 3. Set Permissions

```bash
# Set ownership
sudo chown -R www-data:www-data /var/www/happyplace/frontend-customer/build
sudo chown -R www-data:www-data /var/www/happyplace/frontend-admin/build

# Set permissions
sudo find /var/www/happyplace/frontend-*/build -type d -exec chmod 755 {} \;
sudo find /var/www/happyplace/frontend-*/build -type f -exec chmod 644 {} \;
```

---

## Nginx Configuration

### 1. Install SSL Certificates (Let's Encrypt)

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Obtain SSL certificate
sudo certbot certonly --standalone -d happyplace.com -d www.happyplace.com -d admin.happyplace.com

# Certificates will be saved to:
# /etc/letsencrypt/live/happyplace.com/fullchain.pem
# /etc/letsencrypt/live/happyplace.com/privkey.pem
```

### 2. Configure Nginx

```bash
# Copy nginx configuration
sudo cp /var/www/happyplace/backend/nginx.conf /etc/nginx/sites-available/happyplace.com

# Create symlink
sudo ln -s /etc/nginx/sites-available/happyplace.com /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 3. Set Up SSL Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically creates a cron job/systemd timer
# Verify:
sudo systemctl status certbot.timer

# Manual renewal (if needed):
# sudo certbot renew
```

---

## Monitoring & Logging

### 1. Configure Log Rotation

Create `/etc/logrotate.d/happyplace`:

```conf
/var/log/happyplace/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        systemctl reload happyplace-backend > /dev/null 2>&1 || true
    endscript
}
```

### 2. Set Up Health Monitoring

```bash
# Add health check to cron
crontab -e

# Add this line (check every 5 minutes)
*/5 * * * * /var/www/happyplace/backend/scripts/health_check.sh || mail -s "Health Check Failed" admin@happyplace.com
```

### 3. Configure System Monitoring (Optional)

Install monitoring tools:

```bash
# Install htop for process monitoring
sudo apt install -y htop

# Install netdata for real-time monitoring (optional)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

---

## Backup Configuration

### 1. Set Up Automated Backups

```bash
# Add backup to cron (daily at 2 AM)
sudo crontab -e

# Add this line:
0 2 * * * /var/www/happyplace/backend/scripts/backup_database.sh

# Test backup manually
sudo /var/www/happyplace/backend/scripts/backup_database.sh
```

### 2. Verify Backup

```bash
# Check backup files
ls -lh /var/backups/happy_place/

# Test restore (on a separate test database)
# /var/www/happyplace/backend/scripts/restore_database.sh /var/backups/happy_place/happyplace_db_YYYYMMDD_HHMMSS.sql.gz
```

### 3. Off-Site Backup (Recommended)

```bash
# Set up S3 sync (example using AWS S3)
sudo apt install -y awscli

# Configure AWS credentials
aws configure

# Add to daily cron after database backup:
0 3 * * * aws s3 sync /var/backups/happy_place/ s3://your-bucket/happy-place-backups/
```

---

## Production Checklist

### Pre-Launch Checklist

- [ ] **Server Configuration**
  - [ ] Server provisioned and accessible via SSH
  - [ ] Firewall configured (ports 22, 80, 443 open)
  - [ ] System packages updated
  - [ ] Required software installed

- [ ] **Database**
  - [ ] PostgreSQL installed and running
  - [ ] Production database created
  - [ ] Database user created with strong password
  - [ ] Schema initialized
  - [ ] Test data removed (if any)

- [ ] **Backend**
  - [ ] Repository cloned to /var/www/happyplace
  - [ ] Python virtual environment set up
  - [ ] Dependencies installed
  - [ ] .env.production configured with production values
  - [ ] All secret keys generated and unique
  - [ ] M-Pesa production credentials configured
  - [ ] Email SMTP configured and tested
  - [ ] Gunicorn service running
  - [ ] Health check endpoint responding

- [ ] **Frontend**
  - [ ] Customer frontend built for production
  - [ ] Admin frontend built for production
  - [ ] Environment variables set correctly
  - [ ] Build files deployed to /var/www/happyplace/frontend-*/build
  - [ ] File permissions set correctly

- [ ] **Nginx & SSL**
  - [ ] Nginx installed and configured
  - [ ] SSL certificates obtained (Let's Encrypt)
  - [ ] HTTPS redirect working
  - [ ] All domains accessible via HTTPS
  - [ ] SSL auto-renewal configured

- [ ] **Security**
  - [ ] All passwords are strong and unique
  - [ ] .env.production file secured (chmod 600)
  - [ ] Database user has minimum required privileges
  - [ ] Firewall rules configured
  - [ ] Security headers configured in Nginx
  - [ ] CORS origins restricted to production domains

- [ ] **Monitoring & Logging**
  - [ ] Application logs configured
  - [ ] Log rotation set up
  - [ ] Health monitoring configured
  - [ ] Error alerting configured

- [ ] **Backups**
  - [ ] Automated database backups configured
  - [ ] Backup retention policy set
  - [ ] Backup restoration tested
  - [ ] Off-site backup configured (recommended)

- [ ] **Testing**
  - [ ] All critical user flows tested in production environment
  - [ ] Payment integration tested with real transactions
  - [ ] Email notifications verified
  - [ ] Mobile responsiveness verified
  - [ ] Cross-browser compatibility checked

---

## Troubleshooting

### Backend Not Starting

**Check logs:**
```bash
sudo journalctl -u happyplace-backend -n 50
```

**Common issues:**
- Database connection error: Check DATABASE_URL and PostgreSQL status
- Missing dependencies: Reinstall with `pip install -r requirements.txt`
- Port already in use: Check for other processes on port 5001

### Nginx 502 Bad Gateway

**Check Gunicorn:**
```bash
sudo systemctl status happyplace-backend
curl http://127.0.0.1:5001/api/health
```

**Check Nginx error logs:**
```bash
sudo tail -f /var/log/nginx/happyplace-error.log
```

### SSL Certificate Issues

**Check certificate:**
```bash
sudo certbot certificates
```

**Renew manually:**
```bash
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

### Database Connection Issues

**Check PostgreSQL:**
```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT 1;"
```

**Test connection:**
```bash
psql -h localhost -U happy_place_user -d happy_place_production
```

---

## Deployment Commands Reference

### Start/Stop Services

```bash
# Backend
sudo systemctl start happyplace-backend
sudo systemctl stop happyplace-backend
sudo systemctl restart happyplace-backend
sudo systemctl status happyplace-backend

# Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl reload nginx

# PostgreSQL
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql
```

### View Logs

```bash
# Backend application logs
sudo journalctl -u happyplace-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/happyplace-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/happyplace-error.log

# Application logs
sudo tail -f /var/log/happyplace/application.log
sudo tail -f /var/log/happyplace/error.log
```

### Update Deployment

```bash
# Pull latest code
cd /var/www/happyplace
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart happyplace-backend

# Update frontend
cd ../frontend-customer
npm install
npm run build

cd ../frontend-admin
npm install
npm run build

# Reload Nginx
sudo systemctl reload nginx
```

---

## Support & Resources

**Documentation:**
- Backend API: `/api/docs` (when deployed)
- SSL Setup Guide: `backend/SSL_PRODUCTION_SETUP.md`
- Recovery Plan: `RECOVERY_PLAN_2025.md`

**Monitoring:**
- Health Check: `https://happyplace.com/api/health`
- Server Status: `/var/www/happyplace/backend/scripts/health_check.sh`

**Backups:**
- Backup Directory: `/var/backups/happy_place/`
- Restore Script: `backend/scripts/restore_database.sh`

---

**Deployment Guide Version:** 1.0
**Last Updated:** January 7, 2026
**Maintained By:** Happy Place Boutique Development Team
