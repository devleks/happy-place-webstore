# Database Stored Procedure Migration - Quick Reference Guide

**Last Updated:** November 26, 2025
**For:** Development Team

---

## Quick Lookup: Functions to Migrate

### Priority 1: CRITICAL (Do First)

| Current Function | File | Lines | New Stored Procedure | Priority | Effort |
|------------------|------|-------|---------------------|----------|--------|
| `OrderService.create_order()` | `services/order_service.py` | 24-190 | `sp_create_order()` | P1 | 3-5d |
| `add_to_cart()` | `routes/cart.py` | 54-136 | `sp_add_to_cart()` | P1 | 2-3d |
| `update_cart_item()` | `routes/cart.py` | 138-190 | `sp_update_cart_item()` | P1 | 1d |
| Payment confirmation | (NEW FUNCTION) | N/A | `sp_process_payment_confirmation()` | P1 | 3-4d |
| `validate_promotion()` | `routes/promotions.py` | 14-114 | `sp_validate_and_apply_promotion()` | P1 | 2-3d |
| `create_return_request()` | `routes/returns_api.py` | 95-238 | `sp_create_return_request()` | P1 | 4-5d |

### Priority 2: HIGH (Do Next)

| Current Function | File | Lines | New Stored Procedure | Priority | Effort |
|------------------|------|-------|---------------------|----------|--------|
| `customer_register()` | `routes/auth.py` | 17-123 | `sp_register_customer()` | P2 | 2-3d |
| `Customer.anonymize()` | `models/database_models.py` | 134-147 | `sp_anonymize_customer()` | P2 | 2-3d |
| `decrypt_customer_field()` | `services/encryption.py` | 130-161 | `sp_decrypt_customer_field()` | P2 | 3-4d |

### Priority 3: MEDIUM (Do Later)

| Current Function | File | Lines | New Stored Procedure | Priority | Effort |
|------------------|------|-------|---------------------|----------|--------|
| `create_product()` | `routes/products.py` | 197-292 | `sp_create_product_with_variants()` | P3 | 2-3d |
| `ShippingService.calculate_shipping()` | `services/shipping_service.py` | 47-77 | `sp_calculate_shipping()` | P3 | 1-2d |

---

## Security Issues by Function

### OrderService.create_order()

**Current Code:** `/backend/services/order_service.py:24-190`

**Security Issues:**
1. Race condition in order number generation (line 118-125)
2. Manual transaction boundaries (line 115, 170, 189)
3. Price calculated in Python, can be manipulated (line 89-92)
4. Inventory not atomically reserved
5. Cart cleared separately from order creation (line 175)

**Why This Is Critical:**
- Two orders can get the same order number
- Order creation can fail after payment recorded
- Customer can modify prices in cart before checkout
- Inventory can be oversold

**Attack Scenario:**
```python
# Attacker modifies cart item price in memory/session
# Between validation (line 86) and order creation (line 128)
# Results in order created with wrong price
```

---

### add_to_cart()

**Current Code:** `/backend/routes/cart.py:54-136`

**Security Issues:**
1. TOCTOU vulnerability (line 85-91 vs line 101-124)
2. Inventory checked but not locked (line 85)
3. No atomic inventory reservation
4. Race condition when adding same item simultaneously

**Why This Is Critical:**
- Two customers can reserve the last item at the same time
- Inventory quantity checked but not locked
- Leads to overselling

**Attack Scenario:**
```python
# Customer A: Check inventory (10 available) ✓
# Customer B: Check inventory (10 available) ✓
# Customer A: Add 10 to cart ✓
# Customer B: Add 10 to cart ✓
# Result: 20 items in carts, only 10 in stock
```

---

### validate_promotion()

**Current Code:** `/backend/routes/promotions.py:14-114`

**Security Issues:**
1. Race condition in usage count (line 61-66)
2. No atomic usage increment
3. Discount calculated in Python (line 95)
4. Customer usage not locked during check

**Why This Is Critical:**
- Customer can use promotion code multiple times
- Usage limit can be exceeded
- Discount calculation can be manipulated

**Attack Scenario:**
```python
# Send 10 simultaneous requests with same promo code
# All pass usage check before any increment usage
# Result: Code used 10 times, limit was 1
```

---

### create_return_request()

**Current Code:** `/backend/routes/returns_api.py:95-238`

**Security Issues:**
1. Return window validation in Python (line 137-142)
2. Restocking fee calculated in Python (line 208)
3. Business rules not enforced at DB level (line 178-185)
4. Refund amount can be manipulated

**Why This Is Critical:**
- Returns can be approved outside policy window
- Restocking fee calculation can be bypassed
- Clearance/sale items can be returned despite policy
- Refund amounts can be manipulated

**Attack Scenario:**
```python
# Modify request to skip business rule checks
# Submit return after 2-day window
# Skip restocking fee calculation
# Return clearance items despite FINAL SALE policy
```

---

## Code Migration Patterns

### Pattern 1: Replace Direct DB Operations

**BEFORE (Python):**
```python
def create_order(customer_id, cart_items, ...):
    # Calculate totals
    subtotal = calculate_subtotal(cart_items)
    shipping = calculate_shipping(city, weight)
    total = subtotal + shipping

    # Create order
    order = Order(
        customer_id=customer_id,
        subtotal=subtotal,
        total=total,
        ...
    )
    db.session.add(order)
    db.session.commit()

    return order
```

**AFTER (Stored Procedure Call):**
```python
def create_order(customer_id, cart_items, ...):
    # Call stored procedure
    result = db.session.execute(
        text("SELECT sp_create_order(:customer_id, :items, :shipping, :billing, :payment, :ip, :ua)"),
        {
            'customer_id': customer_id,
            'items': json.dumps([item.to_dict() for item in cart_items]),
            'shipping': encrypt_address(json.dumps(shipping_address)),
            'billing': encrypt_address(json.dumps(billing_address)),
            'payment': payment_method,
            'ip': ip_address,
            'ua': user_agent
        }
    ).fetchone()

    # Parse JSON result
    order_data = json.loads(result[0])

    if not order_data['success']:
        raise RuntimeError(order_data.get('error', 'Order creation failed'))

    return order_data
```

---

### Pattern 2: Replace Business Logic Calculations

**BEFORE (Python):**
```python
# Restocking fee calculated in Python
total_return_value = sum(item.price * item.qty for item in items)
restocking_fee = total_return_value * 0.10  # Can be manipulated!
refund_amount = total_return_value - restocking_fee
```

**AFTER (Stored Procedure):**
```sql
-- Restocking fee calculated in database (secure)
v_restocking_fee := v_total_return_value * 0.10;
v_refund_amount := v_total_return_value - v_restocking_fee;
```

---

### Pattern 3: Replace Multi-Step Transactions

**BEFORE (Python):**
```python
try:
    # Step 1
    order = create_order_record(...)
    db.session.flush()

    # Step 2
    for item in cart_items:
        create_order_item(order.id, item)

    # Step 3
    create_payment(order.id, ...)

    # Step 4
    clear_cart(customer_id)

    db.session.commit()
except Exception:
    db.session.rollback()
    raise
```

**AFTER (Stored Procedure):**
```sql
BEGIN
    -- All steps atomic
    -- Auto-rollback on any error
    -- No manual transaction management needed

    -- Step 1: Create order
    INSERT INTO orders (...) RETURNING id INTO v_order_id;

    -- Step 2: Create order items
    FOR v_item IN ... LOOP
        INSERT INTO order_items (...);
    END LOOP;

    -- Step 3: Create payment
    INSERT INTO payments (...);

    -- Step 4: Clear cart
    DELETE FROM cart_items WHERE ...;

    RETURN jsonb_build_object('success', TRUE, ...);
END;
```

---

## Testing Checklist

### For Each Migrated Function

- [ ] **Unit Tests**: Test stored procedure with valid inputs
- [ ] **Error Tests**: Test with invalid inputs (expect EXCEPTION)
- [ ] **Race Condition Tests**: Run concurrent calls, verify no duplicates
- [ ] **Rollback Tests**: Verify transaction rollback on errors
- [ ] **Performance Tests**: Compare execution time before/after
- [ ] **Audit Log Tests**: Verify all operations logged
- [ ] **Security Tests**: Attempt SQL injection, parameter manipulation

### Race Condition Test Example

```python
import concurrent.futures
import pytest

def test_concurrent_cart_add_no_overselling():
    """Test that concurrent cart adds don't oversell inventory"""

    variant_id = 123
    initial_inventory = 10

    # Set inventory to 10
    set_inventory(variant_id, 10)

    # 20 concurrent requests trying to add 1 item each
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(add_to_cart, customer_id=i, variant_id=variant_id, quantity=1)
            for i in range(20)
        ]

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Count successes and failures
    successes = sum(1 for r in results if r['success'])
    failures = sum(1 for r in results if not r['success'])

    # Should have exactly 10 successes, 10 failures
    assert successes == 10
    assert failures == 10

    # Inventory should be exactly 0 (10 items sold)
    remaining = get_inventory(variant_id)
    assert remaining == 0
```

---

## Common Pitfalls to Avoid

### Pitfall 1: Not Using Row Locking

**WRONG:**
```sql
-- Check inventory without locking
SELECT quantity FROM inventory WHERE variant_id = p_variant_id;
-- Another transaction can modify between SELECT and UPDATE!
```

**CORRECT:**
```sql
-- Lock row for update
SELECT quantity INTO v_quantity
FROM inventory
WHERE variant_id = p_variant_id
FOR UPDATE;  -- This locks the row!
```

### Pitfall 2: Not Validating Business Rules in DB

**WRONG:**
```python
# Python: Business rule
if product.is_clearance:
    raise ValueError("Clearance items cannot be returned")
```

**CORRECT:**
```sql
-- Database: Business rule enforced
IF v_is_clearance THEN
    RAISE EXCEPTION 'Clearance items are FINAL SALE';
END IF;
```

### Pitfall 3: Not Logging All Operations

**WRONG:**
```sql
-- Create order without logging
INSERT INTO orders (...);
RETURN v_order_id;
```

**CORRECT:**
```sql
-- Create order with audit log
INSERT INTO orders (...) RETURNING id INTO v_order_id;

-- Log activity (MANDATORY)
INSERT INTO activity_logs (action, resource_type, resource_id, ...)
VALUES ('order_created', 'order', v_order_id, ...);

RETURN v_order_id;
```

---

## Debugging Stored Procedures

### Enable Query Logging

```sql
-- In PostgreSQL
SET log_statement = 'all';
SET log_min_duration_statement = 0;
```

### Raise Debug Messages

```sql
-- In stored procedure
RAISE NOTICE 'Debug: v_order_id = %', v_order_id;
RAISE NOTICE 'Debug: v_total = %', v_total;
```

### Test in psql

```sql
-- Run procedure directly
SELECT sp_create_order(
    p_customer_id := 1,
    p_shipping_address_encrypted := 'encrypted_data',
    ...
);

-- View result
\x  -- Expanded display
SELECT * FROM orders ORDER BY id DESC LIMIT 1;
```

---

## Performance Optimization

### Use Bulk Operations

**Instead of:**
```sql
FOR v_item IN SELECT * FROM cart_items LOOP
    INSERT INTO order_items VALUES (...);
END LOOP;
```

**Use:**
```sql
INSERT INTO order_items (order_id, variant_id, quantity, ...)
SELECT v_order_id, variant_id, quantity, ...
FROM cart_items
WHERE cart_id = v_cart_id;
```

### Use CTEs for Complex Queries

```sql
WITH inventory_check AS (
    SELECT variant_id, quantity - reserved_quantity as available
    FROM inventory
    WHERE variant_id IN (...)
    FOR UPDATE
),
validation AS (
    SELECT ...
)
INSERT INTO order_items
SELECT ... FROM inventory_check JOIN validation ...;
```

---

## Rollback Strategy

### Feature Flag Implementation

```python
# In config
USE_STORED_PROCEDURES = os.getenv('USE_STORED_PROCEDURES', 'false').lower() == 'true'

# In service
def create_order(...):
    if USE_STORED_PROCEDURES:
        return _create_order_sp(...)  # New stored procedure
    else:
        return _create_order_legacy(...)  # Old Python code
```

### Gradual Rollout

1. Week 1: Deploy stored procedure, flag=OFF (0% traffic)
2. Week 2: Enable for internal testing, flag=ON for admin users (1% traffic)
3. Week 3: Enable for 10% of users, monitor metrics
4. Week 4: Enable for 50% of users
5. Week 5: Enable for 100% of users
6. Week 6+: Remove legacy code after 2 weeks of stability

---

## Monitoring & Alerts

### Key Metrics to Track

```python
# Prometheus metrics example
stored_proc_duration = Histogram(
    'stored_proc_duration_seconds',
    'Stored procedure execution time',
    ['procedure_name']
)

stored_proc_errors = Counter(
    'stored_proc_errors_total',
    'Stored procedure errors',
    ['procedure_name', 'error_type']
)
```

### Alert Thresholds

- Procedure execution time > 5 seconds → WARNING
- Procedure execution time > 10 seconds → CRITICAL
- Error rate > 1% → WARNING
- Error rate > 5% → CRITICAL
- Rollback rate > 5% → WARNING

---

## Resources

### Documentation
- Full audit report: `SECURITY_AUDIT_DB_MIGRATION.md`
- Executive summary: `SECURITY_AUDIT_EXECUTIVE_SUMMARY.md`
- PostgreSQL docs: https://www.postgresql.org/docs/current/plpgsql.html

### Training Materials
- PostgreSQL PL/pgSQL tutorial: https://www.postgresqltutorial.com/postgresql-plpgsql/
- pgAudit documentation: https://github.com/pgaudit/pgaudit

### Support
- Database team: db-team@happyplace.com
- Security team: security@happyplace.com
- DevOps team: devops@happyplace.com

---

**Last Updated:** November 26, 2025
**Maintained By:** Database Team
