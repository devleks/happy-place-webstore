# 🔧 PHASE 1: COMMAND REFERENCE
**Quick Copy-Paste Commands**

---

## 🚀 GETTING STARTED

### Create Feature Branch
```bash
cd /Users/xreatives/Documents/Code/cli_projects/happy_place_webstore
git checkout -b feature/phase-1-order-tracking
git push -u origin feature/phase-1-order-tracking
```

### Backup Database
```bash
mkdir -p backups
pg_dump -U postgres happy_place_dev > backups/backup_before_phase1_$(date +%Y%m%d_%H%M%S).sql
```

---

## 📊 TASK 1.1.1: DATABASE MIGRATION

### Run Migration
```bash
cd backend
source venv/bin/activate
psql -U postgres -d happy_place_dev -f migrations/020_add_order_tracking.sql
```

### Verify Migration
```bash
# Check shipment_updates table
psql -U postgres -d happy_place_dev -c "\d shipment_updates"

# Check shipping_carriers table
psql -U postgres -d happy_place_dev -c "\d shipping_carriers"

# Check orders table columns
psql -U postgres -d happy_place_dev -c "\d orders" | grep tracking

# View carriers data
psql -U postgres -d happy_place_dev -c "SELECT * FROM shipping_carriers;"
```

### Rollback (if needed)
```bash
psql -U postgres -d happy_place_dev -c "
ALTER TABLE orders 
DROP COLUMN IF EXISTS tracking_number,
DROP COLUMN IF EXISTS carrier,
DROP COLUMN IF EXISTS tracking_url,
DROP COLUMN IF EXISTS estimated_delivery_date,
DROP COLUMN IF EXISTS shipping_notes;

DROP TABLE IF EXISTS shipment_updates CASCADE;
DROP TABLE IF EXISTS shipping_carriers CASCADE;
"
```

### Commit Changes
```bash
git add backend/migrations/020_add_order_tracking.sql
git commit -m "feat: Add order tracking database schema"
git push origin feature/phase-1-order-tracking
```

---

## 🔧 TASK 1.1.2: BACKEND MODELS

### Test Models in Python Shell
```bash
cd backend
source venv/bin/activate
python

# In Python shell:
from app import app, db
from models.database_models import Order, ShipmentUpdate, ShippingCarrier

# Test ShippingCarrier
carriers = ShippingCarrier.query.all()
for c in carriers:
    print(c.name)

# Test Order with tracking
order = Order.query.first()
print(order.tracking_number)

exit()
```

### Commit Changes
```bash
git add backend/models/database_models.py
git commit -m "feat: Add tracking models (ShipmentUpdate, ShippingCarrier)"
git push origin feature/phase-1-order-tracking
```

---

## 🌐 TASK 1.1.3: BACKEND API

### Test API Endpoints
```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/employee/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.co.ke","password":"your_password"}' \
  | jq -r '.access_token')

# Test get carriers
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/shipping/carriers

# Test add tracking
curl -X POST http://localhost:5001/api/admin/orders/1/tracking \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number": "DHL123456789",
    "carrier": "DHL Express",
    "estimated_delivery": "2025-12-15",
    "notes": "Package dispatched"
  }'

# Test get tracking
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/admin/orders/1/tracking
```

### Commit Changes
```bash
git add backend/routes/admin_routes.py
git commit -m "feat: Add order tracking API endpoints"
git push origin feature/phase-1-order-tracking
```

---

## 💻 TASK 1.1.4: ADMIN UI

### Start Frontend Dev Server
```bash
cd frontend
npm install
npm start
# Opens http://localhost:3000
```

### Test in Browser
1. Login as admin
2. Go to Orders page
3. Click on an order
4. Click "Add Tracking" button
5. Fill form and submit
6. Verify tracking appears

### Commit Changes
```bash
git add frontend/src/pages/admin/AdminOrders.js
git add frontend/src/services/adminAPI.js
git commit -m "feat: Add tracking modal to admin orders"
git push origin feature/phase-1-order-tracking
```

---

## 👤 TASK 1.1.5: CUSTOMER TRACKING

### Test Customer View
1. Open http://localhost:3000/track-order/1
2. Verify tracking information displays
3. Check timeline shows updates
4. Test tracking URL link

### Commit Changes
```bash
git add frontend/src/pages/TrackOrder.js
git add frontend/src/App.js
git commit -m "feat: Add customer order tracking page"
git push origin feature/phase-1-order-tracking
```

---

## 📦 TASK 1.2.1: FULFILLMENT DATABASE

### Run Migration
```bash
cd backend
psql -U postgres -d happy_place_dev -f migrations/021_add_fulfillment_roles.sql
```

### Verify Migration
```bash
# Check role constraint
psql -U postgres -d happy_place_dev -c "\d employees" | grep role

# Check role_definitions table
psql -U postgres -d happy_place_dev -c "SELECT * FROM role_definitions;"

# Check order_assignments table
psql -U postgres -d happy_place_dev -c "\d order_assignments"
```

### Commit Changes
```bash
git add backend/migrations/021_add_fulfillment_roles.sql
git commit -m "feat: Add fulfillment roles and order assignments"
git push origin feature/phase-1-order-tracking
```

---

## 🔐 TASK 1.2.2: FULFILLMENT MIDDLEWARE

### Test Middleware
```bash
cd backend
python

# In Python shell:
from middleware.auth import fulfillment_required, warehouse_required
# Test decorator functionality

exit()
```

### Commit Changes
```bash
git add backend/middleware/auth.py
git commit -m "feat: Add fulfillment middleware decorators"
git push origin feature/phase-1-order-tracking
```

---

## 🌐 TASK 1.2.3: FULFILLMENT API

### Test Fulfillment Endpoints
```bash
# Login as fulfillment agent
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/employee/login \
  -H "Content-Type: application/json" \
  -d '{"email":"fulfillment@happyplace.co.ke","password":"password"}' \
  | jq -r '.access_token')

# Get dashboard metrics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/fulfillment/dashboard

# Get pending orders
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/fulfillment/orders/pending

# Assign order
curl -X POST http://localhost:5001/api/fulfillment/orders/1/assign \
  -H "Authorization: Bearer $TOKEN"

# Get my orders
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/fulfillment/orders/my-orders
```

### Commit Changes
```bash
git add backend/routes/fulfillment_routes.py
git add backend/app.py
git commit -m "feat: Add fulfillment API endpoints"
git push origin feature/phase-1-order-tracking
```

---

## 💻 TASK 1.2.4: FULFILLMENT DASHBOARD

### Test Fulfillment UI
1. Login as fulfillment agent
2. Go to /fulfillment/dashboard
3. View pending orders
4. Assign order to self
5. View my orders

### Commit Changes
```bash
git add frontend/src/pages/fulfillment/
git add frontend/src/services/fulfillmentAPI.js
git commit -m "feat: Add fulfillment dashboard UI"
git push origin feature/phase-1-order-tracking
```

---

## ✅ FINAL TESTING

### Run All Tests
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test -- --watchAll=false

# Integration tests
bash qa_automated_tests.sh
```

### Create Pull Request
```bash
# Push final changes
git push origin feature/phase-1-order-tracking

# Create PR (via GitHub UI or gh CLI)
gh pr create --title "Phase 1: Order Tracking & Fulfillment" \
  --body "Implements order tracking system and fulfillment workflow"
```

---

## 🔄 USEFUL COMMANDS

### Check Database
```bash
# Connect to database
psql -U postgres -d happy_place_dev

# List tables
\dt

# Describe table
\d table_name

# Exit
\q
```

### Check Git Status
```bash
git status
git log --oneline -10
git diff
```

### Restart Services
```bash
# Backend
cd backend
python app.py

# Frontend
cd frontend
npm start
```

---

**Save this file for quick reference during implementation!**
