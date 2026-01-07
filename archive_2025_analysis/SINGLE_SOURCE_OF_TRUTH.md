# Happy Place Webstore — Single Source of Truth (SSOT)

**Repo:** `happy_place_webstore/`

This document is the **single source of truth** for:
- Architecture and runtime topology (what runs where)
- How to run the system locally
- Environment/configuration requirements (without embedding secrets)
- Canonical business rules and where they are enforced
- An “authority map” to deeper documentation

---

## 1) Authority & Precedence (how to resolve conflicts)

When different files disagree, use the following precedence order:

1. **Database schema + migrations + stored procedures**
   - `backend/migrations/*.sql` (especially stored procedure migrations)
   - Reason: These enforce rules at the data layer and are the most authoritative.

2. **Backend service layer + middleware**
   - `backend/services/*.py`, `backend/middleware/*.py`, `backend/routes/*.py`
   - Reason: Enforces application-level business rules and access control.

3. **Backend configuration**
   - `backend/config.py`, runtime env vars

4. **Frontends (portals)**
   - UI constraints/validation can exist but must not override backend/DB rules.

5. **Documentation**
   - `README.md`, `QUICKSTART.md`, `SYSTEM_STATUS.md`, etc.

If a conflict exists between DB rules and backend/docs, the SSOT rule should reflect the **DB-enforced behavior**, and the mismatch should be tracked under **Known Inconsistencies**.

---

## 2) System Architecture (what this repo contains)

### 2.1 Components

- **Backend API**: Flask REST API
  - Folder: `backend/`
  - Entrypoint: `backend/app.py`
  - Production server config: `backend/gunicorn_config.py`

- **Customer Portal**: React SPA
  - Folder: `frontend-customer/`

- **Admin Portal**: React SPA
  - Folder: `frontend-admin/`

- **Employee Portal**: React SPA
  - Folder: `frontend-employee/`

- **POS App**: React PWA (offline-capable)
  - Folder: `pos-app/`

- **Database**: PostgreSQL
  - Migrations: `backend/migrations/`

### 2.2 Ports (local development)

- **Backend API**: `http://localhost:5001`
  - Verified in: `backend/app.py`, `backend/gunicorn_config.py`

- **Customer Portal**: CRA default `http://localhost:3000`

- **Admin Portal**:
  - CRA default `3000` unless you set `PORT=3001`

- **Employee Portal**:
  - CRA default `3000` unless you set `PORT=3002`

- **POS App**: `http://127.0.0.1:3003`
  - Verified in: `pos-app/package.json` start script

- **PostgreSQL**: `localhost:5432`

---

## 3) How to Run Locally (canonical)

### 3.1 Backend (Terminal 1)

- **Virtualenv**: run backend inside the project virtual environment
  - Expected activation: `source backend/venv/bin/activate`

- **Environment variables**
  - Use `backend/.env` (not committed) for `DATABASE_URL` and secrets.
  - Do **not** hardcode secrets in code or docs.

- **Start backend**
  - Run: `python backend/app.py`
  - Health check: `GET http://localhost:5001/health`

### 3.2 Customer Portal (Terminal 2)

- Folder: `frontend-customer/`
- Run: `npm start`
- URL: `http://localhost:3000`

### 3.3 Admin Portal (Terminal 3)

- Folder: `frontend-admin/`
- Run:
  - `export PORT=3001 && npm start`

### 3.4 Employee Portal (Terminal 4)

- Folder: `frontend-employee/`
- Run:
  - `export PORT=3002 && npm start`

### 3.5 POS App (Terminal 5)

- Folder: `pos-app/`
- Run: `npm start`
- URL: `http://127.0.0.1:3003`

---

## 4) Environment & Configuration (canonical)

### 4.1 Backend configuration

- Primary config file: `backend/config.py`
- DB config comes from env var `DATABASE_URL`.
- CORS is configured via `CORS_ORIGINS` (defaults include `localhost:3000` and `127.0.0.1:3003`).

### 4.2 Required environment variables (development)

Minimum required for typical local use:
- `DATABASE_URL`
- `JWT_SECRET_KEY`

Required for encryption features:
- `ENCRYPTION_KEY_PRIMARY`
- `ENCRYPTION_KEY_SECONDARY`

Optional integrations:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `REDIS_URL` (rate limit storage)

### 4.3 Production requirements

`Config.validate_secrets()` enforces production-only requirements (see `backend/config.py`).

---

## 5) Identity, Roles, and Access Control (canonical)

### 5.1 User types

- **Customer**
- **Employee**

The backend enforces user type via JWT claim `user_type`.

### 5.2 Employee roles

Roles enforced in middleware decorators (`backend/middleware/auth.py`):
- `admin`
- `manager`
- `packer`
- `shipper`
- `cashier`
- `staff`

Authorization rules:
- **Admin-only**: `admin_required`
- **Manager or Admin**: `manager_required`
- **Packer/Manager/Admin**: `packer_required`
- **Shipper/Manager/Admin**: `shipper_required`
- **Employee active** and **Customer active** are required for access.

---

## 6) Canonical Business Rules (single source of truth)

This section lists the **official rules** and where they are enforced.

### 6.1 Orders

- **Create order requires a non-empty cart**
  - Enforced in: `backend/routes/orders.py`

- **Shipping address validation**
  - Required: `street`, `city`, `state`, `zip`, `phone`
  - Phone must start with `+254` or `0`
  - Enforced in: `backend/routes/orders.py`

- **Allowed payment methods at order creation**
  - Allowed values: `cod`, `mpesa`
  - Current behavior: `mpesa` is blocked as “coming soon” (returns HTTP 501)
  - Enforced in: `backend/routes/orders.py`

- **Order status timestamps**
  - `shipped` sets `shipped_at`
  - `delivered` or `completed` sets `delivered_at`
  - Enforced in: `backend/services/order_management_service.py`

### 6.2 Payments

- **Payment completion is atomic**
  - Completing payment:
    - updates payment status
    - updates order status
    - converts reserved inventory into deducted inventory
    - logs audit
  - Enforced in DB: `sp_process_payment_secure` (called by `backend/services/payment_service.py`)

- **COD delivery completion**
  - Only allowed if payment method is `cod`
  - Enforced in: `backend/services/payment_service.py`

- **M-Pesa callback processing**
  - Only allowed if payment method is `mpesa`
  - Enforced in: `backend/services/payment_service.py`

### 6.3 Inventory

- Inventory movements are enforced via stored procedures:
  - Deduct inventory: `sp_deduct_inventory`
  - Add inventory: `sp_add_inventory`
  - Enforced in: `backend/services/inventory_service.py`

### 6.4 Returns (authoritative)

**Return processing is enforced by DB stored procedure**:
- Procedure: `sp_process_return_secure`
- Source: `backend/migrations/001_priority1_stored_procedures_final_fix.sql`

Canonical rules enforced by DB:
- **Return window**: **30 days**
- **Cannot return** orders with status `cancelled` or `returned`
- **Quantity validation**: cannot return more than purchased
- **Restocking fee**: **15%** applied for item condition `used` or `damaged`
- **Inventory restoration**: if approved and condition is `new`, inventory increases

### 6.5 Promotions

Canonical promotion rules are defined in models + service layer:
- Time-bound validity and active flag
- Minimum order amount enforcement (if configured)
- Usage limits (global and per-customer)
- Discount types: percentage, fixed amount, free shipping (model supports)

Enforced in:
- `backend/models/extended_models.py` (`Promotion.is_valid`, `Promotion.can_use`, `Promotion.calculate_discount`)
- `backend/services/promotion_service.py`

### 6.6 GDPR / Privacy

Authoritative GDPR procedures:
- Export: `sp_gdpr_export_customer_data`
- Anonymize: `sp_gdpr_anonymize_customer`
- Delete: `sp_gdpr_delete_customer`

Canonical anonymization rules (DB-enforced):
- Cannot anonymize customer with **outstanding orders** (`pending`, `processing`, `shipped`)
- Deletes addresses, clears carts/wishlists
- Anonymizes order addresses but preserves order records

Source:
- `backend/migrations/002_priority2_gdpr_procedures.sql`
- Called by: `backend/services/gdpr_service.py`

### 6.7 POS (Shifts)

POS shifts are feature-gated by schema:
- If shifts table is missing, operations return an error directing you to apply migration `005_pos_enhancements.sql`.
- One open shift per employee.
- Shift number format: `YYYYMMDD-LOC{location_id}-EMP{employee_id}-{sequence}`.

Enforced in:
- `backend/services/pos_service.py`

---

## 7) System Settings (DB is authoritative)

The `system_settings` table is seeded in:
- `backend/migrations/008_admin_dashboard.sql`

Examples seeded by migration:
- `return_window_days = 30`
- `restocking_fee = 10`
- `low_stock_threshold = 10`

**Important:** some backend defaults in `backend/services/settings_service.py` do not match the seeded DB settings. See Known Inconsistencies.

---

## 8) Known Inconsistencies (must be reconciled)

These conflicts exist today; SSOT chooses DB-enforced behavior as canonical.

1. **Return window**
   - DB stored procedure: **30 days** (`sp_process_return_secure`)
   - DB seeded setting: **30 days** (`system_settings.return_window_days`)
   - Backend default setting: **2 days** (`SettingsService.DEFAULT_SETTINGS['return_window_days']`)
   - Canonical: **30 days**

2. **Restocking fee**
   - DB stored procedure: **15%** for `used`/`damaged` items
   - DB seeded setting: **10%** (`system_settings.restocking_fee`)
   - Backend default setting: **10%** (`SettingsService.DEFAULT_SETTINGS['restocking_fee_percentage']`)
   - Canonical: **15% for used/damaged items** (DB-enforced). The meaning of the `restocking_fee` setting should be clarified or the procedure should be updated to use it.

3. **Backend port in older docs**
   - Some docs mention port `5000`; backend is currently on **5001**.

---

## 9) Operational Status (where to look)

- Current runtime health and known issues are tracked in:
  - `SYSTEM_STATUS.md`

---

## 10) Authority Map (deep docs)

- **Project overview**: `README.md`
- **Quick start**: `QUICKSTART.md`
- **API reference**: `API_REFERENCE.md`
- **Database schema**: `DATABASE_SCHEMA.md`
- **Security**: `SECURITY_GUIDE.md`
- **Tech stack review**: `TECHNOLOGY_STACK_REVIEW.md`
- **Current state / incidents**: `SYSTEM_STATUS.md`
- **Test accounts**: `TEST_CREDENTIALS.md`
- **Project discovery report**: `PROJECT_DISCOVERY_REPORT.md`
- **Feature completeness / priorities**: `analysis/FEATURE_COMPLETENESS.md`, `analysis/P0_CRITICAL_ISSUES.md`, `analysis/P1_HIGH_PRIORITY.md`, `analysis/P2_MEDIUM_PRIORITY.md`

---

## 11) Update Policy (how to keep SSOT true)

When you change:
- a business rule
- a port
- an env var
- a migration/procedure

Update:
- This file (`SINGLE_SOURCE_OF_TRUTH.md`) first
- The relevant deep-doc in the Authority Map

This prevents future drift and keeps this folder maintainable.
