# Test Credentials - Happy Place Boutique

**Environment:** Development  
**Created:** December 12, 2025  
**Database:** PostgreSQL (happy_place_db)

---

## 🔐 Employee Test Accounts

All passwords follow the pattern: `[Role]123!`

### 1. ADMIN - Full System Access

```
Email:    admin@happyplace.com
Password: Admin123!
Name:     Admin User
Role:     admin
```

**Permissions:**
- ✅ All system permissions
- ✅ User management
- ✅ System settings
- ✅ Financial reports
- ✅ GDPR operations

---

### 2. MANAGER - Store Management

```
Email:    manager@happyplace.com
Password: Manager123!
Name:     Manager Sarah
Role:     manager
```

**Permissions:**
- ✅ View reports
- ✅ Manage inventory
- ✅ Manage employees (limited)
- ✅ Process refunds
- ❌ System settings

---

### 3. CASHIER - POS Operations

```
Email:    cashier@happyplace.com
Password: Cashier123!
Name:     Cashier John
Role:     cashier
```

**Permissions:**
- ✅ POS operations
- ✅ Process sales
- ✅ Handle payments
- ❌ View reports
- ❌ Manage inventory

---

### 4. STAFF - Basic Operations

```
Email:    staff@happyplace.com
Password: Staff123!
Name:     Staff Mary
Role:     staff
```

**Permissions:**
- ✅ View inventory
- ✅ Assist customers
- ❌ POS operations
- ❌ Reports

---

### 5. PACKER - Order Fulfillment

```
Email:    packer@happyplace.com
Password: Packer123!
Name:     Packer David
Role:     packer
```

**Permissions:**
- ✅ View orders
- ✅ Pack orders
- ✅ Update fulfillment status
- ❌ Process payments

---

### 6. SHIPPER - Shipping Operations

```
Email:    shipper@happyplace.com
Password: Shipper123!
Name:     Shipper Lisa
Role:     shipper
```

**Permissions:**
- ✅ View shipments
- ✅ Update shipping status
- ✅ Print labels
- ❌ Modify orders

---

## 👥 Customer Test Account

```
Email:    customer@test.com
Password: Customer123!
Name:     Test Customer
Phone:    +254712345678
```

**Features:**
- ✅ GDPR consent given
- ❌ Marketing consent (opted out)
- ✅ Active account
- ❌ Email not verified
- 🔐 All PII encrypted

---

## 🏪 Store Information

**Store Location:**
```
Name:     Happy Place Main Store
Address:  123 Main Street
City:     Nairobi
State:    Nairobi County
Zip:      00100
Phone:    +254700000000
Email:    store@happyplace.com
```

---

## 📁 Product Categories

1. Women's Tops
2. Women's Bottoms
3. Women's Dresses
4. Maternity Tops
5. Maternity Bottoms
6. Maternity Dresses
7. Nursing Wear

---

## 🔐 Encryption Keys

**Status:** ✅ Active and working

All customer PII is encrypted using MultiFernet encryption:
- Customer emails (hash + encrypted)
- Customer names (first & last)
- Phone numbers
- Addresses
- Payment information

**Encryption Keys Configured:**
- `CUSTOMER_ENCRYPTION_KEYS` - 2 keys (primary + secondary)
- `ADDRESS_ENCRYPTION_KEYS` - 2 keys (primary + secondary)
- `PAYMENT_ENCRYPTION_KEYS` - 2 keys (primary + secondary)

---

## 🌐 API Endpoints

**Base URL:** `http://localhost:5001`

**Health Check:**
```bash
GET /health
```

**Customer Login:**
```bash
POST /api/auth/customer/login
Content-Type: application/json

{
  "email": "customer@test.com",
  "password": "Customer123!"
}
```

**Employee Login:**
```bash
POST /api/auth/employee/login
Content-Type: application/json

{
  "email": "admin@happyplace.com",
  "password": "Admin123!"
}
```

---

## 📊 Database Summary

- **Employees:** 6 (one per role)
- **Customers:** 1 (test customer)
- **Categories:** 7 (product categories)
- **Store Locations:** 1 (main store)
- **Products:** 0 (ready to add)
- **Orders:** 0 (ready to create)

---

## ⚠️ Security Notes

**Development Only:**
- These credentials are for **development/testing only**
- **DO NOT** use these in production
- Change all passwords before production deployment
- Generate new encryption keys for production

**Production Checklist:**
- [ ] Generate strong passwords (32+ characters)
- [ ] Generate new encryption keys
- [ ] Enable 2FA for admin accounts
- [ ] Set up proper RBAC permissions
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Set up monitoring

---

## 🧪 Testing Scenarios

### Test Customer Registration
```bash
curl -X POST http://localhost:5001/api/auth/customer/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newcustomer@test.com",
    "password": "NewCustomer123!",
    "first_name": "New",
    "last_name": "Customer",
    "phone": "+254700000001",
    "gdpr_consent": true
  }'
```

### Test Employee Login
```bash
curl -X POST http://localhost:5001/api/auth/employee/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cashier@happyplace.com",
    "password": "Cashier123!"
  }'
```

### Test Health Check
```bash
curl http://localhost:5001/health
```

---

**Last Updated:** December 12, 2025  
**Database:** Clean and ready for development  
**Encryption:** ✅ Working with new keys
