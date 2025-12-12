# Troubleshooting Guide - Happy Place Boutique

Common issues and solutions for the Happy Place Boutique e-commerce platform.

---

## Table of Contents

1. [Backend Issues](#backend-issues)
2. [Frontend Issues](#frontend-issues)
3. [Database Issues](#database-issues)
4. [Authentication Issues](#authentication-issues)
5. [POS System Issues](#pos-system-issues)
6. [Deployment Issues](#deployment-issues)
7. [Performance Issues](#performance-issues)

---

## Backend Issues

### Flask Server Won't Start

**Symptom:** `python app.py` fails or server crashes immediately

**Solutions:**

1. **Check virtual environment is activated:**
   ```bash
   source backend/venv/bin/activate  # macOS/Linux
   venv\Scripts\activate  # Windows
   ```

2. **Verify all dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check database connection:**
   ```bash
   # Test PostgreSQL connection
   psql -U postgres -d happy_place_db -c "SELECT 1;"
   ```

4. **Verify environment variables:**
   ```bash
   # Check .env file exists
   ls backend/.env
   
   # Verify DATABASE_URL is set
   cat backend/.env | grep DATABASE_URL
   ```

5. **Check port availability:**
   ```bash
   # Port 5000 already in use?
   lsof -i :5000
   
   # Kill process if needed
   kill -9 <PID>
   ```

---

### Import Errors

**Symptom:** `ModuleNotFoundError` or `ImportError`

**Solutions:**

1. **Reinstall dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.11+
   ```

3. **Verify PYTHONPATH:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
   ```

---

### Database Migration Errors

**Symptom:** Migration fails or database schema mismatch

**Solutions:**

1. **Check migration files:**
   ```bash
   ls backend/migrations/
   ```

2. **Run migrations manually:**
   ```bash
   cd backend
   python scripts/migrate_database.py
   ```

3. **Reset database (CAUTION - deletes all data):**
   ```bash
   dropdb happy_place_db
   createdb happy_place_db
   python seed.py
   ```

---

## Frontend Issues

### React App Won't Start

**Symptom:** `npm start` fails

**Solutions:**

1. **Delete node_modules and reinstall:**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm start
   ```

2. **Check Node.js version:**
   ```bash
   node --version  # Should be 16+
   ```

3. **Clear npm cache:**
   ```bash
   npm cache clean --force
   ```

4. **Check port 3000:**
   ```bash
   lsof -i :3000
   kill -9 <PID>
   ```

---

### API Connection Errors

**Symptom:** Frontend can't connect to backend API

**Solutions:**

1. **Verify backend is running:**
   ```bash
   curl http://localhost:5000/api/health
   ```

2. **Check CORS configuration:**
   ```python
   # backend/app.py
   CORS(app, origins=["http://localhost:3000"])
   ```

3. **Verify API base URL:**
   ```javascript
   // frontend/src/services/api.js
   const API_BASE_URL = 'http://localhost:5000/api';
   ```

4. **Check browser console for errors:**
   - Open DevTools (F12)
   - Check Console and Network tabs

---

### Build Errors

**Symptom:** `npm run build` fails

**Solutions:**

1. **Increase Node memory:**
   ```bash
   export NODE_OPTIONS="--max-old-space-size=4096"
   npm run build
   ```

2. **Check for syntax errors:**
   ```bash
   npm run lint
   ```

3. **Clear build cache:**
   ```bash
   rm -rf build/
   npm run build
   ```

---

## Database Issues

### Connection Refused

**Symptom:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   # macOS
   brew services list | grep postgresql
   brew services start postgresql@14
   
   # Linux
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. **Verify connection string:**
   ```bash
   # Check .env file
   DATABASE_URL=postgresql://postgres:password@localhost:5432/happy_place_db
   ```

3. **Test connection:**
   ```bash
   psql -U postgres -d happy_place_db
   ```

4. **Check pg_hba.conf:**
   ```bash
   # Allow local connections
   # Add: local   all   all   trust
   ```

---

### Database Does Not Exist

**Symptom:** `database "happy_place_db" does not exist`

**Solution:**

```bash
createdb -U postgres happy_place_db
cd backend
python seed.py
```

---

### Encryption Key Errors

**Symptom:** `cryptography.fernet.InvalidToken`

**Solutions:**

1. **Verify encryption keys in .env:**
   ```bash
   cat backend/.env | grep ENCRYPTION_KEY
   ```

2. **Regenerate keys (CAUTION - will lose encrypted data):**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Re-encrypt data after key change:**
   ```bash
   python scripts/rotate_encryption_keys.py
   ```

---

## Authentication Issues

### Login Fails with Correct Credentials

**Symptom:** 401 Unauthorized despite correct password

**Solutions:**

1. **Check password hashing method:**
   ```python
   # Should use scrypt (Werkzeug default)
   from werkzeug.security import check_password_hash
   ```

2. **Reset password:**
   ```bash
   cd backend
   python reset_admin_password.py
   ```

3. **Check user exists:**
   ```sql
   SELECT id, email_hash, is_active FROM customers WHERE email_hash = '<hash>';
   ```

4. **Verify JWT secret:**
   ```bash
   cat backend/.env | grep JWT_SECRET_KEY
   ```

---

### Token Expired Errors

**Symptom:** `Token has expired`

**Solutions:**

1. **Refresh token:**
   ```javascript
   // Frontend should automatically refresh
   // Check refresh token endpoint
   POST /api/auth/refresh
   ```

2. **Check token expiration settings:**
   ```python
   # backend/config.py
   JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
   JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
   ```

3. **Clear browser storage and re-login:**
   ```javascript
   localStorage.clear();
   sessionStorage.clear();
   ```

---

### CORS Errors

**Symptom:** `Access-Control-Allow-Origin` errors

**Solutions:**

1. **Update CORS origins:**
   ```python
   # backend/app.py
   CORS(app, origins=[
       "http://localhost:3000",
       "http://127.0.0.1:3000"
   ], supports_credentials=True)
   ```

2. **Check request headers:**
   ```javascript
   // Include credentials
   axios.defaults.withCredentials = true;
   ```

---

## POS System Issues

### POS Login Fails

**Symptom:** Employee cannot login to POS

**Solutions:**

1. **Verify employee exists:**
   ```sql
   SELECT id, email, role, is_active FROM employees WHERE email = 'cashier@happyplace.com';
   ```

2. **Create test employee:**
   ```bash
   cd backend
   python create_test_employees.py
   ```

3. **Reset employee password:**
   ```bash
   python scripts/reset_admin_passwords.py
   ```

---

### Shift Cannot Start

**Symptom:** "Cannot start shift" error

**Solutions:**

1. **Check for open shifts:**
   ```sql
   SELECT * FROM pos_shifts WHERE employee_id = <id> AND end_time IS NULL;
   ```

2. **Close previous shift:**
   ```sql
   UPDATE pos_shifts SET end_time = NOW() WHERE id = <shift_id>;
   ```

---

### Barcode Scanner Not Working

**Symptom:** Barcode scanner input not recognized

**Solutions:**

1. **Check scanner mode:**
   - Should be in keyboard emulation mode
   - Test in notepad/text editor first

2. **Verify barcode format:**
   ```sql
   SELECT barcode FROM inventory WHERE barcode IS NOT NULL LIMIT 5;
   ```

3. **Check input focus:**
   - Ensure search input has focus
   - Scanner should append Enter key

---

## Deployment Issues

### Gunicorn Won't Start

**Symptom:** Production server fails to start

**Solutions:**

1. **Check Gunicorn config:**
   ```bash
   cat backend/gunicorn_config.py
   ```

2. **Test Gunicorn manually:**
   ```bash
   cd backend
   gunicorn -c gunicorn_config.py app:app
   ```

3. **Check logs:**
   ```bash
   tail -f /var/log/gunicorn/error.log
   ```

---

### Static Files Not Loading

**Symptom:** CSS/JS files return 404

**Solutions:**

1. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Configure Nginx:**
   ```nginx
   location /static {
       alias /path/to/frontend/build/static;
   }
   ```

3. **Check file permissions:**
   ```bash
   chmod -R 755 frontend/build
   ```

---

### SSL Certificate Errors

**Symptom:** HTTPS not working

**Solutions:**

1. **Renew Let's Encrypt certificate:**
   ```bash
   sudo certbot renew
   sudo systemctl reload nginx
   ```

2. **Check certificate expiry:**
   ```bash
   echo | openssl s_client -servername happyplace.com -connect happyplace.com:443 2>/dev/null | openssl x509 -noout -dates
   ```

---

## Performance Issues

### Slow API Responses

**Symptom:** API endpoints taking >1 second

**Solutions:**

1. **Check database indexes:**
   ```sql
   SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
   ```

2. **Analyze slow queries:**
   ```sql
   SELECT query, mean_exec_time 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;
   ```

3. **Add missing indexes:**
   ```sql
   CREATE INDEX idx_orders_customer ON orders(customer_id);
   CREATE INDEX idx_orders_status ON orders(status);
   ```

4. **Enable query caching:**
   ```python
   # Use Flask-Caching
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   ```

---

### High Memory Usage

**Symptom:** Server using excessive RAM

**Solutions:**

1. **Check for memory leaks:**
   ```bash
   # Monitor memory
   top -p $(pgrep -f gunicorn)
   ```

2. **Reduce Gunicorn workers:**
   ```python
   # gunicorn_config.py
   workers = 2  # Reduce from 4
   ```

3. **Optimize queries:**
   ```python
   # Use pagination
   products = Product.query.paginate(page=1, per_page=20)
   
   # Use lazy loading
   customer = Customer.query.options(lazyload('*')).get(id)
   ```

---

### Database Connection Pool Exhausted

**Symptom:** `QueuePool limit exceeded`

**Solutions:**

1. **Increase pool size:**
   ```python
   # backend/config.py
   SQLALCHEMY_ENGINE_OPTIONS = {
       'pool_size': 20,
       'max_overflow': 10
   }
   ```

2. **Close connections properly:**
   ```python
   @app.teardown_appcontext
   def shutdown_session(exception=None):
       db.session.remove()
   ```

---

## Common Error Messages

### "Token has been revoked"

**Cause:** Refresh token was used after logout

**Solution:** Login again to get new tokens

---

### "Insufficient stock"

**Cause:** Product variant out of stock

**Solution:** 
```sql
-- Check stock
SELECT stock_quantity FROM inventory WHERE id = <variant_id>;

-- Add stock
UPDATE inventory SET stock_quantity = stock_quantity + 10 WHERE id = <variant_id>;
```

---

### "GDPR consent required"

**Cause:** Customer registration without GDPR consent

**Solution:** Ensure `gdpr_consent: true` in registration payload

---

### "Rate limit exceeded"

**Cause:** Too many requests from same IP

**Solution:** Wait 60 seconds or contact admin to whitelist IP

---

## Debug Mode

### Enable Debug Logging

```python
# backend/app.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in .env
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# Application logs
tail -f backend/logs/app.log

# Error logs
tail -f backend/logs/error.log

# Access logs
tail -f backend/logs/access.log
```

---

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Search error message in documentation
3. Check GitHub issues
4. Review application logs

### How to Report Issues

Include:
1. **Environment:** OS, Python version, Node version
2. **Steps to reproduce:** Exact commands run
3. **Expected behavior:** What should happen
4. **Actual behavior:** What actually happens
5. **Error messages:** Full error output
6. **Logs:** Relevant log entries

### Contact

- **Technical Support:** dev@happyplace.com
- **Bug Reports:** GitHub Issues
- **Security Issues:** security@happyplace.com

---

## Quick Fixes

### Reset Everything (Development Only)

```bash
# Stop all services
pkill -f "python app.py"
pkill -f "npm start"

# Reset database
dropdb happy_place_db
createdb happy_place_db

# Reinstall dependencies
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py

cd ../frontend
rm -rf node_modules
npm install

# Restart services
cd ../backend
python app.py &

cd ../frontend
npm start
```

---

## Health Checks

### Backend Health

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-12T20:00:00Z"
}
```

### Database Health

```bash
psql -U postgres -d happy_place_db -c "SELECT COUNT(*) FROM customers;"
```

### Frontend Health

```bash
curl http://localhost:3000
# Should return HTML
```

---

## Useful Commands

```bash
# Check all running services
ps aux | grep -E "python|node|postgres"

# Check port usage
lsof -i :5000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL

# Database backup
pg_dump -U postgres happy_place_db > backup.sql

# Database restore
psql -U postgres happy_place_db < backup.sql

# View active database connections
psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Kill all Python processes
pkill -9 python

# Clear all caches
rm -rf backend/__pycache__
rm -rf frontend/node_modules/.cache
```

---

## Still Having Issues?

If you've tried everything and still experiencing problems:

1. **Create a GitHub issue** with full details
2. **Email support** at dev@happyplace.com
3. **Check documentation** at docs.happyplace.com
4. **Join community** Discord/Slack (if available)
