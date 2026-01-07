# API Routes Testing - Day 1

## Authentication Routes Discovered

Based on code analysis in `routes/auth_routes.py` and `routes/auth.py`:

### Customer Portal (Port 3000)
- POST `/api/auth/customer/login` - Customer login
- Blueprint: `auth_bp` with prefix `/api/auth`

### Admin Portal (Port 3001)
- POST `/api/auth/admin/login` - Admin login  
- Blueprint: `auth_bp` with prefix `/api/auth`

### Employee Portal (Port 3002)
- POST `/api/auth/employee/login` - Employee login
- POST `/api/auth/employee/pin-login` - POS PIN login
- Blueprint: `auth_bp` with prefix `/api/auth`

### Common Auth Routes
- GET `/api/auth/me` - Get current user info
- POST `/api/auth/refresh` - Refresh JWT token
- POST `/api/auth/logout` - Logout

## Testing Results

| Route | Method | Expected Status | Actual Status | Response Time | Notes |
|-------|--------|----------------|---------------|---------------|-------|
| /health | GET | 200/503 | 503 | 15ms | DB health check warning |
| /api/products | GET | 200 | 200 | 96ms | ✅ Working |
| /api/categories | GET | 200 | 200 | 2ms | ✅ Working |
| /api/products/:slug | GET | 200 | 200 | 22ms | ✅ Fixed - SP created |
| /api/auth/customer/login | POST | 200 | 500 | 4ms | ⚠️ Internal error |
| /api/auth/employee/login | POST | 200 | ? | ? | Not tested yet |
| /api/auth/admin/login | POST | 200 | ? | ? | Not tested yet |

## Summary

**Performance:** ✅ ALL responses < 100ms  
**Routes:** ⚠️ Auth routes need debugging  
**Database:** ✅ Stored procedures working  

