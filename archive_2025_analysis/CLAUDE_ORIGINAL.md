# CLAUDE.md - Happy Place Boutique E-Commerce Platform

**AI Assistant Guide for Claude Code & Other LLMs**

**Last Updated:** December 22, 2025
**Project Version:** 1.0
**Status:** Production-Ready Multi-Channel Retail System

---

## TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Architecture & Tech Stack](#architecture--tech-stack)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Authentication & Security](#authentication--security)
8. [Development Workflow](#development-workflow)
9. [Testing Strategy](#testing-strategy)
10. [Common Tasks & Patterns](#common-tasks--patterns)
11. [Troubleshooting](#troubleshooting)
12. [Contributing Guidelines](#contributing-guidelines)

---

## PROJECT OVERVIEW

### What is Happy Place Boutique?

Happy Place Boutique is a **full-stack, multi-channel e-commerce platform** for women's and maternity clothing retail. It supports both online shopping and physical store operations through a sophisticated architecture with separated concerns and privacy-by-design principles.

### Key Features

- **Online Store**: Full e-commerce experience with product catalog, cart, wishlist, checkout
- **Point of Sale (POS)**: Complete POS system for in-store transactions with barcode scanning
- **Multi-Portal Architecture**: Separate portals for customers, employees, and administrators
- **GDPR Compliance**: Encrypted PII, consent tracking, right to erasure, audit logging
- **International Support**: Size conversion (8 regional systems), multi-currency support
- **Inventory Management**: Unified inventory tracking for online and physical store
- **Order Fulfillment**: Automated workflow with status tracking and notifications
- **Security**: JWT authentication, field-level encryption, Argon2/Scrypt password hashing

### Business Domain

- **Industry**: Fashion Retail (Women's & Maternity Clothing)
- **Target Users**:
  - B2C customers (online shopping)
  - Store employees (POS, order fulfillment)
  - Store managers (operations oversight)
  - System administrators (full platform control)
- **Deployment Model**: Hybrid (Online + Physical Store in Nairobi, Kenya)

### Project Metrics

| Metric | Value |
|--------|-------|
| **Project Size** | 1.9 GB |
| **Total Files** | 800+ files |
| **Backend Language** | Python 3.11+ |
| **Frontend Language** | JavaScript (React 18) |
| **Database Tables** | 22 tables |
| **API Endpoints** | 50+ REST endpoints |
| **Frontends** | 4 React SPAs (Customer, Admin, Employee, POS) |
| **Overall Completion** | ~75% |

---

## QUICK START GUIDE

### Prerequisites

- **Python 3.11+**
- **Node.js 16+** and npm
- **PostgreSQL 12+**
- **Git**

### Initial Setup (First Time)

1. **Clone the repository**
   ```bash
   cd /Users/ml_labs/Documents/Code/cli_projects/happy_place_webstore
   ```

2. **Set up PostgreSQL database**
   ```bash
   # macOS (Homebrew)
   brew install postgresql@14
   brew services start postgresql@14
   /usr/local/opt/postgresql@14/bin/createdb happy_place_db

   # Or set password and create DB
   PGPASSWORD='Alway$ B3l13ving' /usr/local/opt/postgresql@14/bin/psql -U postgres postgres -c "CREATE DATABASE happy_place_db;"
   ```

3. **Set up Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   python seed.py  # Initialize database with sample data
   ```

4. **Set up Frontends**
   ```bash
   # Customer Portal (Port 3000)
   cd ../frontend-customer
   npm install
   cp .env.example .env

   # Admin Portal (Port 3001)
   cd ../frontend-admin
   npm install
   cp .env.example .env

   # Employee Portal (Port 3002)
   cd ../frontend-employee
   npm install
   cp .env.example .env

   # POS App (Port 3003)
   cd ../pos-app
   npm install
   ```

### Running the Application

**Start Backend (Terminal 1):**
```bash
cd backend
source venv/bin/activate
python app.py  # Development server on http://127.0.0.1:5001
# OR for production:
gunicorn --config gunicorn_config.py app:app
```

**Start Customer Portal (Terminal 2):**
```bash
cd frontend-customer
npm start  # Runs on http://localhost:3000
```

**Start Admin Portal (Terminal 3):**
```bash
cd frontend-admin
PORT=3001 npm start  # Runs on http://localhost:3001
```

**Start Employee Portal (Terminal 4):**
```bash
cd frontend-employee
PORT=3002 npm start  # Runs on http://localhost:3002
```

**Start POS App (Terminal 5):**
```bash
cd pos-app
npm start  # Runs on http://localhost:3003
```

### Test Credentials

See `TEST_CREDENTIALS.md` for complete list. Quick reference:

```
# Admin Portal
Email: admin@happyplace.com
Password: AdminPass123!

# Employee Portal (Manager)
Email: manager@happyplace.com
Password: ManagerPass123!

# Customer Portal
Email: customer@example.com
Password: CustomerPass123!
```

---

## ARCHITECTURE & TECH STACK

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION TIER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Customer   │  │    Admin     │  │   Employee   │     │
│  │   Portal     │  │   Portal     │  │   Portal     │     │
│  │ (React SPA)  │  │ (React SPA)  │  │ (React SPA)  │     │
│  │  Port 3000   │  │  Port 3001   │  │  Port 3002   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│          │                  │                  │           │
│  ┌──────────────┐           │                  │           │
│  │   POS App    │           │                  │           │
│  │  (PWA/React) │           │                  │           │
│  │  Port 3003   │           │                  │           │
│  └──────────────┘           │                  │           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION TIER                        │
│              ┌──────────────────────────┐                   │
│              │    Flask REST API        │                   │
│              │    (Python 3.11+)        │                   │
│              │      Port 5001           │                   │
│              │                          │                   │
│              │  Blueprints:             │                   │
│              │  - /api/*                │                   │
│              │  - /api/auth/*           │                   │
│              │  - /api/admin/*          │                   │
│              │  - /api/fulfillment/*    │                   │
│              │  - /api/pos/*            │                   │
│              └──────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       DATA TIER                             │
│              ┌──────────────────────────┐                   │
│              │   PostgreSQL 12+         │                   │
│              │   (happy_place_db)       │                   │
│              │      Port 5432           │                   │
│              │                          │                   │
│              │  22 Tables:              │                   │
│              │  - customers             │                   │
│              │  - employees             │                   │
│              │  - products              │                   │
│              │  - orders                │                   │
│              │  - pos_transactions      │                   │
│              │  - inventory             │                   │
│              │  - ... and more          │                   │
│              └──────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.11+ | Application runtime |
| **Framework** | Flask | 3.0.0 | Web framework & REST API |
| **ORM** | SQLAlchemy | 2.0.23 | Database abstraction |
| **Database** | PostgreSQL | 12+ | Primary data store |
| **Authentication** | JWT | 4.6.0 (Flask-JWT-Extended) | Token-based auth |
| **Password Hashing** | Werkzeug/Bcrypt | - | Scrypt/Argon2 password storage |
| **Encryption** | Cryptography | 46.0.3 | MultiFernet PII encryption |
| **WSGI Server** | Gunicorn | 23.0.0 | Production server |
| **CORS** | Flask-CORS | 4.0.0 | Cross-origin requests |
| **Rate Limiting** | Flask-Limiter | 3.5.0 | API rate limiting |
| **Monitoring** | New Relic | 11.1.0 | APM (optional) |

**Key Backend Dependencies:**
```python
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-JWT-Extended==4.6.0
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
psycopg2-binary==2.9.9
cryptography==46.0.3
gunicorn==23.0.0
python-dotenv==1.0.0
```

#### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18 | UI framework |
| **Routing** | React Router | 6 | Client-side routing |
| **HTTP Client** | Axios | Latest | API communication |
| **State Management** | React Context | Built-in | Global state |
| **Build Tool** | Create React App | Latest | Build tooling |
| **Styling** | CSS3 | - | Component styling |

**Frontend Apps:**
1. **frontend-customer**: Public-facing online store
2. **frontend-admin**: Administrator dashboard
3. **frontend-employee**: Employee operations portal
4. **pos-app**: Point of Sale Progressive Web App

---

## PROJECT STRUCTURE

```
happy_place_webstore/
├── backend/                      # Flask REST API
│   ├── app.py                   # Application factory
│   ├── config.py                # Configuration management
│   ├── models.py                # SQLAlchemy models
│   ├── extensions.py            # Flask extensions
│   ├── seed.py                  # Database seeding script
│   ├── requirements.txt         # Python dependencies
│   ├── gunicorn_config.py       # Gunicorn production config
│   ├── logging_utils.py         # Logging configuration
│   ├── routes/                  # API route blueprints
│   │   ├── __init__.py         # Main API blueprint
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   ├── admin_routes.py     # Admin dashboard endpoints
│   │   └── fulfillment_routes.py # Order fulfillment endpoints
│   ├── models/                  # Database models (organized)
│   ├── middleware/              # Custom middleware
│   ├── services/                # Business logic services
│   ├── utils/                   # Utility functions
│   ├── scripts/                 # Maintenance scripts
│   ├── tests/                   # Backend tests
│   └── .env.example             # Environment variables template
│
├── frontend-customer/           # Customer-facing React app (Port 3000)
│   ├── public/
│   ├── src/
│   │   ├── components/         # Reusable components
│   │   │   ├── Header.js
│   │   │   ├── ProductCard.js
│   │   │   ├── CustomerLayout.js
│   │   │   └── ...
│   │   ├── pages/              # Page components
│   │   │   ├── Home.js
│   │   │   ├── Products.js
│   │   │   ├── Cart.js
│   │   │   ├── Checkout.js
│   │   │   └── ...
│   │   ├── context/            # React context providers
│   │   │   ├── AuthContext.js
│   │   │   ├── CartContext.js
│   │   │   └── WishlistContext.js
│   │   ├── services/           # API service layer
│   │   │   └── api.js
│   │   ├── styles/             # CSS modules
│   │   ├── utils/              # Utility functions
│   │   ├── App.js              # Main app component
│   │   └── index.js            # Entry point
│   ├── package.json
│   └── .env.example
│
├── frontend-admin/              # Admin dashboard React app (Port 3001)
│   ├── src/
│   │   ├── pages/
│   │   │   └── admin/
│   │   │       ├── AdminDashboard.js
│   │   │       ├── AdminInventory.js
│   │   │       ├── AdminOrders.js
│   │   │       ├── AdminCustomers.js
│   │   │       ├── AdminEmployees.js
│   │   │       ├── AdminSettings.js
│   │   │       └── AdminReports.js
│   │   └── ...
│   └── package.json
│
├── frontend-employee/           # Employee portal React app (Port 3002)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── EmployeeDashboard.js
│   │   │   ├── OrderFulfillment.js
│   │   │   └── ...
│   │   └── ...
│   └── package.json
│
├── pos-app/                     # Point of Sale PWA (Port 3003)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── POSLogin.js
│   │   │   ├── POSDashboard.js
│   │   │   ├── POSNewSale.js
│   │   │   └── ...
│   │   └── ...
│   └── package.json
│
├── documentation/               # Project documentation
│   ├── API_REFERENCE.md
│   ├── DATABASE_SCHEMA.md
│   ├── SECURITY_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   └── ...
│
├── .claude/                     # Claude Code configuration
│   ├── README.md
│   ├── PHASE_1_STATUS.md
│   ├── PHASE_1_TESTING.md
│   └── agents/
│
├── .git/                        # Git repository
├── README.md                    # Project README
├── CLAUDE.md                    # This file
├── TEST_CREDENTIALS.md          # Test account credentials
└── .gitignore

Total Structure:
- 4 Frontend Applications
- 1 Unified Backend API
- 22 Database Tables
- 800+ Total Files
```

### Key Files to Know

#### Backend Core Files

- `backend/app.py` - Flask application factory, blueprint registration
- `backend/config.py` - Configuration management (env vars, secrets)
- `backend/models.py` - Main database models file
- `backend/seed.py` - Database initialization with sample data
- `backend/gunicorn_config.py` - Production server configuration

#### Route Files (Blueprints)

- `backend/routes/__init__.py` - Main API blueprint (`/api/*`)
- `backend/routes/auth_routes.py` - Authentication (`/api/auth/*`)
- `backend/routes/admin_routes.py` - Admin endpoints (`/api/admin/*`)
- `backend/routes/fulfillment_routes.py` - Order fulfillment (`/api/fulfillment/*`)

#### Frontend Core Files

**Customer Portal:**
- `frontend-customer/src/App.js` - Main app with routing
- `frontend-customer/src/components/Header.js` - Site header with cart/wishlist
- `frontend-customer/src/components/ProductCard.js` - Product display card
- `frontend-customer/src/services/api.js` - Axios API client

**Admin Portal:**
- `frontend-admin/src/pages/admin/AdminDashboard.js` - Admin homepage
- `frontend-admin/src/services/adminAPI.js` - Admin API client

---

## DATABASE SCHEMA

### Schema Overview

The database consists of **22 tables** organized into logical domains:

| Category | Tables | Purpose |
|----------|--------|---------|
| **Customer Management** | customers, customer_addresses | Customer accounts with encrypted PII |
| **Employee Management** | employees | Staff accounts with role-based access |
| **Product Catalog** | categories, products, product_images, inventory | Product hierarchy and stock |
| **Shopping Experience** | carts, cart_items, wishlists, wishlist_items | Shopping cart and wishlist |
| **Orders & Payments** | orders, order_items, payments, reviews | Order lifecycle |
| **POS System** | pos_transactions, pos_transaction_items | In-store sales |
| **Store Locations** | store_locations | Physical store info |
| **GDPR Compliance** | gdpr_data_requests, gdpr_consent_log | Privacy compliance |
| **Audit & Logging** | data_access_log, activity_logs | Security audit trail |

### Key Tables

#### customers
```sql
- id (PRIMARY KEY)
- email_hash (SHA-256, UNIQUE, INDEXED) -- for login lookup
- email_encrypted (MultiFernet) -- actual email encrypted
- first_name_encrypted, last_name_encrypted, phone_encrypted
- password_hash (Scrypt/Argon2)
- gdpr_consent, marketing_consent
- anonymized, anonymized_at
- created_at, updated_at
```

#### employees
```sql
- id (PRIMARY KEY)
- email (UNIQUE)
- password_hash
- full_name
- role (admin, manager, cashier, fulfillment)
- is_active
- created_at
```

#### products
```sql
- id (PRIMARY KEY)
- name, slug (UNIQUE)
- description
- price (NUMERIC)
- category_id (FOREIGN KEY → categories.id)
- image_url
- sizes (JSON), colors (JSON)
- is_active
```

#### inventory
```sql
- id (PRIMARY KEY)
- product_id (FOREIGN KEY → products.id)
- size, color
- quantity
- location (online, store)
- sku (UNIQUE)
- barcode
```

#### orders
```sql
- id (PRIMARY KEY)
- customer_id (FOREIGN KEY → customers.id)
- status (pending, processing, shipped, delivered, cancelled)
- total_amount
- shipping_address_encrypted
- created_at, updated_at
```

#### pos_transactions
```sql
- id (PRIMARY KEY)
- employee_id (FOREIGN KEY → employees.id)
- total_amount
- payment_method (cash, mpesa, card)
- transaction_type (sale, return, void)
- shift_id
- receipt_number (UNIQUE)
- created_at
```

For complete schema details, see:
- `DATABASE_SCHEMA.md` - Full table definitions with relationships
- `backend/models.py` - SQLAlchemy model implementations

---

## API ENDPOINTS

### Base URL
```
Development: http://127.0.0.1:5001
Production: https://api.happyplace.com (configured in deployment)
```

### Authentication Endpoints (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new customer | No |
| POST | `/api/auth/login` | Customer login | No |
| POST | `/api/auth/employee/login` | Employee login | No |
| GET | `/api/auth/me` | Get current user | Yes |
| POST | `/api/auth/refresh` | Refresh JWT token | Yes |
| POST | `/api/auth/logout` | Logout user | Yes |

### Product Endpoints (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/products` | Get all products (paginated, searchable) | No |
| GET | `/api/products/:slug` | Get product by slug | No |
| GET | `/api/products/:id/inventory` | Get product inventory | No |
| GET | `/api/categories` | Get all categories | No |
| GET | `/api/categories/:slug` | Get category by slug | No |

### Cart & Wishlist Endpoints (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/cart` | Get user's cart | Yes (Customer) |
| POST | `/api/cart/items` | Add item to cart | Yes (Customer) |
| PUT | `/api/cart/items/:id` | Update cart item quantity | Yes (Customer) |
| DELETE | `/api/cart/items/:id` | Remove item from cart | Yes (Customer) |
| GET | `/api/wishlist` | Get user's wishlist | Yes (Customer) |
| POST | `/api/wishlist/items` | Add item to wishlist | Yes (Customer) |
| DELETE | `/api/wishlist/items/:id` | Remove from wishlist | Yes (Customer) |

### Order Endpoints (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/orders` | Create new order | Yes (Customer) |
| GET | `/api/orders` | Get user's orders | Yes (Customer) |
| GET | `/api/orders/:id` | Get order details | Yes (Customer/Employee) |
| PUT | `/api/orders/:id/cancel` | Cancel order | Yes (Customer) |

### Admin Endpoints (`/api/admin`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/dashboard/metrics` | Dashboard metrics | Yes (Admin) |
| GET | `/api/admin/dashboard/activity` | Recent activity | Yes (Admin) |
| GET | `/api/admin/dashboard/alerts` | System alerts | Yes (Admin) |
| GET | `/api/admin/inventory` | Inventory management | Yes (Admin) |
| GET | `/api/admin/orders` | All orders | Yes (Admin) |
| GET | `/api/admin/customers` | Customer list | Yes (Admin) |
| GET | `/api/admin/employees` | Employee management | Yes (Admin) |
| POST | `/api/admin/employees` | Create employee | Yes (Admin) |
| GET | `/api/admin/promotions` | Promotions list | Yes (Admin) |
| GET | `/api/admin/reports/sales` | Sales reports | Yes (Admin) |
| GET | `/api/admin/settings/currency` | Currency settings | Yes (Admin) |

### POS Endpoints (`/api/pos`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/pos/shifts/start` | Start POS shift | Yes (Employee) |
| GET | `/api/pos/shifts/current` | Get current shift | Yes (Employee) |
| POST | `/api/pos/shifts/close` | Close shift | Yes (Employee) |
| POST | `/api/pos/transactions` | Create sale transaction | Yes (Employee) |
| GET | `/api/pos/transactions/:id` | Get transaction details | Yes (Employee) |
| POST | `/api/pos/transactions/:id/void` | Void transaction | Yes (Manager) |
| GET | `/api/pos/products/search` | Search products by barcode/name | Yes (Employee) |

### Fulfillment Endpoints (`/api/fulfillment`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/fulfillment/orders/pending` | Get pending orders | Yes (Employee) |
| PUT | `/api/fulfillment/orders/:id/pick` | Mark order as picked | Yes (Employee) |
| PUT | `/api/fulfillment/orders/:id/pack` | Mark order as packed | Yes (Employee) |
| PUT | `/api/fulfillment/orders/:id/ship` | Mark order as shipped | Yes (Employee) |

For complete API documentation with request/response examples, see:
- `API_REFERENCE.md` - Detailed API documentation
- Backend route files for implementation details

---

## AUTHENTICATION & SECURITY

### Authentication Flow

1. **Customer Authentication**
   - Endpoint: `POST /api/auth/login`
   - Email lookup via SHA-256 hash (email_hash field)
   - Password verified with Scrypt/Argon2
   - Returns JWT access token (expires in 30 days)
   - Token stored in localStorage on frontend

2. **Employee Authentication**
   - Endpoint: `POST /api/auth/employee/login`
   - Email/password login
   - Returns JWT with role claim (admin, manager, cashier, fulfillment)
   - Role-based access control on protected routes

3. **JWT Token Structure**
   ```json
   {
     "fresh": false,
     "iat": 1234567890,
     "jti": "unique-token-id",
     "type": "access",
     "sub": "user-id",
     "nbf": 1234567890,
     "csrf": "csrf-token",
     "exp": 1234567890,
     "user_type": "customer|employee",
     "role": "admin|manager|cashier|fulfillment" // for employees only
   }
   ```

### Security Features

#### Password Security
- **Customer Passwords**: Werkzeug Scrypt hashing (`generate_password_hash(..., method='scrypt')`)
- **Employee Passwords**: Bcrypt/Argon2 hashing
- Minimum password requirements enforced in frontend

#### PII Encryption
- **MultiFernet Encryption**: Customer PII (email, name, phone, address) encrypted at rest
- **Dual-Key Encryption**: Uses `ENCRYPTION_KEY` and `ENCRYPTION_KEY_2` from environment
- **Hash-Based Lookup**: Email searches use SHA-256 hash (`email_hash` field)

#### GDPR Compliance
- **Data Minimization**: Only collect necessary data
- **Consent Tracking**: `gdpr_consent`, `marketing_consent` flags
- **Right to Erasure**: Anonymization workflow (sets `anonymized=True`, clears PII)
- **Audit Logging**: All PII access logged in `data_access_log` table
- **Data Requests**: Track via `gdpr_data_requests` table

#### API Security
- **CORS**: Configured origins in `config.py`
- **Rate Limiting**: Flask-Limiter on sensitive endpoints
- **Input Validation**: SQLAlchemy ORM prevents SQL injection
- **HTTPS**: Required in production (configured in deployment)
- **CSRF Protection**: JWT CSRF tokens

### Environment Variables

**Backend (.env)**
```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development  # or production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/happy_place_db

# Encryption Keys (MultiFernet)
ENCRYPTION_KEY=your-encryption-key-1
ENCRYPTION_KEY_2=your-encryption-key-2

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003

# Optional: External Services
NEWRELIC_LICENSE_KEY=your-newrelic-key
```

**Frontend (.env for each app)**
```bash
REACT_APP_API_URL=http://127.0.0.1:5001
REACT_APP_ENVIRONMENT=development
```

---

## DEVELOPMENT WORKFLOW

### Git Workflow

**Current Branch:**
```
feature/phase-1-order-tracking
```

**Main Branch:**
```
main
```

**Typical Workflow:**
1. Create feature branch from `main`
2. Develop and test locally
3. Commit changes with descriptive messages
4. Push to remote and create Pull Request
5. Merge to `main` after review

### Code Style & Conventions

#### Python (Backend)
- **PEP 8** style guide
- **Type hints** for function signatures
- **Docstrings** for classes and functions
- **Blueprint pattern** for routes
- **Service layer** for business logic

**Example:**
```python
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard/metrics', methods=['GET'])
@jwt_required()
def get_dashboard_metrics():
    """Get dashboard metrics for admin panel.

    Returns:
        JSON response with metrics data
    """
    user_id = get_jwt_identity()
    # Implementation...
    return jsonify({'metrics': {...}})
```

#### JavaScript/React (Frontend)
- **Functional components** with hooks
- **Context API** for global state
- **Component composition** over inheritance
- **CSS modules** or component-level CSS
- **PropTypes** or TypeScript (if migrating)

**Example:**
```javascript
import React, { useContext, useEffect } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';

const Dashboard = () => {
  const { user } = useContext(AuthContext);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await api.get('/admin/dashboard/metrics');
      // Handle response...
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="dashboard">
      <h1>Welcome, {user?.full_name}</h1>
      {/* Components... */}
    </div>
  );
};

export default Dashboard;
```

### Database Migrations

**Current Approach:**
- Using SQLAlchemy's `db.create_all()` in development
- Manual SQL migrations tracked in `backend/migrations/` (if exists)

**Making Schema Changes:**
1. Update model in `backend/models.py`
2. Create migration SQL script (if in production)
3. Test migration on copy of database
4. Apply migration during deployment window

**Future Enhancement:**
Consider adding Flask-Migrate (Alembic) for automated migrations.

### Testing Locally

**Backend Testing:**
```bash
cd backend
source venv/bin/activate

# Test specific endpoint
curl -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.com","password":"AdminPass123!"}'

# Run test scripts
python test_admin_dashboard_endpoints.py
python test_pos_service_direct.py
```

**Frontend Testing:**
```bash
cd frontend-customer
npm start
# Open http://localhost:3000 in browser
# Test user flows manually

# Check for console errors in DevTools (F12)
```

**Database Testing:**
```bash
# Connect to database
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -d happy_place_db

# Run queries
SELECT * FROM customers LIMIT 5;
SELECT * FROM orders WHERE status = 'pending';
```

---

## TESTING STRATEGY

### Manual Testing

**Phase 1 Testing Checklist:**
See `.claude/PHASE_1_TESTING.md` for comprehensive testing checklist (80+ test cases).

**Key Areas to Test:**
1. **Authentication**: Login/logout for customers and employees
2. **Product Browsing**: Search, filter, pagination
3. **Shopping Cart**: Add/remove items, update quantities
4. **Checkout**: Complete order flow
5. **Admin Dashboard**: Metrics, inventory, orders
6. **POS System**: Shift management, transactions, receipt printing

### API Testing

**Using curl:**
```bash
# Login and get token
TOKEN=$(curl -X POST http://127.0.0.1:5001/api/auth/employee/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.com","password":"AdminPass123!"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Use token for authenticated requests
curl -X GET http://127.0.0.1:5001/api/admin/dashboard/metrics \
  -H "Authorization: Bearer $TOKEN" -s | python3 -m json.tool
```

**Test Scripts:**
- `backend/test_admin_dashboard_endpoints.py` - Admin API tests
- `backend/test_pos_service_direct.py` - POS endpoint tests
- Various shell scripts in `backend/*.sh` - Integration tests

### Automated Testing

**Future Enhancements:**
- **Backend**: pytest with fixtures for API testing
- **Frontend**: Jest + React Testing Library for component tests
- **E2E**: Cypress or Playwright for full user flow tests

---

## COMMON TASKS & PATTERNS

### Adding a New API Endpoint

**Backend (Flask):**

1. **Choose appropriate blueprint** (`routes/admin_routes.py`, `routes/auth_routes.py`, etc.)

2. **Add route handler:**
```python
@admin_bp.route('/new-endpoint', methods=['GET', 'POST'])
@jwt_required()
@role_required(['admin', 'manager'])  # Custom decorator
def new_endpoint():
    """Endpoint description."""
    try:
        # Get request data
        data = request.get_json()

        # Business logic
        result = some_service.process(data)

        # Return response
        return jsonify({
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

3. **Update API client on frontend** (`services/api.js` or `services/adminAPI.js`):
```javascript
export const newEndpoint = async (data) => {
  const response = await api.post('/admin/new-endpoint', data);
  return response.data;
};
```

### Adding a Database Table

1. **Define model in `backend/models.py`:**
```python
class NewTable(db.Model):
    __tablename__ = 'new_table'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='new_items')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }
```

2. **Create table:**
```bash
cd backend
source venv/bin/activate
python
>>> from app import create_app
>>> from models import db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
```

### Adding a Frontend Page

1. **Create page component** (`frontend-customer/src/pages/NewPage.js`):
```javascript
import React from 'react';
import './NewPage.css';

const NewPage = () => {
  return (
    <div className="new-page">
      <h1>New Page</h1>
      {/* Content */}
    </div>
  );
};

export default NewPage;
```

2. **Add route in App.js:**
```javascript
import NewPage from './pages/NewPage';

function App() {
  return (
    <Routes>
      {/* Existing routes */}
      <Route path="/new-page" element={<NewPage />} />
    </Routes>
  );
}
```

3. **Add navigation link** (in Header or menu):
```javascript
<Link to="/new-page">New Page</Link>
```

### Encrypting PII Fields

When adding new PII fields to customer data:

```python
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from config import Config

class Customer(db.Model):
    # New PII field
    new_pii_field_encrypted = db.Column(
        EncryptedType(db.String(255), Config.ENCRYPTION_KEY, AesEngine, 'multifernet'),
        nullable=True
    )

    # Getter/setter for transparent access
    @property
    def new_pii_field(self):
        return self.new_pii_field_encrypted

    @new_pii_field.setter
    def new_pii_field(self, value):
        self.new_pii_field_encrypted = value
```

---

## TROUBLESHOOTING

### Common Issues

#### Backend Won't Start

**Problem:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
cd backend
source venv/bin/activate  # Make sure venv is activated
pip install -r requirements.txt
```

---

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Start PostgreSQL
brew services start postgresql@14

# Verify it's running
brew services list

# Check connection
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -d happy_place_db
```

---

#### Frontend Issues

**Problem:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**
- Check backend `config.py` has correct `CORS_ORIGINS`
- Verify frontend `.env` has correct `REACT_APP_API_URL`
- Restart both backend and frontend

---

**Problem:** JWT token expired or invalid

**Solution:**
```javascript
// Clear localStorage and re-login
localStorage.removeItem('token');
window.location.href = '/login';
```

---

#### Database Issues

**Problem:** Table doesn't exist

**Solution:**
```bash
cd backend
source venv/bin/activate
python
>>> from app import create_app
>>> from models import db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
```

---

**Problem:** Need to reset database

**Solution:**
```bash
# Drop and recreate database
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -c "DROP DATABASE happy_place_db;"
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -c "CREATE DATABASE happy_place_db;"

# Re-seed
cd backend
source venv/bin/activate
python seed.py
```

### Getting Help

1. **Check Documentation:**
   - `TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
   - `API_REFERENCE.md` - API documentation
   - `DATABASE_SCHEMA.md` - Database structure
   - `SECURITY_GUIDE.md` - Security best practices

2. **Check Logs:**
   - Backend: `backend/logs/app.log`
   - Frontend: Browser DevTools Console (F12)
   - Database: PostgreSQL logs

3. **Review Recent Changes:**
   - Git history: `git log --oneline -10`
   - Recent commits may have introduced issues

---

## CONTRIBUTING GUIDELINES

### Before You Start

1. **Read Documentation:**
   - This CLAUDE.md file (you're here!)
   - `CONTRIBUTING.md` - Contribution guidelines
   - `CODE_REVIEW_PRODUCTION_QUALITY.md` - Code quality standards

2. **Set Up Environment:**
   - Follow Quick Start Guide
   - Verify all services start correctly
   - Run manual tests to ensure baseline works

### Making Changes

1. **Create Feature Branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes:**
   - Follow code style conventions
   - Add comments for complex logic
   - Update documentation if needed

3. **Test Changes:**
   - Test locally on all affected frontends
   - Verify API endpoints work correctly
   - Check for console errors

4. **Commit Changes:**
   ```bash
   git add .
   git commit -m "feat: Add new feature description

   - Detailed change 1
   - Detailed change 2

   🤖 Generated with Claude Code"
   ```

5. **Push and Create PR:**
   ```bash
   git push -u origin feature/your-feature-name
   # Create Pull Request on GitHub
   ```

### Code Review Checklist

**Before Submitting PR:**
- [ ] Code follows project conventions
- [ ] No console errors in browser
- [ ] API endpoints tested with curl/Postman
- [ ] Database changes documented
- [ ] Security implications considered
- [ ] Documentation updated (if needed)
- [ ] No hardcoded credentials or secrets
- [ ] GDPR compliance maintained (for PII handling)

---

## ADDITIONAL RESOURCES

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and setup |
| `CLAUDE.md` | This comprehensive AI assistant guide |
| `API_REFERENCE.md` | Detailed API endpoint documentation |
| `DATABASE_SCHEMA.md` | Complete database schema |
| `SECURITY_GUIDE.md` | Security best practices |
| `TROUBLESHOOTING.md` | Common issues and solutions |
| `CONTRIBUTING.md` | Contribution guidelines |
| `TEST_CREDENTIALS.md` | Test account credentials |
| `PROJECT_DISCOVERY_REPORT.md` | Project analysis and metrics |
| `TECHNOLOGY_STACK_REVIEW.md` | Technology stack details |

### Phase Documentation

| File | Purpose |
|------|---------|
| `.claude/PHASE_1_STATUS.md` | Phase 1 implementation status |
| `.claude/PHASE_1_TESTING.md` | Phase 1 testing checklist |
| `PHASE_1_PROGRESS.md` | Phase 1 progress tracking |

### Session Summaries

- `SESSION_SUMMARY_2025-12-09.md` - December 9 session
- `SESSION_SUMMARY_2025-12-13.md` - December 13 session
- `SESSION_SUMMARY_2025-12-14.md` - December 14 session

---

## PROJECT STATUS & ROADMAP

### Current Status (December 2025)

**Completed Features (~75%):**
- ✅ Customer authentication and registration
- ✅ Employee authentication with role-based access
- ✅ Product catalog with categories
- ✅ Shopping cart and wishlist
- ✅ Order creation and tracking
- ✅ Admin dashboard with metrics
- ✅ Inventory management
- ✅ POS system with shift management
- ✅ Order fulfillment workflow
- ✅ GDPR compliance features
- ✅ Encrypted PII storage
- ✅ Audit logging

**In Progress:**
- 🔄 Phase 1: Order tracking enhancements (current branch: `feature/phase-1-order-tracking`)
- 🔄 Admin portal refinements
- 🔄 Employee portal features

**Upcoming Features:**
- 📋 Payment gateway integration (M-Pesa, Stripe)
- 📋 Email notifications
- 📋 Product reviews and ratings
- 📋 Loyalty program
- 📋 Advanced reporting and analytics
- 📋 Mobile app (React Native)
- 📋 Automated testing suite

### Known Limitations

1. **Cart Badge**: Currently hardcoded to 0 on customer portal header
   - TODO: Connect to CartContext

2. **Wishlist Persistence**: Frontend state only, doesn't persist on refresh
   - TODO: Backend integration

3. **Testing**: Manual testing only
   - TODO: Automated test suite (pytest, Jest, Cypress)

4. **Deployment**: Development setup only
   - TODO: Production deployment configuration

---

## TIPS FOR AI ASSISTANTS

### When Working with This Project

1. **Always Check Current Branch:**
   ```bash
   git branch --show-current
   # Currently: feature/phase-1-order-tracking
   ```

2. **Backend Port is 5001, not 5000:**
   - Flask runs on `http://127.0.0.1:5001`
   - Update code examples accordingly

3. **Multiple Frontends on Different Ports:**
   - Customer: 3000 (default CRA port)
   - Admin: 3001 (set PORT=3001)
   - Employee: 3002 (set PORT=3002)
   - POS: 3003 (configured in package.json)

4. **Database Connection String:**
   - Uses environment variable: `DATABASE_URL`
   - Default: `postgresql://postgres:Alway$ B3l13ving@localhost:5432/happy_place_db`

5. **Password Hashing Varies:**
   - Customers: Werkzeug Scrypt
   - Employees: Bcrypt/Argon2

6. **PII Fields are Encrypted:**
   - Don't try to query encrypted fields directly
   - Use hash fields for lookups (e.g., `email_hash`)

7. **Blueprint URL Prefixes:**
   - Main API: `/api`
   - Auth: `/api/auth`
   - Admin: `/api/admin`
   - Fulfillment: `/api/fulfillment`
   - POS: `/api/pos`

8. **Testing Credentials:**
   - See `TEST_CREDENTIALS.md` for complete list
   - Admin: `admin@happyplace.com` / `AdminPass123!`

9. **Documentation is Your Friend:**
   - Check existing docs before asking questions
   - Update docs when making changes

10. **Security First:**
    - Never commit secrets to git
    - Always use environment variables
    - Follow GDPR compliance patterns
    - Validate all user input

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-22 | Initial CLAUDE.md creation - comprehensive guide for AI assistants |

---

## CONTACT & SUPPORT

**Project Owner:** ml_labs
**Project Path:** `/Users/ml_labs/Documents/Code/cli_projects/happy_place_webstore`
**Repository:** (Configure in deployment)

For issues, questions, or contributions:
1. Check documentation in `documentation/` folder
2. Review session summaries for recent changes
3. Consult troubleshooting guide
4. Create issue or discussion (if repository configured)

---

**Last Updated:** December 22, 2025
**Document Maintained By:** AI Assistants & Development Team
