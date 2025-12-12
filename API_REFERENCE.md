# API Reference - Happy Place Boutique

Complete API documentation for the Happy Place Boutique e-commerce platform.

**Base URL:** `http://localhost:5000/api`

**Authentication:** JWT Bearer tokens (except public endpoints)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Products](#products)
3. [Categories](#categories)
4. [Cart](#cart)
5. [Orders](#orders)
6. [Wishlist](#wishlist)
7. [Reviews](#reviews)
8. [Shipping](#shipping)
9. [Returns](#returns)
10. [Admin](#admin)
11. [POS System](#pos-system)
12. [Fulfillment](#fulfillment)

---

## Authentication

### Customer Registration
```http
POST /api/auth/customer/register
```

**Request Body:**
```json
{
  "email": "customer@example.com",
  "password": "SecurePass123",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone": "+254712345678",
  "gdpr_consent": true,
  "marketing_consent": false
}
```

**Response:** `201 Created`
```json
{
  "message": "Customer registered successfully",
  "customer_id": 1
}
```

---

### Customer Login
```http
POST /api/auth/customer/login
```

**Request Body:**
```json
{
  "email": "customer@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "customer": {
    "id": 1,
    "email": "customer@example.com",
    "first_name": "Jane",
    "last_name": "Doe"
  }
}
```

---

### Employee Login
```http
POST /api/auth/employee/login
```

**Request Body:**
```json
{
  "email": "employee@happyplace.com",
  "password": "EmployeePass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "employee": {
    "id": 1,
    "email": "employee@happyplace.com",
    "role": "cashier",
    "first_name": "John"
  }
}
```

---

### Refresh Token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Logout
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

## Products

### Get All Products
```http
GET /api/products
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `search` (string): Search term
- `category` (string): Category slug
- `min_price` (float): Minimum price
- `max_price` (float): Maximum price
- `sort` (string): Sort by (price_asc, price_desc, newest, popular)

**Response:** `200 OK`
```json
{
  "products": [
    {
      "id": 1,
      "name": "Floral Summer Dress",
      "slug": "floral-summer-dress",
      "description": "Beautiful floral print dress",
      "base_price": 2999.00,
      "category": {
        "id": 1,
        "name": "Women's Dresses",
        "slug": "womens-dresses"
      },
      "images": [
        {
          "id": 1,
          "url": "/uploads/products/dress1.jpg",
          "alt_text": "Floral dress front view",
          "is_primary": true
        }
      ],
      "variants": [
        {
          "id": 1,
          "size": "M",
          "color": "Blue",
          "sku": "FSD-M-BLU",
          "price": 2999.00,
          "stock_quantity": 15
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

---

### Get Product by Slug
```http
GET /api/products/:slug
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Floral Summer Dress",
  "slug": "floral-summer-dress",
  "description": "Beautiful floral print dress perfect for summer occasions",
  "base_price": 2999.00,
  "category": {
    "id": 1,
    "name": "Women's Dresses"
  },
  "images": [...],
  "variants": [...],
  "average_rating": 4.5,
  "review_count": 12
}
```

---

## Categories

### Get All Categories
```http
GET /api/categories
```

**Response:** `200 OK`
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Women's Dresses",
      "slug": "womens-dresses",
      "description": "Elegant dresses for every occasion",
      "product_count": 25
    }
  ]
}
```

---

## Cart

### Get Cart
```http
GET /api/cart
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "cart": {
    "id": 1,
    "items": [
      {
        "id": 1,
        "variant": {
          "id": 1,
          "product": {
            "name": "Floral Summer Dress",
            "slug": "floral-summer-dress"
          },
          "size": "M",
          "color": "Blue",
          "price": 2999.00
        },
        "quantity": 2,
        "subtotal": 5998.00
      }
    ],
    "total": 5998.00,
    "item_count": 2
  }
}
```

---

### Add to Cart
```http
POST /api/cart/items
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "variant_id": 1,
  "quantity": 2
}
```

**Response:** `201 Created`
```json
{
  "message": "Item added to cart",
  "cart_item": {
    "id": 1,
    "variant_id": 1,
    "quantity": 2
  }
}
```

---

### Update Cart Item
```http
PUT /api/cart/items/:id
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "quantity": 3
}
```

**Response:** `200 OK`

---

### Remove from Cart
```http
DELETE /api/cart/items/:id
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

---

## Orders

### Create Order
```http
POST /api/orders
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "shipping_address_id": 1,
  "billing_address_id": 1,
  "payment_method": "mpesa",
  "shipping_method": "standard",
  "notes": "Please call before delivery"
}
```

**Response:** `201 Created`
```json
{
  "order": {
    "id": 1,
    "order_number": "ORD-2025-001",
    "status": "pending_payment",
    "total_amount": 6498.00,
    "items": [...],
    "created_at": "2025-12-12T20:00:00Z"
  }
}
```

---

### Get Customer Orders
```http
GET /api/orders
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` (string): Filter by status
- `page` (int): Page number

**Response:** `200 OK`
```json
{
  "orders": [
    {
      "id": 1,
      "order_number": "ORD-2025-001",
      "status": "processing",
      "total_amount": 6498.00,
      "created_at": "2025-12-12T20:00:00Z",
      "items_count": 3
    }
  ],
  "pagination": {...}
}
```

---

### Get Order Details
```http
GET /api/orders/:id
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "order": {
    "id": 1,
    "order_number": "ORD-2025-001",
    "status": "processing",
    "total_amount": 6498.00,
    "shipping_cost": 500.00,
    "items": [
      {
        "id": 1,
        "product_name": "Floral Summer Dress",
        "variant": "M / Blue",
        "quantity": 2,
        "price": 2999.00,
        "subtotal": 5998.00
      }
    ],
    "shipping_address": {...},
    "tracking": {
      "tracking_number": "TRK123456",
      "carrier": "DHL",
      "status": "in_transit"
    },
    "created_at": "2025-12-12T20:00:00Z"
  }
}
```

---

## Admin

### Get Dashboard Stats
```http
GET /api/admin/dashboard/stats
Authorization: Bearer <admin_token>
```

**Response:** `200 OK`
```json
{
  "stats": {
    "total_orders": 156,
    "pending_orders": 12,
    "total_revenue": 456789.00,
    "total_customers": 89,
    "low_stock_products": 5
  }
}
```

---

### Get All Orders (Admin)
```http
GET /api/admin/orders
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status` (string): Filter by status
- `page` (int): Page number
- `search` (string): Search by order number or customer

**Response:** `200 OK`

---

### Update Order Status
```http
PUT /api/admin/orders/:id/status
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "status": "processing",
  "notes": "Order confirmed and being prepared"
}
```

**Response:** `200 OK`

---

### Add Order Tracking
```http
POST /api/admin/orders/:id/tracking
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "tracking_number": "TRK123456",
  "carrier": "DHL",
  "estimated_delivery": "2025-12-20"
}
```

**Response:** `201 Created`

---

## POS System

### POS Login
```http
POST /api/pos/login
```

**Request Body:**
```json
{
  "email": "cashier@happyplace.com",
  "password": "CashierPass123"
}
```

**Response:** `200 OK`

---

### Start Shift
```http
POST /api/pos/shifts/start
Authorization: Bearer <employee_token>
```

**Request Body:**
```json
{
  "opening_cash": 5000.00
}
```

**Response:** `201 Created`

---

### Create POS Transaction
```http
POST /api/pos/transactions
Authorization: Bearer <employee_token>
```

**Request Body:**
```json
{
  "items": [
    {
      "variant_id": 1,
      "quantity": 1,
      "price": 2999.00
    }
  ],
  "payment_method": "cash",
  "amount_paid": 3000.00
}
```

**Response:** `201 Created`
```json
{
  "transaction": {
    "id": 1,
    "receipt_number": "RCP-2025-001",
    "total": 2999.00,
    "change": 1.00,
    "items": [...]
  }
}
```

---

### End Shift
```http
POST /api/pos/shifts/:id/end
Authorization: Bearer <employee_token>
```

**Request Body:**
```json
{
  "closing_cash": 15000.00,
  "notes": "Successful shift"
}
```

**Response:** `200 OK`

---

## Fulfillment

### Get Pending Orders (Packer)
```http
GET /api/fulfillment/orders/pending
Authorization: Bearer <packer_token>
```

**Response:** `200 OK`
```json
{
  "orders": [
    {
      "id": 1,
      "order_number": "ORD-2025-001",
      "customer_name": "Jane Doe",
      "items_count": 3,
      "created_at": "2025-12-12T20:00:00Z"
    }
  ]
}
```

---

### Assign Order to Packer
```http
POST /api/fulfillment/orders/:id/assign
Authorization: Bearer <manager_token>
```

**Request Body:**
```json
{
  "packer_id": 5
}
```

**Response:** `200 OK`

---

### Mark Order as Packed
```http
POST /api/fulfillment/orders/:id/packed
Authorization: Bearer <packer_token>
```

**Response:** `200 OK`

---

### Mark Order as Shipped
```http
POST /api/fulfillment/orders/:id/shipped
Authorization: Bearer <shipper_token>
```

**Request Body:**
```json
{
  "tracking_number": "TRK123456",
  "carrier": "DHL"
}
```

**Response:** `200 OK`

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Validation error",
  "details": {
    "email": "Invalid email format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limiting

- **Authentication endpoints:** 3 requests per 5 minutes
- **General API:** 100 requests per minute
- **Admin endpoints:** 200 requests per minute

---

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

Response includes pagination metadata:
```json
{
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 156,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Webhooks

### Order Status Change
Triggered when order status changes.

**Payload:**
```json
{
  "event": "order.status_changed",
  "order_id": 1,
  "order_number": "ORD-2025-001",
  "old_status": "pending",
  "new_status": "processing",
  "timestamp": "2025-12-12T20:00:00Z"
}
```

---

## Testing

Use the following test credentials:

**Customer:**
- Email: `test@customer.com`
- Password: `TestPass123`

**Admin:**
- Email: `admin@happyplace.com`
- Password: `AdminPass123`

**Employee (Cashier):**
- Email: `cashier@happyplace.com`
- Password: `CashierPass123`

---

## Support

For API support, contact: dev@happyplace.com
