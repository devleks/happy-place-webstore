# Inventory Management Strategy: Online vs Physical Store

**Date:** November 26, 2025
**Status:** 📋 PROPOSAL & RECOMMENDATIONS
**Current System:** Unified inventory (single quantity pool)

---

## Current State Analysis

### Current Inventory Table
```sql
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER UNIQUE NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,           -- Total available
    reserved_quantity INTEGER NOT NULL DEFAULT 0,  -- Locked for orders
    low_stock_threshold INTEGER DEFAULT 5,
    last_restocked_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Current Approach:** **Unified Inventory Pool**
- Single `quantity` field serves both online and physical store
- `reserved_quantity` locks items during online checkout
- Simple but has limitations for multi-channel retail

---

## Three Strategic Approaches

### Option 1: **Unified Inventory (Current) ✅ RECOMMENDED FOR NOW**

**How It Works:**
- Single quantity pool shared between online and store
- Both channels pull from same inventory
- Real-time sync automatically

**Pros:**
- ✅ Simple to implement (already in place)
- ✅ No complex sync logic needed
- ✅ Maximum flexibility (inventory goes where demand is)
- ✅ No "stuck inventory" in one channel
- ✅ Automatic balancing
- ✅ Lower total inventory requirements

**Cons:**
- ⚠️ Race conditions (online order vs in-store sale)
- ⚠️ No channel-specific allocation
- ⚠️ Can't reserve inventory for store displays
- ⚠️ Store might sell item reserved for online order

**Best For:**
- Small to medium stores (1-2 locations)
- Similar demand patterns online and in-store
- Fast-moving inventory
- **Your current business model** ✅

---

### Option 2: **Separated Inventory** (Split Pool)

**How It Works:**
```sql
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER UNIQUE NOT NULL,

    -- Separate quantities
    online_quantity INTEGER NOT NULL DEFAULT 0,
    store_quantity INTEGER NOT NULL DEFAULT 0,
    online_reserved INTEGER NOT NULL DEFAULT 0,

    low_stock_threshold INTEGER DEFAULT 5,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Business Rules:**
- New stock gets allocated: 70% online, 30% store (configurable)
- Each channel has dedicated inventory
- Manual or automated transfers between channels

**Pros:**
- ✅ No race conditions between channels
- ✅ Can reserve store inventory for displays
- ✅ Clear channel-specific metrics
- ✅ Predictable inventory per channel
- ✅ Can set minimum store quantities

**Cons:**
- ❌ More complex inventory management
- ❌ Can have stock in store but "sold out" online (or vice versa)
- ❌ Requires inventory transfer workflows
- ❌ Higher total inventory needed
- ❌ Manual balancing required

**Best For:**
- Multiple physical locations
- Different product mixes per channel
- High-value items
- Store displays/demo units

---

### Option 3: **Hybrid Inventory** (Recommended for Growth)

**How It Works:**
```sql
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER UNIQUE NOT NULL,

    -- Total inventory
    total_quantity INTEGER NOT NULL DEFAULT 0,

    -- Channel allocations
    online_available INTEGER NOT NULL DEFAULT 0,     -- Dedicated online
    store_allocated INTEGER NOT NULL DEFAULT 0,      -- Minimum store stock
    shared_pool INTEGER NOT NULL DEFAULT 0,          -- Flex inventory

    -- Reservations
    online_reserved INTEGER NOT NULL DEFAULT 0,
    store_reserved INTEGER NOT NULL DEFAULT 0,

    -- Constraints
    CHECK (total_quantity = online_available + store_allocated + shared_pool),
    CHECK (online_available >= online_reserved),

    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Business Rules:**
1. **Store gets minimum allocation:**
   - Reserve 2-5 units for store (for displays, walk-ins)
   - Store can dip into shared pool

2. **Online gets dedicated inventory:**
   - Guaranteed availability for website
   - Can overflow into shared pool

3. **Shared pool is flexible:**
   - Both channels can use
   - Priority rules (e.g., first-come-first-served)
   - Automatically redistributed based on demand

**Calculation Logic:**
```python
# Available for online customer
online_available_now = online_available + shared_pool - online_reserved

# Available for store customer
store_available_now = store_allocated + shared_pool - store_reserved

# Can item be sold online?
if online_available_now > 0:
    # Yes, reserve it
    online_reserved += 1
    # Deduct from appropriate pool
    if online_available > online_reserved:
        # Use online pool
        pass
    else:
        # Use shared pool
        shared_pool -= 1
```

**Pros:**
- ✅ Best of both worlds
- ✅ Guaranteed minimum store stock
- ✅ Flexibility for high-demand items
- ✅ Prevents complete stock-outs in one channel
- ✅ Automatic balancing via shared pool
- ✅ Can prioritize profitable channels

**Cons:**
- ⚠️ More complex logic
- ⚠️ Requires monitoring and adjustment
- ⚠️ Need to tune allocation percentages

**Best For:**
- Growing businesses (3+ locations)
- Seasonal inventory
- High-value or flagship products
- Omnichannel strategies (buy online, pickup in store)

---

## Detailed Comparison

| Feature | Unified (Current) | Separated | Hybrid |
|---------|------------------|-----------|--------|
| **Implementation Complexity** | ⭐ Simple | ⭐⭐⭐ Complex | ⭐⭐ Moderate |
| **Race Conditions** | ⚠️ Possible | ✅ None | ✅ Minimal |
| **Flexibility** | ✅ Maximum | ❌ Low | ✅ High |
| **Inventory Efficiency** | ✅ Best | ❌ Worst | ⭐⭐⭐ Good |
| **Store Display Protection** | ❌ No | ✅ Yes | ✅ Yes |
| **Channel Metrics** | ❌ Combined | ✅ Clear | ✅ Clear |
| **Omnichannel Support** | ⚠️ Limited | ❌ Difficult | ✅ Excellent |
| **Maintenance** | ✅ Low | ⚠️ High | ⚠️ Moderate |

---

## Recommended Implementation Path

### Phase 1: Enhance Current Unified System (1-2 weeks)

**Keep unified inventory BUT add:**

```sql
-- Add location tracking
ALTER TABLE inventory ADD COLUMN primary_location VARCHAR(50) DEFAULT 'warehouse';
ALTER TABLE inventory ADD COLUMN store_display_units INTEGER DEFAULT 0;

-- Track where stock physically is
CREATE TABLE inventory_locations (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    location_type VARCHAR(20) NOT NULL,  -- 'warehouse', 'store', 'transit'
    location_name VARCHAR(100),          -- 'Main Store Nairobi', 'Warehouse A'
    quantity INTEGER NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),

    CONSTRAINT check_location_type CHECK (location_type IN ('warehouse', 'store', 'transit', 'display'))
);

-- Inventory movements log
CREATE TABLE inventory_movements (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    from_location VARCHAR(100),
    to_location VARCHAR(100),
    quantity INTEGER NOT NULL,
    movement_type VARCHAR(20) NOT NULL,  -- 'sale', 'transfer', 'restock', 'return', 'adjustment'
    channel VARCHAR(20),                  -- 'online', 'store', 'pos'
    reference_id INTEGER,                 -- order_id or transaction_id
    performed_by INTEGER REFERENCES employees(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_movements_variant ON inventory_movements(variant_id);
CREATE INDEX idx_movements_created ON inventory_movements(created_at);
CREATE INDEX idx_movements_channel ON inventory_movements(channel);
```

**Benefits:**
- ✅ Track WHERE inventory is
- ✅ Full audit trail of movements
- ✅ Can generate location-specific reports
- ✅ Supports future expansion
- ✅ Doesn't break existing system

---

### Phase 2: Add Smart Reservations (2-3 weeks)

```sql
-- Enhanced reservations with channel tracking
CREATE TABLE inventory_reservations (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    quantity INTEGER NOT NULL,
    channel VARCHAR(20) NOT NULL,        -- 'online', 'store'
    reservation_type VARCHAR(30) NOT NULL, -- 'cart', 'checkout', 'display', 'hold'

    -- Who/what reserved it
    customer_id INTEGER REFERENCES customers(id),
    order_id INTEGER REFERENCES orders(id),
    employee_id INTEGER REFERENCES employees(id),

    -- Expiration
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'fulfilled', 'expired', 'cancelled'

    CONSTRAINT check_channel CHECK (channel IN ('online', 'store', 'pos')),
    CONSTRAINT check_type CHECK (reservation_type IN ('cart', 'checkout', 'display', 'hold', 'layaway'))
);

CREATE INDEX idx_reservations_variant ON inventory_reservations(variant_id);
CREATE INDEX idx_reservations_expires ON inventory_reservations(expires_at);
CREATE INDEX idx_reservations_status ON inventory_reservations(status);
```

**Reservation Rules:**
1. **Online Cart:** 15-minute reservation
2. **Online Checkout:** 10-minute reservation
3. **Store Hold:** 24-48 hour reservation
4. **Display Units:** Permanent until removed
5. **Layaway:** Duration of layaway plan

**Stored Procedure:**
```sql
CREATE OR REPLACE FUNCTION sp_reserve_inventory(
    p_variant_id INTEGER,
    p_quantity INTEGER,
    p_channel VARCHAR(20),
    p_reservation_type VARCHAR(30),
    p_customer_id INTEGER DEFAULT NULL,
    p_employee_id INTEGER DEFAULT NULL,
    p_duration_minutes INTEGER DEFAULT 15
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_available INTEGER;
    v_reservation_id INTEGER;
BEGIN
    -- Get available quantity (total - all active reservations)
    SELECT i.quantity - COALESCE(SUM(r.quantity), 0)
    INTO v_available
    FROM inventory i
    LEFT JOIN inventory_reservations r ON r.variant_id = i.variant_id
        AND r.status = 'active'
        AND r.expires_at > NOW()
    WHERE i.variant_id = p_variant_id
    GROUP BY i.quantity;

    -- Check availability
    IF v_available < p_quantity THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'error', 'Insufficient inventory',
            'available', v_available,
            'requested', p_quantity
        );
    END IF;

    -- Create reservation
    INSERT INTO inventory_reservations (
        variant_id, quantity, channel, reservation_type,
        customer_id, employee_id,
        expires_at, status
    ) VALUES (
        p_variant_id, p_quantity, p_channel, p_reservation_type,
        p_customer_id, p_employee_id,
        NOW() + (p_duration_minutes || ' minutes')::INTERVAL,
        'active'
    )
    RETURNING id INTO v_reservation_id;

    -- Log movement
    INSERT INTO inventory_movements (
        variant_id, movement_type, channel,
        quantity, reference_id, notes
    ) VALUES (
        p_variant_id, 'reservation', p_channel,
        p_quantity, v_reservation_id,
        'Reserved for ' || p_reservation_type
    );

    RETURN jsonb_build_object(
        'success', TRUE,
        'reservation_id', v_reservation_id,
        'expires_at', NOW() + (p_duration_minutes || ' minutes')::INTERVAL
    );
END;
$$;
```

---

### Phase 3: Implement Hybrid Model (1-2 months)

If business grows to multiple locations or omnichannel needs:

1. **Add allocation columns** to inventory table
2. **Create allocation rules** engine
3. **Build rebalancing system** (automatic or manual)
4. **Implement** "buy online, pick up in store" (BOPIS)
5. **Add** store-to-store transfers

---

## Business Rules & Policies

### Stock Allocation Policy

**New Stock Arrival:**
```python
# Default allocation for new inventory
total_units = 100

# Option A: Fixed percentages
online_allocation = total_units * 0.80  # 80 units online
store_allocation = total_units * 0.20   # 20 units store

# Option B: Based on velocity
last_30_days_online_sales = get_sales('online', days=30)
last_30_days_store_sales = get_sales('store', days=30)

online_ratio = last_30_days_online_sales / (last_30_days_online_sales + last_30_days_store_sales)
online_allocation = total_units * online_ratio
store_allocation = total_units - online_allocation

# Option C: Minimum store, rest online
store_allocation = min(20, total_units * 0.20)  # Min 20 or 20%
online_allocation = total_units - store_allocation
```

### Low Stock Handling

```python
# When inventory gets low
current_stock = 8  # Total available
online_reserved = 3
store_reserved = 2

available = current_stock - online_reserved - store_reserved  # 3 units

# Strategy 1: First-come-first-served (current)
# Both channels compete for remaining 3 units

# Strategy 2: Channel priority
if store_reserved > 0:
    # Reserve 1 unit for store (walk-in customers are priority)
    store_guaranteed = 1
    online_max = available - store_guaranteed  # 2 units for online

# Strategy 3: Value-based priority
avg_order_value_online = 2500  # KSh
avg_order_value_store = 3500   # KSh

if avg_order_value_store > avg_order_value_online:
    # Prioritize store
    pass
```

### Transfer Policy

**Store to Online:**
- Triggered when online demand exceeds allocation
- Requires manager approval
- Min 24-hour notice
- Max 50% of store inventory

**Online to Store:**
- For special customer requests
- Store pickup orders
- Display unit needs
- Immediate transfer available

---

## Recommended Stored Procedures

### 1. Get Available Inventory by Channel

```sql
CREATE OR REPLACE FUNCTION sp_get_available_inventory(
    p_variant_id INTEGER,
    p_channel VARCHAR(20)
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_total_quantity INTEGER;
    v_reserved_online INTEGER;
    v_reserved_store INTEGER;
    v_display_units INTEGER;
    v_available INTEGER;
BEGIN
    -- Get current inventory
    SELECT
        quantity,
        COALESCE(store_display_units, 0)
    INTO v_total_quantity, v_display_units
    FROM inventory
    WHERE variant_id = p_variant_id;

    -- Get active reservations
    SELECT
        COALESCE(SUM(CASE WHEN channel = 'online' THEN quantity ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN channel = 'store' THEN quantity ELSE 0 END), 0)
    INTO v_reserved_online, v_reserved_store
    FROM inventory_reservations
    WHERE variant_id = p_variant_id
      AND status = 'active'
      AND expires_at > NOW();

    -- Calculate available
    IF p_channel = 'online' THEN
        v_available := v_total_quantity - v_display_units - v_reserved_online - v_reserved_store;
    ELSIF p_channel = 'store' THEN
        v_available := v_total_quantity - v_reserved_online - v_reserved_store;
    ELSE
        v_available := v_total_quantity - v_display_units - v_reserved_online - v_reserved_store;
    END IF;

    RETURN GREATEST(v_available, 0);
END;
$$;
```

### 2. Process Sale (Deduct Inventory)

```sql
CREATE OR REPLACE FUNCTION sp_process_inventory_sale(
    p_variant_id INTEGER,
    p_quantity INTEGER,
    p_channel VARCHAR(20),
    p_reference_id INTEGER,  -- order_id or transaction_id
    p_location VARCHAR(100) DEFAULT 'Main Store'
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_available INTEGER;
BEGIN
    -- Check availability
    v_available := sp_get_available_inventory(p_variant_id, p_channel);

    IF v_available < p_quantity THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'error', 'Insufficient inventory',
            'available', v_available
        );
    END IF;

    -- Deduct inventory
    UPDATE inventory
    SET quantity = quantity - p_quantity,
        updated_at = NOW()
    WHERE variant_id = p_variant_id;

    -- Log movement
    INSERT INTO inventory_movements (
        variant_id, movement_type, channel,
        quantity, to_location, reference_id, created_at
    ) VALUES (
        p_variant_id, 'sale', p_channel,
        -p_quantity, p_location, p_reference_id, NOW()
    );

    RETURN jsonb_build_object(
        'success', TRUE,
        'new_quantity', (SELECT quantity FROM inventory WHERE variant_id = p_variant_id)
    );
END;
$$;
```

---

## Implementation Recommendation

### For Your Current Scale (1 store + online):

**✅ STICK WITH UNIFIED INVENTORY**

**But add these enhancements:**

1. **Inventory Movements Table** (Week 1)
   - Track every sale/return/transfer
   - Record which channel made the sale
   - Build audit trail

2. **Store Display Protection** (Week 1)
   - Add `store_display_units` column
   - Reserve 1-2 units per SKU for store display
   - Online can't sell display units

3. **Channel Reporting** (Week 2)
   - Sales by channel dashboard
   - Inventory velocity by channel
   - Identify fast movers per channel

4. **Smart Reservations** (Week 3-4)
   - 15-minute cart reservations online
   - 24-hour hold reservations in store
   - Automatic expiration cleanup

5. **Low Stock Alerts by Channel** (Week 4)
   - Notify when online selling faster than store
   - Suggest restocking priorities
   - Alert on display unit depletion

### Future Growth (6-12 months):

When you add 2nd/3rd store location:
- Migrate to **Hybrid Model**
- Add location-based inventory
- Implement store-to-store transfers
- Build omnichannel features (BOPIS)

---

## Quick Wins (Implement This Week)

### 1. Add Display Units Column

```sql
ALTER TABLE inventory
ADD COLUMN store_display_units INTEGER DEFAULT 0 CHECK (store_display_units >= 0);

-- Set display units for existing products
UPDATE inventory i
SET store_display_units = 2
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
WHERE i.variant_id = pv.id
  AND p.is_featured = TRUE;
```

### 2. Create Inventory Movements Table

```sql
CREATE TABLE inventory_movements (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    movement_type VARCHAR(20) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    from_location VARCHAR(100),
    to_location VARCHAR(100),
    reference_id INTEGER,
    performed_by INTEGER REFERENCES employees(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_movements_variant ON inventory_movements(variant_id);
CREATE INDEX idx_movements_channel ON inventory_movements(channel);
CREATE INDEX idx_movements_created ON inventory_movements(created_at);
```

### 3. Update Existing Sale Logic

Every time inventory is reduced (online order or POS sale), log it:

```python
# After successful sale
log_inventory_movement(
    variant_id=item.variant_id,
    movement_type='sale',
    channel='online',  # or 'store'
    quantity=-item.quantity,
    reference_id=order.id,
    notes=f'Order #{order.order_number}'
)
```

---

## Summary & Decision Matrix

| If You Have... | Recommended Approach |
|----------------|---------------------|
| 1 store + online, same location | **Unified** (current) + enhancements |
| 1 store + online, high-value items | **Unified** + display protection |
| 2-3 stores + online | **Hybrid** model |
| 4+ stores + online | **Separated** or **Hybrid** |
| Omnichannel (BOPIS, etc.) | **Hybrid** model |
| Different product mix per channel | **Separated** model |

**Your Situation:** 1 store + online
**Recommendation:** ✅ **Keep Unified, Add Enhancements**

---

**Next Steps:**
1. Review this document
2. Decide on Phase 1 enhancements
3. I can implement chosen enhancements
4. Plan future migration if business grows

Would you like me to implement any of these enhancements?
