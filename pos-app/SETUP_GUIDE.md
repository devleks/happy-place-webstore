# Happy Place POS - Setup Guide

## 🚀 First-Time Setup (Sync from Backend)

The POS PWA needs to sync employee and product data from your Happy Place backend API before you can use it.

### Step 1: Start the Backend API

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```

Backend should be running at: `http://127.0.0.1:5001`

### Step 2: Get Backend Auth Token

1. Open the main Happy Place admin panel: http://127.0.0.1:5001
2. Login with admin credentials:
   - **Email**: `admin@happyplace.com`
   - **Password**: `admin123`
3. Open browser DevTools (F12)
4. Go to **Console** tab
5. Type: `localStorage.getItem('access_token')`
6. Copy the token (the long string **without quotes**)

### Step 3: Open POS Setup Page

1. Open POS app: http://localhost:3003
2. Go to setup page: http://localhost:3003/#/setup
3. Paste the auth token from Step 2
4. Click **"🔄 Sync from Backend"**

The PWA will:
- ✅ Fetch all employees from backend
- ✅ Fetch all products from backend
- ✅ Store data locally in IndexedDB
- ✅ Redirect you to login page

### Step 4: Login with Backend Credentials

After sync completes, you can login with any employee from the backend:

**Example employees** (from backend seed data):
- **Admin**: `admin@happyplace.com` / `admin123`
- **Manager**: `manager1@happyplace.co.ke` / `manager123`
- **Cashier**: `cashier1@happyplace.co.ke` / `cashier123`

---

## 🔄 Re-sync Data from Backend

If backend data changes (new employees, products, etc.), you can re-sync:

### Method 1: Via Setup Page
1. Go to: http://localhost:3003/#/setup
2. Paste a fresh auth token
3. Click "Sync from Backend"

### Method 2: Via Browser Console
```javascript
// In browser console (F12)
import('./db').then(async (db) => {
  const token = 'YOUR_BACKEND_JWT_TOKEN';
  const result = await db.initializeFromBackend(token);
  console.log('Sync result:', result);
});
```

---

## 🧪 Skip Setup (Use Test Data)

For testing without backend connection:

1. On setup page, click **"Skip (Use Test Data)"**
2. Clear IndexedDB in DevTools (Application → IndexedDB → Delete)
3. Refresh page - test employees will be seeded

**Test credentials** (local only):
- **Admin**: `admin@happyplace.com` / `admin123`
- **Manager**: `manager1@happyplace.co.ke` / `manager123`
- **Cashier**: `cashier1@happyplace.co.ke` / `cashier123`

---

## 📋 What Data Gets Synced

### Employees
- Email, name, role (admin/manager/cashier)
- PIN for quick login
- Active status

### Products
- SKU, barcode, name, description
- Category, price, cost
- Quantity (stock level)
- Image URLs

### What's NOT Synced
- Orders (created locally, synced to backend when online)
- Shifts (created locally, synced to backend when online)
- Transactions (created locally, synced to backend when online)

---

## 🔧 Troubleshooting

### "Invalid email or password" on login

**Cause**: IndexedDB has old data or no backend sync

**Solution**:
1. Go to setup page: http://localhost:3003/#/setup
2. Sync from backend with fresh token
3. OR: Clear IndexedDB (DevTools → Application → IndexedDB → Delete HappyPlacePOS)
4. Refresh page

### "Backend API error: 401"

**Cause**: Auth token expired or invalid

**Solution**:
1. Login to backend admin panel again
2. Get fresh token from console
3. Re-run sync

### "Backend API error: 404"

**Cause**: Backend is not running

**Solution**:
1. Start backend: `cd backend && python app.py`
2. Verify backend is at: http://127.0.0.1:5001
3. Try sync again

### No employees synced

**Cause**: Backend has no employee data

**Solution**:
1. Seed backend database: `cd backend && python seed.py`
2. Re-run POS sync

---

## 🎯 Production Setup

For production deployment:

1. **Set Backend API URL**:
   ```bash
   # In pos-app/.env
   REACT_APP_API_URL=https://your-backend-domain.com
   ```

2. **Build PWA**:
   ```bash
   cd pos-app
   npm run build
   ```

3. **Deploy build/ folder** to web server

4. **Setup HTTPS** (required for PWA features)

5. **First-time sync**: Open `/setup` route on deployed PWA

---

## 💡 Tips

- **Auto-sync**: PWA checks for updates every 24 hours
- **Offline mode**: All POS features work without internet
- **Background sync**: Shifts/transactions sync automatically when online
- **Multi-device**: Sync same data to multiple POS terminals

---

**Need help?** Check [PWA_IMPLEMENTATION_COMPLETE.md](PWA_IMPLEMENTATION_COMPLETE.md) for full documentation.
