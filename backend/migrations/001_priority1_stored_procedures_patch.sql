-- ====================================================================
-- PATCH FOR PRIORITY 1 STORED PROCEDURES
-- ====================================================================
-- Fixes audit log column names to match actual schema
-- ====================================================================

-- Drop existing functions
DROP FUNCTION IF EXISTS sp_create_order_secure(INTEGER, TEXT, TEXT, VARCHAR(20), JSONB, INTEGER, BOOLEAN, NUMERIC(10,2));
DROP FUNCTION IF EXISTS sp_process_payment_secure(INTEGER, TEXT, TEXT);

-- ====================================================================
-- 1. ORDER CREATION STORED PROCEDURE (FIXED)
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_create_order_secure(
    p_customer_id INTEGER,
    p_shipping_address_encrypted TEXT,
    p_billing_address_encrypted TEXT,
    p_payment_method VARCHAR(20),
    p_cart_items JSONB,
    p_shipping_method_id INTEGER DEFAULT NULL,
    p_is_nairobi BOOLEAN DEFAULT FALSE,
    p_shipping_cost NUMERIC(10,2) DEFAULT 0.00
)
RETURNS TABLE(
    order_id INTEGER,
    order_number VARCHAR(50),
    payment_id INTEGER,
    total_amount NUMERIC(10,2)
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_order_id INTEGER;
    v_order_number VARCHAR(50);
    v_payment_id INTEGER;
    v_subtotal NUMERIC(10,2) := 0;
    v_tax NUMERIC(10,2) := 0;
    v_total NUMERIC(10,2) := 0;
    v_item JSONB;
    v_variant_id INTEGER;
    v_quantity INTEGER;
    v_unit_price NUMERIC(10,2);
    v_product_id INTEGER;
    v_available_qty INTEGER;
BEGIN
    -- Lock order number generation to prevent race conditions
    LOCK TABLE orders IN EXCLUSIVE MODE;

    -- Generate unique order number with collision prevention
    SELECT 'ORD-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
           LPAD((
               SELECT COALESCE(COUNT(*), 0) + 1
               FROM orders
               WHERE DATE(created_at) = CURRENT_DATE
           )::TEXT, 5, '0')
    INTO v_order_number;

    -- Validate cart items exist and calculate subtotal
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_cart_items)
    LOOP
        v_variant_id := (v_item->>'variant_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;
        v_unit_price := (v_item->>'unit_price')::NUMERIC(10,2);

        -- Get product_id and verify variant exists
        SELECT pv.product_id INTO v_product_id
        FROM product_variants pv
        WHERE pv.id = v_variant_id AND pv.is_active = TRUE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Invalid or inactive variant_id: %', v_variant_id;
        END IF;

        -- Check inventory availability
        SELECT (quantity - reserved_quantity) INTO v_available_qty
        FROM inventory
        WHERE variant_id = v_variant_id;

        IF v_available_qty < v_quantity THEN
            RAISE EXCEPTION 'Insufficient inventory for variant_id: % (available: %, requested: %)',
                v_variant_id, v_available_qty, v_quantity;
        END IF;

        -- Add to subtotal
        v_subtotal := v_subtotal + (v_unit_price * v_quantity);
    END LOOP;

    -- Calculate tax (VAT 16% - already included in prices)
    -- Extract VAT component: VAT = Subtotal - (Subtotal / 1.16)
    v_tax := v_subtotal - (v_subtotal / 1.16);

    -- Calculate total
    v_total := v_subtotal + p_shipping_cost;

    -- Create order record
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
        created_at,
        updated_at
    ) VALUES (
        p_customer_id,
        v_order_number,
        'pending',
        v_subtotal,
        v_tax,
        p_shipping_cost,
        v_total,
        p_shipping_method_id,
        p_is_nairobi,
        p_shipping_address_encrypted,
        p_billing_address_encrypted,
        NOW(),
        NOW()
    )
    RETURNING id INTO v_order_id;

    -- Create order items
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_cart_items)
    LOOP
        v_variant_id := (v_item->>'variant_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;
        v_unit_price := (v_item->>'unit_price')::NUMERIC(10,2);

        -- Get product_id
        SELECT product_id INTO v_product_id
        FROM product_variants
        WHERE id = v_variant_id;

        -- Insert order item
        INSERT INTO order_items (
            order_id,
            product_id,
            variant_id,
            quantity,
            unit_price,
            total_price
        ) VALUES (
            v_order_id,
            v_product_id,
            v_variant_id,
            v_quantity,
            v_unit_price,
            v_unit_price * v_quantity
        );

        -- Reserve inventory atomically
        UPDATE inventory
        SET reserved_quantity = reserved_quantity + v_quantity,
            updated_at = NOW()
        WHERE variant_id = v_variant_id;
    END LOOP;

    -- Create payment record
    INSERT INTO payments (
        order_id,
        payment_method,
        amount,
        status,
        created_at
    ) VALUES (
        v_order_id,
        p_payment_method,
        v_total,
        CASE
            WHEN p_payment_method = 'cod' THEN 'pending'
            ELSE 'pending'
        END,
        NOW()
    )
    RETURNING id INTO v_payment_id;

    -- Log order creation in audit trail (fixed column names)
    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        metadata,
        created_at
    ) VALUES (
        v_order_id,
        'order_created',
        p_customer_id,
        jsonb_build_object(
            'order_number', v_order_number,
            'payment_method', p_payment_method,
            'total', v_total,
            'items_count', jsonb_array_length(p_cart_items)
        ),
        NOW()
    );

    -- Return order details
    RETURN QUERY
    SELECT v_order_id, v_order_number, v_payment_id, v_total;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_create_order_secure TO postgres;

-- ====================================================================
-- 2. PAYMENT PROCESSING STORED PROCEDURE (FIXED)
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_process_payment_secure(
    p_payment_id INTEGER,
    p_transaction_id_encrypted TEXT DEFAULT NULL,
    p_mpesa_phone_encrypted TEXT DEFAULT NULL
)
RETURNS TABLE(
    success BOOLEAN,
    order_id INTEGER,
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_order_id INTEGER;
    v_payment_status VARCHAR(20);
    v_order_status VARCHAR(20);
    v_item RECORD;
BEGIN
    -- Lock payment for update
    SELECT p.order_id, p.status INTO v_order_id, v_payment_status
    FROM payments p
    WHERE p.id = p_payment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, NULL::INTEGER, 'Payment not found'::TEXT;
        RETURN;
    END IF;

    -- Check if already completed
    IF v_payment_status = 'completed' THEN
        RETURN QUERY
        SELECT FALSE, v_order_id, 'Payment already completed'::TEXT;
        RETURN;
    END IF;

    -- Update payment status
    UPDATE payments
    SET status = 'completed',
        completed_at = NOW(),
        transaction_id_encrypted = p_transaction_id_encrypted,
        mpesa_phone_encrypted = p_mpesa_phone_encrypted
    WHERE id = p_payment_id;

    -- Update order status
    UPDATE orders
    SET status = 'processing',
        updated_at = NOW()
    WHERE id = v_order_id;

    -- Convert reserved inventory to actual deduction
    FOR v_item IN
        SELECT oi.variant_id, oi.quantity
        FROM order_items oi
        WHERE oi.order_id = v_order_id
    LOOP
        -- Deduct from actual quantity and remove from reserved
        UPDATE inventory
        SET quantity = quantity - v_item.quantity,
            reserved_quantity = reserved_quantity - v_item.quantity,
            updated_at = NOW()
        WHERE variant_id = v_item.variant_id;
    END LOOP;

    -- Log payment completion (fixed column names)
    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        metadata,
        created_at
    )
    SELECT
        v_order_id,
        'payment_completed',
        o.customer_id,
        jsonb_build_object(
            'payment_id', p_payment_id,
            'transaction_id', CASE WHEN p_transaction_id_encrypted IS NOT NULL THEN 'encrypted' ELSE NULL END
        ),
        NOW()
    FROM orders o
    WHERE o.id = v_order_id;

    -- Return success
    RETURN QUERY
    SELECT TRUE, v_order_id, 'Payment processed successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_process_payment_secure TO postgres;

-- ====================================================================
-- PATCH COMPLETE
-- ====================================================================
