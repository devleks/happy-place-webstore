# Phase 1 Quick Wins - Testing Checklist

## Test Environment
- **URL**: http://localhost:3000
- **Browser**: Chrome, Safari, or Firefox (test all if possible)
- **Date**: 2025-11-21

---

## 1. HEADER FEATURES

### Wishlist Icon
- [ ] Heart icon is visible in the header (left side near login)
- [ ] Icon is gray by default
- [ ] Hovering over heart changes color to burgundy (#722F37)
- [ ] Clicking heart navigates to /wishlist (may show 404 - that's OK for now)
- [ ] Icon has tooltip "Wishlist" on hover

### Shopping Cart Icon
- [ ] Cart icon is visible in the header (left side, next to wishlist)
- [ ] Cart shows "0" badge by default (if no items)
- [ ] Badge is burgundy with white text
- [ ] Badge is positioned at top-right of cart icon
- [ ] Hovering over cart changes icon color to burgundy
- [ ] Clicking cart navigates to /cart (may show 404 - that's OK for now)
- [ ] Icon has tooltip "Shopping Cart" on hover

### Sticky Header
- [ ] Scroll down the homepage
- [ ] Header stays at the top (sticky behavior)
- [ ] Header doesn't cover content when scrolling back up

---

## 2. PRODUCT CARD FEATURES

### Test Location: Homepage or Products Page
Navigate to either:
- **Homepage**: http://localhost:3000 (featured products section)
- **Products Page**: http://localhost:3000/products (full product grid)

### Rating Stars ⭐
- [ ] Each product card shows star rating
- [ ] Stars are gold (#D4AF37) when filled
- [ ] Some stars should be filled, some empty
- [ ] Review count appears in parentheses, e.g., "(24)"
- [ ] Review count is gray text
- [ ] Stars are positioned below product name

### Wishlist Heart Button ♡
- [ ] Heart icon appears in top-right corner of each product card
- [ ] Heart is in a white circular button
- [ ] Button has subtle shadow
- [ ] Heart is outlined (empty) by default
- [ ] Clicking heart fills it with color (burgundy)
- [ ] Clicking again empties the heart (toggle behavior)
- [ ] Button scales slightly on hover
- [ ] Button background turns burgundy on hover

### Product Badges 🏷️
**Note**: Badges appear on mock products - not all products will have them

- [ ] Look for "NEW" badge (burgundy background, white text)
- [ ] Look for "SALE" badge (red background, white text)
- [ ] Badges appear in top-left corner of product image
- [ ] Badges are small, uppercase, with letter-spacing
- [ ] Multiple badges stack vertically if present

### Color Swatches 🎨
- [ ] Color circles appear below the price
- [ ] Should see 3 colored circles (burgundy, rose gold, soft pink)
- [ ] Circles are small (16px)
- [ ] Circles have light border
- [ ] Hovering over a circle makes it slightly larger
- [ ] Hover changes border color to burgundy

### Pricing Display 💰
**Regular Products:**
- [ ] Price is displayed in gold (#D4AF37)
- [ ] Price is centered and prominent
- [ ] Font size is larger than other text

**Sale Products** (if any):
- [ ] Sale price is shown in gold
- [ ] Original price shown next to it
- [ ] Original price has strikethrough
- [ ] Original price is gray and smaller

---

## 3. HOVER EFFECTS

### Product Card Hover ✨
Hover your mouse over any product card:

- [ ] **Card Lift**: Card moves up slightly (translateY -5px)
- [ ] **Shadow**: Subtle shadow appears under the card
- [ ] **Border Color**: Border changes from gray to rose gold (#B76E79)
- [ ] **Image Zoom**: Product image zooms in slightly (scale 1.05)
- [ ] **Quick View**: "QUICK VIEW" text appears at bottom of image
  - [ ] Burgundy background with white text
  - [ ] Slides up from bottom
  - [ ] Uppercase text with letter-spacing

### Smooth Transitions
- [ ] All hover effects are smooth (not jumpy)
- [ ] Transitions take ~0.3-0.4 seconds
- [ ] Leaving hover reverses all effects smoothly

---

## 4. PRODUCT LINK FUNCTIONALITY

- [ ] Clicking anywhere on the product card (except wishlist button) navigates to product detail page
- [ ] Product detail page loads correctly
- [ ] Can navigate back to homepage/products page

---

## 5. RESPONSIVE DESIGN (Mobile Testing)

### Desktop (1024px+)
- [ ] Product cards in 2-3 column grid
- [ ] All features clearly visible
- [ ] Adequate spacing between elements

### Tablet (768px)
- [ ] Resize browser window to ~768px width
- [ ] Product cards adjust to fewer columns
- [ ] All icons and badges remain visible
- [ ] Text remains readable

### Mobile (480px)
- [ ] Resize browser window to ~480px width
- [ ] Cards may stack to 1 column
- [ ] Wishlist button remains accessible
- [ ] Color swatches don't overflow
- [ ] Badges remain visible
- [ ] Quick View overlay still works on tap/hover

---

## 6. VISUAL CONSISTENCY

### Color Scheme
- [ ] Burgundy (#722F37) used for: badges, hover states, filled hearts
- [ ] Rose Gold (#B76E79) used for: card hover borders
- [ ] Gold (#D4AF37) used for: ratings, prices
- [ ] Red (#DC143C) used for: SALE badges only
- [ ] Gray/white for base colors

### Typography
- [ ] Font is Lato throughout
- [ ] Text is readable and well-spaced
- [ ] Uppercase text has proper letter-spacing
- [ ] Font sizes are hierarchical (headings > body > labels)

---

## 7. BROWSER COMPATIBILITY

Test in multiple browsers if possible:
- [ ] **Chrome/Edge**: All features work
- [ ] **Safari**: All features work
- [ ] **Firefox**: All features work
- [ ] **Mobile Safari** (if on Mac): Responsive features work

---

## 8. CONSOLE ERRORS

Open Browser Developer Tools (F12 or Cmd+Option+I):

### Console Tab
- [ ] No JavaScript errors (red messages)
- [ ] Only warnings are acceptable (yellow messages about useEffect - expected)
- [ ] No broken image errors

### Network Tab
- [ ] All images load successfully (200 status)
- [ ] No 404 errors for CSS/JS files
- [ ] Unsplash images load correctly

---

## 9. PERFORMANCE CHECK

- [ ] Page loads quickly (within 2-3 seconds)
- [ ] Hover effects are smooth, not laggy
- [ ] Scrolling is smooth
- [ ] No flickering or visual glitches
- [ ] Images load progressively (no long white boxes)

---

## 10. SPECIFIC PRODUCT TESTING

Test these specific products on homepage:

### Classic Cotton T-Shirt
- [ ] Unsplash image displays
- [ ] Price: $29.99 in gold
- [ ] Rating stars visible
- [ ] Color swatches appear
- [ ] All hover effects work

### Elegant Blouse
- [ ] Unsplash image displays
- [ ] Price: $49.99 in gold
- [ ] Rating stars visible
- [ ] Color swatches appear
- [ ] All hover effects work

### Maternity Basic Tee
- [ ] Unsplash image displays
- [ ] Price: $34.99 in gold
- [ ] Rating stars visible
- [ ] Color swatches appear
- [ ] All hover effects work

### Maternity Wrap Top
- [ ] Unsplash image displays
- [ ] Price: $54.99 in gold
- [ ] Rating stars visible
- [ ] Color swatches appear
- [ ] All hover effects work

---

## ISSUES FOUND

Document any issues here:

### Critical Issues (Broken Features)
-

### Minor Issues (Visual Glitches)
-

### Enhancement Ideas
-

---

## TEST RESULTS SUMMARY

- **Total Tests**: 80+
- **Passed**: ___
- **Failed**: ___
- **Not Applicable**: ___

### Overall Status
- [ ] ✅ All critical features working
- [ ] ⚠️ Minor issues found (document above)
- [ ] ❌ Critical issues need fixing

---

## NOTES

- Cart and Wishlist pages don't exist yet (404 is expected)
- All product data is currently mock/hardcoded
- Backend integration will come in Phase 2/3
- Badge visibility depends on mock data (may not appear on all products)

---

## NEXT STEPS AFTER TESTING

If all tests pass:
- ✅ Proceed to Phase 2 (Shopping Cart & Search)

If issues found:
- 🔧 Fix critical issues first
- 📝 Document minor issues for later
- 🧪 Re-test after fixes

---

**Tester**: ________________
**Date Completed**: ________________
**Browser Used**: ________________
**Overall Result**: ⬜ Pass / ⬜ Pass with Minor Issues / ⬜ Fail
