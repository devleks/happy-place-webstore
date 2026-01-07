# M-Pesa Sandbox Setup Guide

## ✅ Current Status
- **Authentication:** Working ✅
- **Shortcode Issue:** Needs Lipa Na M-Pesa Online configuration

---

## 🔧 How to Configure Your Shortcode for STK Push

### Step 1: Access Daraja Portal
1. Go to https://developer.safaricom.co.ke
2. Login with your credentials
3. Navigate to "My Apps"

### Step 2: Configure Lipa Na M-Pesa Online
1. Click on your app (the one with Consumer Key: `gzdkc6o3GSEBhRGN6GvD...`)
2. Look for "Test Credentials" section
3. Find the **Lipa Na M-Pesa Shortcode** (might be different from 991668)
4. Note the **Lipa Na M-Pesa Passkey**

### Step 3: Update .env File
Use the Lipa Na M-Pesa specific shortcode and passkey:

```bash
# Use the shortcode shown in "Lipa Na M-Pesa Online" section
MPESA_SHORTCODE=174379  # Default sandbox shortcode (or your specific one)
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
```

---

## 🧪 Testing Options

### Option 1: Use Default Sandbox Shortcode (Recommended)
Most Daraja sandbox accounts work with:
- **Shortcode:** 174379
- **Passkey:** bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
- **Test Phone:** 254708374149
- **Test PIN:** 1234

### Option 2: Check Your Daraja Portal
1. Login to https://developer.safaricom.co.ke
2. Go to your app
3. Look for "Test Credentials" tab
4. Find "Lipa Na M-Pesa Online Shortcode"
5. Use that shortcode in your .env

---

## 📋 Quick Fix (Try This First)

Update your `.env` file line 37:

```bash
# Change from:
MPESA_SHORTCODE=991668

# To:
MPESA_SHORTCODE=174379
```

Then restart Flask and test:
```bash
cd backend
python test_mpesa_stk_push.py
```

---

## 🎯 What's Working Now

✅ **OAuth Authentication** - Your Consumer Key/Secret are valid  
✅ **Token Generation** - Backend can communicate with M-Pesa API  
✅ **Input Validation** - All safety checks working  
✅ **Password Encryption** - STK Push signature working  

**Only missing:** Shortcode registered for Lipa Na M-Pesa Online

---

## 📞 Sandbox Test Details

**Test Phone Numbers (Sandbox):**
- 254708374149 - Works for all tests
- PIN: 1234

**API Status:**
- ✅ https://sandbox.safaricom.co.ke/oauth/v1/generate - Working
- ⏳ https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest - Needs valid shortcode

---

## 🚀 Next Steps

1. **Try default shortcode 174379** in .env
2. **OR** Check Daraja portal for your Lipa Na M-Pesa shortcode
3. **Restart** Flask server
4. **Run:** `python backend/test_mpesa_stk_push.py`

Once shortcode is fixed, you'll be able to:
- ✅ Initiate real STK Push requests
- ✅ Receive payment prompts on test phone
- ✅ Process M-Pesa callbacks
- ✅ Complete full payment flow

