# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI Assistant Instructions


## 🚨 MANDATORY PERSONA SELECTION

**CRITICAL: You MUST adopt one of the specialized personas before proceeding with any work.**

**BEFORE DOING ANYTHING ELSE**, you must read and adopt one of these personas:

1. **Developer Agent** - Read `.promptx/personas/agent-developer.md` - For coding, debugging, and implementation tasks
2. **Code Reviewer Agent** - Read `.promptx/personas/agent-code-reviewer.md` - For reviewing code changes and quality assurance
3. **Rebaser Agent** - Read `.promptx/personas/agent-rebaser.md` - For cleaning git history and rebasing changes
4. **Merger Agent** - Read `.promptx/personas/agent-merger.md` - For merging code across branches
5. **Multiplan Manager Agent** - Read `.promptx/personas/agent-multiplan-manager.md` - For orchestrating parallel work and creating plans

**DO NOT PROCEED WITHOUT SELECTING A PERSONA.** Each persona has specific rules, workflows, and tools that you MUST follow exactly.



## How to Choose Your Persona

- **Asked to write code, fix bugs, or implement features?** → Use Developer Agent
- **Asked to review code changes?** → Use Code Reviewer Agent  
- **Asked to clean git history or rebase changes?** → Use Rebaser Agent
- **Asked to merge branches or consolidate work?** → Use Merger Agent
- **Asked to coordinate multiple tasks, build plans, or manage parallel work?** → Use Multiplan Manager Agent

## Project Context

[CUSTOMIZE THIS SECTION FOR YOUR PROJECT]

This project uses:
- **Language/Framework**: [Add your stack here]
- **Build Tool**: [Add your build commands]
- **Testing**: [Add your test commands]  
- **Architecture**: [Describe your project structure]

## Core Principles (All Personas)

1. **READ FIRST**: Always read at least 1500 lines to understand context fully
2. **DELETE MORE THAN YOU ADD**: Complexity compounds into disasters
3. **FOLLOW EXISTING PATTERNS**: Don't invent new approaches
4. **BUILD AND TEST**: Run your build and test commands after changes
5. **COMMIT FREQUENTLY**: Every 5-10 minutes for meaningful progress

## File Structure Reference

[CUSTOMIZE THIS SECTION FOR YOUR PROJECT]

```
./
├── package.json          # [or your dependency file]
├── src/                  # [your source directory]
│   ├── [your modules]
│   └── [your files]
├── test/                 # [your test directory]
├── .promptx/             # Agent personas (created by promptx init)
│   └── personas/
└── CLAUDE.md            # This file (after merging)
```

## Common Commands (All Personas)

[CUSTOMIZE THIS SECTION FOR YOUR PROJECT]

```bash
# Build project
[your build command]

# Run tests  
[your test command]

# Lint code
[your lint command]

# Deploy locally
[your deploy command]
```

## CRITICAL REMINDER

**You CANNOT proceed without adopting a persona.** Each persona has:
- Specific workflows and rules
- Required tools and commands  
- Success criteria and verification steps
- Commit and progress requirements

**Choose your persona now and follow its instructions exactly.**

---


# Project Overview

Happy Place Boutique is a full-stack e-commerce platform for women's and maternity clothing with both online shopping and physical store Point of Sale (POS) capabilities. The system uses Flask (Python) for the backend, React 18 for the frontend, and PostgreSQL with field-level encryption for customer data.

**Key Characteristics:**
- **Dual-channel retail**: Online store + physical POS system with unified inventory
- **GDPR compliant**: Field-level encryption using Fernet (MultiFernet) for customer PII
- **Service-oriented architecture**: Business logic isolated in service layer
- **JWT authentication**: Separate auth flows for customers and employees (admin, manager, cashier)
- **Production-ready**: Currently deployed with 11 completed feature phases

## Development Commands

### Backend Development

```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (port 5001)
python app.py

# Database operations
python seed.py                           # Seed database with sample data
python scripts/migrate_database.py       # Run migrations
python scripts/seed_extended_data.py     # Seed extended features

# Testing specific endpoints
./test_admin_dashboard.sh                # Test admin dashboard endpoints
./test_pos_endpoints.sh                  # Test POS system endpoints
./test_order_creation.sh                 # Test order creation flow
```

### Frontend Development

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server (port 3000)
npm start

# Build for production
npm run build
```

### Database Management

```bash
# PostgreSQL commands (from backend directory)
# Connect to database
PGPASSWORD='Alway$ B3l13ving' psql -U postgres -d happy_place_db

# Create database
createdb happy_place_db

# Backup database
PGPASSWORD='Alway$ B3l13ving' pg_dump -U postgres happy_place_db > backup.sql

# Restore database
PGPASSWORD='Alway$ B3l13ving' psql -U postgres happy_place_db < backup.sql
```

## High-Level Architecture

### Three-Layer Backend Architecture

The backend follows a strict service-oriented architecture:

1. **Routes Layer** (`backend/routes/`)
   - Handles HTTP requests/responses
   - JWT authentication/authorization decorators
   - Request validation
   - Delegates ALL business logic to services
   - **Never** contains database queries or business rules

2. **Services Layer** (`backend/services/`)
   - Contains ALL business logic
   - Database transactions and queries
   - Encryption/decryption operations
   - Business rule enforcement
   - Returns data to routes for JSON serialization

3. **Models Layer** (`backend/models/`)
   - SQLAlchemy ORM models (29 tables)
   - Encrypted field types (Fernet)
   - Database relationships
   - Property methods for computed values

**Critical Pattern**: Routes MUST call services for any database operation. Services own the session management.

### Backend Module Organization

```
backend/
├── app.py                      # Flask app initialization, blueprint registration
├── config.py                   # Configuration (JWT, database, encryption keys)
├── extensions.py               # Shared Flask extensions
│
├── models/
│   ├── __init__.py            # Exports all 29 models
│   ├── database_models.py     # Core 22 tables (Customer, Order, Payment, etc.)
│   ├── extended_models.py     # 7 extended tables (ProductVariant, Return, etc.)
│   └── encrypted_types.py     # Custom SQLAlchemy types for Fernet encryption
│
├── routes/
│   ├── __init__.py            # Blueprint exports
│   ├── auth_routes.py         # /api/auth/* (customer/employee login, registration)
│   ├── admin_routes.py        # /api/admin/* (inventory, orders, customers, settings)
│   ├── pos.py                 # /api/pos/* (POS transactions, shifts)
│   ├── kiosk.py               # /api/kiosk/* (self-checkout kiosk)
│   ├── products.py            # /api/products/* (catalog, search, filter)
│   ├── cart.py                # /api/cart/* (shopping cart operations)
│   ├── orders.py              # /api/orders/* (customer orders)
│   ├── returns_api.py         # /api/returns/* (return requests)
│   └── ...                    # Other route modules
│
└── services/
    ├── auth_service.py                    # Login, registration, token management
    ├── order_management_service.py        # Admin order operations
    ├── customer_management_service.py     # Admin customer operations
    ├── inventory_management_service.py    # Admin inventory operations
    ├── employee_management_service.py     # Admin employee operations
    ├── pos_service.py                     # POS transactions, shifts, receipts
    ├── product_service.py                 # Product catalog, search, variants
    ├── order_service.py                   # Customer order creation
    ├── payment_service.py                 # Payment processing
    ├── return_service.py                  # Return request processing
    ├── encryption.py                      # Fernet encryption/decryption
    ├── gdpr_service.py                    # GDPR compliance (anonymization, export)
    ├── report_service.py                  # Sales reports, analytics
    └── ...                                # Other service modules
```

### Frontend Architecture

React application using Context API for state management:

```
frontend/src/
├── App.js                     # Main app with routing
├── index.js                   # Entry point
│
├── context/
│   ├── AuthContext.js         # Authentication state (customers + employees)
│   ├── CartContext.js         # Shopping cart state
│   └── WishlistContext.js     # Wishlist state
│
├── pages/
│   ├── Login.js               # Customer login
│   ├── EmployeeLogin.js       # Employee login
│   ├── Products.js            # Product catalog
│   ├── ProductDetail.js       # Product detail page
│   ├── Cart.js                # Shopping cart
│   ├── Checkout.js            # Checkout flow
│   ├── OrderHistory.js        # Customer order history
│   ├── POS/                   # POS system pages
│   │   ├── POSLogin.js
│   │   ├── POSDashboard.js
│   │   ├── POSNewSale.js
│   │   └── POSCloseShift.js
│   └── admin/                 # Admin dashboard pages
│       ├── AdminDashboard.js
│       ├── AdminInventory.js
│       ├── AdminOrders.js
│       ├── AdminCustomers.js
│       └── ...
│
├── components/
│   ├── Header.js              # Site header
│   ├── ProductCard.js         # Product display card
│   ├── SizeGuide.js           # International size conversion
│   └── admin/                 # Admin UI components
│       ├── DataTable.js
│       ├── StatusBadge.js
│       └── ...
│
└── services/
    ├── api.js                 # Main API client (customer endpoints)
    └── adminAPI.js            # Admin API client (admin endpoints)
```

## Critical Database Concepts

### Order Model Attribute Names

**IMPORTANT**: The Order model uses specific attribute names that differ from common conventions:

```python
# ✅ CORRECT attribute names:
order.total              # NOT order.total_amount
order.subtotal           # NOT order.subtotal_amount
order.tax                # NOT order.tax_amount
order.shipping_cost      # NOT order.shipping_amount

# Payment accessed via relationship:
order.payment.payment_method     # NOT order.payment_method
order.payment.status             # NOT order.payment_status

# OrderItem attributes:
orderitem.unit_price     # NOT orderitem.price
orderitem.total_price    # NOT orderitem.amount
```

**Common mistake**: Using `order.total_amount` will cause `AttributeError`. Always use `order.total`.

### Encrypted Fields Pattern

Customer PII is encrypted using Fernet (MultiFernet). The pattern uses dual storage for searchable fields:

```python
# Customer model example:
customer.email_hash          # SHA-256 hash for searching (indexed)
customer.email_encrypted     # Fernet encrypted actual email

# To search by email:
email_hash = hashlib.sha256(email.encode()).hexdigest()
customer = Customer.query.filter_by(email_hash=email_hash).first()

# To decrypt email:
actual_email = customer.email_encrypted  # Auto-decrypted by SQLAlchemy type
```

**Encrypted tables**: Customer, CustomerAddress, Order (addresses), Payment (M-Pesa details)

### Service Layer Session Management

Services manage their own database sessions. Routes should NEVER create sessions:

```python
# ✅ CORRECT pattern in routes:
@admin_bp.route('/orders', methods=['GET'])
@jwt_required()
@admin_required
def get_orders(current_employee):
    # Call service - it handles session
    result = get_services()['order_management'].get_order_list(
        page=page, per_page=per_page, status=status
    )
    return jsonify(result), 200

# ❌ WRONG - don't create sessions in routes:
def get_orders(current_employee):
    orders = Order.query.all()  # NO! This bypasses service layer
```

### Inventory: Single Quantity Model

Inventory uses a single `quantity` field for both online and physical store (per user requirement):

```python
inventory.quantity            # Total stock (online + store combined)
inventory.reserved_quantity   # Currently reserved in carts/pending orders
inventory.available_quantity  # Property: quantity - reserved_quantity
```

**Why**: User wanted clarity when stock is low, avoiding confusion from split quantities.

## Authentication Flows

### Customer Authentication
- Endpoint: `POST /api/auth/customer/login`
- JWT token with claims: `sub` (customer_id), `user_type: "customer"`
- Token expiry: 8 hours (configurable in config.py)

### Employee Authentication
- Endpoint: `POST /api/auth/employee/login`
- JWT token with claims: `sub` (employee_id), `user_type: "employee"`, `role` (admin/manager/cashier)
- Token expiry: 8 hours (configurable in config.py)
- PIN login available: `POST /api/auth/employee/pin-login` (4-digit PIN for POS)

### Protected Route Decorators

```python
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

# Basic JWT protection
@jwt_required()
def protected_route():
    user_id = get_jwt_identity()  # Returns 'sub' claim
    claims = get_jwt()
    user_type = claims.get('user_type')  # 'customer' or 'employee'

# Admin-only protection (in admin_routes.py)
@admin_required  # Custom decorator - checks role in JWT
def admin_only_route(current_employee):
    # current_employee is injected by decorator
    pass
```

## Return Policy Business Rules

The system enforces strict return policies in code:

1. **Return Window**: 2 days from delivery date (checked in `return_service.py`)
2. **Restocking Fee**: 10% on regular-priced items
3. **FINAL SALE Items** (no returns, no exchanges):
   - Clearance items (`product.is_clearance = True`)
   - Sale items (`product.sale_price < product.price`)

```python
# Implementation in models/database_models.py:
@property
def can_be_returned(self):
    if self.is_clearance:
        return False
    if self.is_on_sale:
        return False
    return True
```

## Shipping Cost Calculation

Shipping costs vary by location (Kenya-specific):

```python
# Nairobi: Free shipping (always)
if order.is_nairobi:
    shipping_cost = 0

# Outside Nairobi: Base fee + weight-based
else:
    shipping_cost = 300 + (total_weight_kg * 50)
    # Example: 2kg order = KSh 300 + (2 × KSh 50) = KSh 400
```

## Common Pitfalls & Solutions

### 1. Order Attribute Errors
**Problem**: `AttributeError: 'Order' object has no attribute 'total_amount'`
**Solution**: Use `order.total`, `order.subtotal`, `order.tax` (see Order Model Attribute Names above)

### 2. Variant ID vs Product ID
**Problem**: Stock adjustment fails with "undefined variant_id"
**Solution**: Inventory is linked to `product_variants`, not `products`. Use `variant_id` in cart, orders, and inventory operations.

### 3. Service Import Circular Dependencies
**Problem**: Circular import errors between services
**Solution**: Use the service registry pattern in `routes/__init__.py`:
```python
from services.order_service import OrderService
# Use get_services() to access services at runtime
```

### 4. Missing JWT Claims
**Problem**: Employee routes fail because JWT lacks `role` claim
**Solution**: Ensure employee login generates token with all required claims:
```python
access_token = create_access_token(
    identity=str(employee.id),
    additional_claims={
        'user_type': 'employee',
        'role': employee.role  # REQUIRED for @admin_required
    }
)
```

### 5. CORS Preflight 404 Errors
**Problem**: OPTIONS requests fail with 404 before actual request
**Solution**: Ensure endpoint exists in routes AND blueprint is registered in `app.py`

## Testing Patterns

### Manual API Testing

Use the provided shell scripts for common test scenarios:

```bash
# Test admin dashboard endpoints
./test_admin_dashboard.sh

# Test POS workflow
./test_pos_endpoints.sh

# Test order creation flow
./test_order_creation.sh
```

### Getting Admin Token for Testing

```bash
# Login as admin
curl -X POST 'http://127.0.0.1:5001/api/auth/employee/login' \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@happyplace.com","password":"admin123"}' \
  -s | python -m json.tool

# Extract token and use in subsequent requests
TOKEN="<access_token_from_response>"

curl -X GET 'http://127.0.0.1:5001/api/admin/inventory' \
  -H "Authorization: Bearer $TOKEN" \
  -s | python -m json.tool
```

## Key Files to Reference

- `DATABASE_SCHEMA_COMPLETE_V3.2.md` - Complete 29-table database schema with encryption details
- `API_SPECIFICATION_V3.2.md` - Full API endpoint documentation
- `PROJECT_MASTER_DOCUMENTATION.md` - Comprehensive project documentation
- `backend/models/__init__.py` - All model exports and relationships
- `backend/services/__init__.py` - Service layer exports
- `backend/routes/__init__.py` - Blueprint registration and service registry

## Environment Variables

Required in `backend/.env`:

```bash
# Flask
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/happy_place_db

# JWT
JWT_SECRET_KEY=<your-secret-key>

# Encryption Keys (MultiFernet)
CUSTOMER_ENCRYPTION_KEYS=-ubRgJ-hZY5IU6dVWdqu0_rrsPOKUdCEad1JYxUJhhg=
ADDRESS_ENCRYPTION_KEYS=X38Ljn4bg3ZSnR44NVzvaZCkHls35Dxpq4SyaOox8-o=
PAYMENT_ENCRYPTION_KEYS=BdVB1XRZ2zV9WxSIp5oOrq5sYU1gydxoZiWjMhHXeWo=

# Google OAuth (optional)
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
```

## Port Configuration

- **Backend**: `http://localhost:5001` (changed from 5000 to avoid macOS AirPlay conflict)
- **Frontend**: `http://localhost:3000`
- **Database**: `localhost:5432` (PostgreSQL default)

## Recent Changes & Migrations

The project has undergone 11 major development phases. Recent significant changes:

1. **Phase 11** (Dec 2025): Admin dashboard with comprehensive management features
2. **Phase 10** (Nov 2025): Authentication overhaul with JWT improvements
3. **Phase 9** (Nov 2025): Complete POS system with barcode scanning, receipt printing

If encountering unexpected behavior, check:
- `PHASE_11_COMPLETION_REPORT.md` - Latest feature additions
- `backend/migrations/` - Database migration scripts
- Git commit history for recent structural changes

