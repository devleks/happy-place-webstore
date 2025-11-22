# Happy Place Boutique - Development Roadmap

## Tech Stack

**Frontend:**
- React 18 (UI framework)
- React Router v6 (Client-side routing)
- Axios (HTTP client)
- CSS3 (Styling with responsive design)

**Backend:**
- Python 3.x with Flask (Web framework)
- SQLAlchemy (ORM)
- Flask-JWT-Extended (Authentication)
- PostgreSQL (Database - used throughout all phases)

**Payment:**
- M-Pesa Daraja API (Primary payment method for Kenya)

---

## Prerequisites

Before starting development phases, ensure the following are set up:

**Database Setup:**
- [ ] PostgreSQL installed locally (macOS: Homebrew, Linux: apt/yum, Windows: PostgreSQL installer)
- [ ] Database `happy_place_db` created
- [ ] Database connection string configured in `.env` file
- [ ] Initial database schema created (run `python seed.py`)

**Development Environment:**
- [ ] Python 3.x installed
- [ ] Node.js and npm installed
- [ ] Backend virtual environment created
- [ ] Frontend dependencies installed

See [README.md](README.md) for detailed setup instructions.

---

## Phase 1: UI/UX Quick Wins ✅ COMPLETED

**Goal:** Improve user experience with immediate visual and functional enhancements

**Completed Tasks:**
- ✅ Enhance logo prominence and header layout
- ✅ Replace search button text with search icon
- ✅ Ensure responsive search functionality across all screen sizes
- ✅ Optimize header spacing to prevent element overlapping
- ✅ Remove redundant "Shop by Category" section
- ✅ Fix store location page with fallback data
- ✅ Integrate interactive Google Maps for store location
- ✅ Update store address to actual Bethel Business Centre location
- ✅ Update store hours (Sunday: Closed)
- ✅ Convert currency from USD to Kenya Shillings (KSh)

**Status:** ✅ Complete (12 commits)

---

## Phase 2: Backend API - Inventory & Image Management

**Goal:** Build essential backend APIs for product management, inventory control, and image uploads

### Inventory Management API
- [ ] Create admin authentication/authorization middleware
- [ ] Build inventory CRUD endpoints:
  - `POST /api/admin/inventory` - Add inventory for product variant
  - `PUT /api/admin/inventory/:id` - Update inventory quantities
  - `DELETE /api/admin/inventory/:id` - Remove inventory variant
  - `GET /api/admin/inventory` - List all inventory with filters
- [ ] Add bulk inventory update endpoint
- [ ] Implement inventory adjustment logging (track changes)
- [ ] Add low-stock alert thresholds
- [ ] Create inventory sync endpoint (online ↔ store transfer)

### Image Upload & Management
- [ ] Set up image storage strategy:
  - Local filesystem storage (development)
  - Cloud storage integration (AWS S3, Cloudinary, or DigitalOcean Spaces)
- [ ] Implement image upload endpoint:
  - `POST /api/admin/products/:id/images` - Upload product images
  - Support multiple images per product
  - Image validation (file type, size limits)
- [ ] Add image processing:
  - Resize/optimize images for web
  - Generate thumbnails
  - WebP conversion for performance
- [ ] Create image management endpoints:
  - `GET /api/products/:id/images` - List product images
  - `DELETE /api/admin/images/:id` - Delete image
  - `PUT /api/admin/images/:id/primary` - Set primary image
- [ ] Update Product model to support multiple images:
  - Create ProductImage model/table
  - Relationship: Product → ProductImages (one-to-many)
  - Track image order, alt text, primary flag

### Product Management API Enhancement
- [ ] Admin product CRUD endpoints:
  - `POST /api/admin/products` - Create product
  - `PUT /api/admin/products/:id` - Update product
  - `DELETE /api/admin/products/:id` - Soft delete (set is_active=False)
- [ ] Add product validation and business rules
- [ ] Implement product search/filtering for admin

### Backend Requirements
- [ ] Install Flask-Uploads or similar for file handling
- [ ] Add PIL/Pillow for image processing
- [ ] Configure file upload size limits
- [ ] Set up CORS for file uploads
- [ ] Add admin role to User model
- [ ] Create admin authorization decorators

**Estimated Duration:** 2-3 weeks

---

## Phase 3: Point of Sale (POS) System for Physical Store

**Goal:** Build a complete POS system for in-store transactions using shared PostgreSQL database

### POS Terminal Interface
- [ ] Create POS desktop/tablet application or web interface
- [ ] Build cashier login/logout system
- [ ] Design POS-specific UI (large buttons, touch-friendly)
- [ ] Product search and barcode scanning interface
- [ ] Shopping cart for current transaction
- [ ] Quick access to frequently purchased items
- [ ] Customer display (optional second screen)

### Product & Inventory Management
- [ ] Barcode scanner integration
- [ ] Product lookup by SKU, barcode, or name
- [ ] Real-time inventory checking (store_quantity)
- [ ] Automatic inventory deduction on sale
- [ ] Size and color selection for variants
- [ ] Product image display for verification

### Payment Processing
- [ ] M-Pesa integration for in-store payments (STK Push)
- [ ] Cash payment handling
  - Cash tendered and change calculation
  - Cash drawer integration (optional)
- [ ] Card payment integration (if applicable)
- [ ] Multiple payment methods per transaction (split payment)
- [ ] Payment verification and confirmation

### Receipt & Printing
- [ ] Receipt template design
  - Store details (name, address, phone)
  - Transaction ID and date/time
  - Itemized list (product, quantity, price)
  - Subtotal, tax, total
  - Payment method
  - Cashier name
  - Thank you message
- [ ] Thermal printer integration (USB/Network)
- [ ] Receipt printing on transaction completion
- [ ] Reprint functionality for previous receipts
- [ ] Email receipt option (optional)

### Transaction Management
- [ ] Create Sale/Transaction model and API:
  - Transaction ID, timestamp
  - Cashier/staff ID
  - Items sold (product, quantity, price)
  - Payment method and amount
  - Customer info (optional - for returns)
- [ ] Transaction logging to PostgreSQL
- [ ] Transaction history view
- [ ] Return/refund processing
- [ ] Exchange handling
- [ ] Void/cancel transaction (with authorization)

### Staff Management
- [ ] Staff/Cashier model and authentication
- [ ] Role-based permissions (cashier, supervisor, manager)
- [ ] Shift tracking (clock in/out)
- [ ] Sales attribution to staff members

### Reporting & End-of-Day
- [ ] Daily sales summary
- [ ] Payment method breakdown (M-Pesa, cash, card)
- [ ] Cashier performance reports
- [ ] Inventory sold report
- [ ] End-of-day closing procedures
- [ ] Cash counting and reconciliation
- [ ] Export reports (CSV, PDF)

### Offline Mode (Optional but Recommended)
- [ ] Local transaction queue when internet is down
- [ ] Sync transactions when connection restored
- [ ] Local product/inventory cache
- [ ] Offline mode indicator

### Hardware Integration
- [ ] Barcode scanner (USB/Bluetooth)
- [ ] Receipt printer (thermal, USB/Network)
- [ ] Cash drawer (optional, connected to printer)
- [ ] Customer display (optional secondary screen)
- [ ] Card reader (if supporting card payments)

### Backend Requirements
- [ ] Create Sale/Transaction model
- [ ] Create Staff/Cashier model
- [ ] Build POS-specific API endpoints:
  - `POST /api/pos/sales` - Create sale transaction
  - `GET /api/pos/sales/:id` - Get sale details
  - `POST /api/pos/sales/:id/void` - Void transaction
  - `POST /api/pos/sales/:id/return` - Process return
  - `GET /api/pos/inventory` - Check store inventory
  - `POST /api/pos/staff/login` - Staff authentication
  - `GET /api/pos/reports/daily` - Daily reports
- [ ] Inventory sync logic (deduct from store_quantity)
- [ ] Transaction locking to prevent overselling
- [ ] Receipt data generation API

### Technology Stack Options
- **Desktop POS App:** Electron (React + Node.js)
- **Web POS:** React web app (accessible on tablets/computers)
- **Mobile POS:** React Native (for tablet-based POS)
- **Printer:** ESC/POS protocol for thermal printers
- **Database:** PostgreSQL (shared with online store)

**Estimated Duration:** 4-5 weeks

**Note:** This phase can be developed in parallel with Phase 4 (Shopping Cart) after Phase 2 (Backend API) is complete.

---

## Phase 4: Shopping Cart & Wishlist (Online Store)

**Goal:** Enable online customers to add items to cart and save favorites

### Shopping Cart Features
- [ ] Create Cart context for state management
- [ ] Add "Add to Cart" functionality on product detail page
- [ ] Display cart count badge in header (already has placeholder)
- [ ] Build cart page with item list
- [ ] Implement quantity adjustment (increase/decrease)
- [ ] Calculate subtotal, tax, and total
- [ ] Add "Remove from Cart" functionality
- [ ] Persist cart data in localStorage
- [ ] Handle size and color selection before adding to cart

### Wishlist Features
- [ ] Create Wishlist context for state management
- [ ] Implement wishlist toggle on product cards (heart icon already exists)
- [ ] Build wishlist page showing saved items
- [ ] Add "Move to Cart" functionality from wishlist
- [ ] Persist wishlist data in localStorage
- [ ] Display wishlist count in header

### Backend Requirements
- [ ] Create cart API endpoints (if server-side cart needed)
- [ ] Create wishlist API endpoints
- [ ] Handle cart/wishlist for authenticated users

**Estimated Duration:** 1-2 weeks

---

## Phase 5: Checkout & Payment Integration (Online Store)

**Goal:** Complete the online purchase flow with M-Pesa payment integration for Kenya

### Checkout Flow
- [ ] Create multi-step checkout page
  - Step 1: Review cart items
  - Step 2: Shipping/delivery information
  - Step 3: Payment method selection
  - Step 4: Order confirmation
- [ ] Implement form validation for customer details
- [ ] Add delivery address collection
- [ ] Display order summary with totals in KSh

### M-Pesa Payment Integration
- [ ] Research M-Pesa Daraja API documentation
- [ ] Set up M-Pesa developer account and credentials
- [ ] Implement M-Pesa STK Push (Lipa Na M-Pesa Online)
  - Trigger payment prompt on customer phone
  - Handle payment callback/webhook
  - Verify payment status
- [ ] Create payment confirmation page
- [ ] Handle payment success/failure scenarios
- [ ] Send SMS/email confirmation (optional)
- [ ] Store transaction records in database

### Additional Payment Options (Future)
- [ ] Cash on Delivery (for local deliveries)
- [ ] In-Store Payment option

### Backend Requirements
- [ ] Create Order model and API endpoints
- [ ] Create Payment model for transaction tracking
- [ ] Integrate M-Pesa Daraja API SDK
- [ ] Set up webhook endpoint for M-Pesa callbacks
- [ ] Implement payment verification logic
- [ ] Update inventory after successful payment

**Estimated Duration:** 2-3 weeks

---

## Phase 6: Order Management & Customer Account

**Goal:** Allow customers to track orders and manage their account

### Order History
- [ ] Create order history page
- [ ] Display past orders with status (Pending, Processing, Shipped, Delivered)
- [ ] Show order details (items, payment, delivery info)
- [ ] Add order tracking capability
- [ ] Enable order cancellation (if not shipped)

### Customer Profile
- [ ] Build user profile page
- [ ] Allow editing of personal information
- [ ] Save multiple delivery addresses
- [ ] Display payment history
- [ ] Email/SMS preferences

### Backend Requirements
- [ ] Extend User model for profile data
- [ ] Create order status workflow
- [ ] Build order tracking API endpoints
- [ ] Implement email/SMS notifications for order updates

**Estimated Duration:** 1-2 weeks

---

## Phase 7: Admin Dashboard Frontend

**Goal:** Build admin interface for store management (backend APIs built in Phase 2)

### Product Management UI
- [ ] Admin login page and protected routes
- [ ] Product list page with search/filter
- [ ] Product create/edit forms
- [ ] Image upload interface (drag & drop)
- [ ] Category management interface
- [ ] Bulk product import/export tools

### Inventory Management UI
- [ ] Inventory dashboard showing stock levels (online + store)
- [ ] Quick inventory update interface
- [ ] Low-stock alerts display
- [ ] Inventory adjustment history
- [ ] Stock transfer interface (online ↔ store)

### Order Management
- [ ] View all orders
- [ ] Update order status
- [ ] Generate invoices
- [ ] Manage returns/refunds

### Analytics Dashboard
- [ ] Sales statistics and charts
- [ ] Popular products tracking
- [ ] Revenue reports (daily, weekly, monthly)
- [ ] Customer insights and metrics
- [ ] Export reports to CSV/PDF

### Frontend Requirements
- [ ] Build admin layout/navigation
- [ ] Create reusable admin components (tables, forms, charts)
- [ ] Implement admin routing and guards
- [ ] Add data visualization library (Chart.js or Recharts)
- [ ] File upload UI components

**Estimated Duration:** 3-4 weeks

---

## Phase 8: Advanced Features & Optimization

**Goal:** Enhance functionality and performance

### Customer Features
- [ ] Product reviews and ratings
- [ ] Size guide and fit recommendations
- [ ] Product recommendations ("You may also like")
- [ ] Filter products by size, color, price range
- [ ] Advanced search with autocomplete
- [ ] Newsletter subscription
- [ ] Referral program

### Technical Improvements
- [ ] Implement caching (Redis)
- [ ] Optimize images (lazy loading, compression)
- [ ] Add Progressive Web App (PWA) features
- [ ] Implement error tracking (Sentry)
- [ ] Add Google Analytics
- [ ] SEO optimization
- [ ] Performance monitoring
- [ ] Automated testing (unit, integration, e2e)

### Store Operations
- [ ] Inventory sync between online and physical store
- [ ] Real-time stock updates
- [ ] Barcode scanning for in-store sales
- [ ] Customer loyalty program
- [ ] Gift cards/vouchers

**Estimated Duration:** 4-6 weeks (ongoing)

---

## Phase 9: Deployment & Production

**Goal:** Launch the application to production (Online Store & POS System)

### Deployment Tasks
- [ ] Set up production PostgreSQL database (managed service)
- [ ] Configure production environment variables
- [ ] Deploy backend API to cloud service (Heroku, AWS, DigitalOcean)
- [ ] Deploy online store frontend to hosting service (Netlify, Vercel)
- [ ] Deploy POS application:
  - Desktop/tablet installation at physical store
  - Configure POS to connect to production API
  - Set up receipt printer and barcode scanner
  - Test payment processing (M-Pesa, cash)
- [ ] Set up domain name and SSL certificate
- [ ] Configure M-Pesa production credentials (live Daraja API)
- [ ] Set up automated database backups
- [ ] Implement monitoring and logging (error tracking, performance)
- [ ] Load testing and performance optimization
- [ ] Database migration from development to production
- [ ] Staff training for POS system
- [ ] Create backup/disaster recovery plan

### Documentation
- [ ] User guide for online customers
- [ ] Admin user manual (inventory, products, orders)
- [ ] POS system manual for cashiers
- [ ] POS troubleshooting guide (printer, scanner, payments)
- [ ] API documentation
- [ ] Deployment documentation
- [ ] Staff training materials

**Estimated Duration:** 1-2 weeks

---

## Priority Notes

### Immediate Next Steps (After Phase 1)
1. **Phase 2: Backend API Development** (PRIORITY)
   - Build inventory management API endpoints
   - Implement image upload and storage
   - Add admin authentication and product management APIs
   - Create shared database models for both online and POS

2. **Phase 3: POS System** (Can develop in parallel with Phase 4 after Phase 2)
   - Build POS terminal interface
   - Integrate barcode scanner and receipt printer
   - Implement M-Pesa and cash payment processing
   - Transaction logging and staff management
   - End-of-day reporting

3. **Phase 4: Shopping Cart & Wishlist** (Online Store)
   - Implement cart functionality with localStorage
   - Build wishlist feature

4. **Phase 5: M-Pesa Payment Integration** (Online Store)
   - M-Pesa Daraja API integration for online checkout
   - Implement checkout flow with M-Pesa STK Push

### Critical Dependencies
- **Image Upload & Storage** (Phase 2) requires:
  - Choice of storage solution:
    - **Development:** Local filesystem
    - **Production:** Cloud storage (AWS S3, Cloudinary, or DigitalOcean Spaces)
  - Image processing library (Pillow)
  - File upload size limits configuration
  - CORS configuration for file uploads

- **POS System** (Phase 3) requires:
  - Hardware procurement:
    - Barcode scanner (USB/Bluetooth)
    - Thermal receipt printer (ESC/POS compatible)
    - Cash drawer (optional, connects to printer)
    - Tablet or computer for POS terminal
    - Customer display (optional)
  - POS software choice:
    - Web-based (React app in browser)
    - Desktop app (Electron)
    - Mobile app (React Native for tablets)
  - Network connectivity at physical store
  - Shared PostgreSQL database access

- **M-Pesa Integration** (Phases 3 & 5) requires:
  - M-Pesa developer account with Safaricom
  - Testing phone numbers for sandbox environment
  - Production credentials for live deployment
  - SSL certificate for webhook callbacks
  - Integration for both online checkout and in-store POS payments

### Success Metrics

**Online Store:**
- Page load time < 3 seconds
- Mobile responsive design (100% compatibility)
- Cart abandonment rate < 30%
- Online payment success rate > 95%
- User satisfaction > 4.5/5 stars

**POS System:**
- Transaction completion time < 2 minutes
- Receipt print time < 5 seconds
- POS uptime > 99%
- Inventory sync accuracy 100%
- Payment success rate > 98%
- Staff onboarding time < 1 hour

**Overall:**
- Real-time inventory accuracy between online and store
- Zero overselling incidents
- Customer satisfaction > 4.5/5 stars

---

## Technology Decisions

### Database Architecture
- **Unified Database:** Single PostgreSQL database for both online store and POS system
- **Rationale:**
  - Ensures real-time inventory synchronization
  - Prevents overselling across channels
  - Simplifies reporting and analytics
  - Single source of truth for products, inventory, and transactions
- **Key Tables:**
  - `products` - Shared product catalog
  - `inventory` - Unified stock with `online_quantity` and `store_quantity` fields
  - `transactions/sales` - All sales (online and in-store)
  - `users` - Customer accounts (online)
  - `staff` - Store employees (POS)

### Payment Processing
- **Primary:** M-Pesa (Lipa Na M-Pesa Online / STK Push)
  - Used for both online checkout and in-store payments
- **Rationale:** Most popular mobile payment method in Kenya, trusted by customers
- **Additional:** Cash payments (in-store only)
- **Alternative:** Cash on Delivery for online orders (backup option)

### Deployment
- **Backend API:** Heroku, AWS, or DigitalOcean (Flask app)
  - Serves both online store and POS system
- **Online Store Frontend:** Vercel or Netlify (React app)
- **POS System:**
  - Web-based: Access via browser on store computer/tablet
  - Desktop: Electron app installed on store computer
  - Mobile: React Native app on tablet
- **Database:** PostgreSQL (development and production)
  - Development: Local PostgreSQL instance
  - Production: Managed PostgreSQL service (AWS RDS, Heroku Postgres, DigitalOcean Managed Database)
  - Accessed by both online store backend and POS system

### Future Considerations
- Integration with other payment methods (Airtel Money, PayPal)
- Multi-currency support for international customers
- Multi-store support for business expansion
