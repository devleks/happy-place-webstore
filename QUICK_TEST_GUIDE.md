# Quick Test Guide - Phase 6A
**Happy Place Boutique Checkout & Order Management**

---

## 🚀 START HERE

### Environment Check
✅ Backend: http://127.0.0.1:5001 (should be running)
✅ Frontend: http://localhost:3000 (should be running)

### Automated Tests Already Done ✅
- Backend API endpoints tested
- Public routes working
- Authentication working
- Error handling verified

---

## 📋 30-Minute Critical Test Path

### 1. Registration & Login (5 min)
```
http://localhost:3000
→ Register (create new user)
→ Logout
→ Login again
✓ Verify "Welcome, [Name]!" and "My Orders" link
```

### 2. Add to Cart (5 min)
```
→ Click product (e.g., "Elegant Silk Blouse")
→ Select Size M, Color Blue
→ Test quantity: click +/- buttons, type numbers
→ Change variant → quantity resets to 1 ✓
→ Set quantity to 2
→ Click "Add to Cart"
✓ Toast appears, cart badge shows "2"
```

### 3. Checkout (10 min) ⭐ CRITICAL
```
→ Go to cart → "Proceed to Checkout"

Fill shipping address:
Street: 123 Test Street
City: Nairobi
State: Nairobi County
ZIP: 00100
Phone: +254712345678

✓ Shipping shows "FREE" (Nairobi)

Change city to "Mombasa":
✓ Shipping shows KSh 300+

→ Click "Place Order"
```

### 4. Order Confirmation (5 min) ⭐ CRITICAL
```
✓ Success checkmark animates
✓ Order number: HP-20251125-XXXX
✓ All items shown with images
✓ Shipping address correct
✓ Totals correct
✓ Status: "Pending"
✓ "What's Next?" guide appears
```

### 5. Order History (5 min)
```
→ Click "View Order History"
✓ Order appears in list
✓ Click filter tabs (All, Pending, etc.)
→ Click order card
✓ Goes back to order confirmation
```

---

## 🐛 Quick Error Tests (10 min)

### Form Validation
```
Checkout page:
- Leave fields empty → Submit → ✓ Errors appear
- Phone: "123" → ✓ Error
- Street: "ab" → ✓ Error
```

### Protected Routes
```
- Logout
- Navigate to /checkout directly
✓ Redirected to login with warning
```

### Empty States
```
- Clear cart → ✓ Empty state message
- Orders page with filter "Delivered" (if none) → ✓ Empty state
```

---

## 📱 Responsive Test (10 min)

```
F12 → Toggle Device Toolbar (Ctrl+Shift+M)

iPhone SE (375px):
✓ Products: 1 column
✓ Checkout: Single column, summary at bottom
✓ No horizontal scroll

iPad (768px):
✓ Products: 2 columns
✓ Checkout: Adjusted layout

Desktop (1440px):
✓ Products: 3-4 columns
✓ Checkout: Form + sidebar (two columns)
✓ Sidebar sticky on scroll
```

---

## ✅ Success Checklist

**Must Pass:**
- [ ] Can complete full checkout flow
- [ ] Order created successfully
- [ ] Order confirmation displays correctly
- [ ] Cart cleared after order
- [ ] Order appears in history
- [ ] Forms validate correctly
- [ ] Shipping calculation works (Nairobi free, Upcountry paid)
- [ ] Responsive on mobile/tablet/desktop
- [ ] No critical console errors

---

## 🎯 Priority Order

1. **FIRST** → Complete checkout flow (Steps 1-5 above)
2. **SECOND** → Error tests
3. **THIRD** → Responsive design
4. **OPTIONAL** → Detailed test cases in QA_TEST_PLAN.md

---

## 📊 Where to Record Results

**QA_TEST_RESULTS.md** - Check off items as you test

---

## ⏱️ Total Time: ~50 minutes

| Test | Time |
|------|------|
| Critical Path | 30 min |
| Error Tests | 10 min |
| Responsive | 10 min |

---

## 🆘 If Something Fails

1. Note what you were testing
2. Note expected vs actual behavior
3. Check browser console (F12) for errors
4. Screenshot if helpful
5. Document in QA_TEST_RESULTS.md

---

## 📁 QA Documentation

- **QA_TEST_PLAN.md** - 73 detailed test cases
- **QA_TEST_RESULTS.md** - Track test execution
- **QA_SUMMARY.md** - Complete overview
- **QUICK_TEST_GUIDE.md** - This file

---

**Ready to test!** Open http://localhost:3000 and start with registration.

*Phase 6A: Checkout & Order Management*
*Generated: November 25, 2025*
