-- ====================================================================
-- COD CONFIRMATION & EXPIRY
-- ====================================================================
-- Purpose:
-- - Add COD confirmation tracking fields
-- - Enforce 24h COD confirmation window
-- - Auto-cancel unconfirmed COD orders after expiry and release reserved stock
-- ====================================================================

-- 1) Add COD confirmation fields to orders
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS cod_confirmed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS cod_confirmation_expires_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_orders_cod_confirmation_expires
ON orders(cod_confirmation_expires_at)
WHERE cod_confirmed_at IS NULL AND cod_confirmation_expires_at IS NOT NULL;

-- 2) Update order creation procedure to set COD confirmation expiry
DROP FUNCTION IF EXISTS sp_create_order_secure(INTEGER, TEXT, TEXT, VARCHAR(20), JSONB, INTEGER, BOOLEAN, NUMERIC(10,2));

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

        -- Check inventory availability (channel-aware: respects display units/reservations)
        SELECT sp_get_available_inventory(v_variant_id, 'online') INTO v_available_qty;

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
        cod_confirmation_expires_at,
        created_at,
        updated_at
    ) VALUES (
        p_customer_id,
        v_order_number,
        CASE
            WHEN p_payment_method = 'cod' THEN 'processing'
            ELSE 'pending'
        END,
        v_subtotal,
        v_tax,
        p_shipping_cost,
        v_total,
        p_shipping_method_id,
        p_is_nairobi,
        p_shipping_address_encrypted,
        p_billing_address_encrypted,
        CASE
            WHEN p_payment_method = 'cod' THEN NOW() + INTERVAL '24 hours'
            ELSE NULL
        END,
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
        'pending',
        NOW()
    )
    RETURNING id INTO v_payment_id;

    -- Log order creation in audit trail
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
            'items_count', jsonb_array_length(p_cart_items),
            'cod_confirmation_expires_at', CASE WHEN p_payment_method = 'cod' THEN (NOW() + INTERVAL '24 hours') ELSE NULL END
        ),
        NOW()
    );

    -- Return order details
    RETURN QUERY
    SELECT v_order_id, v_order_number, v_payment_id, v_total;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_create_order_secure TO postgres;

-- 3) COD confirmation procedure
DROP FUNCTION IF EXISTS sp_confirm_cod_order(INTEGER, INTEGER, INTEGER);

CREATE OR REPLACE FUNCTION sp_confirm_cod_order(
    p_order_id INTEGER,
    p_customer_id INTEGER DEFAULT NULL,
    p_employee_id INTEGER DEFAULT NULL
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_payment_method VARCHAR(20);
    v_payment_status VARCHAR(20);
    v_customer_id INTEGER;
    v_expires_at TIMESTAMP;
BEGIN
    SELECT o.customer_id, o.cod_confirmation_expires_at
    INTO v_customer_id, v_expires_at
    FROM orders o
    WHERE o.id = p_order_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Order not found'::TEXT;
        RETURN;
    END IF;

    IF p_customer_id IS NOT NULL AND v_customer_id != p_customer_id THEN
        RETURN QUERY SELECT FALSE, 'Unauthorized'::TEXT;
        RETURN;
    END IF;

    SELECT p.payment_method, p.status
    INTO v_payment_method, v_payment_status
    FROM payments p
    WHERE p.order_id = p_order_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Payment not found'::TEXT;
        RETURN;
    END IF;

    IF v_payment_method != 'cod' THEN
        RETURN QUERY SELECT FALSE, 'Order is not COD'::TEXT;
        RETURN;
    END IF;

    IF v_payment_status IN ('completed', 'refunded') THEN
        RETURN QUERY SELECT FALSE, 'Order payment already processed'::TEXT;
        RETURN;
    END IF;

    IF v_expires_at IS NOT NULL AND v_expires_at < NOW() THEN
        RETURN QUERY SELECT FALSE, 'COD confirmation window expired'::TEXT;
        RETURN;
    END IF;

    UPDATE orders
    SET cod_confirmed_at = NOW(),
        updated_at = NOW()
    WHERE id = p_order_id
      AND cod_confirmed_at IS NULL;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'COD already confirmed'::TEXT;
        RETURN;
    END IF;

    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        metadata,
        created_at
    ) VALUES (
        p_order_id,
        'cod_confirmed',
        COALESCE(p_employee_id, p_customer_id),
        jsonb_build_object(
            'confirmed_by', CASE WHEN p_employee_id IS NOT NULL THEN 'employee' ELSE 'customer' END,
            'employee_id', p_employee_id,
            'customer_id', p_customer_id
        ),
        NOW()
    );

    RETURN QUERY SELECT TRUE, 'COD confirmed'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_confirm_cod_order TO postgres;

-- 4) Expire unconfirmed COD orders and release reserved inventory
DROP FUNCTION IF EXISTS sp_expire_unconfirmed_cod_orders(INTEGER);

CREATE OR REPLACE FUNCTION sp_expire_unconfirmed_cod_orders(
    p_max_orders INTEGER DEFAULT 1000
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_order RECORD;
    v_item RECORD;
    v_cancelled_count INTEGER := 0;
BEGIN
    FOR v_order IN
        SELECT o.id
        FROM orders o
        JOIN payments p ON p.order_id = o.id
        WHERE p.payment_method = 'cod'
          AND p.status = 'pending'
          AND o.cod_confirmed_at IS NULL
          AND o.cod_confirmation_expires_at IS NOT NULL
          AND o.cod_confirmation_expires_at < NOW()
          AND o.status NOT IN ('cancelled', 'delivered', 'completed')
        ORDER BY o.cod_confirmation_expires_at ASC
        LIMIT p_max_orders
        FOR UPDATE
    LOOP
        -- Release reserved inventory
        FOR v_item IN
            SELECT oi.variant_id, oi.quantity
            FROM order_items oi
            WHERE oi.order_id = v_order.id
        LOOP
            UPDATE inventory
            SET reserved_quantity = GREATEST(reserved_quantity - v_item.quantity, 0),
                updated_at = NOW()
            WHERE variant_id = v_item.variant_id;
        END LOOP;

        -- Cancel order and mark payment as failed
        UPDATE orders
        SET status = 'cancelled',
            updated_at = NOW()
        WHERE id = v_order.id;

        UPDATE payments
        SET status = 'failed'
        WHERE order_id = v_order.id
          AND status = 'pending';

        INSERT INTO order_audit_log (
            order_id,
            action,
            performed_by,
            metadata,
            created_at
        ) VALUES (
            v_order.id,
            'cod_expired_cancelled',
            NULL,
            jsonb_build_object(
                'reason', 'COD not confirmed within 24 hours'
            ),
            NOW()
        );

        v_cancelled_count := v_cancelled_count + 1;
    END LOOP;

    RETURN v_cancelled_count;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_expire_unconfirmed_cod_orders TO postgres;
