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

## Phase 3: Shopping Cart & Wishlist

**Goal:** Enable customers to add items to cart and save favorites

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

## Phase 4: Checkout & Payment Integration

**Goal:** Complete the purchase flow with M-Pesa payment integration for Kenya

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

## Phase 5: Order Management & Customer Account

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

## Phase 6: Admin Dashboard Frontend

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

## Phase 7: Advanced Features & Optimization

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

## Phase 8: Deployment & Production

**Goal:** Launch the application to production

### Deployment Tasks
- [ ] Set up production PostgreSQL database (managed service)
- [ ] Configure production environment variables
- [ ] Deploy backend to cloud service (Heroku, AWS, DigitalOcean)
- [ ] Deploy frontend to hosting service (Netlify, Vercel)
- [ ] Set up domain name and SSL certificate
- [ ] Configure M-Pesa production credentials (live Daraja API)
- [ ] Set up automated database backups
- [ ] Implement monitoring and logging (error tracking, performance)
- [ ] Load testing and performance optimization
- [ ] Database migration from development to production

### Documentation
- [ ] User guide for customers
- [ ] Admin user manual
- [ ] API documentation
- [ ] Deployment documentation

**Estimated Duration:** 1-2 weeks

---

## Priority Notes

### Immediate Next Steps (After Phase 1)
1. **Phase 2: Backend API Development**
   - Build inventory management API endpoints
   - Implement image upload and storage
   - Add admin authentication and product management APIs
2. **Phase 3: Shopping Cart & Wishlist**
   - Implement cart functionality with localStorage
   - Build wishlist feature
3. **Phase 4: M-Pesa Payment Integration**
   - Begin M-Pesa Daraja API research and setup
   - Implement checkout flow with M-Pesa STK Push

### Critical Dependencies
- **Image Upload & Storage** (Phase 2) requires:
  - Choice of storage solution:
    - **Development:** Local filesystem
    - **Production:** Cloud storage (AWS S3, Cloudinary, or DigitalOcean Spaces)
  - Image processing library (Pillow)
  - File upload size limits configuration
  - CORS configuration for file uploads

- **M-Pesa Integration** (Phase 4) requires:
  - M-Pesa developer account with Safaricom
  - Testing phone numbers for sandbox environment
  - Production credentials for live deployment
  - SSL certificate for webhook callbacks

### Success Metrics
- Page load time < 3 seconds
- Mobile responsive design (100% compatibility)
- Cart abandonment rate < 30%
- Payment success rate > 95%
- User satisfaction > 4.5/5 stars

---

## Technology Decisions

### Payment Processing
- **Primary:** M-Pesa (Lipa Na M-Pesa Online / STK Push)
- **Rationale:** Most popular mobile payment method in Kenya, trusted by customers
- **Alternative:** Cash on Delivery for backup option

### Deployment
- **Backend:** Heroku, AWS, or DigitalOcean (Flask app)
- **Frontend:** Vercel or Netlify (React app)
- **Database:** PostgreSQL (development and production)
  - Development: Local PostgreSQL instance
  - Production: Managed PostgreSQL service (AWS RDS, Heroku Postgres, DigitalOcean Managed Database)

### Future Considerations
- Integration with other payment methods (Airtel Money, PayPal)
- Multi-currency support for international customers
- Multi-store support for business expansion
