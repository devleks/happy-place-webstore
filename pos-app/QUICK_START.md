# 🚀 QUICK START GUIDE - Happy Place POS App

Get the POS desktop app running in 5 minutes!

## ⚡ Quick Setup

### Step 1: Install Dependencies

```bash
cd pos-app
npm install
```

**Note:** If `better-sqlite3` fails to install:

**macOS:**
```bash
xcode-select --install
npm install
```

**Windows:**
```bash
# Install Visual Studio Build Tools first
npm install --global windows-build-tools
npm install
```

**Linux:**
```bash
sudo apt-get install build-essential
npm install
```

---

### Step 2: Copy React Components

Copy your existing POS components from the employee portal:

```bash
# Create src directory structure
mkdir -p src/{components,pages,services,styles,context}

# Copy CashierKiosk component
cp ../frontend-employee/src/pages/employee/CashierKiosk.js src/pages/

# Copy shared components
cp -r ../frontend-employee/src/components/* src/components/

# Copy styles
cp -r ../frontend-employee/src/styles/* src/styles/

# Copy context
cp -r ../frontend-employee/src/context/* src/context/
```

---

### Step 3: Create React Entry Files

**src/index.js:**
```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**src/App.js:**
```javascript
import React from 'react';
import CashierKiosk from './pages/CashierKiosk';
import { AuthProvider } from './context/AuthContext';
import './styles/App.css';

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <CashierKiosk />
      </div>
    </AuthProvider>
  );
}

export default App;
```

**public/index.html:**
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Happy Place POS</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
```

---

### Step 4: Update API Service

**src/services/api.js:**
```javascript
// Use Electron APIs instead of direct axios
const api = {
  async getProducts() {
    return await window.electron.db.getProducts();
  },

  async searchProducts(query) {
    return await window.electron.db.searchProducts(query);
  },

  async createTransaction(transaction) {
    return await window.electron.db.createTransaction(transaction);
  },

  async printReceipt(receipt) {
    return await window.electron.hardware.printReceipt(receipt);
  },

  // Listen for barcode scans
  onBarcodeScan(callback) {
    window.electron.hardware.onBarcodeScanned(callback);
  }
};

export default api;
```

---

### Step 5: Start Development

```bash
# Terminal 1: Start backend API (if not running)
cd ../backend
source venv/bin/activate
python app.py

# Terminal 2: Start POS app
cd ../pos-app
npm start
```

The app will:
1. Start React dev server on port 3003
2. Launch Electron window
3. Initialize SQLite database
4. Start background sync
5. Connect to backend API

---

## 🎯 First Run Checklist

### ✅ Verify Everything Works

1. **App Launches**
   - Electron window opens
   - No console errors
   - UI loads correctly

2. **Database Initialized**
   - Check: `~/Library/Application Support/happy-place-pos/pos.db` exists
   - Tables created successfully

3. **Products Synced**
   - Products appear in search
   - Stock quantities correct
   - Images load

4. **Offline Mode**
   - Disconnect internet
   - App still works
   - Transactions saved locally

5. **Sync Works**
   - Reconnect internet
   - Pending transactions upload
   - Status indicator updates

---

## 🔧 Common Issues & Fixes

### Issue: "better-sqlite3 not found"

**Fix:**
```bash
npm rebuild better-sqlite3
```

### Issue: "Port 3003 already in use"

**Fix:**
```bash
# Change port in package.json
"react-start": "cross-env BROWSER=none PORT=3004 react-scripts start"
```

### Issue: "Cannot connect to backend"

**Fix:**
1. Verify backend is running: `http://localhost:5001/api/health`
2. Check `.env` file has correct `REACT_APP_API_URL`
3. Check firewall settings

### Issue: "Database locked"

**Fix:**
```bash
# Close all app instances
pkill -f "Happy Place POS"

# Delete database
rm ~/Library/Application\ Support/happy-place-pos/pos.db

# Restart app
npm start
```

---

## 📱 Testing Offline Mode

### Test Scenario 1: Create Transaction Offline

1. Start app (online)
2. Wait for products to sync
3. Disconnect internet
4. Create a transaction
5. Verify it's saved locally
6. Reconnect internet
7. Verify it syncs to backend

### Test Scenario 2: Hold/Recall

1. Add items to cart
2. Click "Hold Transaction"
3. Close app
4. Reopen app
5. Click "Recall"
6. Verify items restored

---

## 🎨 Customization

### Change Store Name

**src/App.js:**
```javascript
const STORE_NAME = "Happy Place Boutique";
```

### Change Tax Rate

**src/services/api.js:**
```javascript
const TAX_RATE = 0.16; // 16% VAT
```

### Change Receipt Footer

**electron/hardware.js:**
```javascript
const RECEIPT_FOOTER = "Thank you for shopping with us!";
```

---

## 🚀 Next Steps

### Phase 1: Basic Functionality (Current)
- ✅ Electron setup
- ✅ SQLite database
- ✅ Background sync
- ⏳ Copy React components
- ⏳ Test offline mode

### Phase 2: Hardware Integration
- [ ] Barcode scanner testing
- [ ] Receipt printer setup
- [ ] Cash drawer integration

### Phase 3: Polish & Deploy
- [ ] Error handling
- [ ] Loading states
- [ ] Build installers
- [ ] User testing

---

## 📚 Useful Commands

```bash
# Development
npm start                 # Start dev mode
npm run react-start       # React only
npm run electron-start    # Electron only

# Building
npm run build            # Build React app
npm run electron-build   # Build Electron app
npm run dist             # Build installers

# Debugging
npm run electron-start   # See console logs
# Open DevTools: View → Toggle Developer Tools

# Database
sqlite3 ~/Library/Application\ Support/happy-place-pos/pos.db
.tables                  # List tables
.schema products         # View schema
SELECT * FROM products;  # Query data
```

---

## 🆘 Need Help?

### Check Logs

**Electron Main Process:**
```bash
# macOS/Linux
tail -f ~/Library/Logs/happy-place-pos/main.log

# Windows
type %APPDATA%\happy-place-pos\logs\main.log
```

**React Console:**
- Open DevTools in app
- Check Console tab

### Debug Mode

Start with debug logging:
```bash
DEBUG=* npm start
```

### Reset Everything

```bash
# Delete database
rm -rf ~/Library/Application\ Support/happy-place-pos/

# Clean build
rm -rf node_modules dist build
npm install
npm start
```

---

## ✅ Success Criteria

You're ready to proceed when:

- ✅ App launches without errors
- ✅ Products load from backend
- ✅ Can create transactions
- ✅ Offline mode works
- ✅ Sync happens automatically
- ✅ Receipt printing works (or simulated)

---

**Ready to build? Let's go!** 🚀

**Next:** Copy your React components and start testing!
