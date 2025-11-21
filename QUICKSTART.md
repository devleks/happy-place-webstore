# Quick Start Guide

Get Happy Place Boutique running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

## 1. Backend Setup (Terminal 1)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed database with sample data
python seed.py

# Start backend server
python app.py
```

Backend will run at: http://localhost:5000

## 2. Frontend Setup (Terminal 2)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start React app
npm start
```

Frontend will run at: http://localhost:3000

## 3. Explore the App

### Browse Products
- Visit http://localhost:3000
- Click "Shop Now" or use the navigation menu
- Browse by category: Women's Tops, Maternity, etc.
- Use the search bar to find specific items

### Create an Account
- Click "Sign Up" in the header
- Fill in your details
- Login with your credentials

### View Store Location
- Click "Store Location" in the menu
- See hours, address, and contact information

## Sample Products Included

The seed script creates:
- 11 products across 7 categories
- Multiple sizes and colors for each product
- Realistic inventory for online and in-store
- 1 physical store location

## Troubleshooting

**Port already in use?**
- Backend: Change port in `backend/app.py`
- Frontend: Set `PORT=3001` before `npm start`

**Database errors?**
- Delete `backend/happy_place.db` and run `python seed.py` again

**Module not found?**
- Backend: Make sure virtual environment is activated
- Frontend: Run `npm install` again

## Next Steps

- Customize products in `backend/seed.py`
- Add your own branding and colors
- Extend with shopping cart functionality
- Add payment processing
- Deploy to production

Enjoy building your online store!
