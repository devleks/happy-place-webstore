# Happy Place Boutique - API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:5001/api`  
**Authentication:** JWT Bearer Token

---

## Table of Contents
1. [Authentication](#authentication)
2. [Products](#products)
3. [Categories](#categories)
4. [Cart](#cart)
5. [Wishlist](#wishlist)
6. [Orders](#orders)
7. [Store Locations](#store-locations)
8. [Error Handling](#error-handling)

---

## Authentication

### Customer Registration
**POST** `/auth/register`

Register a new customer account.

**Request Body:**
```json
{
  "email": "customer@example.com",
  "password": "SecurePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+254712345678"
}
```

**Response (201):**
```json
{
  "message": "Customer registered successfully",
  "access_token": "eyJhbGci...",
  "user_type": "customer"
}
```

---

### Customer Login
**POST** `/auth/login`

Login as a customer.

**Request Body:**
```json
{
  "email": "customer@example.com",
  "password": "SecurePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGci...",
  "user_type": "customer",
  "email": "customer@example.com"
}
```

---

### Employee Login
**POST** `/auth/employee/login`

Login as an employee (admin, manager, cashier).

**Request Body:**
```json
{
  "email": "admin@happyplace.co.ke",
  "password": "AdminPassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGci...",
  "user_type": "employee",
  "role": "admin",
  "email": "admin@happyplace.co.ke"
}
```

---

### Get Current User
**GET** `/auth/me`

Get currently authenticated user information.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "customer@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "customer"
}
```

---

## Products

### List Products
**GET** `/products`

Get paginated list of products with optional filtering.

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 12) - Items per page
- `category` (string) - Filter by category slug (e.g., "women-tops")
- `parent_category` (string) - Filter by parent category (e.g., "women-clothing")
- `search` (string) - Search products by name/description
- `is_on_sale` (boolean) - Filter sale items only
- `is_clearance` (boolean) - Filter clearance items only

**Example Request:**
```
GET /products?parent_category=women-clothing&page=1&per_page=12
```

**Response (200):**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Classic Cotton T-Shirt",
      "slug": "classic-cotton-t-shirt",
      "description": "Comfortable everyday cotton t-shirt",
      "price": 2999.0,
      "sale_price": null,
      "is_on_sale": false,
      "is_clearance": false,
      "is_featured": true,
      "category": "Tops",
      "category_name": "Tops",
      "image_url": "https://images.unsplash.com/...",
      "available_colors": ["White", "Black", "Navy", "Pink"],
      "variants_count": 20
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 12,
    "total": 8,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "total": 8
}
```

---

### Get Product Details
**GET** `/products/:slug`

Get detailed product information including variants and images.

**Response (200):**
```json
{
  "id": 1,
  "name": "Classic Cotton T-Shirt",
  "slug": "classic-cotton-t-shirt",
  "description": "Comfortable everyday cotton t-shirt perfect for casual wear",
  "price": 2999.0,
  "sale_price": null,
  "is_on_sale": false,
  "is_clearance": false,
  "is_featured": true,
  "weight": 0.2,
  "category": {
    "id": 2,
    "name": "Tops",
    "slug": "women-tops"
  },
  "images": [
    {
      "id": 1,
      "image_url": "https://images.unsplash.com/...",
      "alt_text": "Classic Cotton T-Shirt",
      "is_primary": true
    }
  ],
  "variants": [
    {
      "id": 1,
      "sku": "WOMENS-TOP-001-XS-WHITE",
      "size": "XS",
      "color": "White",
      "is_active": true,
      "inventory": {
        "quantity": 15,
        "available_quantity": 15,
        "reserved_quantity": 0,
        "is_low_stock": false,
        "is_out_of_stock": false
      }
    }
  ],
  "available_sizes": ["XS", "S", "M", "L", "XL"],
  "available_colors": ["White", "Black", "Navy", "Pink"]
}
```

---

## Categories

### List Categories
**GET** `/categories`

Get all product categories with hierarchy.

**Response (200):**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Women Clothing",
      "slug": "women-clothing",
      "description": "Clothing for women",
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "Tops",
          "slug": "women-tops",
          "parent_id": 1
        }
      ]
    }
  ]
}
```

---

## Cart

All cart endpoints require authentication.

### Get Cart
**GET** `/cart`

Get current user's shopping cart.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "cart_id": 1,
  "customer_id": 2,
  "items": [
    {
      "id": 1,
      "quantity": 2,
      "added_at": "2025-11-24T10:30:00",
      "variant": {
        "id": 21,
        "sku": "WOMENS-TOP-002-S-IVORY",
        "size": "S",
        "color": "Ivory",
        "product": {
          "id": 2,
          "name": "Elegant Silk Blouse",
          "slug": "elegant-silk-blouse",
          "price": 4999.0,
          "sale_price": 3499.0,
          "is_clearance": false,
          "primary_image": {
            "image_url": "https://images.unsplash.com/...",
            "alt_text": "Elegant Silk Blouse"
          },
          "images": []
        }
      }
    }
  ],
  "total_items": 1,
  "subtotal": 6998.0
}
```

---

### Add to Cart
**POST** `/cart/items`

Add a product variant to cart.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "variant_id": 21,
  "quantity": 2
}
```

**Response (201):**
```json
{
  "message": "Item added to cart",
  "cart_item": {
    "id": 1,
    "quantity": 2,
    "variant": { /* variant details */ }
  }
}
```

**Error Responses:**
- `400` - Insufficient stock
- `404` - Product variant not found

---

### Update Cart Item
**PUT** `/cart/items/:item_id`

Update quantity of an item in cart.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "quantity": 3
}
```

**Response (200):**
```json
{
  "message": "Cart item updated",
  "cart_item": {
    "id": 1,
    "quantity": 3
  }
}
```

---

### Remove from Cart
**DELETE** `/cart/items/:item_id`

Remove an item from cart.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "message": "Item removed from cart"
}
```

---

### Clear Cart
**DELETE** `/cart`

Remove all items from cart.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "message": "Cart cleared"
}
```

---

## Wishlist

All wishlist endpoints require authentication.

### Get Wishlist
**GET** `/wishlist`

Get current user's wishlist.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "wishlist_id": 1,
  "customer_id": 2,
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "added_at": "2025-11-24T09:00:00",
      "product": {
        "id": 1,
        "name": "Classic Cotton T-Shirt",
        "slug": "classic-cotton-t-shirt",
        "price": 2999.0,
        "sale_price": null,
        "is_clearance": false,
        "primary_image": {
          "image_url": "https://images.unsplash.com/..."
        }
      }
    }
  ],
  "total_items": 1
}
```

---

### Add to Wishlist
**POST** `/wishlist/items`

Add a product to wishlist.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "product_id": 1
}
```

**Response (201):**
```json
{
  "message": "Item added to wishlist",
  "wishlist_item": {
    "id": 1,
    "product_id": 1,
    "added_at": "2025-11-24T09:00:00"
  }
}
```

---

### Remove from Wishlist
**DELETE** `/wishlist/items/:item_id`

Remove an item from wishlist.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "message": "Item removed from wishlist"
}
```

---

### Move to Cart
**POST** `/wishlist/move-to-cart/:item_id`

Move an item from wishlist to cart.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body (Optional):**
```json
{
  "variant_id": 21
}
```

**Response (200):**
```json
{
  "message": "Item moved to cart"
}
```

**Note:** If `variant_id` is not provided, the system automatically selects the first available variant.

---

## Orders

All order endpoints require authentication. Orders are created from the customer's shopping cart.

### Create Order
**POST** `/orders`

Create a new order from the current cart items. Cart will be cleared after successful order creation.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "shipping_address": {
    "street": "123 Kimathi Street, Apt 4B",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  },
  "billing_address": {
    "street": "456 Different Street",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  }
}
```

**Response (201):**
```json
{
  "message": "Order created successfully",
  "order": {
    "id": 4,
    "order_number": "HP-20251125-0002",
    "customer_id": 5,
    "status": "pending",
    "subtotal": 6498.0,
    "shipping_cost": 0,
    "tax": 0,
    "total": 6498.0,
    "is_nairobi": true,
    "created_at": "2025-11-25T17:05:11.553437",
    "shipping_address": {
      "street": "123 Kimathi Street, Apt 4B",
      "city": "Nairobi",
      "state": "Nairobi County",
      "zip": "00100",
      "phone": "+254712345678"
    },
    "items": [
      {
        "id": 4,
        "product": {
          "id": 3,
          "name": "Classic Cotton T-Shirt",
          "slug": "classic-cotton-tshirt",
          "image_url": "https://images.unsplash.com/..."
        },
        "variant": {
          "id": 21,
          "sku": "COTTEE-XS-WHI",
          "size": "XS",
          "color": "White"
        },
        "quantity": 1,
        "unit_price": 2999.0,
        "total_price": 2999.0
      }
    ],
    "items_count": 2
  }
}
```

**Shipping Rules:**
- **Nairobi:** Free shipping (KSh 0)
- **Upcountry:** KSh 300 base + KSh 50 per kg

**Security Features:**
- Server-side price validation (prevents price manipulation)
- Atomic inventory reservation with row-level locking
- Address encryption (AES-256 with MultiFernet)
- Audit logging (order_audit_log table)
- IP address and user agent tracking

**Error Responses:**
- `400` - Validation error (empty cart, invalid address, insufficient stock)
- `401` - Unauthorized (missing or invalid token)
- `500` - Order creation failed

**Notes:**
- `billing_address` is optional; if not provided, shipping address is used
- Cart is automatically cleared after successful order creation
- Order number format: `HP-YYYYMMDD-XXXX` (e.g., HP-20251125-0001)
- Inventory is reserved but not deducted until payment is confirmed

---

### Get Order History
**GET** `/orders`

Get all orders for the authenticated customer with pagination.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 10) - Orders per page

**Example Request:**
```
GET /orders?page=1&per_page=10
```

**Response (200):**
```json
{
  "orders": [
    {
      "id": 4,
      "order_number": "HP-20251125-0002",
      "status": "pending",
      "subtotal": 6498.0,
      "shipping_cost": 0,
      "tax": 0,
      "total": 6498.0,
      "created_at": "2025-11-25T17:05:11.553437",
      "items": [
        {
          "product": {
            "name": "Classic Cotton T-Shirt",
            "image_url": "https://images.unsplash.com/..."
          },
          "quantity": 1,
          "unit_price": 2999.0
        }
      ],
      "items_count": 2
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 15,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

**Order Statuses:**
- `pending` - Order created, awaiting payment
- `processing` - Payment confirmed, preparing shipment
- `shipped` - Order dispatched
- `delivered` - Order delivered to customer
- `cancelled` - Order cancelled
- `refunded` - Order refunded

---

### Get Order Details
**GET** `/orders/:id`

Get detailed information about a specific order.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": 4,
  "order_number": "HP-20251125-0002",
  "customer_id": 5,
  "status": "pending",
  "subtotal": 6498.0,
  "shipping_cost": 0,
  "tax": 0,
  "total": 6498.0,
  "is_nairobi": true,
  "created_at": "2025-11-25T17:05:11.553437",
  "updated_at": "2025-11-25T17:05:11.553437",
  "shipping_address": {
    "street": "123 Kimathi Street, Apt 4B",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  },
  "billing_address": {
    "street": "123 Kimathi Street, Apt 4B",
    "city": "Nairobi",
    "state": "Nairobi County",
    "zip": "00100",
    "phone": "+254712345678"
  },
  "items": [
    {
      "id": 4,
      "product": {
        "id": 3,
        "name": "Classic Cotton T-Shirt",
        "slug": "classic-cotton-tshirt",
        "image_url": "https://images.unsplash.com/..."
      },
      "variant": {
        "id": 21,
        "sku": "COTTEE-XS-WHI",
        "size": "XS",
        "color": "White"
      },
      "quantity": 1,
      "unit_price": 2999.0,
      "total_price": 2999.0
    }
  ],
  "items_count": 2
}
```

**Error Responses:**
- `401` - Unauthorized
- `403` - Forbidden (order belongs to different customer)
- `404` - Order not found

---

### Get Order by Number
**GET** `/orders/number/:order_number`

Get order details by order number (alternative to order ID).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Example Request:**
```
GET /orders/number/HP-20251125-0002
```

**Response (200):**
Same as "Get Order Details" endpoint.

**Error Responses:**
- `401` - Unauthorized
- `403` - Forbidden (order belongs to different customer)
- `404` - Order not found

**Note:** This endpoint is useful for customer-facing order lookups where order numbers are easier to reference than internal IDs.

---

### Preview Shipping Cost
**POST** `/orders/shipping-preview`

Calculate shipping cost before checkout based on cart contents and destination city.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "city": "Nairobi"
}
```

**Response (200):**
```json
{
  "shipping_cost": 0,
  "is_nairobi": true,
  "description": "Free shipping within Nairobi",
  "cart_weight_kg": 0.55,
  "cart_items": 2
}
```

**Example (Upcountry):**
```json
{
  "city": "Mombasa"
}
```

**Response (200):**
```json
{
  "shipping_cost": 327.5,
  "is_nairobi": false,
  "description": "Upcountry shipping: KSh 300.0 base + KSh 50.0/kg (0.55kg)",
  "cart_weight_kg": 0.55,
  "cart_items": 2
}
```

**Error Responses:**
- `400` - Invalid city or empty cart
- `401` - Unauthorized

**Notes:**
- Cart must have items to calculate shipping
- Weight is automatically calculated from product weights
- Cities recognized as Nairobi: "Nairobi", "Nai", "Nairobi County", "Nairobi City" (case-insensitive)

---

## Store Locations

### Get Store Locations
**GET** `/store-locations`

Get all physical store locations.

**Response (200):**
```json
{
  "locations": [
    {
      "id": 1,
      "name": "Happy Place Boutique - Nairobi",
      "address": "Store No. 22, 1st Floor, Bethel Business Centre",
      "city": "Nairobi",
      "state": "Kenya",
      "zip_code": "",
      "phone": "+254 XXX XXX XXX",
      "email": "info@happyplace.co.ke",
      "hours": {
        "Monday": "10:00 AM - 7:00 PM",
        "Tuesday": "10:00 AM - 7:00 PM",
        "Wednesday": "10:00 AM - 7:00 PM",
        "Thursday": "10:00 AM - 7:00 PM",
        "Friday": "10:00 AM - 7:00 PM",
        "Saturday": "10:00 AM - 6:00 PM",
        "Sunday": "Closed"
      }
    }
  ]
}
```

---

## Error Handling

All error responses follow this format:

```json
{
  "error": "Error message description"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error, insufficient stock, etc.)
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

### Example Error Response

```json
{
  "error": "Insufficient stock",
  "available": 5,
  "current_in_cart": 2
}
```

---

## Rate Limiting

Currently no rate limiting implemented. Recommended limits for production:
- Authentication endpoints: 5 requests per minute
- Read endpoints: 100 requests per minute
- Write endpoints: 30 requests per minute

---

## Pagination

List endpoints return paginated results:

```json
{
  "pagination": {
    "page": 1,
    "per_page": 12,
    "total": 50,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Testing with cURL

### Example 1: Login and Add to Cart

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@example.com","password":"password"}' \
  -s | python -m json.tool | grep access_token | cut -d'"' -f4)

# 2. Get Products
curl -X GET http://localhost:5001/api/products -s | python -m json.tool

# 3. Add to Cart
curl -X POST http://localhost:5001/api/cart/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variant_id":21,"quantity":2}' \
  -s | python -m json.tool

# 4. Get Cart
curl -X GET http://localhost:5001/api/cart \
  -H "Authorization: Bearer $TOKEN" \
  -s | python -m json.tool
```

### Example 2: Complete Order Flow

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@example.com","password":"password"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

# 2. Add items to cart
curl -X POST http://localhost:5001/api/cart/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variant_id":21,"quantity":1}' \
  -s > /dev/null

# 3. Preview shipping cost
curl -X POST http://localhost:5001/api/orders/shipping-preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city":"Nairobi"}' \
  -s | python3 -m json.tool

# 4. Create order
ORDER_RESPONSE=$(curl -X POST http://localhost:5001/api/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "street": "123 Kimathi Street, Apt 4B",
      "city": "Nairobi",
      "state": "Nairobi County",
      "zip": "00100",
      "phone": "+254712345678"
    }
  }' \
  -s)

echo "$ORDER_RESPONSE" | python3 -m json.tool

# 5. Extract order ID and get order details
ORDER_ID=$(echo "$ORDER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('order', {}).get('id', ''))")

curl -X GET "http://localhost:5001/api/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool

# 6. Get order history
curl -X GET "http://localhost:5001/api/orders?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN" \
  -s | python3 -m json.tool
```

---

## Security Notes

1. **HTTPS Required**: All production traffic must use HTTPS
2. **Token Storage**: Store JWT tokens securely (httpOnly cookies or secure storage)
3. **Token Expiration**: Tokens expire after 30 days
4. **CORS**: Configure CORS origins for production
5. **Input Validation**: All inputs are validated server-side
6. **SQL Injection**: Protected by SQLAlchemy ORM
7. **XSS**: Frontend sanitizes all user input
8. **Encryption**: PII data encrypted with MultiFernet

---

## Future Endpoints

### Phase 6: Payments (In Progress)
- ✅ `POST /orders` - Create order (Implemented)
- ✅ `GET /orders` - List customer orders (Implemented)
- ✅ `GET /orders/:id` - Get order details (Implemented)
- ✅ `POST /orders/shipping-preview` - Preview shipping cost (Implemented)
- ⏳ `POST /payments/mpesa` - Initiate M-Pesa payment (Pending)
- ⏳ `POST /payments/mpesa/callback` - M-Pesa callback handler (Pending)

### Phase 7: Returns & Refunds
- `POST /returns` - Create return request
- `GET /returns/:id` - Get return details
- `PUT /returns/:id/approve` - Approve return (Admin)

### Phase 8: POS System
- `POST /pos/sales` - Create POS sale
- `GET /pos/inventory` - Check store inventory
- `POST /pos/staff/login` - Staff authentication
- `POST /pos/sync` - Sync online/store inventory

### Phase 9: Admin Dashboard
- `POST /admin/products` - Create product
- `PUT /admin/products/:id` - Update product
- `POST /admin/products/:id/images` - Upload images
- `GET /admin/analytics` - Sales analytics
- `GET /admin/orders` - Manage all orders

---

**Last Updated:** 2025-11-25  
**Maintainer:** Happy Place Boutique Development Team
