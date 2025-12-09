# PHASE 11: ADMIN DASHBOARD & MANAGEMENT SYSTEM

**Status:** 🚧 IN PROGRESS
**Priority:** HIGH
**Duration:** 2 weeks (80 hours)
**Budget:** $4,000 @ $50/hr
**Dependencies:** Phase 10 (Authentication Overhaul)
**Completed Features:** Dashboard Metrics/Activity/Alerts, Currency Management

---

## 📋 EXECUTIVE SUMMARY

### What We're Building

A comprehensive admin dashboard system for managers and administrators to efficiently manage the Happy Place Boutique e-commerce operations. This system provides centralized control over inventory, orders, customers, employees, and business analytics.

### Business Value

**For Managers:**
- ✅ Real-time visibility into business operations
- ✅ Quick access to critical alerts (low stock, pending returns)
- ✅ Efficient order and customer management
- ✅ Employee performance tracking
- ✅ Inventory control with bulk operations

**For Business:**
- ✅ Reduced operational overhead (faster decision-making)
- ✅ Better inventory management (prevent stockouts)
- ✅ Improved customer service (faster order processing)
- ✅ Data-driven decisions (sales trends, top products)
- ✅ Compliance ready (GDPR tools, audit logs)

**ROI Projection:**
- 40% reduction in inventory management time
- 30% faster order processing
- 25% reduction in stockouts
- ROI within 3 months

---

## 🎯 SYSTEM OVERVIEW

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ADMIN DASHBOARD                       │
│                   (Manager/Admin Only)                   │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Dashboard  │    │  Inventory   │    │    Orders    │
│   Overview   │    │  Management  │    │  Management  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Customers   │    │  Employees   │    │  Promotions  │
│  Management  │    │  Management  │    │  Management  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Settings   │
                    │  & Reports   │
                    └──────────────┘
```

### Access Control

| Feature | Admin | Manager | Cashier | Staff |
|---------|-------|---------|---------|-------|
| Dashboard Overview | ✅ | ✅ | ❌ | ❌ |
| Inventory Management | ✅ | ✅ | View Only | View Only |
| Order Management | ✅ | ✅ | ❌ | ❌ |
| Customer Management | ✅ | ✅ | View Only | View Only |
| Employee Management | ✅ | ✅ | ❌ | ❌ |
| Promotions | ✅ | ✅ | ❌ | ❌ |
| System Settings | ✅ | ❌ | ❌ | ❌ |
| Audit Logs | ✅ | ✅ | ❌ | ❌ |

---

## 🗂️ FEATURE BREAKDOWN

### 1. Dashboard Overview (Home) ✅ PARTIALLY COMPLETED

**Purpose:** At-a-glance view of business health and urgent actions

**Key Metrics Cards:**
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│  Today's Sales  │ Orders Today    │ Total Customers │ Low Stock Items │
│  KSh 125,450    │      23         │     1,247       │       8         │
│  ↑ 12% vs Yest  │  ↓ 3 vs Yest   │  ↑ 5 new today  │  ⚠️ Critical    │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

**Components:**

1. **Sales Summary** ✅ COMPLETED
   - Today's revenue (total, online, POS)
   - Comparison with yesterday/last week
   - Monthly target progress bar
   - Top performing category today

2. **Order Status Overview** ✅ COMPLETED
   ```
   Pending:     5 orders  [View →]
   Processing: 12 orders  [View →]
   Completed:   6 orders  [View →]
   Cancelled:   1 order   [View →]
   ```

3. **Critical Alerts** (Priority ordered) ✅ COMPLETED
   - 🔴 Out of stock items (0 available)
   - 🟠 Low stock items (<10 available)
   - 🟡 Pending returns (>48 hours old)
   - 🔵 Unverified orders (payment pending)

4. **Recent Activity Feed** ✅ COMPLETED
   - Last 10 orders with status
   - Recent customer registrations
   - Recent inventory changes
   - Employee actions (from audit log)

5. **Quick Actions Panel**
   ```
   [➕ Add Product]  [📦 Update Stock]  [👤 Add Employee]
   [📊 View Reports] [⚙️ Settings]     [📝 Create Promo]
   ```

**API Endpoints:**
- `GET /api/admin/dashboard` - Main dashboard data (EXISTING)
- `GET /api/admin/dashboard/metrics` - Real-time metrics ✅ COMPLETED
- `GET /api/admin/dashboard/activity` - Recent activity feed ✅ COMPLETED
- `GET /api/admin/dashboard/alerts` - Critical alerts ✅ COMPLETED

---

### 2. Inventory Management

**Purpose:** Complete control over product catalog and stock levels

#### 2.1 Inventory List View

**Features:**
- Searchable/filterable product list
- Bulk operations (update stock, change status)
- Low stock highlighting
- Quick edit inline
- Export to CSV

**Table Columns:**
```
SKU | Product | Category | Size | Color | Online Stock | Store Stock | Status | Actions
```

**Filters:**
- Category dropdown
- Stock status (All, In Stock, Low Stock, Out of Stock)
- Product status (Active, Inactive, Clearance)
- Search by name/SKU

**Bulk Actions:**
- Update stock quantities
- Change product status (active/inactive)
- Mark as clearance
- Delete multiple items

#### 2.2 Product Detail/Edit View

**Sections:**

1. **Basic Information**
   ```
   Product Name:     [___________________________]
   SKU:              [___________] (auto-generated)
   Category:         [Dropdown: Women's Tops ▼]
   Description:      [Text area........................]
   ```

2. **Pricing**
   ```
   Regular Price:    KSh [________]
   Sale Price:       KSh [________] (optional)
   Is Clearance:     [ ] Yes (FINAL SALE)
   ```

3. **Variants**
   ```
   ┌──────────────────────────────────────────────────────┐
   │ Size: M  │ Color: Black │ SKU: WOM-TOP-001-M-BLK    │
   │ Online: [50]  Store: [20]  Reserved: 3              │
   │ [Edit] [Delete]                                      │
   ├──────────────────────────────────────────────────────┤
   │ Size: L  │ Color: Blue  │ SKU: WOM-TOP-001-L-BLU    │
   │ Online: [30]  Store: [15]  Reserved: 1              │
   │ [Edit] [Delete]                                      │
   └──────────────────────────────────────────────────────┘
   [+ Add Variant]
   ```

4. **Images**
   ```
   [Primary Image]  [Image 2]  [Image 3]  [+ Upload]
   ```

5. **Inventory Tracking**
   ```
   Total Stock:      120 units
   Available:        115 units (Total - Reserved)
   Reserved:         5 units (in active carts/orders)

   Stock History (Last 30 days):
   ┌────────────────────────────────────────────┐
   │ Date       │ Type      │ Qty  │ By        │
   ├────────────────────────────────────────────┤
   │ 2025-12-02 │ Restock   │ +50  │ Manager   │
   │ 2025-12-01 │ Sale (POS)│ -2   │ Cashier   │
   │ 2025-11-30 │ Sale      │ -1   │ Customer  │
   └────────────────────────────────────────────┘
   ```

#### 2.3 Stock Adjustment

**Quick Adjust Modal:**
```
┌────────────────────────────────────────┐
│  Adjust Stock - SKU: WOM-TOP-001-M-BLK │
├────────────────────────────────────────┤
│  Current Stock: 50                     │
│                                        │
│  Adjustment Type:                      │
│  ○ Add Stock (Restock)                │
│  ○ Remove Stock (Damage/Lost)         │
│  ○ Transfer (Online ↔ Store)          │
│  ○ Set Exact Quantity                 │
│                                        │
│  Quantity: [____]                      │
│  Reason: [Text area...............]    │
│                                        │
│  [Cancel]  [Save Adjustment]          │
└────────────────────────────────────────┘
```

**Stock Transfer:**
```
┌────────────────────────────────────────┐
│  Transfer Stock                        │
├────────────────────────────────────────┤
│  Product: Women's Floral Top (M, Blk)  │
│                                        │
│  From: [Online Store ▼]               │
│  To:   [Physical Store ▼]             │
│                                        │
│  Quantity: [____] (Max: 50)           │
│  Notes: [Text area...............]     │
│                                        │
│  [Cancel]  [Transfer Stock]           │
└────────────────────────────────────────┘
```

**API Endpoints:**
- `GET /api/admin/inventory` - Paginated inventory list (NEW)
- `GET /api/admin/inventory/:id` - Product details (NEW)
- `PUT /api/admin/inventory/:id` - Update product (NEW)
- `POST /api/admin/inventory/bulk-update` - Bulk stock update (NEW)
- `POST /api/admin/inventory/adjust` - Stock adjustment (NEW)
- `POST /api/admin/inventory/transfer` - Stock transfer (NEW)
- `GET /api/admin/inventory/alerts` - Low stock alerts (EXISTING)
- `GET /api/admin/inventory/:id/history` - Stock history (NEW)
- `DELETE /api/admin/inventory/:id` - Delete product (NEW)

---

### 3. Order Management

**Purpose:** Process, track, and manage customer orders

#### 3.1 Order List View

**Features:**
- Real-time order feed
- Status filtering
- Search by order number/customer
- Bulk status updates
- Export orders

**Table Columns:**
```
Order # | Date | Customer | Items | Total | Payment | Status | Actions
```

**Filters:**
- Status: All, Pending, Processing, Completed, Cancelled
- Payment: All, Paid, Unpaid, COD, M-Pesa
- Date range picker
- Customer search

**Status Badge Colors:**
- 🔵 Pending (awaiting payment)
- 🟡 Processing (payment confirmed, preparing)
- 🟢 Completed (shipped/delivered)
- 🔴 Cancelled
- ⚫ Refunded

#### 3.2 Order Detail View

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ Order #ORD-20251203-001                    [Print Invoice]   │
│ Status: Processing                         [Update Status ▼] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ CUSTOMER INFORMATION                 ORDER INFORMATION       │
│ Name: Jane Doe                      Date: Dec 3, 2025       │
│ Email: jane@example.com             Payment: M-Pesa         │
│ Phone: +254712345678                Method: STK Push        │
│                                     Status: Paid ✓          │
│ SHIPPING ADDRESS                                            │
│ 123 Kimathi Street                  BILLING ADDRESS         │
│ Nairobi, Kenya                      Same as shipping        │
│ 00100                                                       │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ORDER ITEMS                                                  │
│                                                              │
│ [Img] Women's Floral Top                                    │
│       Size: M, Color: Black                                 │
│       SKU: WOM-TOP-001-M-BLK                                │
│       Qty: 2 × KSh 1,500.00 = KSh 3,000.00                 │
│                                                              │
│ [Img] Maternity Dress                                       │
│       Size: L, Color: Blue                                  │
│       SKU: MAT-DRS-005-L-BLU                                │
│       Qty: 1 × KSh 2,500.00 = KSh 2,500.00                 │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ SUMMARY                                                      │
│ Subtotal:                                    KSh 5,500.00   │
│ Shipping (Standard - 3-5 days):              KSh 300.00     │
│ Tax (16% VAT):                                KSh 880.00     │
│ ───────────────────────────────────────────────────────────  │
│ TOTAL:                                       KSh 6,680.00   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ORDER TIMELINE                                               │
│ ● Dec 3, 10:30 AM - Order placed                           │
│ ● Dec 3, 10:31 AM - Payment confirmed (M-Pesa)             │
│ ● Dec 3, 11:00 AM - Order marked as Processing (Manager)   │
│ ○ Pending - Shipped                                        │
│ ○ Pending - Delivered                                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ INTERNAL NOTES                                               │
│ [Text area for manager notes............................]   │
│ [Add Note]                                                  │
└──────────────────────────────────────────────────────────────┘

[Mark as Shipped]  [Cancel Order]  [Initiate Refund]
```

#### 3.3 Order Actions

**Update Order Status:**
```
Current Status: Processing

Update to:
○ Pending (awaiting payment)
○ Processing (preparing order) [CURRENT]
● Shipped (in transit)
○ Completed (delivered)
○ Cancelled (cancel order)

Add tracking info (if shipped):
Carrier: [Dropdown: DHL, Posta Kenya ▼]
Tracking #: [___________________]
Notes: [Text area................]

[Update Status]
```

**Cancel Order:**
```
┌────────────────────────────────────────┐
│  Cancel Order #ORD-20251203-001        │
├────────────────────────────────────────┤
│  ⚠️ This action cannot be undone      │
│                                        │
│  Reason for cancellation:              │
│  ○ Out of stock                       │
│  ○ Customer request                   │
│  ○ Payment failed                     │
│  ○ Duplicate order                    │
│  ○ Other (specify below)              │
│                                        │
│  Notes: [Text area...............]     │
│                                        │
│  [ ] Refund payment (if paid)         │
│  [ ] Notify customer via email        │
│                                        │
│  [Go Back]  [Confirm Cancellation]    │
└────────────────────────────────────────┘
```

**Initiate Refund:**
```
┌────────────────────────────────────────┐
│  Process Refund                        │
├────────────────────────────────────────┤
│  Order Total: KSh 6,680.00            │
│                                        │
│  Refund Type:                          │
│  ● Full Refund (KSh 6,680.00)         │
│  ○ Partial Refund                     │
│                                        │
│  Reason:                               │
│  [Dropdown: Defective Item ▼]         │
│                                        │
│  Refund Method:                        │
│  ● Original Payment Method (M-Pesa)   │
│  ○ Store Credit                       │
│                                        │
│  Internal Notes:                       │
│  [Text area................]           │
│                                        │
│  [Cancel]  [Process Refund]           │
└────────────────────────────────────────┘
```

**API Endpoints:**
- `GET /api/admin/orders` - Paginated order list (NEW)
- `GET /api/admin/orders/:id` - Order details (NEW)
- `PUT /api/admin/orders/:id/status` - Update order status (NEW)
- `POST /api/admin/orders/:id/cancel` - Cancel order (NEW)
- `POST /api/admin/orders/:id/refund` - Process refund (NEW)
- `POST /api/admin/orders/:id/notes` - Add internal note (NEW)
- `GET /api/admin/orders/:id/timeline` - Order event timeline (NEW)
- `POST /api/admin/orders/:id/notify` - Send notification to customer (NEW)

---

### 4. Customer Management

**Purpose:** View and manage customer accounts, handle GDPR requests

#### 4.1 Customer List View

**Features:**
- Searchable customer database
- Filter by status, registration date
- View order history per customer
- GDPR compliance tools
- Export customer list (anonymized)

**Table Columns:**
```
ID | Name | Email | Phone | Orders | Total Spent | Registered | Status | Actions
```

**Filters:**
- Status: All, Active, Inactive, Anonymized
- Registration date range
- Has orders / No orders
- Email verified / Unverified
- GDPR consent given / Not given

#### 4.2 Customer Detail View

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ Customer #1234                            [Edit] [Delete]    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ PERSONAL INFORMATION                                         │
│ Name: Jane Doe                     Status: Active ✓          │
│ Email: jane@example.com            Verified: Yes ✓           │
│ Phone: +254712345678               Registered: Jan 15, 2025  │
│ Last Login: Dec 3, 2025                                     │
│                                                              │
│ GDPR COMPLIANCE                                             │
│ GDPR Consent: Yes ✓                Marketing: No ✗          │
│ Data Retention: Until Dec 2028                              │
│ Anonymized: No                                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ SAVED ADDRESSES                                             │
│ [Primary] 123 Kimathi Street, Nairobi, 00100 (Shipping)    │
│           456 Moi Avenue, Nairobi, 00100 (Billing)         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ORDER HISTORY                                                │
│ Total Orders: 15                   Total Spent: KSh 45,200   │
│ Average Order: KSh 3,013           Last Order: Dec 1, 2025  │
│                                                              │
│ Recent Orders:                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ #ORD-001 │ Dec 1  │ 2 items │ KSh 3,200 │ Completed   │││
│ │ #ORD-002 │ Nov 28 │ 1 item  │ KSh 1,500 │ Completed   │││
│ │ #ORD-003 │ Nov 20 │ 3 items │ KSh 4,800 │ Refunded    │││
│ └──────────────────────────────────────────────────────────┘│
│ [View All Orders →]                                         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ACTIVITY LOG (Last 30 days)                                │
│ ● Dec 3 - Logged in                                        │
│ ● Dec 1 - Placed order #ORD-001                           │
│ ● Nov 28 - Added item to wishlist                         │
│ ● Nov 28 - Placed order #ORD-002                          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ GDPR ACTIONS                                                │
│ [Export Customer Data]  [Anonymize Account]                │
│ [View Consent History]  [Delete Account]                   │
└──────────────────────────────────────────────────────────────┘
```

#### 4.3 GDPR Tools

**Export Customer Data:**
```
Generates JSON file with all customer data:
- Personal information
- Order history
- Addresses
- Consent logs
- Activity logs

[Download Customer Data (.json)]
```

**Anonymize Account:**
```
┌────────────────────────────────────────┐
│  Anonymize Customer Account            │
├────────────────────────────────────────┤
│  ⚠️ IRREVERSIBLE ACTION                │
│                                        │
│  This will:                            │
│  ✓ Replace name with "ANONYMIZED"     │
│  ✓ Replace email with deleted_xxx      │
│  ✓ Remove phone number                 │
│  ✓ Delete all addresses                │
│  ✓ Preserve order history (anonymized)│
│  ✓ Mark account as inactive            │
│                                        │
│  Reason: [Dropdown: Right to be       │
│           Forgotten (GDPR) ▼]          │
│                                        │
│  Confirm by typing: ANONYMIZE          │
│  [___________________]                 │
│                                        │
│  [Cancel]  [Confirm Anonymization]    │
└────────────────────────────────────────┘
```

**API Endpoints:**
- `GET /api/admin/customers` - Paginated customer list (NEW)
- `GET /api/admin/customers/:id` - Customer details (NEW)
- `PUT /api/admin/customers/:id` - Update customer (NEW)
- `DELETE /api/admin/customers/:id` - Delete customer (NEW)
- `GET /api/admin/customers/:id/orders` - Customer orders (NEW)
- `GET /api/admin/customers/:id/activity` - Customer activity log (NEW)
- `POST /api/admin/customers/:id/export` - Export customer data (GDPR) (NEW)
- `POST /api/admin/customers/:id/anonymize` - Anonymize account (GDPR) (NEW)
- `GET /api/admin/customers/:id/consent-history` - GDPR consent log (NEW)

---

### 5. Employee Management

**Purpose:** Manage employee accounts, roles, and permissions

#### 5.1 Employee List View

**Features:**
- Employee directory
- Filter by role, status
- View performance metrics
- Manage access permissions
- Track login activity

**Table Columns:**
```
ID | Name | Email | Role | Status | Last Login | Created | Actions
```

**Filters:**
- Role: All, Admin, Manager, Cashier, Staff
- Status: Active, Inactive
- Last login date range

#### 5.2 Employee Detail/Edit View

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ Employee #5                              [Edit] [Deactivate] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ EMPLOYEE INFORMATION                                         │
│ Full Name: [John Smith________________]                      │
│ Email:     [john.smith@happyplace.com__]                     │
│ Role:      [Manager ▼]                                       │
│ Status:    [Active ▼]                                        │
│                                                              │
│ Created: Jan 1, 2025          Last Login: Dec 3, 2025      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ AUTHENTICATION                                              │
│ 2FA Enabled: Yes ✓             PIN Set: Yes ✓               │
│ Account Locked: No             Failed Logins: 0             │
│                                                              │
│ [Reset Password]  [Disable 2FA]  [Generate New PIN]        │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ PERMISSIONS                                                  │
│                                                              │
│ Role-based permissions (Manager):                           │
│ ✓ pos.create_sale          ✓ pos.void_transaction          │
│ ✓ shift.open               ✓ shift.close                   │
│ ✓ shift.view_all           ✓ inventory.view                │
│ ✓ inventory.update         ✓ inventory.transfer            │
│ ✓ customer.view            ✓ customer.edit                 │
│ ✓ reports.sales            ✓ reports.inventory             │
│ ✓ reports.employee         ✓ reports.financial             │
│ ✗ admin.employees          ✗ admin.roles                   │
│ ✗ admin.settings                                            │
│                                                              │
│ [View All Permissions]                                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ACTIVITY SUMMARY                                            │
│ Total POS Sales: KSh 450,000      Transactions: 235         │
│ Shifts Worked: 42                  Avg Shift Sales: KSh 10k │
│ Last Shift: Dec 3, 2025                                     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ RECENT ACTIVITY (Last 7 days)                              │
│ ● Dec 3, 10:00 AM - Opened shift #125                      │
│ ● Dec 3, 3:45 PM  - Processed sale KSh 3,200               │
│ ● Dec 3, 6:00 PM  - Closed shift #125                      │
│ ● Dec 2, 9:30 AM  - Updated inventory (SKU: WOM-TOP-001)   │
│                                                              │
│ [View Full Activity Log →]                                  │
└──────────────────────────────────────────────────────────────┘

[Save Changes]  [Cancel]
```

#### 5.3 Add New Employee

**Form:**
```
┌────────────────────────────────────────┐
│  Add New Employee                      │
├────────────────────────────────────────┤
│  Full Name: [___________________]      │
│  Email:     [___________________]      │
│                                        │
│  Role:      [Select Role ▼]           │
│             - Admin (Full Access)      │
│             - Manager (Most Access)    │
│             - Cashier (POS Only)       │
│             - Staff (View Only)        │
│                                        │
│  Initial Password:                     │
│  [Generate Random]  OR  [_________]    │
│                                        │
│  □ Send welcome email with login info │
│  □ Require password change on login   │
│  □ Enable 2FA immediately             │
│                                        │
│  [Cancel]  [Create Employee]          │
└────────────────────────────────────────┘
```

**API Endpoints:**
- `GET /api/admin/employees` - Employee list (NEW)
- `GET /api/admin/employees/:id` - Employee details (NEW)
- `POST /api/admin/employees` - Create employee (NEW)
- `PUT /api/admin/employees/:id` - Update employee (NEW)
- `DELETE /api/admin/employees/:id` - Deactivate employee (NEW)
- `POST /api/admin/employees/:id/reset-password` - Reset password (NEW)
- `POST /api/admin/employees/:id/disable-2fa` - Disable 2FA (NEW)
- `GET /api/admin/employees/:id/activity` - Employee activity log (NEW)
- `GET /api/admin/employees/:id/performance` - Performance metrics (NEW)

---

### 6. Promotions & Discounts

**Purpose:** Create and manage promotional campaigns

#### 6.1 Promotion List View

**Features:**
- Active/scheduled promotions
- Performance tracking
- Quick enable/disable
- Duplicate campaigns

**Table Columns:**
```
Name | Code | Type | Discount | Start Date | End Date | Status | Usage | Actions
```

**Status:**
- 🟢 Active (currently running)
- 🟡 Scheduled (future start date)
- 🔴 Expired (past end date)
- ⚫ Disabled (manually disabled)

#### 6.2 Create/Edit Promotion

**Form:**
```
┌──────────────────────────────────────────────────────────────┐
│ Create Promotion                                             │
├──────────────────────────────────────────────────────────────┤
│ BASIC INFORMATION                                            │
│ Name: [Black Friday Sale________________]                    │
│ Description: [Text area..................]                   │
│                                                              │
│ DISCOUNT DETAILS                                             │
│ Type: ● Percentage  ○ Fixed Amount                          │
│ Value: [20] %                                                │
│                                                              │
│ CODE SETTINGS                                                │
│ Promo Code: [BLACKFRIDAY] [Generate Random]                 │
│ □ Case sensitive                                             │
│                                                              │
│ DURATION                                                     │
│ Start Date: [Nov 25, 2025 00:00] [📅]                       │
│ End Date:   [Nov 30, 2025 23:59] [📅]                       │
│                                                              │
│ USAGE LIMITS                                                 │
│ Max Uses Total:    [1000] (0 = unlimited)                   │
│ Max Per Customer:  [5] (0 = unlimited)                      │
│ Min Order Amount:  KSh [2000] (0 = no minimum)              │
│                                                              │
│ APPLICABLE TO                                                │
│ ○ All Products                                              │
│ ● Specific Categories: [Select Categories ▼]               │
│   ✓ Women's Clothing                                        │
│   ✓ Maternity Wear                                          │
│ ○ Specific Products: [Select Products ▼]                   │
│                                                              │
│ CHANNELS                                                     │
│ ✓ Online Store    ✓ POS (Physical Store)                   │
│                                                              │
│ [Cancel]  [Save as Draft]  [Activate Promotion]            │
└──────────────────────────────────────────────────────────────┘
```

#### 6.3 Promotion Analytics

**View:**
```
┌──────────────────────────────────────────────────────────────┐
│ Black Friday Sale - Analytics                                │
├──────────────────────────────────────────────────────────────┤
│ Status: Active (2 days remaining)                            │
│                                                              │
│ USAGE STATISTICS                                             │
│ Total Uses: 247 / 1000  (24.7%)                             │
│ Unique Customers: 203                                        │
│ Total Discount Given: KSh 124,500                           │
│ Revenue Generated: KSh 498,000                              │
│                                                              │
│ DAILY BREAKDOWN                                              │
│ Day 1 (Nov 25): 89 uses  → KSh 178,000                     │
│ Day 2 (Nov 26): 92 uses  → KSh 184,000                     │
│ Day 3 (Nov 27): 66 uses  → KSh 136,000                     │
│                                                              │
│ TOP PRODUCTS SOLD WITH PROMO                                │
│ 1. Women's Floral Top - 45 units                           │
│ 2. Maternity Dress - 38 units                              │
│ 3. Summer Pants - 32 units                                 │
│                                                              │
│ [Download Report (.csv)]  [Edit Promotion]  [Disable]       │
└──────────────────────────────────────────────────────────────┘
```

**API Endpoints:**
- `GET /api/admin/promotions` - Promotion list (NEW)
- `GET /api/admin/promotions/:id` - Promotion details (NEW)
- `POST /api/admin/promotions` - Create promotion (NEW)
- `PUT /api/admin/promotions/:id` - Update promotion (NEW)
- `DELETE /api/admin/promotions/:id` - Delete promotion (NEW)
- `POST /api/admin/promotions/:id/enable` - Enable promotion (NEW)
- `POST /api/admin/promotions/:id/disable` - Disable promotion (NEW)
- `GET /api/admin/promotions/:id/analytics` - Promotion analytics (NEW)
- `POST /api/admin/promotions/:id/duplicate` - Duplicate promotion (NEW)

---

### 7. Returns Management

**Purpose:** Process and track return requests

#### 7.1 Returns List View

**Features:**
- Pending return requests
- Filter by status, reason
- Quick approve/reject
- Track return shipments

**Table Columns:**
```
Return # | Order # | Customer | Date | Reason | Amount | Status | Actions
```

**Status:**
- 🟡 Pending (awaiting review)
- 🔵 Approved (awaiting item return)
- 🟢 Completed (refund processed)
- 🔴 Rejected

#### 7.2 Return Request Detail

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ Return Request #RET-20251203-001                             │
│ Status: Pending Review                  [Approve] [Reject]   │
├──────────────────────────────────────────────────────────────┤
│ ORIGINAL ORDER                                               │
│ Order #: ORD-20251201-015               Date: Dec 1, 2025   │
│ Customer: Jane Doe                      Email: jane@...      │
│                                                              │
│ RETURN REQUEST DETAILS                                       │
│ Requested: Dec 3, 2025                  Reason: Wrong Size   │
│ Customer Notes:                                              │
│ "Item arrived in correct size M but fits too small.         │
│  Would like to exchange for size L or get refund."          │
│                                                              │
│ ITEMS TO RETURN                                              │
│ [Img] Women's Floral Top                                    │
│       Size: M, Color: Black                                 │
│       Qty: 1 × KSh 1,500.00                                 │
│       Return Policy: Restocking Fee (10%) = KSh 150         │
│       Refund Amount: KSh 1,350.00                           │
│                                                              │
│ PHOTOS UPLOADED BY CUSTOMER                                  │
│ [Photo 1]  [Photo 2]  [Photo 3]                             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ADMIN DECISION                                               │
│ ○ Approve Return                                            │
│   Refund Method: [Original Payment ▼]                       │
│   Refund Amount: KSh [1,350.00] (with 10% fee)             │
│                                                              │
│ ○ Approve Exchange                                           │
│   Exchange For: [Select Product ▼]                          │
│   Size: [L ▼]  Color: [Black ▼]                            │
│                                                              │
│ ○ Reject Return                                              │
│   Reason: [Dropdown: Outside Return Window ▼]               │
│                                                              │
│ Internal Notes:                                              │
│ [Text area................................]                  │
│                                                              │
│ [Submit Decision]                                            │
└──────────────────────────────────────────────────────────────┘
```

**API Endpoints:**
- `GET /api/admin/returns` - Return requests list (NEW)
- `GET /api/admin/returns/:id` - Return details (NEW)
- `POST /api/admin/returns/:id/approve` - Approve return (NEW)
- `POST /api/admin/returns/:id/reject` - Reject return (NEW)
- `POST /api/admin/returns/:id/complete` - Mark as completed (NEW)

---

### 8. Reports & Analytics Preview

**Purpose:** Quick access to key business reports (detailed analytics in Phase 12)

**Available Reports:**

1. **Sales Report**
   - Daily/weekly/monthly revenue
   - Sales by channel (online vs POS)
   - Sales by category
   - Top selling products

2. **Inventory Report**
   - Stock valuation
   - Low stock items
   - Overstock items
   - Stock movement history

3. **Customer Report**
   - New customers (trend)
   - Customer lifetime value
   - Top customers by spend
   - Customer retention rate

4. **Employee Performance**
   - Sales per employee
   - Average transaction value
   - Shifts worked
   - Hours logged

**UI:**
```
┌────────────────────────────────────────┐
│  Reports                               │
├────────────────────────────────────────┤
│  [📊 Sales Report]                     │
│  [📦 Inventory Report]                 │
│  [👥 Customer Report]                  │
│  [👤 Employee Performance]             │
│                                        │
│  ℹ️ Full analytics dashboard coming   │
│     in Phase 12: Analytics & Reporting │
└────────────────────────────────────────┘
```

**API Endpoints:**
- `GET /api/admin/reports/sales` - Sales report (NEW)
- `GET /api/admin/reports/inventory` - Inventory report (NEW)
- `GET /api/admin/reports/customers` - Customer report (NEW)
- `GET /api/admin/reports/employees` - Employee performance (NEW)

---

### 9. System Settings

**Purpose:** Configure system-wide settings (Admin only)

**Sections:**

#### 9.1 Store Information
```
Store Name:     [Happy Place Boutique_______]
Business Email: [info@happyplace.com________]
Support Phone:  [+254-XXX-XXXXXX___________]
Website:        [www.happyplace.com_________]

Physical Store Address:
[123 Kimathi Street___________________]
[Nairobi, Kenya_______________________]
[00100____]
```

#### 9.2 Business Hours
```
Monday:    [9:00 AM ▼] to [6:00 PM ▼]  [ ] Closed
Tuesday:   [9:00 AM ▼] to [6:00 PM ▼]  [ ] Closed
Wednesday: [9:00 AM ▼] to [6:00 PM ▼]  [ ] Closed
Thursday:  [9:00 AM ▼] to [6:00 PM ▼]  [ ] Closed
Friday:    [9:00 AM ▼] to [6:00 PM ▼]  [ ] Closed
Saturday:  [9:00 AM ▼] to [4:00 PM ▼]  [ ] Closed
Sunday:    [Closed___] to [_______]     [✓] Closed
```

#### 9.3 Email Settings
```
SMTP Server:   [smtp.gmail.com____________]
SMTP Port:     [587_]
Email:         [noreply@happyplace.com____]
Password:      [••••••••••••]

[Test Email Configuration]
```

#### 9.4 Payment Settings
```
Cash on Delivery:  [✓] Enabled
M-Pesa:           [✓] Enabled  [Configure M-Pesa →]
Card Payments:    [ ] Disabled (Coming in Phase 13)
```

#### 9.5 Tax & Fees
```
VAT Rate:           [16] %
Restocking Fee:     [10] % (for returns)
```

#### 9.6 Return Policy Settings
```
Return Window:      [30] days
Restocking Fee:     [10] %

Items Not Returnable:
[✓] Clearance items (FINAL SALE)
[✓] Sale items (FINAL SALE)
[ ] Undergarments (health reasons)
```

#### 9.7 Currency Settings ✅ COMPLETED
```
Currency Code:     [KES - Kenyan Shilling (KSh) ▼]
                   Options:
                   - KES - Kenyan Shilling (KSh)
                   - USD - US Dollar ($)
                   - EUR - Euro (€)
                   - GBP - British Pound (£)
                   - TZS - Tanzanian Shilling (TSh)
                   - UGX - Ugandan Shilling (USh)

Currency Symbol:   [KSh]

Preview:           KSh 1,000.00

[Save Currency Settings]
```

**Features:**
- ✅ Change default currency from USD to Kenyan Shillings
- ✅ Support for 6 African and international currencies
- ✅ Live preview of currency formatting
- ✅ Auto-populates currency symbol based on code selection
- ✅ Public API endpoint for frontend currency display
- ✅ Currency settings cached in localStorage for performance

**API Endpoints:**
- `GET /api/admin/settings` - Get all settings (NEW)
- `PUT /api/admin/settings/store` - Update store info (NEW)
- `PUT /api/admin/settings/hours` - Update business hours (NEW)
- `PUT /api/admin/settings/email` - Update email config (NEW)
- `PUT /api/admin/settings/payments` - Update payment settings (NEW)
- `PUT /api/admin/settings/tax` - Update tax settings (NEW)
- `PUT /api/admin/settings/returns` - Update return policy (NEW)
- `GET /api/admin/settings/currency` - Get currency settings ✅ COMPLETED
- `PUT /api/admin/settings/currency` - Update currency settings ✅ COMPLETED
- `GET /api/settings/public` - Get public settings (no auth) ✅ COMPLETED

---

## 📊 DATABASE CHANGES

### New Tables (3)

#### 1. PROMOTIONS

```sql
CREATE TABLE promotions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) NOT NULL,     -- percentage, fixed_amount
    discount_value NUMERIC(10,2) NOT NULL,

    -- Duration
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,

    -- Usage limits
    max_uses INTEGER DEFAULT 0,              -- 0 = unlimited
    max_uses_per_customer INTEGER DEFAULT 0, -- 0 = unlimited
    min_order_amount NUMERIC(10,2) DEFAULT 0,
    current_uses INTEGER DEFAULT 0,

    -- Applicability
    applicable_to VARCHAR(20) DEFAULT 'all', -- all, categories, products
    applicable_ids TEXT,                     -- Comma-separated category/product IDs

    -- Channels
    enabled_online BOOLEAN DEFAULT TRUE,
    enabled_pos BOOLEAN DEFAULT TRUE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES employees(id),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_promotions_code ON promotions(code);
CREATE INDEX idx_promotions_active ON promotions(is_active);
CREATE INDEX idx_promotions_dates ON promotions(start_date, end_date);
```

#### 2. PROMOTION_USAGE

```sql
CREATE TABLE promotion_usage (
    id SERIAL PRIMARY KEY,
    promotion_id INTEGER NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id),
    pos_transaction_id INTEGER REFERENCES pos_transactions(id),
    customer_id INTEGER REFERENCES customers(id),

    discount_amount NUMERIC(10,2) NOT NULL,
    used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_promotion_usage_promotion ON promotion_usage(promotion_id);
CREATE INDEX idx_promotion_usage_customer ON promotion_usage(customer_id);
CREATE INDEX idx_promotion_usage_date ON promotion_usage(used_at);
```

#### 3. SYSTEM_SETTINGS

```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string',  -- string, integer, boolean, json
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by INTEGER REFERENCES employees(id)
);

CREATE INDEX idx_system_settings_key ON system_settings(setting_key);

-- Seed default settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
    ('store_name', 'Happy Place Boutique', 'string', 'Store name'),
    ('store_email', 'info@happyplace.com', 'string', 'Store email'),
    ('store_phone', '+254-XXX-XXXXXX', 'string', 'Store phone'),
    ('vat_rate', '16', 'integer', 'VAT rate percentage'),
    ('restocking_fee', '10', 'integer', 'Restocking fee percentage'),
    ('return_window_days', '30', 'integer', 'Return window in days'),
    ('low_stock_threshold', '10', 'integer', 'Low stock alert threshold'),
    ('smtp_server', 'smtp.gmail.com', 'string', 'SMTP server'),
    ('smtp_port', '587', 'string', 'SMTP port');
```

### Modified Tables (2)

#### 1. ORDERS - Add promotion tracking

```sql
ALTER TABLE orders
ADD COLUMN promotion_id INTEGER REFERENCES promotions(id),
ADD COLUMN discount_amount NUMERIC(10,2) DEFAULT 0,
ADD COLUMN discount_code VARCHAR(50);

CREATE INDEX idx_orders_promotion ON orders(promotion_id);
```

#### 2. POS_TRANSACTIONS - Add promotion tracking

```sql
ALTER TABLE pos_transactions
ADD COLUMN promotion_id INTEGER REFERENCES promotions(id),
ADD COLUMN discount_amount NUMERIC(10,2) DEFAULT 0,
ADD COLUMN discount_code VARCHAR(50);

CREATE INDEX idx_pos_transactions_promotion ON pos_transactions(promotion_id);
```

---

## 🔧 BACKEND IMPLEMENTATION

### Service Layer (New Services)

#### 1. AdminDashboardService (`services/admin_dashboard_service.py`)

**Methods:**
```python
class AdminDashboardService:
    def get_dashboard_metrics(self, date_range: str) -> dict:
        """Get key metrics for dashboard"""

    def get_recent_activity(self, limit: int = 20) -> list:
        """Get recent activity feed"""

    def get_critical_alerts(self) -> dict:
        """Get critical alerts requiring attention"""

    def get_sales_trends(self, period: str) -> dict:
        """Get sales trends for charts"""
```

#### 2. InventoryManagementService (`services/inventory_management_service.py`)

**Methods:**
```python
class InventoryManagementService:
    def get_inventory_list(self, filters: dict, page: int, per_page: int) -> dict:
        """Get paginated inventory with filters"""

    def get_product_details(self, product_id: int) -> dict:
        """Get complete product details with variants"""

    def update_product(self, product_id: int, data: dict) -> bool:
        """Update product information"""

    def bulk_update_stock(self, updates: list) -> dict:
        """Bulk update stock quantities"""

    def adjust_stock(self, variant_id: int, adjustment: dict) -> bool:
        """Adjust stock with reason tracking"""

    def transfer_stock(self, transfer_data: dict) -> bool:
        """Transfer stock between online and store"""

    def get_stock_history(self, variant_id: int, days: int = 30) -> list:
        """Get stock movement history"""

    def delete_product(self, product_id: int) -> bool:
        """Soft delete product (mark as inactive)"""
```

#### 3. OrderManagementService (`services/order_management_service.py`)

**Methods:**
```python
class OrderManagementService:
    def get_order_list(self, filters: dict, page: int, per_page: int) -> dict:
        """Get paginated order list with filters"""

    def get_order_details(self, order_id: int) -> dict:
        """Get complete order details"""

    def update_order_status(self, order_id: int, status: str, tracking: dict = None) -> bool:
        """Update order status and tracking info"""

    def cancel_order(self, order_id: int, reason: str, notify: bool = True) -> bool:
        """Cancel order with optional notification"""

    def process_refund(self, order_id: int, refund_data: dict) -> dict:
        """Process full or partial refund"""

    def add_order_note(self, order_id: int, note: str, employee_id: int) -> bool:
        """Add internal note to order"""

    def get_order_timeline(self, order_id: int) -> list:
        """Get order event timeline"""

    def notify_customer(self, order_id: int, notification_type: str) -> bool:
        """Send notification to customer"""
```

#### 4. CustomerManagementService (`services/customer_management_service.py`)

**Methods:**
```python
class CustomerManagementService:
    def get_customer_list(self, filters: dict, page: int, per_page: int) -> dict:
        """Get paginated customer list"""

    def get_customer_details(self, customer_id: int) -> dict:
        """Get complete customer profile"""

    def update_customer(self, customer_id: int, data: dict) -> bool:
        """Update customer information"""

    def get_customer_orders(self, customer_id: int, page: int = 1) -> dict:
        """Get customer order history"""

    def get_customer_activity(self, customer_id: int, days: int = 30) -> list:
        """Get customer activity log"""

    def export_customer_data(self, customer_id: int) -> dict:
        """Export all customer data (GDPR)"""

    def anonymize_customer(self, customer_id: int, reason: str) -> bool:
        """Anonymize customer account (GDPR)"""

    def delete_customer(self, customer_id: int) -> bool:
        """Delete customer account completely"""

    def get_consent_history(self, customer_id: int) -> list:
        """Get GDPR consent change history"""
```

#### 5. EmployeeManagementService (`services/employee_management_service.py`)

**Methods:**
```python
class EmployeeManagementService:
    def get_employee_list(self, filters: dict) -> list:
        """Get employee list with filters"""

    def get_employee_details(self, employee_id: int) -> dict:
        """Get employee profile and permissions"""

    def create_employee(self, data: dict) -> dict:
        """Create new employee account"""

    def update_employee(self, employee_id: int, data: dict) -> bool:
        """Update employee information"""

    def deactivate_employee(self, employee_id: int) -> bool:
        """Deactivate employee account"""

    def reset_employee_password(self, employee_id: int) -> str:
        """Reset password and return temp password"""

    def disable_employee_2fa(self, employee_id: int) -> bool:
        """Disable 2FA for employee"""

    def get_employee_activity(self, employee_id: int, days: int = 7) -> list:
        """Get employee activity log"""

    def get_employee_performance(self, employee_id: int, period: str) -> dict:
        """Get employee performance metrics"""
```

#### 6. PromotionService (`services/promotion_service.py`)

**Methods:**
```python
class PromotionService:
    def get_promotion_list(self, filters: dict) -> list:
        """Get promotions with filters"""

    def get_promotion_details(self, promotion_id: int) -> dict:
        """Get promotion details"""

    def create_promotion(self, data: dict, created_by: int) -> dict:
        """Create new promotion"""

    def update_promotion(self, promotion_id: int, data: dict) -> bool:
        """Update promotion"""

    def delete_promotion(self, promotion_id: int) -> bool:
        """Delete promotion"""

    def enable_promotion(self, promotion_id: int) -> bool:
        """Enable promotion"""

    def disable_promotion(self, promotion_id: int) -> bool:
        """Disable promotion"""

    def validate_promotion(self, code: str, order_total: float, customer_id: int) -> dict:
        """Validate promotion code and return discount"""

    def apply_promotion(self, promotion_id: int, order_id: int = None,
                       pos_transaction_id: int = None, customer_id: int = None) -> bool:
        """Record promotion usage"""

    def get_promotion_analytics(self, promotion_id: int) -> dict:
        """Get promotion usage analytics"""

    def duplicate_promotion(self, promotion_id: int) -> dict:
        """Duplicate existing promotion"""
```

#### 7. ReportService (`services/report_service.py`)

**Methods:**
```python
class ReportService:
    def get_sales_report(self, start_date: date, end_date: date, filters: dict) -> dict:
        """Generate sales report"""

    def get_inventory_report(self, filters: dict) -> dict:
        """Generate inventory report"""

    def get_customer_report(self, period: str) -> dict:
        """Generate customer report"""

    def get_employee_performance_report(self, employee_id: int = None, period: str = 'month') -> dict:
        """Generate employee performance report"""
```

#### 8. SettingsService (`services/settings_service.py`)

**Methods:**
```python
class SettingsService:
    def get_all_settings(self) -> dict:
        """Get all system settings"""

    def get_setting(self, key: str) -> any:
        """Get single setting value"""

    def update_setting(self, key: str, value: any, updated_by: int) -> bool:
        """Update single setting"""

    def update_settings_bulk(self, settings: dict, updated_by: int) -> bool:
        """Update multiple settings"""
```

---

## 🎨 FRONTEND IMPLEMENTATION

### Page Structure

```
/admin
├── /dashboard              (Dashboard Overview)
├── /inventory              (Inventory List)
│   ├── /new                (Add New Product)
│   └── /:id                (Product Detail/Edit)
├── /orders                 (Order List)
│   └── /:id                (Order Detail)
├── /customers              (Customer List)
│   └── /:id                (Customer Detail)
├── /employees              (Employee List)
│   ├── /new                (Add New Employee)
│   └── /:id                (Employee Detail)
├── /promotions             (Promotion List)
│   ├── /new                (Create Promotion)
│   └── /:id                (Promotion Detail/Edit)
├── /returns                (Returns Management)
│   └── /:id                (Return Detail)
├── /reports                (Reports Menu)
│   ├── /sales              (Sales Report)
│   ├── /inventory          (Inventory Report)
│   ├── /customers          (Customer Report)
│   └── /employees          (Employee Performance)
└── /settings               (System Settings - Admin Only)
```

### Component Hierarchy

```
AdminLayout
├── AdminSidebar
│   ├── NavigationMenu
│   └── UserProfile
├── AdminHeader
│   ├── Breadcrumbs
│   ├── SearchBar
│   └── NotificationBell
└── MainContent
    ├── DashboardOverview
    │   ├── MetricsCards
    │   ├── SalesTrendChart
    │   ├── AlertsPanel
    │   ├── RecentActivityFeed
    │   └── QuickActionsPanel
    ├── InventoryManagement
    │   ├── InventoryList
    │   │   ├── DataTable
    │   │   ├── Filters
    │   │   └── BulkActions
    │   ├── ProductDetail
    │   │   ├── ProductForm
    │   │   ├── VariantsManager
    │   │   ├── ImageUploader
    │   │   └── StockHistoryTable
    │   └── StockAdjustmentModal
    ├── OrderManagement
    │   ├── OrderList
    │   │   ├── DataTable
    │   │   ├── Filters
    │   │   └── StatusBadges
    │   ├── OrderDetail
    │   │   ├── OrderSummary
    │   │   ├── CustomerInfo
    │   │   ├── OrderItems
    │   │   ├── OrderTimeline
    │   │   └── OrderActions
    │   └── CancelOrderModal
    ├── CustomerManagement
    │   ├── CustomerList
    │   │   ├── DataTable
    │   │   └── Filters
    │   ├── CustomerDetail
    │   │   ├── CustomerProfile
    │   │   ├── OrderHistory
    │   │   ├── ActivityLog
    │   │   └── GDPRActions
    │   └── AnonymizeModal
    ├── EmployeeManagement
    │   ├── EmployeeList
    │   ├── EmployeeDetail
    │   │   ├── EmployeeForm
    │   │   ├── PermissionsPanel
    │   │   ├── ActivitySummary
    │   │   └── PerformanceMetrics
    │   └── AddEmployeeModal
    ├── PromotionManagement
    │   ├── PromotionList
    │   ├── PromotionForm
    │   └── PromotionAnalytics
    ├── ReturnsManagement
    │   ├── ReturnsList
    │   └── ReturnDetail
    │       ├── ReturnInfo
    │       ├── CustomerPhotos
    │       └── DecisionForm
    ├── Reports
    │   ├── SalesReport
    │   ├── InventoryReport
    │   ├── CustomerReport
    │   └── EmployeeReport
    └── Settings
        ├── StoreInfoForm
        ├── BusinessHoursForm
        ├── EmailSettingsForm
        ├── PaymentSettingsForm
        └── ReturnPolicyForm
```

### Shared Components

**DataTable Component:**
```jsx
<DataTable
  columns={columns}
  data={data}
  filters={filters}
  onFilterChange={handleFilterChange}
  pagination={pagination}
  onPageChange={handlePageChange}
  sortable
  selectable
  bulkActions={bulkActions}
/>
```

**MetricCard Component:**
```jsx
<MetricCard
  title="Today's Sales"
  value="KSh 125,450"
  change="+12%"
  trend="up"
  icon={<DollarIcon />}
/>
```

**AlertBanner Component:**
```jsx
<AlertBanner
  type="critical"  // critical, warning, info
  title="8 items out of stock"
  message="Some products need restocking immediately"
  action={{ label: "View Items", link: "/admin/inventory?filter=out-of-stock" }}
/>
```

**StatusBadge Component:**
```jsx
<StatusBadge
  status="processing"  // pending, processing, completed, cancelled
  label="Processing"
/>
```

---

## 📋 API ENDPOINTS SUMMARY

### Total New Endpoints: 58

#### Dashboard (4)
- `GET /api/admin/dashboard` - Main dashboard (EXISTING)
- `GET /api/admin/dashboard/metrics` - Real-time metrics
- `GET /api/admin/dashboard/activity` - Activity feed
- `GET /api/admin/dashboard/alerts` - Critical alerts

#### Inventory (9)
- `GET /api/admin/inventory` - Inventory list
- `GET /api/admin/inventory/:id` - Product details
- `PUT /api/admin/inventory/:id` - Update product
- `POST /api/admin/inventory/bulk-update` - Bulk update
- `POST /api/admin/inventory/adjust` - Stock adjustment
- `POST /api/admin/inventory/transfer` - Stock transfer
- `GET /api/admin/inventory/:id/history` - Stock history
- `DELETE /api/admin/inventory/:id` - Delete product
- `GET /api/admin/inventory/alerts` - Low stock (EXISTING)

#### Orders (8)
- `GET /api/admin/orders` - Order list
- `GET /api/admin/orders/:id` - Order details
- `PUT /api/admin/orders/:id/status` - Update status
- `POST /api/admin/orders/:id/cancel` - Cancel order
- `POST /api/admin/orders/:id/refund` - Process refund
- `POST /api/admin/orders/:id/notes` - Add note
- `GET /api/admin/orders/:id/timeline` - Timeline
- `POST /api/admin/orders/:id/notify` - Notify customer

#### Customers (9)
- `GET /api/admin/customers` - Customer list
- `GET /api/admin/customers/:id` - Customer details
- `PUT /api/admin/customers/:id` - Update customer
- `DELETE /api/admin/customers/:id` - Delete customer
- `GET /api/admin/customers/:id/orders` - Customer orders
- `GET /api/admin/customers/:id/activity` - Activity log
- `POST /api/admin/customers/:id/export` - Export data (GDPR)
- `POST /api/admin/customers/:id/anonymize` - Anonymize (GDPR)
- `GET /api/admin/customers/:id/consent-history` - Consent log

#### Employees (9)
- `GET /api/admin/employees` - Employee list
- `GET /api/admin/employees/:id` - Employee details
- `POST /api/admin/employees` - Create employee
- `PUT /api/admin/employees/:id` - Update employee
- `DELETE /api/admin/employees/:id` - Deactivate
- `POST /api/admin/employees/:id/reset-password` - Reset password
- `POST /api/admin/employees/:id/disable-2fa` - Disable 2FA
- `GET /api/admin/employees/:id/activity` - Activity log
- `GET /api/admin/employees/:id/performance` - Performance metrics

#### Promotions (9)
- `GET /api/admin/promotions` - Promotion list
- `GET /api/admin/promotions/:id` - Promotion details
- `POST /api/admin/promotions` - Create promotion
- `PUT /api/admin/promotions/:id` - Update promotion
- `DELETE /api/admin/promotions/:id` - Delete promotion
- `POST /api/admin/promotions/:id/enable` - Enable
- `POST /api/admin/promotions/:id/disable` - Disable
- `GET /api/admin/promotions/:id/analytics` - Analytics
- `POST /api/admin/promotions/:id/duplicate` - Duplicate

#### Returns (5)
- `GET /api/admin/returns` - Returns list
- `GET /api/admin/returns/:id` - Return details
- `POST /api/admin/returns/:id/approve` - Approve return
- `POST /api/admin/returns/:id/reject` - Reject return
- `POST /api/admin/returns/:id/complete` - Mark completed

#### Reports (4)
- `GET /api/admin/reports/sales` - Sales report
- `GET /api/admin/reports/inventory` - Inventory report
- `GET /api/admin/reports/customers` - Customer report
- `GET /api/admin/reports/employees` - Employee report

#### Settings (8)
- `GET /api/admin/settings` - All settings
- `PUT /api/admin/settings/store` - Store info
- `PUT /api/admin/settings/hours` - Business hours
- `PUT /api/admin/settings/email` - Email config
- `PUT /api/admin/settings/payments` - Payment settings
- `PUT /api/admin/settings/tax` - Tax settings
- `PUT /api/admin/settings/returns` - Return policy
- `POST /api/admin/settings/test-email` - Test email

---

## 🗓️ IMPLEMENTATION TIMELINE

### Week 1: Backend Foundation (40 hours)

#### Day 1-2: Database & Core Services (16 hours)
- Create migration 008 (3 new tables, 2 modified)
- Implement PromotionService
- Implement SettingsService
- Implement AdminDashboardService enhancements
- Write unit tests for services

#### Day 3-4: Management Services (16 hours)
- Implement InventoryManagementService
- Implement OrderManagementService
- Implement CustomerManagementService
- Write unit tests

#### Day 5: Employee & Report Services (8 hours)
- Implement EmployeeManagementService
- Implement ReportService
- Integration tests for all services

### Week 2: API Routes & Frontend (40 hours)

#### Day 6-7: API Routes (16 hours)
- Create all 58 API endpoints
- Add permission checks (@manager_required, @admin_required)
- API integration tests
- API documentation

#### Day 8-9: Frontend Core (16 hours)
- AdminLayout with sidebar navigation
- Dashboard Overview page
- Inventory Management pages
- Order Management pages

#### Day 10: Frontend Final & Testing (8 hours)
- Customer Management pages
- Employee Management pages
- Promotion Management pages
- Settings page
- End-to-end testing
- Bug fixes and polish

---

## ✅ TESTING STRATEGY

### Unit Tests (Backend)

**Service Tests:**
```python
# test_admin_dashboard_service.py
def test_get_dashboard_metrics()
def test_get_recent_activity()
def test_get_critical_alerts()

# test_inventory_management_service.py
def test_get_inventory_list_with_filters()
def test_bulk_update_stock()
def test_adjust_stock()
def test_transfer_stock()

# test_order_management_service.py
def test_update_order_status()
def test_cancel_order()
def test_process_refund()

# test_customer_management_service.py
def test_export_customer_data()
def test_anonymize_customer()

# test_promotion_service.py
def test_validate_promotion()
def test_apply_promotion()
def test_get_promotion_analytics()
```

### Integration Tests (API)

```python
# test_admin_api.py
def test_dashboard_access_requires_manager_role()
def test_get_inventory_list_pagination()
def test_update_order_status_creates_timeline_event()
def test_bulk_stock_update()
def test_apply_promotion_to_order()
def test_anonymize_customer_gdpr_compliance()
```

### E2E Tests (Frontend)

```javascript
// admin-dashboard.spec.js
describe('Admin Dashboard', () => {
  it('should display key metrics', () => {})
  it('should show low stock alerts', () => {})
  it('should filter recent orders', () => {})
})

// inventory-management.spec.js
describe('Inventory Management', () => {
  it('should filter products by category', () => {})
  it('should update stock quantity', () => {})
  it('should transfer stock between locations', () => {})
})

// order-management.spec.js
describe('Order Management', () => {
  it('should update order status', () => {})
  it('should cancel order with reason', () => {})
  it('should process full refund', () => {})
})
```

### Manual Testing Checklist

**Dashboard:**
- [ ] Metrics cards display correct data
- [ ] Alerts update in real-time
- [ ] Activity feed shows recent events
- [ ] Quick actions work correctly

**Inventory:**
- [ ] Product list loads with pagination
- [ ] Filters work (category, status, stock level)
- [ ] Bulk stock update processes multiple items
- [ ] Stock transfer between online/store works
- [ ] Low stock alerts appear correctly

**Orders:**
- [ ] Order list filters work (status, date, payment)
- [ ] Order detail shows complete information
- [ ] Status update triggers email notification
- [ ] Cancel order refunds payment
- [ ] Timeline shows all events

**Customers:**
- [ ] Customer search works
- [ ] Customer detail shows order history
- [ ] GDPR export generates correct JSON
- [ ] Anonymize removes all PII correctly

**Employees:**
- [ ] Create employee sends welcome email
- [ ] Permission matrix displays correctly
- [ ] Reset password generates temp password
- [ ] Deactivate prevents login

**Promotions:**
- [ ] Create promotion with date range
- [ ] Validate code at checkout
- [ ] Analytics show correct usage stats
- [ ] Expired promotions don't apply

**Settings:**
- [ ] Update store info persists
- [ ] Email test sends correctly
- [ ] Business hours save properly

---

## 🚀 DEPLOYMENT PLAN

### Pre-Deployment

1. **Database Backup**
   ```bash
   PGPASSWORD='password' pg_dump -U postgres happy_place_db > backup_pre_phase11.sql
   ```

2. **Run Migration**
   ```bash
   cd backend/migrations
   psql -U postgres -d happy_place_db -f 008_admin_dashboard.sql
   ```

3. **Verify Migration**
   ```sql
   -- Check new tables exist
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public'
   AND table_name IN ('promotions', 'promotion_usage', 'system_settings');

   -- Check columns added
   SELECT column_name FROM information_schema.columns
   WHERE table_name = 'orders' AND column_name = 'promotion_id';
   ```

### Deployment Steps

1. **Backend Deployment**
   ```bash
   cd backend
   git pull origin main
   pip install -r requirements.txt
   sudo systemctl restart happy_place_backend
   ```

2. **Frontend Deployment**
   ```bash
   cd frontend
   git pull origin main
   npm install
   npm run build
   sudo cp -r build/* /var/www/html/
   ```

3. **Verify Services**
   ```bash
   # Check backend is running
   curl http://localhost:5001/api/admin/dashboard

   # Check frontend is accessible
   curl http://localhost:3000/admin
   ```

### Post-Deployment

1. **Smoke Tests**
   - Login as admin
   - Access dashboard
   - Create test promotion
   - Update inventory
   - Process test order

2. **Monitor Logs**
   ```bash
   tail -f /var/log/happy_place/backend.log
   tail -f /var/log/happy_place/frontend.log
   ```

3. **Train Staff**
   - Provide admin dashboard walkthrough
   - Document common workflows
   - Answer questions

---

## 💰 BUDGET BREAKDOWN

| Task | Hours | Cost @ $50/hr |
|------|-------|---------------|
| Database migration + models | 8 | $400 |
| Service layer (8 services) | 24 | $1,200 |
| API routes (58 endpoints) | 16 | $800 |
| Frontend pages (9 sections) | 20 | $1,000 |
| Testing (unit + integration + E2E) | 8 | $400 |
| Documentation | 4 | $200 |
| **Total** | **80 hours** | **$4,000** |

---

## 📊 SUCCESS METRICS

### Performance Metrics

**After 1 Month:**
- Admin dashboard loads in <2 seconds
- Inventory search returns results in <500ms
- Order updates process in <1 second
- 90% reduction in manual CSV exports
- 50% reduction in customer support tickets (better order management)

**After 3 Months:**
- 40% reduction in time spent on inventory management
- 30% faster order processing time
- 25% reduction in stockouts (better alerts)
- 100% of staff using admin dashboard daily
- ROI achieved (time savings justify development cost)

### Usage Metrics

Track in analytics:
- Daily active admin users
- Most used features
- Average time per task (inventory update, order processing)
- Number of promotions created
- Number of GDPR requests processed

---

## 🔐 SECURITY CONSIDERATIONS

### Access Control

- All admin endpoints require authentication (@jwt_required)
- Manager/Admin role required (@manager_required, @admin_required)
- Permission checks for sensitive operations
- Audit logging for all admin actions

### Data Protection

- GDPR compliance tools (export, anonymize)
- Encrypted customer PII display
- Masked payment information
- Secure password reset process

### Input Validation

- Validate all form inputs (frontend + backend)
- Sanitize user-generated content
- Prevent SQL injection (use parameterized queries)
- Rate limiting on API endpoints

---

## 📚 DOCUMENTATION

### For Developers

1. **API Documentation**
   - Endpoint reference guide
   - Request/response examples
   - Authentication requirements
   - Error codes

2. **Service Documentation**
   - Method signatures
   - Parameter descriptions
   - Return types
   - Usage examples

### For Administrators

1. **User Guide**
   - Dashboard overview
   - Managing inventory
   - Processing orders
   - Managing customers
   - Creating promotions
   - System settings

2. **Video Tutorials**
   - 5-minute dashboard tour
   - How to update inventory
   - How to process returns
   - How to create promotions

---

## 🔄 FUTURE ENHANCEMENTS (Post Phase 11)

### Phase 12: Analytics & Reporting
- Advanced charts and visualizations
- Custom report builder
- Scheduled email reports
- KPI dashboards
- Predictive analytics

### Phase 13: M-Pesa Integration
- M-Pesa payment tracking in admin
- Refund processing via M-Pesa
- Reconciliation reports

### Phase 14: Advanced Features
- Multi-store management
- Franchise system
- Advanced inventory forecasting
- Automated reorder points
- Supplier management

---

## ✍️ SIGN-OFF

### Review & Approval

**Prepared By:** Development Team
**Date:** December 3, 2025

**Reviewed By:**

- [ ] **Business Owner** - Approve business requirements
  Name: ________________  Date: ________  Signature: ________

- [ ] **Technical Lead** - Approve technical approach
  Name: ________________  Date: ________  Signature: ________

- [ ] **Project Manager** - Approve timeline and budget
  Name: ________________  Date: ________  Signature: ________

**Approved for Implementation:** [ ] Yes  [ ] No

**Comments/Feedback:**
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## 📞 SUPPORT

For questions or issues during implementation:
- **Technical:** dev@happyplace.com
- **Business:** manager@happyplace.com
- **Emergency:** +254-XXX-XXXXXX

---

**END OF DOCUMENT**

*This plan is ready for review and approval to proceed with Phase 11 implementation.*
