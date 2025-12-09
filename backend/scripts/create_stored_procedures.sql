-- =====================================================
-- Happy Place Boutique - Secure Stored Procedures
-- Phase 6: Checkout & M-Pesa Payment Integration
-- Security: Atomic operations, row-level locking, audit trail
-- =====================================================

-- =====================================================
-- 1. AUDIT LOG TABLES
-- =====================================================

-- Order Audit Log
CREATE TABLE IF NOT EXISTS order_audit_log (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,  -- 'created', 'payment_initiated', 'paid', 'shipped', 'delivered', etc.
    performed_by INTEGER,          -- customer_id or employee_id
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,                -- Additional context
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_audit_order ON order_audit_log(order_id);
CREATE INDEX IF NOT EXISTS idx_order_audit_action ON order_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_order_audit_created ON order_audit_log(created_at);

-- Payment Callback Log
CREATE TABLE IF NOT EXISTS payment_callback_log (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    callback_data_encrypted TEXT,  -- Full encrypted callback payload
    source_ip INET,
    signature_valid BOOLEAN,
    processed BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_callback_order ON payment_callback_log(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_callback_processed ON payment_callback_log(processed);

-- =====================================================
-- 2. HELPER FUNCTION: Generate Order Number
-- =====================================================

CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS VARCHAR(50) AS $$
DECLARE
    date_part VARCHAR(8);
    sequence_num INTEGER;
    order_number VARCHAR(50);
BEGIN
    -- Format: HP-YYYYMMDD-XXXX
    date_part := TO_CHAR(NOW(), 'YYYYMMDD');
    
    -- Get count of orders today + 1
    SELECT COUNT(*) + 1 INTO sequence_num
    FROM orders
    WHERE DATE(created_at) = CURRENT_DATE;
    
    order_number := 'HP-' || date_part || '-' || LPAD(sequence_num::TEXT, 4, '0');
    
    RETURN order_number;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. STORED PROCEDURE: Deduct Inventory Atomically
-- =====================================================

CREATE OR REPLACE FUNCTION deduct_inventory_atomic(
    p_variant_id INTEGER,
    p_quantity INTEGER,
    p_order_id INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    v_total_quantity INTEGER;
    v_reserved_quantity INTEGER;
    v_available_quantity INTEGER;
BEGIN
    -- Lock inventory row for update (prevent race conditions)
    SELECT quantity, reserved_quantity
    INTO v_total_quantity, v_reserved_quantity
    FROM inventory
    WHERE variant_id = p_variant_id
    FOR UPDATE;

    -- Check if row exists
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Inventory record not found for variant_id %', p_variant_id;
    END IF;

    -- Calculate available quantity (total - reserved)
    v_available_quantity := v_total_quantity - v_reserved_quantity;

    -- Check sufficient stock
    IF v_available_quantity < p_quantity THEN
        RAISE EXCEPTION 'Insufficient stock. Available: %, Requested: %',
            v_available_quantity, p_quantity;
    END IF;

    -- Add to reserved_quantity (don't change total quantity yet)
    UPDATE inventory
    SET reserved_quantity = reserved_quantity + p_quantity,
        updated_at = NOW()
    WHERE variant_id = p_variant_id;

    -- Create inventory transaction record (if table exists)
    BEGIN
        INSERT INTO inventory_transactions (
            variant_id,
            quantity_change,
            transaction_type,
            reference_id,
            notes
        ) VALUES (
            p_variant_id,
            -p_quantity,
            'order_created',
            p_order_id,
            'Inventory reserved for order'
        );
    EXCEPTION
        WHEN undefined_table THEN
            -- Table doesn't exist, skip logging
            NULL;
    END;

    RETURN TRUE;

EXCEPTION
    WHEN OTHERS THEN
        -- Log error and re-raise
        RAISE NOTICE 'Error in deduct_inventory_atomic: %', SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 4. STORED PROCEDURE: Create Order Securely
-- =====================================================

CREATE OR REPLACE FUNCTION create_order_secure(
    p_customer_id INTEGER,
    p_shipping_address_encrypted TEXT,
    p_billing_address_encrypted TEXT,
    p_shipping_method_id INTEGER,
    p_is_nairobi BOOLEAN,
    p_subtotal NUMERIC(10,2),
    p_shipping_cost NUMERIC(10,2),
    p_tax NUMERIC(10,2),
    p_total NUMERIC(10,2),
    p_cart_items JSONB,
    p_ip_address INET,
    p_user_agent TEXT
) RETURNS TABLE(
    order_id INTEGER,
    order_number VARCHAR(50)
) AS $$
DECLARE
    v_order_id INTEGER;
    v_order_number VARCHAR(50);
    v_item JSONB;
    v_order_item_id INTEGER;
    v_actual_subtotal NUMERIC(10,2) := 0;
    v_actual_total_weight NUMERIC(10,2) := 0;
    v_variant RECORD;
BEGIN
    -- Generate order number
    v_order_number := generate_order_number();
    
    -- Validate customer exists
    IF NOT EXISTS (SELECT 1 FROM customers WHERE id = p_customer_id) THEN
        RAISE EXCEPTION 'Customer not found: %', p_customer_id;
    END IF;
    
    -- Validate shipping method
    IF p_shipping_method_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM shipping_methods WHERE id = p_shipping_method_id) THEN
            RAISE EXCEPTION 'Shipping method not found: %', p_shipping_method_id;
        END IF;
    END IF;
    
    -- Re-validate cart items and recalculate subtotal (NEVER trust client)
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_cart_items)
    LOOP
        -- Get variant details
        SELECT pv.id, pv.product_id, p.price, p.sale_price, p.weight
        INTO v_variant
        FROM product_variants pv
        JOIN products p ON pv.product_id = p.id
        WHERE pv.id = (v_item->>'variant_id')::INTEGER
        AND pv.is_active = TRUE
        AND p.is_active = TRUE;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Variant not found or inactive: %', v_item->>'variant_id';
        END IF;
        
        -- Use sale_price if available, otherwise regular price
        v_actual_subtotal := v_actual_subtotal + 
            (COALESCE(v_variant.sale_price, v_variant.price) * (v_item->>'quantity')::INTEGER);
        
        -- Calculate total weight
        v_actual_total_weight := v_actual_total_weight + 
            (v_variant.weight * (v_item->>'quantity')::INTEGER);
    END LOOP;
    
    -- Verify subtotal matches (prevent price manipulation)
    IF ABS(v_actual_subtotal - p_subtotal) > 0.01 THEN
        RAISE EXCEPTION 'Subtotal mismatch. Expected: %, Received: %', 
            v_actual_subtotal, p_subtotal;
    END IF;
    
    -- Create order
    INSERT INTO orders (
        customer_id,
        order_number,
        status,
        subtotal,
        tax,
        shipping_cost,
        total,
        shipping_method_id,
        is_nairobi,
        shipping_address_encrypted,
        billing_address_encrypted,
        created_at
    ) VALUES (
        p_customer_id,
        v_order_number,
        'pending',
        v_actual_subtotal,
        p_tax,
        p_shipping_cost,
        p_total,
        p_shipping_method_id,
        p_is_nairobi,
        p_shipping_address_encrypted,
        p_billing_address_encrypted,
        NOW()
    ) RETURNING id INTO v_order_id;
    
    -- Create order items and deduct inventory
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_cart_items)
    LOOP
        -- Get variant details again
        SELECT pv.id, pv.product_id, p.price, p.sale_price
        INTO v_variant
        FROM product_variants pv
        JOIN products p ON pv.product_id = p.id
        WHERE pv.id = (v_item->>'variant_id')::INTEGER;
        
        -- Create order item
        INSERT INTO order_items (
            order_id,
            product_id,
            variant_id,
            quantity,
            unit_price,
            total_price
        ) VALUES (
            v_order_id,
            v_variant.product_id,
            v_variant.id,
            (v_item->>'quantity')::INTEGER,
            COALESCE(v_variant.sale_price, v_variant.price),
            COALESCE(v_variant.sale_price, v_variant.price) * (v_item->>'quantity')::INTEGER
        ) RETURNING id INTO v_order_item_id;
        
        -- Deduct inventory atomically
        IF NOT deduct_inventory_atomic(
            v_variant.id,
            (v_item->>'quantity')::INTEGER,
            v_order_id
        ) THEN
            RAISE EXCEPTION 'Failed to deduct inventory for variant %', v_variant.id;
        END IF;
    END LOOP;
    
    -- Create audit log entry
    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        ip_address,
        user_agent,
        metadata
    ) VALUES (
        v_order_id,
        'created',
        p_customer_id,
        p_ip_address,
        p_user_agent,
        jsonb_build_object(
            'subtotal', v_actual_subtotal,
            'shipping_cost', p_shipping_cost,
            'total', p_total,
            'item_count', jsonb_array_length(p_cart_items)
        )
    );
    
    -- Return order details
    RETURN QUERY SELECT v_order_id, v_order_number;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log error
        RAISE NOTICE 'Error in create_order_secure: %', SQLERRM;
        -- Rollback happens automatically
        RAISE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 5. STORED PROCEDURE: Process Payment Securely
-- =====================================================

CREATE OR REPLACE FUNCTION process_payment_secure(
    p_order_id INTEGER,
    p_transaction_id_encrypted TEXT,
    p_mpesa_phone_encrypted TEXT,
    p_amount NUMERIC(10,2),
    p_payment_method VARCHAR(20),
    p_ip_address INET
) RETURNS BOOLEAN AS $$
DECLARE
    v_order_total NUMERIC(10,2);
    v_order_status VARCHAR(20);
    v_payment_exists BOOLEAN;
BEGIN
    -- Lock order row
    SELECT total, status INTO v_order_total, v_order_status
    FROM orders
    WHERE id = p_order_id
    FOR UPDATE;
    
    -- Verify order exists
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found: %', p_order_id;
    END IF;
    
    -- Verify order is in pending state
    IF v_order_status != 'pending' THEN
        RAISE EXCEPTION 'Order is not pending. Status: %', v_order_status;
    END IF;
    
    -- Verify amount matches (prevent manipulation)
    IF ABS(v_order_total - p_amount) > 0.01 THEN
        RAISE EXCEPTION 'Payment amount mismatch. Expected: %, Received: %',
            v_order_total, p_amount;
    END IF;
    
    -- Check if payment already exists (idempotency)
    SELECT EXISTS(SELECT 1 FROM payments WHERE order_id = p_order_id)
    INTO v_payment_exists;
    
    IF v_payment_exists THEN
        -- Payment already processed, return success
        RAISE NOTICE 'Payment already exists for order %', p_order_id;
        RETURN TRUE;
    END IF;
    
    -- Create payment record
    INSERT INTO payments (
        order_id,
        amount,
        payment_method,
        mpesa_phone_encrypted,
        transaction_id_encrypted,
        status,
        created_at
    ) VALUES (
        p_order_id,
        p_amount,
        p_payment_method,
        p_mpesa_phone_encrypted,
        p_transaction_id_encrypted,
        'pending',
        NOW()
    );
    
    -- Create audit log
    INSERT INTO order_audit_log (
        order_id,
        action,
        ip_address,
        metadata
    ) VALUES (
        p_order_id,
        'payment_initiated',
        p_ip_address,
        jsonb_build_object(
            'payment_method', p_payment_method,
            'amount', p_amount
        )
    );
    
    RETURN TRUE;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error in process_payment_secure: %', SQLERRM;
        RAISE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 6. STORED PROCEDURE: Complete Payment (After Callback)
-- =====================================================

CREATE OR REPLACE FUNCTION complete_payment(
    p_order_id INTEGER,
    p_ip_address INET
) RETURNS BOOLEAN AS $$
BEGIN
    -- Update payment status
    UPDATE payments
    SET status = 'completed',
        completed_at = NOW()
    WHERE order_id = p_order_id
    AND status = 'pending';

    -- Update order status
    UPDATE orders
    SET status = 'processing'
    WHERE id = p_order_id
    AND status = 'pending';

    -- Unreserve inventory and deduct from total quantity
    UPDATE inventory i
    SET reserved_quantity = reserved_quantity - oi.quantity,
        quantity = quantity - oi.quantity
    FROM order_items oi
    WHERE i.variant_id = oi.variant_id
    AND oi.order_id = p_order_id;

    -- Create audit log
    INSERT INTO order_audit_log (
        order_id,
        action,
        ip_address,
        metadata
    ) VALUES (
        p_order_id,
        'payment_completed',
        p_ip_address,
        jsonb_build_object('timestamp', NOW())
    );

    RETURN TRUE;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error in complete_payment: %', SQLERRM;
        RAISE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 7. GRANT PERMISSIONS
-- =====================================================

-- Grant execute permission to application user
-- GRANT EXECUTE ON FUNCTION create_order_secure TO your_app_user;
-- GRANT EXECUTE ON FUNCTION process_payment_secure TO your_app_user;
-- GRANT EXECUTE ON FUNCTION deduct_inventory_atomic TO your_app_user;
-- GRANT EXECUTE ON FUNCTION complete_payment TO your_app_user;

-- =====================================================
-- END OF STORED PROCEDURES
-- =====================================================
