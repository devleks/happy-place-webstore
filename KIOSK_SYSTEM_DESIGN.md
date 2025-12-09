# Happy Place Kiosk System Design

## Overview
Self-service kiosk system for in-store customers to browse products, check availability, and request assistance.

## Kiosk Strategy

### 1. Customer Self-Service Kiosk
**Purpose**: Allow customers to browse products independently, check sizes/colors, and add items to a cart for staff-assisted checkout.

**Key Features**:
- Touch-friendly large interface (tablet/large screen)
- Product browsing by category
- Search by name/SKU
- View product details, images, and availability
- Check size/color availability in real-time
- Add items to cart
- Request staff assistance
- Print/display cart summary for staff
- No payment processing (staff-assisted checkout at POS)

### 2. Kiosk Modes

#### Mode A: Browse & Request (Recommended)
- Customer browses products on kiosk
- Adds items to cart
- Requests staff assistance when ready
- Staff receives notification with cart details
- Staff retrieves items and processes payment at POS

#### Mode B: Self-Service with Staff Approval
- Customer completes selection
- Generates a cart ID/QR code
- Customer takes code to cashier
- Cashier loads cart and completes transaction

### 3. Database Schema

```sql
-- Kiosk Sessions Table
CREATE TABLE kiosk_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    store_location_id INTEGER REFERENCES store_locations(id),
    kiosk_device_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- active, assistance_requested, completed, abandoned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assistance_requested_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);

-- Kiosk Cart Items Table
CREATE TABLE kiosk_cart_items (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES kiosk_sessions(session_id) ON DELETE CASCADE,
    variant_id INTEGER REFERENCES product_variants(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assistance Requests Table
CREATE TABLE assistance_requests (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES kiosk_sessions(session_id),
    request_type VARCHAR(50) NOT NULL, -- item_retrieval, size_help, general_question
    status VARCHAR(20) DEFAULT 'pending', -- pending, acknowledged, completed
    priority INTEGER DEFAULT 1, -- 1=normal, 2=high
    customer_location VARCHAR(100),
    message TEXT,
    assigned_to INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 4. API Endpoints

#### Kiosk Session Management
- `POST /api/kiosk/sessions` - Start new kiosk session
- `GET /api/kiosk/sessions/:session_id` - Get session details
- `PUT /api/kiosk/sessions/:session_id/activity` - Update last activity
- `DELETE /api/kiosk/sessions/:session_id` - End/abandon session

#### Kiosk Cart Management
- `GET /api/kiosk/cart/:session_id` - Get cart items
- `POST /api/kiosk/cart/:session_id/items` - Add item to cart
- `PUT /api/kiosk/cart/:session_id/items/:item_id` - Update quantity
- `DELETE /api/kiosk/cart/:session_id/items/:item_id` - Remove item

#### Assistance Requests
- `POST /api/kiosk/assistance` - Request staff assistance
- `GET /api/kiosk/assistance/:session_id` - Get assistance status
- `GET /api/pos/assistance/pending` - Get pending requests (staff view)
- `PUT /api/pos/assistance/:id/acknowledge` - Staff acknowledges request
- `PUT /api/pos/assistance/:id/complete` - Staff completes request

#### Product Browsing (Public)
- `GET /api/kiosk/products` - Browse products (no auth required)
- `GET /api/kiosk/products/:slug` - Get product details
- `GET /api/kiosk/categories` - Get categories

### 5. Frontend Components

```
/frontend/src/pages/Kiosk/
├── KioskHome.js          # Welcome screen with start session
├── KioskBrowse.js        # Product browsing by category
├── KioskSearch.js        # Product search
├── KioskProduct.js       # Product detail view
├── KioskCart.js          # Cart summary
├── KioskAssistance.js    # Request assistance screen
└── KioskThankYou.js      # Completion screen

/frontend/src/components/Kiosk/
├── KioskHeader.js        # Persistent header with cart count
├── KioskProductCard.js   # Touch-friendly product card
├── KioskCategoryNav.js   # Category navigation
└── KioskTimer.js         # Inactivity timer

/frontend/src/styles/
└── Kiosk.css             # Kiosk-specific styles (large touch targets)
```

### 6. User Flow

```
1. Welcome Screen
   ↓
2. Browse Products / Search
   ↓
3. View Product Details
   ↓
4. Add to Cart (select size/color)
   ↓
5. Continue Shopping or View Cart
   ↓
6. Review Cart
   ↓
7. Request Assistance
   ↓
8. Staff Notification
   ↓
9. Staff Retrieves Items & Processes at POS
   ↓
10. Thank You Screen / Reset
```

### 7. Security & Session Management

- **Session Timeout**: 5 minutes of inactivity
- **No Authentication Required**: Public kiosk access
- **Session Cleanup**: Auto-abandon after 10 minutes idle
- **Data Privacy**: No personal data collected
- **Cart Limit**: Maximum 20 items per session
- **Rate Limiting**: Prevent abuse

### 8. Staff Integration

#### POS Dashboard Enhancement
- Real-time assistance request notifications
- Display pending kiosk carts
- One-click load cart to POS transaction
- Customer queue management

#### Notification System
- Visual alerts on POS dashboard
- Sound notification for new requests
- Request aging indicators (time waiting)

### 9. Hardware Requirements

- Touch-enabled display (21-27 inch recommended)
- Stable mount/kiosk enclosure
- Network connectivity (WiFi/Ethernet)
- Optional: Receipt printer for cart summary
- Optional: QR code scanner for quick access

### 10. Implementation Phases

**Phase 1: Core Kiosk Functionality**
- Session management
- Product browsing
- Cart management
- Basic assistance requests

**Phase 2: Staff Integration**
- POS notifications
- Load cart to POS
- Assistance queue management

**Phase 3: Enhanced Features**
- QR code generation for carts
- Product recommendations
- Digital signage mode when idle
- Analytics dashboard

## Benefits

1. **Customer Experience**
   - Self-paced browsing
   - Check availability without asking staff
   - Reduce wait time to see products
   - Touch-friendly interface

2. **Staff Efficiency**
   - Pre-selected items ready to retrieve
   - Reduced interruptions while serving others
   - Better queue management
   - Faster checkout process

3. **Business Value**
   - Increased customer engagement
   - Better inventory visibility
   - Data on browsing patterns
   - Reduced checkout time
   - Handle more customers simultaneously

## Configuration

```json
{
  "kiosk": {
    "sessionTimeoutMinutes": 5,
    "maxCartItems": 20,
    "autoAbandonMinutes": 10,
    "storeLocationId": 1,
    "deviceId": "KIOSK-001",
    "idleScreenTimeout": 2,
    "enableSoundNotifications": true,
    "theme": "customer-friendly"
  }
}
```
