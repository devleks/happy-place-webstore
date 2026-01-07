-- ====================================================================
-- FIX PAYMENT COMPLETION STATUS UPDATE
-- ====================================================================
-- Purpose:
-- - Prevent sp_process_payment_secure from overwriting advanced order statuses
--   (e.g. shipped/delivered) when marking COD as paid.
-- ====================================================================

DROP FUNCTION IF EXISTS sp_process_payment_secure(INTEGER, TEXT, TEXT);

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
    v_item RECORD;
    v_customer_id INTEGER;
    v_current_order_status VARCHAR(20);
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

    SELECT status INTO v_current_order_status
    FROM orders
    WHERE id = v_order_id
    FOR UPDATE;

    -- Update payment status
    UPDATE payments
    SET status = 'completed',
        completed_at = NOW(),
        transaction_id_encrypted = p_transaction_id_encrypted,
        mpesa_phone_encrypted = p_mpesa_phone_encrypted
    WHERE id = p_payment_id;

    -- Update order status (preserve advanced statuses)
    UPDATE orders
    SET status = CASE
            WHEN status IN ('shipped', 'delivered', 'completed', 'cancelled', 'packing', 'packed', 'shipping') THEN status
            ELSE 'processing'
        END,
        updated_at = NOW()
    WHERE id = v_order_id;

    SELECT customer_id INTO v_customer_id
    FROM orders
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

        -- Log inventory movement
        PERFORM sp_log_inventory_movement(
            v_item.variant_id,
            'sale',
            'online',
            -v_item.quantity,
            'order',
            v_order_id,
            NULL,
            v_customer_id,
            'inventory',
            'customer',
            'Online order payment completed'
        );
    END LOOP;

    -- Log payment completion
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
            'transaction_id', CASE WHEN p_transaction_id_encrypted IS NOT NULL THEN 'encrypted' ELSE NULL END,
            'previous_order_status', v_current_order_status
        ),
        NOW()
    FROM orders o
    WHERE o.id = v_order_id;

    RETURN QUERY
    SELECT TRUE, v_order_id, 'Payment processed successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_process_payment_secure TO postgres;
