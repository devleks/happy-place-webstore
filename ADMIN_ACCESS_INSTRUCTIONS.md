# How to Access Admin Dashboard

## Problem Identified and Fixed

You've been experiencing issues accessing the admin dashboard with multiple authentication failures. We've identified and fixed **TWO CRITICAL BUGS** in the authentication system:

### Bug 1: Incorrect Redirect Logic in API Interceptor
**Location:** `frontend/src/services/api.js:65`

**Problem:** When a 401 error occurred with no refresh token, the system ALWAYS redirected to `/customer/login` regardless of whether you were trying to access admin or POS pages.

**Fix Applied:** The interceptor now checks the user type and current path to redirect to the appropriate login page:
- Employee accessing `/admin/*` → `/admin/login`
- Employee accessing `/pos/*` → `/pos/login`
- Customer → `/customer/login`

### Bug 2: Missing Refresh Token Conditional
**Location:** `frontend/src/context/AuthContext.js:53`

**Problem:** The code tried to set `refresh_token` in localStorage even when employee login didn't return one, potentially causing authentication issues.

**Fix Applied:** Added conditional check to only set refresh_token if it exists in the response.

---

## Testing the Admin Login

### Step 1: Clear Browser Session

**You MUST clear your browser storage before testing:**

**Option A: Clear via Browser DevTools (Recommended)**
1. Open browser DevTools (F12 or Right-click → Inspect)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Find **Local Storage** in left sidebar
4. Click on `http://localhost:3000`
5. **Right-click** and select **Clear** or click the **🗑️ Clear** button
6. Refresh the page (F5)

**Option B: Use Console to Clear**
1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Type and press Enter:
   ```javascript
   localStorage.clear()
   location.reload()
   ```

### Step 2: Access Admin Login

Navigate to: **http://localhost:3000/admin/login**

You should see:
- Purple-themed login page
- "Admin Portal" heading
- Email and password fields
- NO customer shopping header (cart/wishlist icons)
- NO Google Sign-In button

### Step 3: Login with Admin Credentials

**Email:** `admin@happyplace.co.ke`
**Password:** `admin123`

Click the **Login** button.

### Step 4: Verify Success

After successful login, you should:
- Be redirected to: `http://localhost:3000/admin/dashboard`
- See admin dashboard with:
  - Left sidebar navigation (Dashboard, Inventory, Orders, etc.)
  - Metrics cards (Today's Sales, Orders, Customers)
  - Recent activity feed
  - System alerts
- NO customer header/footer
- NO console errors related to authentication

---

## What Changed in This Session

### 1. Google OAuth Disabled for Localhost
**File:** `frontend/.env`
- Commented out `REACT_APP_GOOGLE_CLIENT_ID` to prevent origin errors

### 2. Layout Separation Implemented
**Files:** `frontend/src/App.js`, `frontend/src/components/CustomerLayout.js`
- Created `CustomerLayout` wrapper for customer pages
- Separated admin routes to use `AdminLayout`
- Customer header/footer no longer appear on admin pages

### 3. Authentication Fix #1: API Interceptor
**File:** `frontend/src/services/api.js` (lines 60-76)
```javascript
// BEFORE: Always redirected to customer login
window.location.href = '/customer/login';

// AFTER: Context-aware redirect
if (userType === 'employee' || window.location.pathname.startsWith('/admin')) {
  window.location.href = '/admin/login';
} else if (window.location.pathname.startsWith('/pos')) {
  window.location.href = '/pos/login';
} else {
  window.location.href = '/customer/login';
}
```

### 4. Authentication Fix #2: Refresh Token Handling
**File:** `frontend/src/context/AuthContext.js` (lines 54-57)
```javascript
// BEFORE: Always tried to set refresh_token
localStorage.setItem('refresh_token', response.data.refresh_token);

// AFTER: Conditional check
if (response.data.refresh_token) {
  localStorage.setItem('refresh_token', response.data.refresh_token);
}
```

---

## Current System Status

### Services Running
✅ **Backend:** http://127.0.0.1:5001 (Flask API)
✅ **Frontend:** http://localhost:3000 (React App)
✅ **Database:** PostgreSQL (happy_place_db)

### Verified Working
✅ Customer login and shopping cart
✅ Backend admin login endpoint (via curl test)
✅ Frontend compiled successfully
✅ Admin credentials reset to simple password

### Fixed Issues
✅ Google OAuth errors on localhost
✅ Customer header appearing on admin pages
✅ Incorrect redirect on 401 errors
✅ Refresh token handling for employee logins

---

## Troubleshooting

### Still Getting 401 Errors?

**Check the backend logs for the exact error:**

Look at the terminal running the backend for messages like:
```
127.0.0.1 - - [Date] "[31m[1mPOST /api/auth/employee/login HTTP/1.1[0m" 401 -
```

**Common causes:**
1. **Wrong credentials** - Make sure you're using exactly:
   - Email: `admin@happyplace.co.ke`
   - Password: `admin123` (lowercase, no special characters)

2. **Old token in localStorage** - Clear localStorage completely as shown in Step 1

3. **Private window with customer token** - Even in private window, if you visited the customer portal first, clear localStorage

### Verify Credentials Via Backend

If login still fails, verify credentials directly with curl:
```bash
curl -X POST 'http://127.0.0.1:5001/api/auth/employee/login' \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@happyplace.co.ke", "password": "admin123"}' \
  -s | python -m json.tool
```

**Expected response:**
```json
{
  "access_token": "eyJhbGc...",
  "employee": {
    "email": "admin@happyplace.co.ke",
    "full_name": "Admin User",
    "id": 1,
    "is_active": true,
    "role": "admin"
  }
}
```

### Reset Admin Password

If password verification fails, run:
```bash
cd backend
source venv/bin/activate
python test_admin_dashboard_endpoints.py
```

This will reset the admin password to `admin123`.

---

## What to Check in Browser DevTools

### Console (Should See NO Errors)
Open DevTools Console (F12 → Console tab)

**Good signs:**
- No red errors
- No "401 Unauthorized" messages
- No Google OAuth errors

### Network Tab (Check API Calls)
Open DevTools Network tab (F12 → Network)

**When you click Login:**
1. Look for `POST /api/auth/employee/login`
2. Click on it → Response tab
3. **Success = Status 200** with `access_token` in response
4. **Failure = Status 401** - check Response for error message

### Application/Storage (Check Tokens)
Open DevTools Application tab (Chrome) or Storage tab (Firefox)

**After successful login, you should see:**
- `token`: Long JWT string starting with "eyJ..."
- `user_type`: "employee"
- `refresh_token`: (May or may not be present - that's OK)

---

## Next Steps After Successful Login

Once you successfully access the admin dashboard, we'll continue with Phase 11 implementation:

### Remaining Phase 11 Features:
1. **Inventory Management** - Full CRUD for products/variants
2. **Order Management** - View, update, fulfill orders
3. **Customer Management** - View customer details and history
4. **Employee Management** - Add/edit employees, assign roles
5. **Promotions & Discounts** - Create and manage promotions
6. **Returns Management** - Process return requests
7. **Reports & Analytics** - Generate business reports
8. **System Settings** - Complete all settings tabs

---

## Summary of Fixes

**Two critical authentication bugs have been fixed:**

1. **API Interceptor Redirect Bug** - No longer sends admin users to customer login
2. **Refresh Token Handling Bug** - Now properly handles employee logins without refresh tokens

**The system is ready for testing. Please:**
1. Clear localStorage
2. Navigate to http://localhost:3000/admin/login
3. Login with admin@happyplace.co.ke / admin123
4. Report any errors you see in the browser console

**Current Status:** ✅ Both services running, fixes applied, ready for testing
