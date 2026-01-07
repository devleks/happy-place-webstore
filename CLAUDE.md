# CLAUDE.md - Happy Place Boutique E-Commerce Platform

**AI Assistant Guide for Claude Code & Other LLMs**

**Last Updated:** December 26, 2025
**Project Version:** 1.0
**Status:** 75% Complete - Recovery Phase

---

## TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Authentication & Security](#authentication--security)
8. [Common Patterns](#common-patterns)
9. [Current Status](#current-status)

---

## PROJECT OVERVIEW

### What is Happy Place Boutique?

Full-stack e-commerce platform for women's and maternity clothing retail. Supports online shopping and physical store operations (Nairobi, Kenya).

### Key Features

- **Online Store**: Product catalog, cart, wishlist, checkout
- **POS System**: In-store transactions with barcode scanning
- **Multi-Portal**: Separate customer, employee, admin interfaces
- **GDPR Compliant**: Encrypted PII, consent tracking, audit logs
- **Security**: JWT auth, field-level encryption, Scrypt/Argon2 passwords

### Project Metrics

| Metric | Value |
|--------|-------|
| **Backend** | Python 3.11+, Flask |
| **Frontend** | React 18 (4 SPAs) |
| **Database** | PostgreSQL (22 tables) |
| **API Endpoints** | 50+ REST endpoints |
| **Completion** | ~75% |

---

## QUICK START

### Prerequisites
- Python 3.11+, Node.js 16+, PostgreSQL 12+

### Setup (5 minutes)

```bash
# 1. Database
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -c "CREATE DATABASE happy_place_db;"

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed.py  # Initialize with sample data
python app.py   # Start on http://127.0.0.1:5001

# 3. Frontend (Customer)
cd ../frontend-customer
npm install && npm start  # Port 3000

# 4. Frontend (Admin)
cd ../frontend-admin
PORT=3001 npm install && npm start  # Port 3001
```

### Test Credentials

```
Admin:    admin@happyplace.com / AdminPass123!
Manager:  manager@happyplace.com / ManagerPass123!
Customer: customer@example.com / CustomerPass123!
```

Full credentials in `TEST_CREDENTIALS.md`

---

## ARCHITECTURE

### System Overview

```
┌─────────────────────────────────────────┐
│         PRESENTATION TIER               │
│  [Customer] [Admin] [Employee] [POS]    │
│   :3000      :3001    :3002     :3003   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       APPLICATION TIER                  │
│      Flask REST API :5001               │
│  /api/auth  /api/admin  /api/pos        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           DATA TIER                     │
│   PostgreSQL :5432 (22 tables)          │
└─────────────────────────────────────────┘
```

### Tech Stack

**Backend:**
- Flask 3.0 + SQLAlchemy 2.0
- JWT authentication, MultiFernet encryption
- Gunicorn (production), PostgreSQL

**Frontend:**
- React 18, React Router 6, Axios
- Context API for state management
- 4 separate SPAs (customer, admin, employee, POS)

---

## PROJECT STRUCTURE

```
happy_place_webstore/
├── backend/                  # Flask REST API
│   ├── app.py               # Application factory
│   ├── config.py            # Configuration
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # API blueprints
│   │   ├── auth_routes.py
│   │   ├── admin_routes.py
│   │   └── fulfillment_routes.py
│   ├── services/            # Business logic
│   ├── middleware/          # Auth, CORS, monitoring
│   └── .env                 # Environment variables
│
├── frontend-customer/       # Customer portal (Port 3000)
│   └── src/
│       ├── pages/           # Routes (Home, Products, Cart, Checkout)
│       ├── components/      # Reusable UI (Header, ProductCard)
│       ├── context/         # Global state (Auth, Cart, Wishlist)
│       └── services/api.js  # HTTP client
│
├── frontend-admin/          # Admin portal (Port 3001)
│   └── src/pages/admin/     # Dashboard, Orders, Inventory, Settings
│
├── frontend-employee/       # Employee portal (Port 3002)
├── pos-app/                 # POS PWA (Port 3003)
│
├── documentation/           # Project docs
├── CLAUDE.md               # This file (AI guide)
├── RECOVERY_PLAN_2025.md   # Current execution plan
└── TEST_CREDENTIALS.md     # Login credentials
```

---

## DATABASE SCHEMA

### Core Tables (22 total)

**Customer Management:**
- `customers`, `customer_addresses`

**Employee Management:**
- `employees` (roles: admin, manager, cashier, fulfillment_agent)

**Product Catalog:**
- `categories`, `products`, `product_images`, `inventory`

**Shopping Experience:**
- `carts`, `cart_items`, `wishlists`, `wishlist_items`

**Orders & Payments:**
- `orders`, `order_items`, `payments`, `reviews`

**POS System:**
- `pos_transactions`, `pos_transaction_items`, `store_locations`

**GDPR Compliance:**
- `gdpr_data_requests`, `gdpr_consent_log`, `data_access_log`

### Key Model: Customer

```python
class Customer(db.Model):
    id                      # Primary key
    email_hash              # SHA-256 (for login lookup, indexed)
    email_encrypted         # MultiFernet encrypted
    first_name_encrypted    # PII encrypted at rest
    last_name_encrypted     # PII encrypted at rest
    phone_encrypted         # PII encrypted at rest
    password_hash           # Scrypt/Argon2
    gdpr_consent            # Boolean
    marketing_consent       # Boolean
    anonymized              # For GDPR right to erasure
    created_at, updated_at
```

Full schema: `documentation/DATABASE_SCHEMA.md`

---

## API ENDPOINTS

### Base URL
```
Development: http://127.0.0.1:5001
Production:  https://api.happyplace.com
```

### Endpoint Groups

**Authentication** (`/api/auth`)
- POST `/register`, `/login`, `/employee/login`
- GET `/me`, POST `/refresh`, `/logout`

**Products** (`/api`)
- GET `/products`, `/products/:slug`, `/categories`

**Cart & Wishlist** (`/api`)
- GET/POST/PUT/DELETE `/cart/items`, `/wishlist/items`

**Orders** (`/api`)
- POST `/orders` (create), GET `/orders` (list), PUT `/orders/:id/cancel`

**Admin** (`/api/admin`)
- GET `/dashboard/metrics`, `/inventory`, `/orders`, `/customers`
- POST `/employees`, GET `/reports/sales`

**POS** (`/api/pos`)
- POST `/shifts/start`, `/shifts/close`, `/transactions`

**Fulfillment** (`/api/fulfillment`)
- GET `/orders/pending`, PUT `/orders/:id/pick|pack|ship`

📖 **Complete API reference:** `documentation/API_REFERENCE.md`

---

## AUTHENTICATION & SECURITY

### Authentication Flow

**Customer Login:**
1. POST `/api/auth/login` with email/password
2. Email lookup via SHA-256 hash (`email_hash` field)
3. Password verified with Scrypt
4. Returns JWT access token (expires 30 days)
5. Frontend stores token in localStorage

**Employee Login:**
1. POST `/api/auth/employee/login`
2. Returns JWT with `role` claim (admin, manager, cashier, etc.)
3. Role-based access control via middleware decorators

### JWT Token Structure
```json
{
  "sub": "user-id",
  "user_type": "customer|employee",
  "role": "admin|manager|cashier|fulfillment_agent",
  "exp": 1234567890
}
```

### Security Features

**Encryption:**
- MultiFernet PII encryption (dual-key: `ENCRYPTION_KEY` + `ENCRYPTION_KEY_2`)
- Customer email, name, phone, address encrypted at rest
- Hash-based lookup for search (`email_hash` SHA-256)

**Password Security:**
- Werkzeug Scrypt for customers
- Bcrypt/Argon2 for employees

**API Security:**
- CORS configured for allowed origins
- Rate limiting on sensitive endpoints
- HTTPS required (production)
- CSRF protection via JWT

### Environment Variables

```bash
# backend/.env
DATABASE_URL=postgresql://postgres:password@localhost:5432/happy_place_db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key-1
ENCRYPTION_KEY_2=your-encryption-key-2
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## COMMON PATTERNS

### Adding API Endpoint

```python
# backend/routes/admin_routes.py
@admin_bp.route('/new-endpoint', methods=['POST'])
@jwt_required()
@role_required(['admin', 'manager'])
def new_endpoint():
    data = request.get_json()
    result = some_service.process(data)
    return jsonify({'success': True, 'data': result}), 200
```

```javascript
// frontend/src/services/adminAPI.js
export const newEndpoint = async (data) => {
  const response = await api.post('/admin/new-endpoint', data);
  return response.data;
};
```

### Adding Database Table

```python
# backend/models.py
class NewTable(db.Model):
    __tablename__ = 'new_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}
```

```bash
# Create table
cd backend && source venv/bin/activate
python -c "from app import create_app; from models import db; app=create_app(); app.app_context().push(); db.create_all()"
```

### Adding Frontend Page

```javascript
// frontend-customer/src/pages/NewPage.js
import React from 'react';

const NewPage = () => {
  return <div className="new-page"><h1>New Page</h1></div>;
};

export default NewPage;
```

```javascript
// frontend-customer/src/App.js
import NewPage from './pages/NewPage';

<Route path="/new-page" element={<NewPage />} />
```

---

## CURRENT STATUS

### ✅ Completed (75%)

**Backend:**
- Database schema (22 tables)
- Authentication system
- 50+ API endpoints
- Product catalog
- Order management
- POS transactions
- GDPR compliance

**Frontend:**
- Customer portal (shopping, cart, checkout UI)
- Admin portal (dashboard, orders, inventory)
- Product browsing/search
- Order tracking page
- Basic responsive design

### ❌ Missing (25%) - **CRITICAL FOR LAUNCH**

**P0 Blockers:**
1. **Backend HTTP hanging** (blocks all frontend testing)
2. **Payment integration** (M-Pesa/COD - can't sell without this)
3. **Email notifications** (order confirmations, tracking updates)
4. **Cart backend connection** (frontend cart doesn't persist)

**P1 High Priority:**
5. Fulfillment workflow (order assignment system)
6. SSL/HTTPS setup
7. Production deployment configuration

**P2 Post-Launch:**
- Portal separation (employee/admin)
- Real-time dashboard updates
- Advanced reporting
- Audit log viewer

### Recovery Plan

📋 **See RECOVERY_PLAN_2025.md for 4-week execution plan**

**Target Launch:** January 24, 2026
**Current Phase:** Week 1 - Unblocking (Dec 26 - Jan 1)

---

## TROUBLESHOOTING

### Backend Won't Start

**HTTP Hanging Issue:**
```bash
# Kill process
lsof -ti:5001 | xargs kill -9

# Minimal debug version
cd backend
cp app.py app.py.backup
# Comment out: newrelic, rate limiting, custom monitoring
python app.py

# Test
curl http://127.0.0.1:5001/api/products
```

**Database Connection:**
```bash
# Verify PostgreSQL running
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -d happy_place_db -c "SELECT 1;"

# Check .env
cat backend/.env | grep DATABASE_URL
```

### Frontend Issues

**CORS Errors:**
- Check `backend/config.py` has correct `CORS_ORIGINS`
- Verify frontend `.env` has `REACT_APP_API_URL=http://127.0.0.1:5001`
- Restart both backend and frontend

**Token Expired:**
```javascript
localStorage.removeItem('token');
window.location.href = '/login';
```

📖 **Full troubleshooting:** `documentation/TROUBLESHOOTING.md`

---

## DEVELOPMENT WORKFLOW

### Git Workflow
- **Main branch:** `main`
- **Current branch:** `chore/git-cleanup-working-tree-20251219`
- Create feature branches from `main`

### Code Style
- **Python:** PEP 8, type hints, docstrings
- **JavaScript:** Functional components, hooks, PropTypes
- **Avoid:** Over-engineering, premature abstraction

### Testing Locally

```bash
# Backend endpoint test
curl -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.com","password":"AdminPass123!"}'

# Frontend: Open browser to http://localhost:3000
# Check DevTools console for errors (F12)
```

---

## TIPS FOR AI ASSISTANTS

### Critical Info

1. **Backend runs on port 5001** (not 5000)
2. **4 frontends on different ports** (3000, 3001, 3002, 3003)
3. **Password hashing varies:**
   - Customers: Werkzeug Scrypt
   - Employees: Bcrypt/Argon2
4. **PII fields are encrypted** (use `email_hash` for lookups, not `email`)
5. **Blueprint URL prefixes:**
   - `/api` (main), `/api/auth`, `/api/admin`, `/api/pos`, `/api/fulfillment`

### Current Priority

**Focus on RECOVERY_PLAN_2025.md execution:**
- Week 1: Fix backend, integrate payments, add email
- Don't add new features not in the plan
- Ship working code, not perfect documentation

### Security First

- Never commit secrets to git
- Use environment variables
- Follow GDPR patterns for PII
- Validate all user input

---

## ADDITIONAL RESOURCES

**Documentation:**
- `RECOVERY_PLAN_2025.md` - Current execution plan (START HERE)
- `API_REFERENCE.md` - Detailed API documentation
- `DATABASE_SCHEMA.md` - Complete schema with relationships
- `SECURITY_GUIDE.md` - Security best practices
- `TROUBLESHOOTING.md` - Common issues and solutions
- `TEST_CREDENTIALS.md` - All test account credentials

**Phase Documentation:**
- `.claude/PHASE_1_STATUS.md` - Phase 1 implementation status
- `.claude/PHASE_1_TESTING.md` - Testing checklist (80+ test cases)

---

**Last Updated:** December 26, 2025
**Project Path:** `/Users/ml_labs/Documents/Code/cli_projects/happy_place_webstore`
**Next Action:** Open `RECOVERY_PLAN_2025.md` or `START_HERE.md`
