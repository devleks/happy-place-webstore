-- ====================================================================
-- PHASE 1: INVENTORY ENHANCEMENTS
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Add display unit protection and inventory movement tracking
--
-- Enhancements:
-- 1. Store display units protection
-- 2. Inventory movements tracking
-- 3. Channel-aware inventory operations
-- 4. Comprehensive audit trail
-- ====================================================================

-- ====================================================================
-- 1. ENHANCE INVENTORY TABLE
-- ====================================================================

-- Add store display units column
ALTER TABLE inventory
ADD COLUMN IF NOT EXISTS store_display_units INTEGER DEFAULT 0 CHECK (store_display_units >= 0);

-- Add primary location tracking
ALTER TABLE inventory
ADD COLUMN IF NOT EXISTS primary_location VARCHAR(50) DEFAULT 'warehouse';

-- Add comments for documentation
COMMENT ON COLUMN inventory.store_display_units IS 'Units reserved for in-store display (cannot be sold online)';
COMMENT ON COLUMN inventory.primary_location IS 'Primary storage location: warehouse, store, transit';

-- Set display units for existing featured products
UPDATE inventory i
SET store_display_units = 2
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
WHERE i.variant_id = pv.id
  AND p.is_featured = TRUE
  AND i.quantity >= 2
  AND i.store_display_units = 0;

-- ====================================================================
-- 2. CREATE INVENTORY MOVEMENTS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS inventory_movements (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,

    -- Movement details
    movement_type VARCHAR(20) NOT NULL,    -- 'sale', 'restock', 'return', 'transfer', 'adjustment', 'reservation'
    channel VARCHAR(20) NOT NULL,          -- 'online', 'store', 'pos', 'admin'
    quantity INTEGER NOT NULL,             -- Positive for additions, negative for deductions

    -- Location tracking
    from_location VARCHAR(100),
    to_location VARCHAR(100),

    -- References
    reference_type VARCHAR(30),            -- 'order', 'transaction', 'return', 'transfer'
    reference_id INTEGER,                  -- order_id, transaction_id, etc.

    -- Who performed the action
    performed_by INTEGER REFERENCES employees(id),
    customer_id INTEGER REFERENCES customers(id),

    -- Additional context
    notes TEXT,
    metadata JSONB,                        -- Flexible field for additional data

    -- Inventory snapshot (for reporting)
    quantity_before INTEGER,
    quantity_after INTEGER,

    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT check_movement_type CHECK (
        movement_type IN ('sale', 'restock', 'return', 'transfer', 'adjustment', 'reservation', 'cancellation', 'display_set', 'display_remove')
    ),
    CONSTRAINT check_channel CHECK (
        channel IN ('online', 'store', 'pos', 'admin', 'system')
    )
);

-- Indexes for performance
CREATE INDEX idx_movements_variant ON inventory_movements(variant_id);
CREATE INDEX idx_movements_created ON inventory_movements(created_at DESC);
CREATE INDEX idx_movements_channel ON inventory_movements(channel);
CREATE INDEX idx_movements_type ON inventory_movements(movement_type);
CREATE INDEX idx_movements_reference ON inventory_movements(reference_type, reference_id);
CREATE INDEX idx_movements_performed_by ON inventory_movements(performed_by);

-- Composite index for common queries
CREATE INDEX idx_movements_variant_created ON inventory_movements(variant_id, created_at DESC);
CREATE INDEX idx_movements_channel_type ON inventory_movements(channel, movement_type);

COMMENT ON TABLE inventory_movements IS 'Complete audit trail of all inventory changes with channel tracking';

-- ====================================================================
-- 3. CREATE INVENTORY RESERVATIONS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS inventory_reservations (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,

    quantity INTEGER NOT NULL CHECK (quantity > 0),
    channel VARCHAR(20) NOT NULL,

    -- Reservation type
    reservation_type VARCHAR(30) NOT NULL,  -- 'cart', 'checkout', 'display', 'hold', 'layaway'

    -- Who reserved it
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employees(id),

    -- Expiration
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'active' NOT NULL,  -- 'active', 'fulfilled', 'expired', 'cancelled'

    -- Metadata
    notes TEXT,

    CONSTRAINT check_reservation_channel CHECK (channel IN ('online', 'store', 'pos')),
    CONSTRAINT check_reservation_type CHECK (
        reservation_type IN ('cart', 'checkout', 'display', 'hold', 'layaway', 'transfer')
    ),
    CONSTRAINT check_reservation_status CHECK (
        status IN ('active', 'fulfilled', 'expired', 'cancelled')
    )
);

-- Indexes
CREATE INDEX idx_reservations_variant ON inventory_reservations(variant_id);
CREATE INDEX idx_reservations_status ON inventory_reservations(status) WHERE status = 'active';
CREATE INDEX idx_reservations_expires ON inventory_reservations(expires_at) WHERE status = 'active';
CREATE INDEX idx_reservations_customer ON inventory_reservations(customer_id);
CREATE INDEX idx_reservations_order ON inventory_reservations(order_id);

COMMENT ON TABLE inventory_reservations IS 'Track inventory reservations with automatic expiration';

-- ====================================================================
-- 4. STORED PROCEDURE: Get Available Inventory
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_get_available_inventory(
    p_variant_id INTEGER,
    p_channel VARCHAR(20) DEFAULT 'online'
)
RETURNS INTEGER
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_total_quantity INTEGER;
    v_reserved_quantity INTEGER;
    v_display_units INTEGER;
    v_active_reservations INTEGER;
    v_available INTEGER;
BEGIN
    -- Get current inventory
    SELECT
        quantity,
        reserved_quantity,
        COALESCE(store_display_units, 0)
    INTO v_total_quantity, v_reserved_quantity, v_display_units
    FROM inventory
    WHERE variant_id = p_variant_id;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    -- Get active reservations (excluding old system reserved_quantity to avoid double-counting)
    SELECT COALESCE(SUM(quantity), 0)
    INTO v_active_reservations
    FROM inventory_reservations
    WHERE variant_id = p_variant_id
      AND status = 'active'
      AND expires_at > NOW();

    -- Calculate available based on channel
    IF p_channel = 'online' THEN
        -- Online: Cannot sell display units or reserved items
        v_available := v_total_quantity - v_display_units - v_reserved_quantity - v_active_reservations;
    ELSIF p_channel IN ('store', 'pos') THEN
        -- Store: Can sell anything except reserved items
        v_available := v_total_quantity - v_reserved_quantity - v_active_reservations;
    ELSE
        -- Admin/other: See total available
        v_available := v_total_quantity - v_reserved_quantity - v_active_reservations;
    END IF;

    -- Return max of 0 (never negative)
    RETURN GREATEST(v_available, 0);
END;
$$;

GRANT EXECUTE ON FUNCTION sp_get_available_inventory TO postgres;

-- ====================================================================
-- 5. STORED PROCEDURE: Log Inventory Movement
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_log_inventory_movement(
    p_variant_id INTEGER,
    p_movement_type VARCHAR(20),
    p_channel VARCHAR(20),
    p_quantity INTEGER,
    p_reference_type VARCHAR(30) DEFAULT NULL,
    p_reference_id INTEGER DEFAULT NULL,
    p_performed_by INTEGER DEFAULT NULL,
    p_customer_id INTEGER DEFAULT NULL,
    p_from_location VARCHAR(100) DEFAULT NULL,
    p_to_location VARCHAR(100) DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_movement_id INTEGER;
    v_quantity_before INTEGER;
    v_quantity_after INTEGER;
BEGIN
    -- Get current quantity for snapshot
    SELECT quantity INTO v_quantity_before
    FROM inventory
    WHERE variant_id = p_variant_id;

    -- Calculate quantity after
    v_quantity_after := v_quantity_before + p_quantity;

    -- Insert movement record
    INSERT INTO inventory_movements (
        variant_id,
        movement_type,
        channel,
        quantity,
        reference_type,
        reference_id,
        performed_by,
        customer_id,
        from_location,
        to_location,
        notes,
        quantity_before,
        quantity_after,
        created_at
    ) VALUES (
        p_variant_id,
        p_movement_type,
        p_channel,
        p_quantity,
        p_reference_type,
        p_reference_id,
        p_performed_by,
        p_customer_id,
        p_from_location,
        p_to_location,
        p_notes,
        v_quantity_before,
        v_quantity_after,
        NOW()
    )
    RETURNING id INTO v_movement_id;

    RETURN v_movement_id;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_log_inventory_movement TO postgres;

-- ====================================================================
-- 6. STORED PROCEDURE: Deduct Inventory with Logging
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_deduct_inventory(
    p_variant_id INTEGER,
    p_quantity INTEGER,
    p_channel VARCHAR(20),
    p_reference_type VARCHAR(30),
    p_reference_id INTEGER,
    p_performed_by INTEGER DEFAULT NULL,
    p_customer_id INTEGER DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_available INTEGER;
    v_movement_id INTEGER;
    v_new_quantity INTEGER;
BEGIN
    -- Check availability
    v_available := sp_get_available_inventory(p_variant_id, p_channel);

    IF v_available < p_quantity THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'error', 'Insufficient inventory',
            'available', v_available,
            'requested', p_quantity,
            'channel', p_channel
        );
    END IF;

    -- Deduct inventory
    UPDATE inventory
    SET quantity = quantity - p_quantity,
        updated_at = NOW()
    WHERE variant_id = p_variant_id
    RETURNING quantity INTO v_new_quantity;

    -- Log movement (negative quantity for sale)
    v_movement_id := sp_log_inventory_movement(
        p_variant_id,
        'sale',
        p_channel,
        -p_quantity,
        p_reference_type,
        p_reference_id,
        p_performed_by,
        p_customer_id,
        'inventory',
        'customer',
        p_notes
    );

    RETURN jsonb_build_object(
        'success', TRUE,
        'movement_id', v_movement_id,
        'new_quantity', v_new_quantity,
        'deducted', p_quantity
    );
END;
$$;

GRANT EXECUTE ON FUNCTION sp_deduct_inventory TO postgres;

-- ====================================================================
-- 7. STORED PROCEDURE: Add Inventory with Logging
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_add_inventory(
    p_variant_id INTEGER,
    p_quantity INTEGER,
    p_channel VARCHAR(20),
    p_movement_type VARCHAR(20) DEFAULT 'restock',
    p_performed_by INTEGER DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_movement_id INTEGER;
    v_new_quantity INTEGER;
BEGIN
    -- Add to inventory
    UPDATE inventory
    SET quantity = quantity + p_quantity,
        last_restocked_at = CASE WHEN p_movement_type = 'restock' THEN NOW() ELSE last_restocked_at END,
        updated_at = NOW()
    WHERE variant_id = p_variant_id
    RETURNING quantity INTO v_new_quantity;

    -- Log movement (positive quantity for addition)
    v_movement_id := sp_log_inventory_movement(
        p_variant_id,
        p_movement_type,
        p_channel,
        p_quantity,
        NULL,
        NULL,
        p_performed_by,
        NULL,
        'supplier',
        'inventory',
        p_notes
    );

    RETURN jsonb_build_object(
        'success', TRUE,
        'movement_id', v_movement_id,
        'new_quantity', v_new_quantity,
        'added', p_quantity
    );
END;
$$;

GRANT EXECUTE ON FUNCTION sp_add_inventory TO postgres;

-- ====================================================================
-- 8. STORED PROCEDURE: Clean Up Expired Reservations
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_cleanup_expired_reservations()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_expired_count INTEGER;
BEGIN
    -- Update expired reservations
    WITH expired AS (
        UPDATE inventory_reservations
        SET status = 'expired'
        WHERE status = 'active'
          AND expires_at <= NOW()
        RETURNING id, variant_id, quantity
    )
    SELECT COUNT(*) INTO v_expired_count FROM expired;

    RETURN v_expired_count;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_cleanup_expired_reservations TO postgres;

-- ====================================================================
-- 9. CREATE VIEW: Inventory Summary by Channel
-- ====================================================================

CREATE OR REPLACE VIEW v_inventory_summary AS
SELECT
    i.variant_id,
    p.name AS product_name,
    pv.size,
    pv.color,
    pv.sku,

    -- Total inventory
    i.quantity AS total_quantity,
    i.reserved_quantity,
    i.store_display_units,

    -- Active reservations
    COALESCE(SUM(CASE WHEN r.channel = 'online' AND r.status = 'active' THEN r.quantity ELSE 0 END), 0) AS online_reserved,
    COALESCE(SUM(CASE WHEN r.channel = 'store' AND r.status = 'active' THEN r.quantity ELSE 0 END), 0) AS store_reserved,

    -- Available by channel
    sp_get_available_inventory(i.variant_id, 'online') AS online_available,
    sp_get_available_inventory(i.variant_id, 'store') AS store_available,

    -- Stock status
    CASE
        WHEN i.quantity = 0 THEN 'out_of_stock'
        WHEN i.quantity <= i.low_stock_threshold THEN 'low_stock'
        ELSE 'in_stock'
    END AS stock_status,

    i.primary_location,
    i.last_restocked_at,
    i.updated_at

FROM inventory i
JOIN product_variants pv ON pv.id = i.variant_id
JOIN products p ON p.id = pv.product_id
LEFT JOIN inventory_reservations r ON r.variant_id = i.variant_id
    AND r.status = 'active'
    AND r.expires_at > NOW()
GROUP BY i.id, i.variant_id, p.name, pv.size, pv.color, pv.sku;

COMMENT ON VIEW v_inventory_summary IS 'Comprehensive inventory view with channel-specific availability';

-- ====================================================================
-- 10. CREATE VIEW: Inventory Movements Summary
-- ====================================================================

CREATE OR REPLACE VIEW v_inventory_movements_summary AS
SELECT
    p.name AS product_name,
    pv.sku,
    pv.size,
    pv.color,
    im.movement_type,
    im.channel,
    im.quantity,
    im.quantity_before,
    im.quantity_after,
    im.reference_type,
    im.reference_id,
    COALESCE(e.email, 'System') AS performed_by_email,
    im.notes,
    im.created_at
FROM inventory_movements im
JOIN product_variants pv ON pv.id = im.variant_id
JOIN products p ON p.id = pv.product_id
LEFT JOIN employees e ON e.id = im.performed_by
ORDER BY im.created_at DESC;

COMMENT ON VIEW v_inventory_movements_summary IS 'User-friendly view of inventory movements with product details';

-- ====================================================================
-- MIGRATION COMPLETE
-- ====================================================================
-- Phase 1 inventory enhancements successfully deployed:
-- ✅ Store display units protection
-- ✅ Inventory movements tracking
-- ✅ Channel-aware operations
-- ✅ Comprehensive audit trail
-- ✅ Helpful views for reporting
--
-- Next steps:
-- 1. Create inventory service layer
-- 2. Update existing sale logic to use new procedures
-- 3. Build reporting dashboard
--
-- Rollback: See 004_inventory_enhancements_rollback.sql
-- ====================================================================
