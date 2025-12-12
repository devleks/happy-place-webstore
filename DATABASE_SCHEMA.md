# Database Schema - Happy Place Boutique

Complete PostgreSQL database schema with 22 tables supporting e-commerce, POS, GDPR compliance, and audit logging.

**Database:** PostgreSQL 14+  
**ORM:** SQLAlchemy  
**Encryption:** MultiFernet (PII fields)

---

## Table of Contents

1. [Overview](#overview)
2. [Customer Management](#customer-management)
3. [Employee Management](#employee-management)
4. [Product Catalog](#product-catalog)
5. [Shopping Experience](#shopping-experience)
6. [Orders & Payments](#orders--payments)
7. [POS System](#pos-system)
8. [Fulfillment](#fulfillment)
9. [GDPR Compliance](#gdpr-compliance)
10. [Audit & Logging](#audit--logging)
11. [Relationships](#relationships)
12. [Indexes](#indexes)

---

## Overview

### Architecture Features

- **GDPR Compliant:** Encrypted PII, consent tracking, right to erasure
- **Security:** MultiFernet encryption, Argon2 password hashing, audit logging
- **Multi-Channel:** Online store + Physical POS system
- **Scalable:** Indexed queries, optimized relationships
- **Audit Trail:** Complete activity logging for compliance

### Table Summary

| Category | Tables | Count |
|----------|--------|-------|
| Customer Management | customers, customer_addresses | 2 |
| Employee Management | employees | 1 |
| Product Catalog | categories, products, product_images, inventory | 4 |
| Shopping | carts, cart_items, wishlists, wishlist_items | 4 |
| Orders | orders, order_items, payments, reviews | 4 |
| POS | pos_transactions, pos_transaction_items, store_locations | 3 |
| GDPR | gdpr_data_requests, gdpr_consent_log | 2 |
| Audit | data_access_log, activity_logs | 2 |
| **Total** | | **22** |

---

## Customer Management

### customers

Customer accounts for online shoppers with GDPR compliance.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Customer ID |
| email_hash | VARCHAR(64) | UNIQUE, NOT NULL, INDEXED | SHA-256 hash for login lookup |
| email_encrypted | ENCRYPTED_STRING | NOT NULL | Encrypted email (MultiFernet) |
| first_name_encrypted | ENCRYPTED_STRING | NOT NULL | Encrypted first name |
| last_name_encrypted | ENCRYPTED_STRING | NOT NULL | Encrypted last name |
| phone_encrypted | ENCRYPTED_STRING | | Encrypted phone number |
| password_hash | VARCHAR(255) | NOT NULL | Argon2 password hash |
| gdpr_consent | BOOLEAN | NOT NULL, DEFAULT FALSE | GDPR consent given |
| marketing_consent | BOOLEAN | NOT NULL, DEFAULT FALSE | Marketing consent |
| data_retention_date | DATE | | Auto-anonymization date |
| anonymized | BOOLEAN | NOT NULL, DEFAULT FALSE | Account anonymized flag |
| anonymized_at | DATETIME | | Anonymization timestamp |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active status |
| email_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| last_login | DATETIME | | Last login timestamp |
| created_at | DATETIME | NOT NULL | Account creation date |
| updated_at | DATETIME | | Last update timestamp |

**Relationships:**
- `addresses` → customer_addresses (1:N)
- `orders` → orders (1:N)
- `reviews` → reviews (1:N)
- `cart` → carts (1:1)
- `wishlist` → wishlists (1:1)

**Indexes:**
- `email_hash` (UNIQUE)
- `created_at`
- `anonymized`

---

### customer_addresses

Shipping and billing addresses for customers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Address ID |
| customer_id | INTEGER | FOREIGN KEY → customers.id | Owner customer |
| address_type | VARCHAR(20) | NOT NULL | 'shipping' or 'billing' |
| full_name_encrypted | ENCRYPTED_STRING | NOT NULL | Recipient name |
| phone_encrypted | ENCRYPTED_STRING | NOT NULL | Contact phone |
| address_line1_encrypted | ENCRYPTED_STRING | NOT NULL | Street address |
| address_line2_encrypted | ENCRYPTED_STRING | | Apartment/suite |
| city_encrypted | ENCRYPTED_STRING | NOT NULL | City |
| state_encrypted | ENCRYPTED_STRING | | State/province |
| postal_code_encrypted | ENCRYPTED_STRING | NOT NULL | Postal code |
| country | VARCHAR(2) | NOT NULL | ISO country code |
| is_default | BOOLEAN | DEFAULT FALSE | Default address flag |
| created_at | DATETIME | NOT NULL | Creation timestamp |

**Indexes:**
- `customer_id`
- `is_default`

---

## Employee Management

### employees

Staff accounts for POS, fulfillment, and admin access.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Employee ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Employee email |
| password_hash | VARCHAR(255) | NOT NULL | Argon2 password hash |
| first_name | VARCHAR(100) | NOT NULL | First name |
| last_name | VARCHAR(100) | NOT NULL | Last name |
| role | VARCHAR(50) | NOT NULL | Role (admin, manager, cashier, packer, shipper) |
| pin_hash | VARCHAR(255) | | Optional PIN for quick login |
| two_factor_enabled | BOOLEAN | DEFAULT FALSE | 2FA enabled |
| two_factor_secret | VARCHAR(32) | | TOTP secret |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active |
| last_login | DATETIME | | Last login timestamp |
| created_at | DATETIME | NOT NULL | Account creation |
| updated_at | DATETIME | | Last update |

**Roles:**
- `admin` - Full system access
- `manager` - Store management, reports
- `cashier` - POS transactions
- `packer` - Order fulfillment
- `shipper` - Shipping management

**Indexes:**
- `email` (UNIQUE)
- `role`
- `is_active`

---

## Product Catalog

### categories

Product categories (Women's, Maternity, etc.).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Category ID |
| name | VARCHAR(100) | NOT NULL | Category name |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly slug |
| description | TEXT | | Category description |
| parent_id | INTEGER | FOREIGN KEY → categories.id | Parent category (for subcategories) |
| display_order | INTEGER | DEFAULT 0 | Sort order |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Visibility flag |
| created_at | DATETIME | NOT NULL | Creation timestamp |

**Indexes:**
- `slug` (UNIQUE)
- `parent_id`
- `is_active`

---

### products

Product master data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Product ID |
| category_id | INTEGER | FOREIGN KEY → categories.id | Product category |
| name | VARCHAR(200) | NOT NULL | Product name |
| slug | VARCHAR(200) | UNIQUE, NOT NULL | URL slug |
| description | TEXT | | Product description |
| base_price | DECIMAL(10,2) | NOT NULL | Base price (KES) |
| sku_prefix | VARCHAR(50) | | SKU prefix |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Product active |
| featured | BOOLEAN | DEFAULT FALSE | Featured product |
| created_at | DATETIME | NOT NULL | Creation date |
| updated_at | DATETIME | | Last update |

**Indexes:**
- `slug` (UNIQUE)
- `category_id`
- `is_active`
- `featured`

---

### product_images

Product photos.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Image ID |
| product_id | INTEGER | FOREIGN KEY → products.id | Product |
| image_url | VARCHAR(500) | NOT NULL | Image path/URL |
| alt_text | VARCHAR(200) | | Alt text for accessibility |
| display_order | INTEGER | DEFAULT 0 | Sort order |
| is_primary | BOOLEAN | DEFAULT FALSE | Primary image flag |
| created_at | DATETIME | NOT NULL | Upload timestamp |

**Indexes:**
- `product_id`
- `is_primary`

---

### inventory

Stock tracking with variants (size, color).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Variant ID |
| product_id | INTEGER | FOREIGN KEY → products.id | Product |
| size | VARCHAR(20) | NOT NULL | Size (XS, S, M, L, XL, etc.) |
| color | VARCHAR(50) | | Color name |
| sku | VARCHAR(100) | UNIQUE, NOT NULL | Stock keeping unit |
| barcode | VARCHAR(100) | UNIQUE | Barcode for scanning |
| price | DECIMAL(10,2) | NOT NULL | Variant price |
| stock_quantity | INTEGER | NOT NULL, DEFAULT 0 | Available stock |
| reserved_quantity | INTEGER | DEFAULT 0 | Reserved (in carts) |
| reorder_level | INTEGER | DEFAULT 5 | Low stock threshold |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Variant active |
| created_at | DATETIME | NOT NULL | Creation date |
| updated_at | DATETIME | | Last stock update |

**Indexes:**
- `product_id`
- `sku` (UNIQUE)
- `barcode` (UNIQUE)
- `stock_quantity`

---

## Shopping Experience

### carts

Customer shopping carts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Cart ID |
| customer_id | INTEGER | FOREIGN KEY → customers.id, UNIQUE | Cart owner |
| created_at | DATETIME | NOT NULL | Cart creation |
| updated_at | DATETIME | | Last update |

---

### cart_items

Items in shopping carts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Cart item ID |
| cart_id | INTEGER | FOREIGN KEY → carts.id | Parent cart |
| variant_id | INTEGER | FOREIGN KEY → inventory.id | Product variant |
| quantity | INTEGER | NOT NULL | Item quantity |
| added_at | DATETIME | NOT NULL | Added timestamp |

**Indexes:**
- `cart_id`
- `variant_id`

---

### wishlists

Customer wishlists.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Wishlist ID |
| customer_id | INTEGER | FOREIGN KEY → customers.id, UNIQUE | Owner |
| created_at | DATETIME | NOT NULL | Creation date |

---

### wishlist_items

Items in wishlists.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Wishlist item ID |
| wishlist_id | INTEGER | FOREIGN KEY → wishlists.id | Parent wishlist |
| product_id | INTEGER | FOREIGN KEY → products.id | Product |
| added_at | DATETIME | NOT NULL | Added timestamp |

---

## Orders & Payments

### orders

Customer orders.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Order ID |
| customer_id | INTEGER | FOREIGN KEY → customers.id | Customer |
| order_number | VARCHAR(50) | UNIQUE, NOT NULL | Order number (ORD-YYYY-NNN) |
| status | VARCHAR(50) | NOT NULL | Order status |
| subtotal | DECIMAL(10,2) | NOT NULL | Items subtotal |
| shipping_cost | DECIMAL(10,2) | DEFAULT 0 | Shipping fee |
| tax | DECIMAL(10,2) | DEFAULT 0 | Tax amount |
| total_amount | DECIMAL(10,2) | NOT NULL | Total order amount |
| shipping_address_id | INTEGER | FOREIGN KEY → customer_addresses.id | Shipping address |
| billing_address_id | INTEGER | FOREIGN KEY → customer_addresses.id | Billing address |
| payment_method | VARCHAR(50) | | Payment method |
| payment_status | VARCHAR(50) | DEFAULT 'pending' | Payment status |
| notes | TEXT | | Customer notes |
| tracking_number | VARCHAR(100) | | Shipment tracking |
| carrier | VARCHAR(100) | | Shipping carrier |
| estimated_delivery | DATE | | Estimated delivery date |
| packer_id | INTEGER | FOREIGN KEY → employees.id | Assigned packer |
| shipper_id | INTEGER | FOREIGN KEY → employees.id | Assigned shipper |
| packed_at | DATETIME | | Packing completion |
| shipped_at | DATETIME | | Shipping timestamp |
| delivered_at | DATETIME | | Delivery timestamp |
| created_at | DATETIME | NOT NULL | Order creation |
| updated_at | DATETIME | | Last update |

**Order Statuses:**
- `pending_payment` - Awaiting payment
- `paid` - Payment confirmed
- `processing` - Being prepared
- `packed` - Ready for shipping
- `shipped` - In transit
- `delivered` - Completed
- `cancelled` - Cancelled
- `returned` - Returned

**Indexes:**
- `order_number` (UNIQUE)
- `customer_id`
- `status`
- `created_at`

---

### order_items

Line items in orders.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Order item ID |
| order_id | INTEGER | FOREIGN KEY → orders.id | Parent order |
| variant_id | INTEGER | FOREIGN KEY → inventory.id | Product variant |
| product_name | VARCHAR(200) | NOT NULL | Product name (snapshot) |
| variant_details | VARCHAR(100) | | Size/color (snapshot) |
| quantity | INTEGER | NOT NULL | Quantity ordered |
| unit_price | DECIMAL(10,2) | NOT NULL | Price per unit |
| subtotal | DECIMAL(10,2) | NOT NULL | Line total |
| created_at | DATETIME | NOT NULL | Creation timestamp |

---

### payments

Payment transactions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Payment ID |
| order_id | INTEGER | FOREIGN KEY → orders.id | Related order |
| payment_method | VARCHAR(50) | NOT NULL | Payment method |
| amount | DECIMAL(10,2) | NOT NULL | Payment amount |
| status | VARCHAR(50) | NOT NULL | Payment status |
| transaction_id | VARCHAR(255) | | External transaction ID |
| payment_details_encrypted | ENCRYPTED_STRING | | Encrypted payment info |
| processed_at | DATETIME | | Processing timestamp |
| created_at | DATETIME | NOT NULL | Creation timestamp |

---

### reviews

Product reviews.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Review ID |
| product_id | INTEGER | FOREIGN KEY → products.id | Product |
| customer_id | INTEGER | FOREIGN KEY → customers.id | Reviewer |
| order_id | INTEGER | FOREIGN KEY → orders.id | Verified purchase |
| rating | INTEGER | NOT NULL | Rating (1-5) |
| title | VARCHAR(200) | | Review title |
| comment | TEXT | | Review text |
| is_verified_purchase | BOOLEAN | DEFAULT FALSE | Verified purchase |
| is_approved | BOOLEAN | DEFAULT FALSE | Admin approved |
| created_at | DATETIME | NOT NULL | Review date |

---

## POS System

### pos_transactions

Point of sale transactions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Transaction ID |
| employee_id | INTEGER | FOREIGN KEY → employees.id | Cashier |
| receipt_number | VARCHAR(50) | UNIQUE, NOT NULL | Receipt number |
| subtotal | DECIMAL(10,2) | NOT NULL | Items subtotal |
| tax | DECIMAL(10,2) | DEFAULT 0 | Tax amount |
| total | DECIMAL(10,2) | NOT NULL | Total amount |
| payment_method | VARCHAR(50) | NOT NULL | Payment method |
| amount_paid | DECIMAL(10,2) | NOT NULL | Amount tendered |
| change_given | DECIMAL(10,2) | DEFAULT 0 | Change returned |
| status | VARCHAR(50) | DEFAULT 'completed' | Transaction status |
| voided_at | DATETIME | | Void timestamp |
| voided_by | INTEGER | FOREIGN KEY → employees.id | Voiding employee |
| void_reason | TEXT | | Void reason |
| created_at | DATETIME | NOT NULL | Transaction time |

---

### pos_transaction_items

Items in POS transactions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Item ID |
| transaction_id | INTEGER | FOREIGN KEY → pos_transactions.id | Parent transaction |
| variant_id | INTEGER | FOREIGN KEY → inventory.id | Product variant |
| product_name | VARCHAR(200) | NOT NULL | Product name |
| variant_details | VARCHAR(100) | | Size/color |
| quantity | INTEGER | NOT NULL | Quantity sold |
| unit_price | DECIMAL(10,2) | NOT NULL | Price per unit |
| subtotal | DECIMAL(10,2) | NOT NULL | Line total |

---

### store_locations

Physical store information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Location ID |
| name | VARCHAR(200) | NOT NULL | Store name |
| address | TEXT | NOT NULL | Street address |
| city | VARCHAR(100) | NOT NULL | City |
| phone | VARCHAR(20) | | Contact phone |
| email | VARCHAR(255) | | Contact email |
| hours | TEXT | | Operating hours |
| latitude | DECIMAL(10,8) | | GPS latitude |
| longitude | DECIMAL(11,8) | | GPS longitude |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Store active |
| created_at | DATETIME | NOT NULL | Creation date |

---

## GDPR Compliance

### gdpr_data_requests

Customer data access/deletion requests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Request ID |
| customer_id | INTEGER | FOREIGN KEY → customers.id | Requesting customer |
| request_type | VARCHAR(50) | NOT NULL | 'access' or 'deletion' |
| status | VARCHAR(50) | NOT NULL | Request status |
| requested_at | DATETIME | NOT NULL | Request timestamp |
| processed_at | DATETIME | | Processing timestamp |
| processed_by | INTEGER | FOREIGN KEY → employees.id | Processing employee |
| notes | TEXT | | Processing notes |

---

### gdpr_consent_log

Consent tracking history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Log ID |
| customer_id | INTEGER | FOREIGN KEY → customers.id | Customer |
| consent_type | VARCHAR(50) | NOT NULL | Consent type |
| consent_given | BOOLEAN | NOT NULL | Consent status |
| ip_address | VARCHAR(45) | | Request IP |
| user_agent | TEXT | | Browser info |
| created_at | DATETIME | NOT NULL | Consent timestamp |

---

## Audit & Logging

### data_access_log

PII access audit trail.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Log ID |
| employee_id | INTEGER | FOREIGN KEY → employees.id | Accessing employee |
| customer_id | INTEGER | FOREIGN KEY → customers.id | Accessed customer |
| access_type | VARCHAR(50) | NOT NULL | Access type |
| accessed_fields | TEXT | | Fields accessed |
| reason | TEXT | | Access reason |
| ip_address | VARCHAR(45) | | Request IP |
| created_at | DATETIME | NOT NULL | Access timestamp |

---

### activity_logs

General system activity log.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Log ID |
| user_type | VARCHAR(50) | NOT NULL | 'customer' or 'employee' |
| user_id | INTEGER | NOT NULL | User ID |
| action | VARCHAR(100) | NOT NULL | Action performed |
| entity_type | VARCHAR(50) | | Affected entity type |
| entity_id | INTEGER | | Affected entity ID |
| details | TEXT | | Additional details (JSON) |
| ip_address | VARCHAR(45) | | Request IP |
| created_at | DATETIME | NOT NULL | Action timestamp |

**Indexes:**
- `user_type, user_id`
- `entity_type, entity_id`
- `created_at`

---

## Relationships

### Entity Relationship Diagram

```
customers (1) ──< (N) customer_addresses
customers (1) ──< (N) orders
customers (1) ──< (N) reviews
customers (1) ──── (1) carts
customers (1) ──── (1) wishlists

orders (1) ──< (N) order_items
orders (1) ──< (N) payments

products (1) ──< (N) inventory (variants)
products (1) ──< (N) product_images
products (1) ──< (N) reviews

categories (1) ──< (N) products

employees (1) ──< (N) pos_transactions
employees (1) ──< (N) orders (as packer/shipper)

pos_transactions (1) ──< (N) pos_transaction_items
```

---

## Indexes

### Performance Indexes

```sql
-- Customer lookups
CREATE INDEX idx_customers_email_hash ON customers(email_hash);
CREATE INDEX idx_customers_anonymized ON customers(anonymized);

-- Order queries
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);

-- Product searches
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_sku ON inventory(sku);

-- POS operations
CREATE INDEX idx_pos_employee ON pos_transactions(employee_id);
CREATE INDEX idx_pos_created ON pos_transactions(created_at);

-- Audit trails
CREATE INDEX idx_activity_user ON activity_logs(user_type, user_id);
CREATE INDEX idx_activity_created ON activity_logs(created_at);
```

---

## Migrations

Database migrations are managed in `/backend/migrations/`:

- `001_initial_schema.sql` - Base schema
- `020_add_order_tracking.sql` - Order tracking fields
- `021_add_fulfillment.sql` - Fulfillment workflow

Run migrations:
```bash
cd backend
python scripts/migrate_database.py
```

---

## Backup & Recovery

### Backup Command
```bash
pg_dump -U postgres -d happy_place_db > backup_$(date +%Y%m%d).sql
```

### Restore Command
```bash
psql -U postgres -d happy_place_db < backup_20251212.sql
```

---

## Security Notes

1. **Encrypted Fields:** PII fields use MultiFernet encryption
2. **Password Hashing:** Argon2 for all passwords
3. **Audit Trail:** All PII access is logged
4. **GDPR:** Right to access, right to erasure implemented
5. **Data Retention:** Automatic anonymization after 3 years inactive

---

## Database Connection

**Connection String:**
```
postgresql://postgres:password@localhost:5432/happy_place_db
```

**Environment Variable:**
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/happy_place_db
```

---

## Support

For database questions: dev@happyplace.com
