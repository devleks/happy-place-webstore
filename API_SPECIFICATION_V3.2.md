# Happy Place Boutique - API Specification V3.2

**Date:** November 23, 2025
**Version:** 3.2
**Database Schema:** 29 tables (22 core + 7 extended)

---

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Product Variants API](#product-variants-api)
3. [Promotions API](#promotions-api)
4. [Returns & Refunds API](#returns--refunds-api)
5. [Shipping Methods API](#shipping-methods-api)
6. [Category Hierarchy API](#category-hierarchy-api)
7. [Updated Endpoints](#updated-endpoints)
8. [Admin API](#admin-api)
9. [Error Handling](#error-handling)
10. [Business Rules Validation](#business-rules-validation)

---

## Authentication & Authorization

### Overview
The system now has **two separate user types**:
- **Customers** - Online shoppers (GDPR-compliant, encrypted PII)
- **Employees** - System users (admin, manager, cashier, staff)

### Authentication Endpoints

#### 1. Customer Registration
```http
POST /api/auth/customer/register
```

**Request:**
```json
{
  "email": "jane@example.com",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone": "+254712345678",
  "gdpr_consent": true,
  "marketing_consent": false
}
```

**Response (201 Created):**
```json
{
  "message": "Customer registered successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "customer": {
    "id": 1,
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone": "+254712345678",
    "gdpr_consent": true,
    "marketing_consent": false,
    "is_active": true,
    "created_at": "2025-11-23T10:00:00Z"
  }
}
```

**Business Rules:**
- Email must be unique
- Password minimum 8 characters
- GDPR consent required (must be true)
- First name and last name required
- Phone is optional
- All PII fields are encrypted in database

---

#### 2. Customer Login
```http
POST /api/auth/customer/login
```

**Request:**
```json
{
  "email": "jane@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "customer": {
    "id": 1,
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "is_active": true
  }
}
```

**Error (401 Unauthorized):**
```json
{
  "error": "Invalid email or password"
}
```

---

#### 3. Employee Login
```http
POST /api/auth/employee/login
```

**Request:**
```json
{
  "email": "admin@happyplace.com",
  "password": "AdminPass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "employee": {
    "id": 1,
    "email": "admin@happyplace.com",
    "full_name": "Admin User",
    "role": "admin",
    "is_active": true
  }
}
```

**Roles:**
- `admin` - Full system access
- `manager` - Product, inventory, order management
- `cashier` - POS transactions only
- `staff` - Limited read access

---

#### 4. Get Current User (Customer)
```http
GET /api/auth/customer/me
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone": "+254712345678",
  "gdpr_consent": true,
  "marketing_consent": false,
  "is_active": true,
  "email_verified": true,
  "created_at": "2025-11-23T10:00:00Z"
}
```

---

## Product Variants API

### Overview
Product variants represent size/color combinations with unique SKUs. Each variant has one-to-one relationship with inventory.

---

### 1. Get Product Variants
```http
GET /api/products/{product_id}/variants
```

**Response (200 OK):**
```json
{
  "product_id": 5,
  "product_name": "Floral Maternity Dress",
  "variants": [
    {
      "id": 1,
      "sku": "FMD-S-BLUE",
      "size": "S",
      "color": "Blue",
      "is_active": true,
      "inventory": {
        "quantity": 15,
        "reserved_quantity": 2,
        "available_quantity": 13,
        "is_low_stock": false,
        "is_out_of_stock": false
      }
    },
    {
      "id": 2,
      "sku": "FMD-M-BLUE",
      "size": "M",
      "color": "Blue",
      "is_active": true,
      "inventory": {
        "quantity": 8,
        "reserved_quantity": 1,
        "available_quantity": 7,
        "is_low_stock": true,
        "is_out_of_stock": false
      }
    }
  ]
}
```

---

### 2. Create Product Variant (Admin Only)
```http
POST /api/products/{product_id}/variants
Authorization: Bearer {admin_token}
```

**Request:**
```json
{
  "sku": "FMD-L-BLUE",
  "size": "L",
  "color": "Blue",
  "initial_quantity": 20
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "product_id": 5,
  "sku": "FMD-L-BLUE",
  "size": "L",
  "color": "Blue",
  "is_active": true,
  "created_at": "2025-11-23T12:00:00Z",
  "inventory": {
    "quantity": 20,
    "available_quantity": 20,
    "is_low_stock": false
  }
}
```

**Business Rules:**
- SKU must be unique
- Size and color are required
- Automatically creates inventory record
- Only admin/manager can create variants

---

### 3. Update Variant Inventory (Admin Only)
```http
PATCH /api/variants/{variant_id}/inventory
Authorization: Bearer {admin_token}
```

**Request:**
```json
{
  "quantity": 25,
  "action": "set"
}
```

**Actions:**
- `set` - Set to exact quantity
- `add` - Add to current quantity
- `subtract` - Subtract from current quantity

**Response (200 OK):**
```json
{
  "variant_id": 3,
  "sku": "FMD-L-BLUE",
  "previous_quantity": 20,
  "new_quantity": 25,
  "available_quantity": 25,
  "updated_at": "2025-11-23T12:30:00Z"
}
```

---

### 4. Check Variant Availability
```http
GET /api/variants/{variant_id}/availability
```

**Response (200 OK):**
```json
{
  "variant_id": 1,
  "sku": "FMD-S-BLUE",
  "size": "S",
  "color": "Blue",
  "available": true,
  "quantity": 15,
  "reserved_quantity": 2,
  "available_quantity": 13,
  "is_low_stock": false,
  "is_out_of_stock": false,
  "can_purchase": true
}
```

---

## Promotions API

### Overview
Promotions support discount codes, percentage discounts, fixed amount discounts, and free shipping.

---

### 1. Validate Promotion Code
```http
POST /api/promotions/validate
```

**Request:**
```json
{
  "code": "REFER5",
  "customer_id": 1,
  "order_total": 5000,
  "category_id": 1
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "promotion": {
    "id": 1,
    "code": "REFER5",
    "name": "Referral Discount",
    "description": "5% discount for referrals",
    "discount_type": "percentage",
    "discount_value": 5.0,
    "applies_to": "all",
    "minimum_order_amount": null,
    "maximum_discount_amount": null
  },
  "discount_amount": 250.0,
  "final_total": 4750.0,
  "message": "Promotion applied successfully"
}
```

**Business Rules:**
- Check if code is active
- Verify start_date and end_date
- Check usage_limit and usage_per_customer
- Validate minimum_order_amount
- Apply maximum_discount_amount cap
- Verify category/product restrictions

**Error (400 Bad Request) - Invalid Code:**
```json
{
  "valid": false,
  "error": "Promotion code not found or expired"
}
```

**Error (400 Bad Request) - Already Used:**
```json
{
  "valid": false,
  "error": "You have already used this promotion code"
}
```

**Error (400 Bad Request) - Minimum Not Met:**
```json
{
  "valid": false,
  "error": "Minimum order amount of KSh 2000 required",
  "minimum_required": 2000,
  "current_total": 1500
}
```

---

### 2. Apply Promotion to Order
```http
POST /api/orders/{order_id}/promotions
Authorization: Bearer {customer_token}
```

**Request:**
```json
{
  "promotion_code": "WELCOME10"
}
```

**Response (200 OK):**
```json
{
  "order_id": 42,
  "promotion_applied": {
    "code": "WELCOME10",
    "discount_amount": 500.0
  },
  "order_totals": {
    "subtotal": 5500.0,
    "promotion_discount": 500.0,
    "shipping_cost": 0.0,
    "tax": 0.0,
    "total": 5000.0
  }
}
```

**Business Rules:**
- Only one promotion per order
- Promotion is recorded in order_promotions table
- Discount amount is frozen at time of application
- Usage count is incremented

---

### 3. Get Active Promotions (Public)
```http
GET /api/promotions/active
```

**Response (200 OK):**
```json
{
  "promotions": [
    {
      "code": "REFER5",
      "name": "Referral Discount",
      "description": "5% discount for referrals",
      "discount_type": "percentage",
      "discount_value": 5.0,
      "minimum_order_amount": null,
      "end_date": "2026-11-23T00:00:00Z"
    },
    {
      "code": "WELCOME10",
      "name": "Welcome Discount",
      "description": "10% off your first purchase",
      "discount_type": "percentage",
      "discount_value": 10.0,
      "maximum_discount_amount": 500.0,
      "minimum_order_amount": null
    }
  ]
}
```

---

## Returns & Refunds API

### Overview
Returns follow a 2-day window policy with 10% restocking fee for regular-priced items only. **Clearance and sale items are FINAL SALE - no returns and no exchanges allowed.**

---

### 1. Check Return Eligibility
```http
GET /api/orders/{order_id}/return-eligibility
Authorization: Bearer {customer_token}
```

**Response (200 OK) - Eligible:**
```json
{
  "order_id": 42,
  "order_number": "ORD-2025-00042",
  "delivered_at": "2025-11-21T14:30:00Z",
  "eligible": true,
  "return_deadline": "2025-11-23T14:30:00Z",
  "hours_remaining": 12,
  "items": [
    {
      "order_item_id": 1,
      "product_name": "Floral Maternity Dress",
      "variant": "M / Blue",
      "quantity": 1,
      "unit_price": 3500.0,
      "can_return": true,
      "return_type": "refund",
      "message": "Full refund available (minus 10% restocking fee)"
    },
    {
      "order_item_id": 2,
      "product_name": "Summer Clearance Top",
      "variant": "S / Red",
      "quantity": 1,
      "unit_price": 1200.0,
      "can_return": false,
      "return_type": "final_sale",
      "message": "Clearance items are FINAL SALE - no returns or exchanges"
    }
  ]
}
```

**Response (200 OK) - Not Eligible:**
```json
{
  "order_id": 42,
  "eligible": false,
  "reason": "Return window expired",
  "delivered_at": "2025-11-15T10:00:00Z",
  "return_deadline": "2025-11-17T10:00:00Z",
  "days_since_deadline": 6
}
```

**Business Rules:**
- 2-day return window from delivery date
- **Clearance items: FINAL SALE - no returns, no exchanges**
- **Sale items: FINAL SALE - no returns, no exchanges**
- Regular-priced items only: full return with 10% restocking fee

---

### 2. Create Return Request
```http
POST /api/returns
Authorization: Bearer {customer_token}
```

**Request:**
```json
{
  "order_id": 42,
  "reason": "wrong_size",
  "reason_description": "Item too small, need larger size",
  "items": [
    {
      "order_item_id": 1,
      "quantity_returned": 1,
      "condition": "new_with_tags"
    }
  ],
  "refund_method": "original_payment"
}
```

**Reasons:**
- `wrong_size`
- `wrong_color`
- `defective`
- `not_as_described`
- `changed_mind`
- `other`

**Conditions:**
- `new_with_tags`
- `new_without_tags`
- `gently_used`
- `defective`

**Refund Methods:**
- `original_payment` - Refund to M-Pesa/payment method
- `store_credit` - Store credit for future purchase
- `exchange` - Exchange for different size/color

**Response (201 Created):**
```json
{
  "return_id": 1,
  "return_number": "RMA-2025-001",
  "order_id": 42,
  "status": "pending",
  "items": [
    {
      "product_name": "Floral Maternity Dress",
      "variant": "M / Blue",
      "quantity_returned": 1,
      "item_value": 3500.0
    }
  ],
  "totals": {
    "total_return_value": 3500.0,
    "restocking_fee": 350.0,
    "refund_amount": 3150.0
  },
  "refund_method": "original_payment",
  "created_at": "2025-11-23T15:00:00Z",
  "instructions": "Please ship items to: Happy Place Boutique, Store No. 22, 1st Floor, Bethel Business Centre, Langata Rd, Nairobi"
}
```

**Business Rules:**
- 10% restocking fee applied
- Return window must be valid
- Items must be eligible for return
- Partial returns allowed

---

### 3. Get Return Status
```http
GET /api/returns/{return_id}
Authorization: Bearer {customer_token}
```

**Response (200 OK):**
```json
{
  "return_id": 1,
  "return_number": "RMA-2025-001",
  "order_number": "ORD-2025-00042",
  "status": "approved",
  "items": [...],
  "totals": {
    "total_return_value": 3500.0,
    "restocking_fee": 350.0,
    "refund_amount": 3150.0
  },
  "refund_method": "original_payment",
  "created_at": "2025-11-23T15:00:00Z",
  "approved_at": "2025-11-23T16:00:00Z",
  "timeline": [
    {
      "status": "pending",
      "timestamp": "2025-11-23T15:00:00Z"
    },
    {
      "status": "approved",
      "timestamp": "2025-11-23T16:00:00Z"
    }
  ]
}
```

**Return Statuses:**
- `pending` - Awaiting approval
- `approved` - Approved, awaiting item receipt
- `received` - Items received and inspected
- `refunded` - Refund processed
- `rejected` - Return rejected
- `cancelled` - Customer cancelled

---

### 4. Admin: Process Return (Admin Only)
```http
PATCH /api/returns/{return_id}/status
Authorization: Bearer {admin_token}
```

**Request:**
```json
{
  "status": "approved",
  "notes": "Return approved. Customer to ship items back."
}
```

**Response (200 OK):**
```json
{
  "return_id": 1,
  "status": "approved",
  "updated_at": "2025-11-23T16:00:00Z",
  "message": "Return status updated successfully"
}
```

---

## Shipping Methods API

### Overview
Shipping costs vary by location: Nairobi is always free, upcountry has variable costs.

---

### 1. Get Available Shipping Methods
```http
GET /api/shipping/methods?is_nairobi=true
```

**Query Parameters:**
- `is_nairobi` (boolean) - Whether delivery is to Nairobi

**Response (200 OK) - Nairobi:**
```json
{
  "location": "Nairobi",
  "is_nairobi": true,
  "methods": [
    {
      "id": 1,
      "name": "Nairobi Free Delivery",
      "description": "Free delivery within Nairobi (2-3 business days)",
      "base_cost": 0.0,
      "cost_per_kg": 0.0,
      "estimated_days_min": 2,
      "estimated_days_max": 3,
      "is_free": true
    },
    {
      "id": 3,
      "name": "Store Pickup",
      "description": "Pickup at our Bethel Business Centre location (Same day)",
      "base_cost": 0.0,
      "cost_per_kg": 0.0,
      "estimated_days_min": 0,
      "estimated_days_max": 0,
      "is_free": true
    }
  ]
}
```

**Response (200 OK) - Outside Nairobi:**
```json
{
  "location": "Upcountry",
  "is_nairobi": false,
  "methods": [
    {
      "id": 2,
      "name": "Upcountry Standard Delivery",
      "description": "Delivery outside Nairobi (3-7 business days)",
      "base_cost": 300.0,
      "cost_per_kg": 50.0,
      "estimated_days_min": 3,
      "estimated_days_max": 7,
      "free_shipping_threshold": 5000.0
    }
  ]
}
```

---

### 2. Calculate Shipping Cost
```http
POST /api/shipping/calculate
```

**Request:**
```json
{
  "shipping_method_id": 2,
  "is_nairobi": false,
  "order_total": 3500.0,
  "total_weight_kg": 2.5,
  "items": [
    {
      "product_id": 5,
      "quantity": 1,
      "weight_kg": 0.5
    },
    {
      "product_id": 8,
      "quantity": 2,
      "weight_kg": 1.0
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "shipping_method": "Upcountry Standard Delivery",
  "is_nairobi": false,
  "calculation": {
    "base_cost": 300.0,
    "weight_kg": 2.5,
    "weight_cost": 125.0,
    "total_cost": 425.0,
    "free_shipping_threshold": 5000.0,
    "qualifies_for_free_shipping": false
  },
  "final_cost": 425.0,
  "estimated_delivery": "3-7 business days"
}
```

**Business Rules:**
- Nairobi: Always free (return 0)
- Upcountry: KSh 300 base + KSh 50 per kg
- Free shipping if order > KSh 5000 (upcountry only)
- Store pickup: Always free

---

### 3. Get Shipping Method Details
```http
GET /api/shipping/methods/{method_id}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "name": "Upcountry Standard Delivery",
  "description": "Delivery outside Nairobi (3-7 business days)",
  "base_cost": 300.0,
  "cost_per_kg": 50.0,
  "estimated_days_min": 3,
  "estimated_days_max": 7,
  "available_for_nairobi": false,
  "available_outside_nairobi": true,
  "free_shipping_threshold": 5000.0,
  "is_active": true
}
```

---

## Category Hierarchy API

### Overview
Uses closure table pattern for O(1) hierarchical queries.

---

### 1. Get Category Tree
```http
GET /api/categories/tree
```

**Response (200 OK):**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Women Clothing",
      "slug": "women-clothing",
      "parent_id": null,
      "is_active": true,
      "subcategories": [
        {
          "id": 2,
          "name": "Tops",
          "slug": "women-tops",
          "parent_id": 1,
          "is_active": true,
          "subcategories": []
        },
        {
          "id": 3,
          "name": "Bottoms",
          "slug": "women-bottoms",
          "parent_id": 1,
          "is_active": true,
          "subcategories": []
        },
        {
          "id": 4,
          "name": "Dresses",
          "slug": "women-dresses",
          "parent_id": 1,
          "is_active": true,
          "subcategories": []
        },
        {
          "id": 5,
          "name": "Accessories",
          "slug": "women-accessories",
          "parent_id": 1,
          "is_active": true,
          "subcategories": []
        }
      ]
    },
    {
      "id": 6,
      "name": "Maternity Clothing",
      "slug": "maternity-clothing",
      "parent_id": null,
      "is_active": true,
      "subcategories": [
        {
          "id": 7,
          "name": "Maternity Tops",
          "slug": "maternity-tops",
          "parent_id": 6,
          "is_active": true,
          "subcategories": []
        },
        {
          "id": 8,
          "name": "Maternity Bottoms",
          "slug": "maternity-bottoms",
          "parent_id": 6,
          "is_active": true,
          "subcategories": []
        },
        {
          "id": 9,
          "name": "Maternity Dresses",
          "slug": "maternity-dresses",
          "parent_id": 6,
          "is_active": true,
          "subcategories": []
        }
      ]
    }
  ]
}
```

---

### 2. Get All Subcategories (Recursive)
```http
GET /api/categories/{category_id}/descendants
```

**Example:** GET /api/categories/1/descendants (Women Clothing)

**Response (200 OK):**
```json
{
  "category_id": 1,
  "category_name": "Women Clothing",
  "descendants": [
    {
      "id": 2,
      "name": "Tops",
      "slug": "women-tops",
      "depth": 1
    },
    {
      "id": 3,
      "name": "Bottoms",
      "slug": "women-bottoms",
      "depth": 1
    },
    {
      "id": 4,
      "name": "Dresses",
      "slug": "women-dresses",
      "depth": 1
    },
    {
      "id": 5,
      "name": "Accessories",
      "slug": "women-accessories",
      "depth": 1
    }
  ],
  "total_descendants": 4
}
```

**SQL Query (O(1) using closure table):**
```sql
SELECT c.* FROM categories c
JOIN category_closure cc ON c.id = cc.descendant_id
WHERE cc.ancestor_id = 1 AND cc.depth > 0;
```

---

### 3. Get Products in Category (Including Subcategories)
```http
GET /api/categories/{category_id}/products?include_subcategories=true
```

**Response (200 OK):**
```json
{
  "category_id": 1,
  "category_name": "Women Clothing",
  "include_subcategories": true,
  "products": [
    {
      "id": 1,
      "name": "Cotton Blouse",
      "slug": "cotton-blouse",
      "price": 2500.0,
      "category_id": 2,
      "category_name": "Tops",
      "variants_count": 6
    },
    {
      "id": 2,
      "name": "Denim Skirt",
      "slug": "denim-skirt",
      "price": 3000.0,
      "category_id": 3,
      "category_name": "Bottoms",
      "variants_count": 4
    }
  ],
  "total": 45,
  "subcategories_included": ["Tops", "Bottoms", "Dresses", "Accessories"]
}
```

**Business Rules:**
- Uses closure table for fast hierarchical queries (O(1))
- Can filter to include/exclude subcategories
- Pagination supported

---

## Updated Endpoints

### Products API Updates

#### Get Product (with Variants)
```http
GET /api/products/{slug}
```

**Response (200 OK):**
```json
{
  "id": 5,
  "name": "Floral Maternity Dress",
  "slug": "floral-maternity-dress",
  "description": "Beautiful floral print maternity dress",
  "price": 3500.0,
  "sale_price": null,
  "category_id": 9,
  "category_name": "Maternity Dresses",
  "sku": "FMD-BASE",
  "is_clearance": false,
  "weight": 0.5,
  "is_active": true,
  "is_featured": false,
  "is_on_sale": false,
  "can_be_returned": true,
  "images": [
    {
      "id": 1,
      "image_url": "/uploads/products/fmd-1.jpg",
      "alt_text": "Floral Maternity Dress - Front View",
      "is_primary": true
    }
  ],
  "variants": [
    {
      "id": 1,
      "sku": "FMD-S-BLUE",
      "size": "S",
      "color": "Blue",
      "is_active": true,
      "inventory": {
        "quantity": 15,
        "available_quantity": 13,
        "is_low_stock": false,
        "is_out_of_stock": false
      }
    },
    {
      "id": 2,
      "sku": "FMD-M-BLUE",
      "size": "M",
      "color": "Blue",
      "is_active": true,
      "inventory": {
        "quantity": 8,
        "available_quantity": 7,
        "is_low_stock": true,
        "is_out_of_stock": false
      }
    }
  ],
  "available_sizes": ["S", "M", "L", "XL"],
  "available_colors": ["Blue", "Pink", "Black"],
  "created_at": "2025-11-20T10:00:00Z",
  "updated_at": "2025-11-23T12:00:00Z"
}
```

---

## Admin API

### Overview
Admin endpoints require employee authentication with appropriate roles.

---

### 1. Admin Dashboard Stats
```http
GET /api/admin/dashboard
Authorization: Bearer {admin_token}
```

**Required Role:** admin, manager

**Response (200 OK):**
```json
{
  "summary": {
    "total_orders_today": 15,
    "revenue_today": 75000.0,
    "total_customers": 342,
    "low_stock_items": 8,
    "pending_returns": 3
  },
  "recent_orders": [...],
  "low_stock_alerts": [
    {
      "variant_id": 2,
      "sku": "FMD-M-BLUE",
      "product_name": "Floral Maternity Dress",
      "size": "M",
      "color": "Blue",
      "available_quantity": 7,
      "threshold": 10
    }
  ]
}
```

---

### 2. Admin: Create Product (with Variants)
```http
POST /api/admin/products
Authorization: Bearer {admin_token}
```

**Required Role:** admin, manager

**Request:**
```json
{
  "name": "Summer Cotton Dress",
  "slug": "summer-cotton-dress",
  "description": "Light and breezy summer dress",
  "price": 2800.0,
  "sale_price": null,
  "category_id": 4,
  "sku": "SCD-BASE",
  "is_clearance": false,
  "weight": 0.4,
  "is_active": true,
  "is_featured": false,
  "variants": [
    {
      "sku": "SCD-S-WHITE",
      "size": "S",
      "color": "White",
      "initial_quantity": 15
    },
    {
      "sku": "SCD-M-WHITE",
      "size": "M",
      "color": "White",
      "initial_quantity": 20
    },
    {
      "sku": "SCD-L-WHITE",
      "size": "L",
      "color": "White",
      "initial_quantity": 12
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 15,
  "name": "Summer Cotton Dress",
  "slug": "summer-cotton-dress",
  "variants_created": 3,
  "total_inventory": 47,
  "message": "Product and variants created successfully"
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error message here",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional context"
  }
}
```

### HTTP Status Codes

- `200` - OK (Success)
- `201` - Created (Resource created)
- `400` - Bad Request (Validation error)
- `401` - Unauthorized (Not authenticated)
- `403` - Forbidden (Not authorized for this action)
- `404` - Not Found (Resource not found)
- `409` - Conflict (Duplicate resource)
- `422` - Unprocessable Entity (Business rule violation)
- `500` - Internal Server Error

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `AUTH_REQUIRED` - Authentication required
- `INSUFFICIENT_PERMISSIONS` - User lacks required role
- `RESOURCE_NOT_FOUND` - Resource does not exist
- `DUPLICATE_RESOURCE` - Resource already exists
- `BUSINESS_RULE_VIOLATION` - Business logic constraint violated
- `OUT_OF_STOCK` - Product variant not available
- `RETURN_WINDOW_EXPIRED` - Return period has passed
- `PROMOTION_INVALID` - Promotion code invalid or expired
- `GDPR_CONSENT_REQUIRED` - GDPR consent not provided

---

## Business Rules Validation

### Return Policy Validation

**Rule 1: 2-Day Return Window**
```python
def check_return_window(order):
    if not order.delivered_at:
        return False, "Order not yet delivered"

    from datetime import timedelta
    return_deadline = order.delivered_at + timedelta(days=2)

    if datetime.utcnow() > return_deadline:
        return False, "Return window expired (2 days from delivery)"

    return True, "Within return window"
```

**Rule 2: Final Sale Items (No Returns/Exchanges)**
```python
def check_item_return_policy(product):
    if product.is_clearance:
        return "final_sale", "Clearance items are FINAL SALE - no returns or exchanges"

    if product.is_on_sale:
        return "final_sale", "Sale items are FINAL SALE - no returns or exchanges"

    return "full_return", "Full return allowed with 10% restocking fee"
```

**Rule 3: Restocking Fee (10%)**
```python
def calculate_refund(return_request):
    total_value = sum(item.value for item in return_request.items)
    restocking_fee = total_value * 0.10
    refund_amount = total_value - restocking_fee

    return {
        'total_value': total_value,
        'restocking_fee': restocking_fee,
        'refund_amount': refund_amount
    }
```

---

### Shipping Cost Validation

**Rule 1: Nairobi Free Shipping**
```python
def calculate_shipping(is_nairobi, weight_kg, order_total, method):
    if is_nairobi:
        return 0.0  # Always free for Nairobi

    # Upcountry shipping
    base = method.base_cost
    weight_cost = weight_kg * method.cost_per_kg
    total = base + weight_cost

    # Free shipping threshold
    if order_total >= method.free_shipping_threshold:
        return 0.0

    return total
```

---

### Promotion Validation

**Rule 1: Check Validity**
```python
def validate_promotion(promo, customer_id, order_total):
    # Check active status
    if not promo.is_active:
        return False, "Promotion is not active"

    # Check dates
    if datetime.utcnow() < promo.start_date:
        return False, "Promotion has not started yet"

    if promo.end_date and datetime.utcnow() > promo.end_date:
        return False, "Promotion has expired"

    # Check usage limits
    if promo.total_usage >= promo.usage_limit:
        return False, "Promotion usage limit reached"

    # Check customer usage
    customer_uses = OrderPromotion.query.filter_by(
        promotion_id=promo.id,
        customer_id=customer_id
    ).count()

    if customer_uses >= promo.usage_per_customer:
        return False, "You have already used this promotion"

    # Check minimum order
    if promo.minimum_order_amount and order_total < promo.minimum_order_amount:
        return False, f"Minimum order of KSh {promo.minimum_order_amount} required"

    return True, "Valid"
```

**Rule 2: Calculate Discount**
```python
def calculate_discount(promo, order_total):
    if promo.discount_type == 'percentage':
        discount = order_total * (promo.discount_value / 100)
    elif promo.discount_type == 'fixed_amount':
        discount = promo.discount_value
    elif promo.discount_type == 'free_shipping':
        return 'free_shipping', 0

    # Apply maximum discount cap
    if promo.maximum_discount_amount:
        discount = min(discount, promo.maximum_discount_amount)

    return discount
```

---

### Inventory Validation

**Rule 1: Check Availability**
```python
def check_variant_availability(variant_id, requested_quantity):
    inventory = Inventory.query.filter_by(variant_id=variant_id).first()

    if not inventory:
        return False, "Variant not found"

    available = inventory.quantity - inventory.reserved_quantity

    if available < requested_quantity:
        return False, f"Only {available} units available"

    return True, "Available"
```

---

## Implementation Notes

### Authentication Flow

1. Customer/Employee login returns JWT token
2. Token includes user_id and user_type (customer/employee)
3. Protected routes verify token and user type
4. Admin routes additionally verify employee role

### GDPR Compliance

All PII access is logged to `data_access_log` table:
```python
def log_pii_access(employee_id, customer_id, action, reason):
    log = DataAccessLog(
        employee_id=employee_id,
        customer_id=customer_id,
        accessed_table='customers',
        accessed_record_id=customer_id,
        action=action,
        ip_address=request.remote_addr,
        reason=reason
    )
    db.session.add(log)
    db.session.commit()
```

### Encryption

All encrypted fields are transparently handled by SQLAlchemy custom types:
- Customer PII: EncryptedCustomerString
- Addresses: EncryptedAddressString
- Payment data: EncryptedPaymentString

No manual encryption/decryption required in route handlers.

---

## Next Steps

1. Review this specification
2. Approve or request changes
3. Implement routes module-by-module
4. Create comprehensive test suite
5. Document API in Postman/Swagger

---

**Status:** 📋 READY FOR REVIEW
**Estimated Implementation Time:** 3-4 days
**Total Endpoints:** 35+ new/updated endpoints
