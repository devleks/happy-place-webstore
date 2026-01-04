# PWA Test Credentials

## Default Employee Accounts

After clearing your browser's IndexedDB and refreshing the app, you can login with:

### Admin Account
- **Email**: `admin@happyplace.com`
- **Password**: `admin123`
- **PIN**: `0000`
- **Role**: Administrator (full access)

### Manager Account
- **Email**: `manager1@happyplace.co.ke`
- **Password**: `manager123`
- **PIN**: `1111`
- **Role**: Manager (shift management, reports)

### Cashier Account
- **Email**: `cashier1@happyplace.co.ke`
- **Password**: `cashier123`
- **PIN**: `2222`
- **Role**: Cashier (POS operations)

## How to Reset Database

If you're getting "Invalid email or password" errors:

1. **Open Chrome DevTools** (F12)
2. Go to **Application** tab
3. In left sidebar, find **Storage** → **IndexedDB**
4. Right-click **HappyPlacePOS** → **Delete database**
5. **Refresh the page** (F5)
6. Database will auto-seed with test accounts
7. Try logging in again

## Quick Login Buttons

The login page has quick login buttons for testing:
- **Admin** button - auto-fills admin credentials
- **Manager** button - auto-fills manager credentials
- **Cashier** button - auto-fills cashier credentials

Just click the button and then click "Login to POS"!

## Syncing Real Employees from Backend

To sync actual employees from the backend API:

1. Login with admin credentials
2. The app will attempt auto-sync on login
3. Or manually set sync token in browser console:
   ```javascript
   // In browser console:
   import('./db').then(db => {
     db.setMetadata('sync_token', 'YOUR_BACKEND_JWT_TOKEN');
   });
   ```
4. Refresh the app - employees will sync from backend

## Notes

- Passwords are **plain text** for local development only
- In production, use backend API for authentication
- PIN login is for quick cashier access
- All data is stored locally in IndexedDB (offline-first)
