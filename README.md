# Happy Place Boutique - E-commerce Store

A full-stack e-commerce web application for women's and maternity clothing with both online shopping and physical store location features.

## Features

- **Product Catalog**: Browse women's and maternity clothing by category
- **Search & Filter**: Search products and filter by category, price
- **User Authentication**: Register and login functionality
- **Unified Inventory**: Track stock for both online and physical store
- **Store Locator**: Find physical store location with hours and contact info
- **Responsive Design**: Mobile-friendly interface

## Tech Stack

### Backend
- Python 3.x
- Flask (Web framework)
- SQLAlchemy (ORM)
- Flask-JWT-Extended (Authentication)
- PostgreSQL/SQLite (Database)

### Frontend
- React 18
- React Router (Routing)
- Axios (API calls)
- CSS3 (Styling)

## Project Structure

```
happy_place_webstore/
├── backend/
│   ├── app.py              # Flask application
│   ├── models.py           # Database models
│   ├── routes.py           # API endpoints
│   ├── config.py           # Configuration
│   ├── seed.py             # Database seeding script
│   └── requirements.txt    # Python dependencies
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/     # Reusable components
    │   ├── pages/          # Page components
    │   ├── services/       # API service layer
    │   ├── context/        # React context
    │   ├── styles/         # CSS files
    │   ├── App.js          # Main App component
    │   └── index.js        # Entry point
    └── package.json        # Node dependencies
```

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and update the following:
   - `JWT_SECRET_KEY`: Your secret key for JWT tokens
   - `DATABASE_URL`: Your database connection string (optional, defaults to SQLite)

5. **Initialize the database with sample data:**
   ```bash
   python seed.py
   ```

6. **Run the Flask server:**
   ```bash
   python app.py
   ```

   The backend API will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory (in a new terminal):**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

   The frontend will be available at `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user (requires auth)

### Products
- `GET /api/products` - Get all products (supports pagination, search, filters)
- `GET /api/products/:slug` - Get product by slug

### Categories
- `GET /api/categories` - Get all categories
- `GET /api/categories/:slug` - Get category by slug

### Inventory
- `GET /api/inventory/product/:id` - Get inventory for a product

### Store Locations
- `GET /api/store-locations` - Get all store locations
- `GET /api/store-locations/:id` - Get store location by ID

## Database Models

- **User**: Customer accounts with authentication
- **Category**: Product categories (Women's, Maternity, etc.)
- **Product**: Product information with pricing and details
- **Inventory**: Stock tracking with separate online/store quantities
- **StoreLocation**: Physical store details with hours and location

## Sample Data

The seed script creates:
- 7 categories (Women's Tops, Bottoms, Dresses, Maternity Tops, Bottoms, Dresses, Nursing Wear)
- 11 sample products with multiple sizes and colors
- Inventory for all product variants
- 1 physical store location in San Francisco

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
python app.py
```

### Frontend Development
```bash
cd frontend
npm start
```

## Testing

### Test User Registration
1. Go to `http://localhost:3000/register`
2. Create an account
3. Login and browse products

### Test Product Search
1. Use the search bar in the header
2. Filter by category using navigation links
3. View product details

### Test Store Locator
1. Navigate to "Store Location" in the menu
2. View store hours, address, and contact info

## Future Enhancements

- Shopping cart functionality
- Checkout and payment processing
- Order history
- Product reviews
- Admin dashboard for inventory management
- Real-time inventory updates
- Email notifications
- Google Maps integration
- Image upload for products

## License

This project is for educational purposes.

## Support

For questions or issues, please contact the development team.
