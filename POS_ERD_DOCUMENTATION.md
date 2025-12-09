# 🏪 POS System - Entity Relationship Diagram (ERD)
**Last Updated:** December 5, 2025  
**Database:** PostgreSQL  
**Schema Version:** 005 (POS Enhancements)

---

## 📊 ERD Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        POS SYSTEM DATABASE SCHEMA                            │
│                                                                              │
│  Core Entities: 6 tables + 4 stored procedures + 1 view                     │
│  Relationships: Employee → Shift → Transaction → Items → Inventory          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Core Tables

### 1. **`employees`** (Existing - from main schema)
**Purpose:** Store employee information and authentication

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique employee identifier |
| `first_name` | VARCHAR(100) | NOT NULL | Employee first name |
| `last_name` | VARCHAR(100) | NOT NULL | Employee last name |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password |
| `role` | VARCHAR(20) | NOT NULL | cashier/manager/admin |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Indexes:**
- `idx_employees_email` on `email`
- `idx_employees_role` on `role`

---

### 2. **`store_locations`** (Existing - from main schema)
**Purpose:** Physical store locations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique location identifier |
| `name` | VARCHAR(255) | NOT NULL | Store name |
| `address` | TEXT | | Physical address |
| `city` | VARCHAR(100) | | City |
| `phone` | VARCHAR(20) | | Contact phone |
| `is_active` | BOOLEAN | DEFAULT TRUE | Operational status |

**Example Data:**
- ID 1: "Happy Place Boutique - Nairobi"

---

### 3. **`pos_shifts`** ⭐ (POS Core Table)
**Purpose:** Track employee work shifts and cash management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique shift identifier |
| `employee_id` | INTEGER | FK → employees(id), NOT NULL | Employee working shift |
| `store_location_id` | INTEGER | FK → store_locations(id), NOT NULL | Store location |
| `shift_number` | VARCHAR(50) | UNIQUE, NOT NULL | Smart shift number |
| `start_time` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Shift start |
| `end_time` | TIMESTAMP | NULLABLE | Shift end (NULL = open) |
| `opening_float` | NUMERIC(10,2) | NOT NULL | Starting cash amount |
| `closing_cash` | NUMERIC(10,2) | NULLABLE | Actual cash counted |
| `expected_cash` | NUMERIC(10,2) | NULLABLE | Calculated expected cash |
| `variance` | NUMERIC(10,2) | NULLABLE | Difference (actual - expected) |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'open' | open/closed |
| `notes` | TEXT | NULLABLE | Shift notes |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update |

**Constraints:**
- `CHECK (status IN ('open', 'closed'))`

**Indexes:**
- `idx_pos_shifts_employee` on `employee_id`
- `idx_pos_shifts_store` on `store_location_id`
- `idx_pos_shifts_status` on `status`
- `idx_pos_shifts_start_time` on `start_time`

**Smart Shift Numbering:**
- Format: `YYYYMMDD-LOC{location_id}-EMP{employee_id}-{sequence}`
- Example: `20251205-LOC1-EMP2-001`
- Benefits: Date tracking, location filtering, employee performance, sequence tracking

---

### 4. **`pos_transactions`** ⭐ (POS Core Table)
**Purpose:** Store all POS sales transactions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique transaction identifier |
| `transaction_number` | VARCHAR(50) | UNIQUE, NOT NULL | POS-YYYYMMDD-NNNN |
| `employee_id` | INTEGER | FK → employees(id), NOT NULL | Cashier |
| `store_location_id` | INTEGER | FK → store_locations(id), NOT NULL | Store |
| `shift_id` | INTEGER | FK → pos_shifts(id), NULLABLE | Associated shift |
| `customer_id` | INTEGER | FK → customers(id), NULLABLE | Optional customer link |
| `payment_method` | VARCHAR(20) | NOT NULL | cash/mpesa/card |
| `subtotal` | NUMERIC(10,2) | NOT NULL | Pre-tax total |
| `tax` | NUMERIC(10,2) | NOT NULL | Tax amount (0% Kenya) |
| `total` | NUMERIC(10,2) | NOT NULL | Final total |
| `cash_tendered` | NUMERIC(10,2) | NULLABLE | Cash given by customer |
| `change_given` | NUMERIC(10,2) | NULLABLE | Change returned |
| `status` | VARCHAR(20) | NOT NULL | completed/voided |
| `receipt_printed` | BOOLEAN | DEFAULT FALSE | Receipt print status |
| `receipt_emailed` | BOOLEAN | DEFAULT FALSE | Email receipt status |
| `voided_at` | TIMESTAMP | NULLABLE | When voided |
| `voided_by` | INTEGER | FK → employees(id), NULLABLE | Manager who voided |
| `void_reason` | TEXT | NULLABLE | Void justification |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Transaction time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update |

**Indexes:**
- `idx_pos_transactions_shift` on `shift_id`
- `idx_pos_transactions_customer` on `customer_id`
- `idx_pos_transactions_voided` on `voided_at` WHERE `voided_at IS NOT NULL`
- `idx_pos_transactions_created` on `created_at`

---

### 5. **`pos_transaction_items`** (Line Items)
**Purpose:** Individual items in each transaction

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique line item identifier |
| `transaction_id` | INTEGER | FK → pos_transactions(id), NOT NULL | Parent transaction |
| `product_id` | INTEGER | FK → products(id), NOT NULL | Product sold |
| `inventory_id` | INTEGER | FK → inventory(id), NOT NULL | Inventory record |
| `quantity` | INTEGER | NOT NULL | Quantity sold |
| `unit_price` | NUMERIC(10,2) | NOT NULL | Price per unit |
| `total_price` | NUMERIC(10,2) | NOT NULL | Line total |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

**Indexes:**
- `idx_pos_transaction_items_transaction` on `transaction_id`
- `idx_pos_transaction_items_product` on `product_id`

---

### 6. **`pos_cash_movements`** (Cash Tracking)
**Purpose:** Track all cash in/out activities during shifts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique movement identifier |
| `shift_id` | INTEGER | FK → pos_shifts(id), NOT NULL, ON DELETE CASCADE | Associated shift |
| `movement_type` | VARCHAR(20) | NOT NULL | Type of movement |
| `amount` | NUMERIC(10,2) | NOT NULL | Amount moved |
| `reason` | TEXT | NULLABLE | Movement reason |
| `performed_by` | INTEGER | FK → employees(id), NOT NULL | Employee who performed |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Movement time |

**Movement Types:**
- `starting_float` - Opening cash
- `cash_in` - Cash added (bank deposit return, etc.)
- `cash_out` - Cash removed (bank deposit, petty cash, etc.)
- `closing_count` - Final cash count
- `adjustment` - Manual adjustments

**Constraints:**
- `CHECK (movement_type IN ('cash_in', 'cash_out', 'starting_float', 'closing_count', 'adjustment'))`

**Indexes:**
- `idx_pos_cash_movements_shift` on `shift_id`
- `idx_pos_cash_movements_type` on `movement_type`

---

## 🔗 Relationships

### **Primary Relationships:**

```
employees (1) ──────< (M) pos_shifts
    │                       │
    │                       │
    └──< (M) pos_transactions
                │
                ├──< (M) pos_transaction_items ──> (1) products
                │                                  │
                │                                  └──> (1) inventory
                │
                └──< (M) pos_cash_movements

store_locations (1) ──< (M) pos_shifts
                │
                └──< (M) pos_transactions

customers (1) ──< (M) pos_transactions (optional)
```

### **Relationship Details:**

1. **Employee → Shifts** (1:M)
   - One employee can have many shifts
   - Each shift belongs to one employee
   - FK: `pos_shifts.employee_id → employees.id`

2. **Store Location → Shifts** (1:M)
   - One location can have many shifts
   - Each shift is at one location
   - FK: `pos_shifts.store_location_id → store_locations.id`

3. **Shift → Transactions** (1:M)
   - One shift can have many transactions
   - Each transaction belongs to one shift
   - FK: `pos_transactions.shift_id → pos_shifts.id`

4. **Shift → Cash Movements** (1:M)
   - One shift can have many cash movements
   - Each movement belongs to one shift
   - FK: `pos_cash_movements.shift_id → pos_shifts.id`
   - ON DELETE CASCADE (movements deleted with shift)

5. **Transaction → Transaction Items** (1:M)
   - One transaction can have many line items
   - Each item belongs to one transaction
   - FK: `pos_transaction_items.transaction_id → pos_transactions.id`

6. **Transaction Items → Products** (M:1)
   - Many items can reference one product
   - Each item references one product
   - FK: `pos_transaction_items.product_id → products.id`

7. **Transaction Items → Inventory** (M:1)
   - Many items can reference one inventory record
   - Each item references one inventory record
   - FK: `pos_transaction_items.inventory_id → inventory.id`

8. **Customer → Transactions** (1:M, Optional)
   - One customer can have many transactions
   - Each transaction optionally links to one customer
   - FK: `pos_transactions.customer_id → customers.id` (NULLABLE)

---

## 🔧 Stored Procedures

### 1. **`sp_create_pos_transaction`**
**Purpose:** Atomically create a transaction with inventory deduction

**Parameters:**
- `p_employee_id` INTEGER
- `p_store_location_id` INTEGER
- `p_shift_id` INTEGER
- `p_payment_method` VARCHAR(20)
- `p_items` JSONB (array of {variant_id, quantity})
- `p_customer_id` INTEGER (optional)
- `p_cash_tendered` NUMERIC(10,2) (optional)

**Returns:** JSONB
```json
{
  "success": true,
  "transaction_id": 123,
  "transaction_number": "POS-20251205-0001",
  "subtotal": 5000.00,
  "tax": 0.00,
  "total": 5000.00,
  "change_given": 0.00
}
```

**Logic:**
1. Validate shift is open
2. Generate unique transaction number
3. Validate inventory availability
4. Calculate totals and change
5. Create transaction record
6. Create transaction items
7. Deduct inventory via `sp_deduct_inventory`

---

### 2. **`sp_void_pos_transaction`**
**Purpose:** Void a transaction and restore inventory

**Parameters:**
- `p_transaction_id` INTEGER
- `p_voided_by` INTEGER (must be manager/admin)
- `p_void_reason` TEXT

**Returns:** JSONB
```json
{
  "success": true,
  "transaction_id": 123,
  "transaction_number": "POS-20251205-0001",
  "voided_at": "2025-12-05T10:30:00"
}
```

**Logic:**
1. Verify transaction exists and not already voided
2. Check user has manager/admin role
3. Restore inventory for each item via `sp_add_inventory`
4. Mark transaction as voided

---

### 3. **`sp_start_shift`**
**Purpose:** Open a new shift for an employee

**Parameters:**
- `p_employee_id` INTEGER
- `p_store_location_id` INTEGER
- `p_opening_float` NUMERIC(10,2)

**Returns:** JSONB
```json
{
  "success": true,
  "shift_id": 10,
  "shift_number": "20251205-LOC1-EMP2-001",
  "opening_float": 5000.00,
  "start_time": "2025-12-05T08:00:00"
}
```

**Logic:**
1. Check employee doesn't have an open shift
2. Generate smart shift number
3. Create shift record
4. Log opening float as cash movement

---

### 4. **`sp_close_shift`**
**Purpose:** Close a shift with cash reconciliation

**Parameters:**
- `p_shift_id` INTEGER
- `p_closing_cash` NUMERIC(10,2)
- `p_notes` TEXT (optional)

**Returns:** JSONB
```json
{
  "success": true,
  "shift_id": 10,
  "shift_number": "20251205-LOC1-EMP2-001",
  "opening_float": 5000.00,
  "cash_sales": 10298.00,
  "cash_in": 0.00,
  "cash_out": 0.00,
  "expected_cash": 15298.00,
  "closing_cash": 15598.00,
  "variance": 300.00,
  "end_time": "2025-12-05T16:00:00"
}
```

**Logic:**
1. Verify shift exists and is open
2. Calculate cash sales from transactions
3. Sum cash in/out movements
4. Calculate expected cash = opening + sales + cash_in - cash_out
5. Calculate variance = closing - expected
6. Log closing count as cash movement
7. Update shift status to 'closed'

---

## 📈 Views

### **`v_pos_shift_summary`**
**Purpose:** User-friendly shift summary with aggregated stats

**Columns:**
- `shift_id`, `shift_number`
- `employee_name`, `employee_email`
- `store_name`
- `start_time`, `end_time`, `status`
- `opening_float`, `closing_cash`, `expected_cash`, `variance`
- `transaction_count`, `total_sales`, `cash_sales`, `mpesa_sales`
- `voided_count`, `notes`, `created_at`

**SQL:**
```sql
SELECT
    ps.id AS shift_id,
    ps.shift_number,
    e.first_name || ' ' || e.last_name AS employee_name,
    sl.name AS store_name,
    COUNT(pt.id) FILTER (WHERE pt.voided_at IS NULL) AS transaction_count,
    COALESCE(SUM(pt.total) FILTER (WHERE pt.voided_at IS NULL), 0) AS total_sales
FROM pos_shifts ps
JOIN employees e ON e.id = ps.employee_id
JOIN store_locations sl ON sl.id = ps.store_location_id
LEFT JOIN pos_transactions pt ON pt.shift_id = ps.id
GROUP BY ps.id, e.first_name, e.last_name, sl.name;
```

---

## 🎯 Business Rules

### **Shift Management:**
1. ✅ Employee can only have ONE open shift at a time
2. ✅ Shift number must be globally unique
3. ✅ Shift must be open to create transactions
4. ✅ Closing cash variance is calculated automatically
5. ✅ Cash movements are logged for audit trail

### **Transaction Processing:**
1. ✅ Transaction number format: `POS-YYYYMMDD-NNNN`
2. ✅ Inventory is deducted atomically with transaction creation
3. ✅ Cash tendered must be >= total for cash payments
4. ✅ Change is calculated automatically
5. ✅ Only managers/admins can void transactions
6. ✅ Voiding restores inventory automatically

### **Cash Reconciliation:**
1. ✅ Expected cash = opening_float + cash_sales + cash_in - cash_out
2. ✅ Variance = closing_cash - expected_cash
3. ✅ Positive variance = cash over (extra cash in drawer)
4. ✅ Negative variance = cash short (missing cash)
5. ✅ All movements are logged with timestamp and employee

---

## 🔍 Query Examples

### **Get Open Shifts:**
```sql
SELECT * FROM pos_shifts
WHERE status = 'open'
ORDER BY start_time DESC;
```

### **Get Today's Transactions:**
```sql
SELECT * FROM pos_transactions
WHERE DATE(created_at) = CURRENT_DATE
AND voided_at IS NULL
ORDER BY created_at DESC;
```

### **Get Shift Summary:**
```sql
SELECT * FROM v_pos_shift_summary
WHERE shift_id = 10;
```

### **Get Employee Performance:**
```sql
SELECT
    e.first_name || ' ' || e.last_name AS employee,
    COUNT(DISTINCT ps.id) AS shifts_worked,
    COUNT(pt.id) AS transactions_processed,
    COALESCE(SUM(pt.total), 0) AS total_sales
FROM employees e
LEFT JOIN pos_shifts ps ON ps.employee_id = e.id
LEFT JOIN pos_transactions pt ON pt.employee_id = e.id
WHERE DATE(ps.start_time) >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY e.id, e.first_name, e.last_name
ORDER BY total_sales DESC;
```

---

## 📊 Data Flow

### **Typical POS Transaction Flow:**

```
1. Employee Login
   ↓
2. Start Shift (sp_start_shift)
   ├─ Create pos_shifts record
   └─ Log opening_float in pos_cash_movements
   ↓
3. Create Transaction (sp_create_pos_transaction)
   ├─ Validate shift is open
   ├─ Check inventory availability
   ├─ Create pos_transactions record
   ├─ Create pos_transaction_items records
   └─ Deduct inventory (sp_deduct_inventory)
   ↓
4. [Optional] Cash In/Out
   └─ Log in pos_cash_movements
   ↓
5. Close Shift (sp_close_shift)
   ├─ Calculate cash_sales from transactions
   ├─ Sum cash_in and cash_out movements
   ├─ Calculate expected_cash
   ├─ Calculate variance
   ├─ Log closing_count in pos_cash_movements
   └─ Update pos_shifts status = 'closed'
```

---

## 🎨 ERD Diagram (Text Format)

```
┌──────────────┐
│  employees   │
│──────────────│
│ id (PK)      │◄──────────┐
│ first_name   │           │
│ last_name    │           │
│ email (UQ)   │           │
│ role         │           │
└──────────────┘           │
       │                   │
       │ 1:M               │
       ▼                   │
┌──────────────────┐       │
│   pos_shifts     │       │
│──────────────────│       │
│ id (PK)          │       │
│ employee_id (FK) │───────┘
│ store_location_id│───────┐
│ shift_number (UQ)│       │
│ start_time       │       │
│ end_time         │       │
│ opening_float    │       │
│ closing_cash     │       │
│ expected_cash    │       │
│ variance         │       │
│ status           │       │
└──────────────────┘       │
       │                   │
       │ 1:M               │
       ▼                   │
┌──────────────────────┐   │
│  pos_transactions    │   │
│──────────────────────│   │
│ id (PK)              │   │
│ transaction_number(UQ│   │
│ employee_id (FK)     │   │
│ shift_id (FK)        │───┘
│ customer_id (FK)     │
│ payment_method       │
│ total                │
│ status               │
│ voided_at            │
└──────────────────────┘
       │
       │ 1:M
       ▼
┌────────────────────────┐
│ pos_transaction_items  │
│────────────────────────│
│ id (PK)                │
│ transaction_id (FK)    │───┐
│ product_id (FK)        │   │
│ inventory_id (FK)      │   │
│ quantity               │   │
│ unit_price             │   │
│ total_price            │   │
└────────────────────────┘   │
                             │
┌──────────────────────┐     │
│ pos_cash_movements   │     │
│──────────────────────│     │
│ id (PK)              │     │
│ shift_id (FK)        │─────┘
│ movement_type        │
│ amount               │
│ reason               │
│ performed_by (FK)    │
└──────────────────────┘

┌──────────────────┐
│ store_locations  │
│──────────────────│
│ id (PK)          │
│ name             │
│ address          │
│ city             │
└──────────────────┘
```

---

## ✅ Schema Validation Checklist

- ✅ All foreign keys have proper indexes
- ✅ Unique constraints on shift_number and transaction_number
- ✅ CHECK constraints for status and movement_type enums
- ✅ CASCADE delete on pos_cash_movements when shift deleted
- ✅ Timestamps on all tables for audit trail
- ✅ NULLABLE fields properly defined
- ✅ Stored procedures return JSONB for consistent API responses
- ✅ Views provide denormalized data for reporting
- ✅ Smart numbering schemes for easy tracking

---

**Document Version:** 1.0  
**Last Updated:** December 5, 2025  
**Schema Migration:** 005_pos_enhancements.sql
