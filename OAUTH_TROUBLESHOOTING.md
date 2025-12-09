# Google OAuth Troubleshooting Guide

## Error: "flowName=GeneralOAuthFlow"

This error typically appears when there's a mismatch between the OAuth configuration in Google Cloud Console and your application settings.

---

## 🔍 Common Causes & Solutions

### 1. **Redirect URI Mismatch**

**Problem:** The redirect URI configured in Google Cloud Console doesn't match the actual redirect from your app.

**Solution:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click on your OAuth 2.0 Client ID
3. Add the following **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://127.0.0.1:3000
   ```

4. Add the following **Authorized redirect URIs**:
   ```
   http://localhost:3000
   http://localhost:3000/customer/login
   http://127.0.0.1:3000
   http://127.0.0.1:3000/customer/login
   ```

5. Click **Save**

---

### 2. **Client ID Mismatch**

**Problem:** The Client ID in your frontend doesn't match the one from Google Cloud Console.

**Current Configuration:**
- Client ID: `200165451700-8251spnb0v3uvf6t7sgrdhuldmegohqm.apps.googleusercontent.com`

**Verify:**
1. Check `frontend/.env`:
   ```bash
   REACT_APP_GOOGLE_CLIENT_ID=200165451700-8251spnb0v3uvf6t7sgrdhuldmegohqm.apps.googleusercontent.com
   ```

2. Check `backend/config.py`:
   ```python
   GOOGLE_CLIENT_ID = '200165451700-8251spnb0v3uvf6t7sgrdhuldmegohqm.apps.googleusercontent.com'
   ```

3. Restart both frontend and backend after changes:
   ```bash
   # Frontend
   cd frontend
   # Press Ctrl+C to stop
   npm start

   # Backend
   cd backend
   # Press Ctrl+C to stop
   python app.py
   ```

---

### 3. **OAuth Consent Screen Not Configured**

**Problem:** The OAuth consent screen needs to be set up in Google Cloud Console.

**Solution:**

1. Go to [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. Select **External** user type (for testing with any Google account)
3. Fill in required fields:
   - **App name**: Happy Place Boutique
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Add scopes (minimum required):
   - `email`
   - `profile`
   - `openid`
5. Add test users (your Google account emails)
6. Click **Save and Continue**

---

### 4. **Browser Console Errors**

**Check for errors:**

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors like:
   - "Invalid Client ID"
   - "Redirect URI mismatch"
   - "Access blocked: Authorization Error"

**Common Fixes:**
- Clear browser cache and cookies
- Try in Incognito/Private window
- Disable browser extensions that might block popups

---

### 5. **CORS Issues**

**Problem:** Backend is not allowing requests from frontend.

**Check:**
```python
# backend/app.py
CORS(app)  # Should allow all origins in development
```

**Fix if needed:**
```python
from flask_cors import CORS

# Allow specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## 🧪 Testing Steps

### Step 1: Verify Backend is Running
```bash
curl http://localhost:5001/api/products
# Should return JSON with products
```

### Step 2: Verify Frontend is Running
- Navigate to: http://localhost:3000
- Should see the webstore homepage

### Step 3: Test OAuth Flow
1. Navigate to: http://localhost:3000/customer/login
2. Click "Sign in with Google" button
3. **Expected:** Google OAuth popup appears
4. **If popup is blocked:** Check browser popup blocker
5. **If "Access blocked":** Check OAuth consent screen configuration
6. **If "Redirect URI mismatch":** Update redirect URIs in Google Cloud Console

---

## 📝 Debug Checklist

- [ ] Google Cloud Console project exists
- [ ] OAuth 2.0 Client ID created
- [ ] OAuth consent screen configured
- [ ] Test users added (if app not published)
- [ ] Redirect URIs include `http://localhost:3000`
- [ ] JavaScript origins include `http://localhost:3000`
- [ ] Frontend `.env` has correct `REACT_APP_GOOGLE_CLIENT_ID`
- [ ] Backend `config.py` has correct `GOOGLE_CLIENT_ID`
- [ ] Both frontend and backend restarted after config changes
- [ ] Browser cache cleared
- [ ] Popup blocker disabled for localhost:3000
- [ ] No CORS errors in browser console

---

## 🔧 Alternative: Test Without Google OAuth

If you want to test the authentication system without Google OAuth:

1. **Use Email/Password Login:**
   - Navigate to: http://localhost:3000/customer/login
   - Enter email and password instead of using Google button
   - This uses the `/api/auth/customer/login` endpoint

2. **Register New Customer:**
   - Navigate to: http://localhost:3000/register
   - Fill in registration form
   - Creates account without OAuth

3. **Employee Login:**
   - Navigate to: http://localhost:3000/employee/login
   - Use employee credentials from database
   - Test 2FA flow if enabled

---

## 📊 Expected OAuth Flow

### Successful Flow:
```
1. User clicks "Sign in with Google"
2. GoogleOAuthProvider opens popup
3. User authenticates with Google
4. Google redirects with ID token
5. Frontend receives credential response
6. Frontend calls POST /api/auth/customer/google-oauth with ID token
7. Backend verifies token with Google
8. Backend creates/links customer account
9. Backend returns access + refresh tokens
10. Frontend stores tokens in localStorage
11. Frontend redirects to /dashboard
```

### Failed Flow Indicators:
- **No popup:** Popup blocker or Client ID issue
- **"Access blocked":** Consent screen not configured
- **"Redirect URI mismatch":** URIs not added to Google Console
- **"Invalid ID token":** Backend verification failed
- **400 error:** Check backend logs for specific error

---

## 🐛 Backend Logs

To see detailed OAuth errors:

```bash
# The backend logs should show:
POST /api/auth/customer/google-oauth HTTP/1.1" 200 -  # Success
POST /api/auth/customer/google-oauth HTTP/1.1" 400 -  # Error
```

Check for specific error messages in the response:
- "Invalid Google ID token"
- "Google token verification failed"
- "Email already exists with different provider"

---

## 🎯 Quick Fix Commands

### Reset Frontend Environment
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Verify Backend Config
```bash
cd backend
python -c "from config import Config; print(f'Client ID: {Config.GOOGLE_CLIENT_ID}')"
```

### Test Backend OAuth Endpoint
```bash
# This will fail without valid token, but shows endpoint is working
curl -X POST http://localhost:5001/api/auth/customer/google-oauth \
  -H "Content-Type: application/json" \
  -d '{"id_token":"test"}'

# Expected: 400 error with "Invalid Google ID token"
```

---

## 📞 Still Having Issues?

1. **Check Google Cloud Console Status:**
   - https://status.cloud.google.com/
   - Verify no service outages

2. **Review Google OAuth Documentation:**
   - https://developers.google.com/identity/protocols/oauth2

3. **Check Browser Compatibility:**
   - Chrome/Edge: Fully supported
   - Firefox: Fully supported
   - Safari: May have popup blocker issues

4. **Network Issues:**
   - Check firewall settings
   - Verify internet connection
   - Try different network (e.g., mobile hotspot)

---

## ✅ Success Indicators

You'll know OAuth is working when:
1. ✅ Google popup opens without being blocked
2. ✅ Google account selector appears
3. ✅ After selecting account, popup closes automatically
4. ✅ User is redirected to `/dashboard`
5. ✅ User data appears in dashboard
6. ✅ Backend logs show: `POST /api/auth/customer/google-oauth HTTP/1.1" 200 -`
7. ✅ Database has new customer record with `oauth_provider='google'`

---

**Last Updated:** December 3, 2025
**Issue:** OAuth flowName=GeneralOAuthFlow error
**Status:** Troubleshooting in progress
