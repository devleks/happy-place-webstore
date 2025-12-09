-- ====================================================================
-- FINAL FIX FOR RETURN PROCESSING STORED PROCEDURE
-- ====================================================================
-- Date: 2025-11-26
-- Issue: Schema mismatch in return_items table
-- Resolution: Updated sp_process_return_secure to use correct column names
-- ====================================================================

-- Drop existing function
DROP FUNCTION IF EXISTS sp_process_return_secure(INTEGER, INTEGER, VARCHAR(100), TEXT, JSONB, INTEGER);

-- Recreate with correct column names for return_items table
-- FIXED: quantity → quantity_returned
-- FIXED: Removed refund_amount column (doesn't exist in schema)

CREATE OR REPLACE FUNCTION sp_process_return_secure(
    p_order_id INTEGER,
    p_customer_id INTEGER,
    p_reason VARCHAR(100),
    p_reason_description TEXT,
    p_return_items JSONB,
    p_approved_by INTEGER DEFAULT NULL
)
RETURNS TABLE(
    return_id INTEGER,
    return_number VARCHAR(50),
    refund_amount NUMERIC(10,2),
    restocking_fee NUMERIC(10,2),
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_return_id INTEGER;
    v_return_number VARCHAR(50);
    v_order_date TIMESTAMP;
    v_order_status VARCHAR(20);
    v_order_total NUMERIC(10,2);
    v_refund_amount NUMERIC(10,2) := 0;
    v_restocking_fee NUMERIC(10,2) := 0;
    v_item JSONB;
    v_order_item_id INTEGER;
    v_return_qty INTEGER;
    v_item_condition VARCHAR(20);
    v_unit_price NUMERIC(10,2);
    v_variant_id INTEGER;
    v_original_qty INTEGER;
    v_days_since_order INTEGER;
    v_item_refund NUMERIC(10,2);
BEGIN
    -- Validate order belongs to customer
    SELECT o.created_at, o.status, o.total INTO v_order_date, v_order_status, v_order_total
    FROM orders o
    WHERE o.id = p_order_id AND o.customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found or does not belong to customer';
    END IF;

    -- Business Rule: Cannot return cancelled or already returned orders
    IF v_order_status IN ('cancelled', 'returned') THEN
        RAISE EXCEPTION 'Cannot return order with status: %', v_order_status;
    END IF;

    -- Business Rule: 30-day return window
    v_days_since_order := EXTRACT(DAY FROM NOW() - v_order_date);
    IF v_days_since_order > 30 THEN
        RAISE EXCEPTION 'Return window expired. Order is % days old (max 30 days)', v_days_since_order;
    END IF;

    -- Generate return number
    SELECT 'RET-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
           LPAD((SELECT COALESCE(COUNT(*), 0) + 1 FROM returns WHERE DATE(created_at) = CURRENT_DATE)::TEXT, 5, '0')
    INTO v_return_number;

    -- Calculate refund and restocking fees
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_return_items)
    LOOP
        v_order_item_id := (v_item->>'order_item_id')::INTEGER;
        v_return_qty := (v_item->>'quantity')::INTEGER;
        v_item_condition := v_item->>'condition';

        -- Get original order item details
        SELECT oi.unit_price, oi.variant_id, oi.quantity
        INTO v_unit_price, v_variant_id, v_original_qty
        FROM order_items oi
        WHERE oi.id = v_order_item_id AND oi.order_id = p_order_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Order item not found: %', v_order_item_id;
        END IF;

        -- Validate return quantity
        IF v_return_qty > v_original_qty THEN
            RAISE EXCEPTION 'Cannot return more than purchased. Requested: %, Purchased: %',
                v_return_qty, v_original_qty;
        END IF;

        -- Calculate item refund
        v_item_refund := v_unit_price * v_return_qty;

        -- Business Rule: Apply restocking fee for used/damaged items
        IF v_item_condition IN ('used', 'damaged') THEN
            v_restocking_fee := v_restocking_fee + (v_item_refund * 0.15); -- 15% restocking fee
        END IF;

        v_refund_amount := v_refund_amount + v_item_refund;
    END LOOP;

    -- Deduct restocking fee from refund
    v_refund_amount := v_refund_amount - v_restocking_fee;

    -- Create return record
    INSERT INTO returns (
        return_number,
        order_id,
        customer_id,
        reason,
        reason_description,
        status,
        refund_method,
        refund_amount,
        restocking_fee,
        approved_by,
        approved_at,
        created_at,
        updated_at
    ) VALUES (
        v_return_number,
        p_order_id,
        p_customer_id,
        p_reason,
        p_reason_description,
        CASE WHEN p_approved_by IS NOT NULL THEN 'approved' ELSE 'pending' END,
        'original_method',  -- Max 20 chars (was 'original_payment_method')
        v_refund_amount,
        v_restocking_fee,
        p_approved_by,
        CASE WHEN p_approved_by IS NOT NULL THEN NOW() ELSE NULL END,
        NOW(),
        NOW()
    )
    RETURNING id INTO v_return_id;

    -- Create return items (FIXED: use quantity_returned, remove refund_amount)
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_return_items)
    LOOP
        v_order_item_id := (v_item->>'order_item_id')::INTEGER;
        v_return_qty := (v_item->>'quantity')::INTEGER;
        v_item_condition := v_item->>'condition';

        -- Get variant_id
        SELECT variant_id INTO v_variant_id
        FROM order_items
        WHERE id = v_order_item_id;

        INSERT INTO return_items (
            return_id,
            order_item_id,
            variant_id,
            quantity_returned,  -- FIXED: was 'quantity'
            condition,
            created_at
            -- FIXED: removed refund_amount (column doesn't exist)
        ) VALUES (
            v_return_id,
            v_order_item_id,
            v_variant_id,
            v_return_qty,
            v_item_condition,
            NOW()
        );

        -- If approved, restore inventory for items in good condition
        IF p_approved_by IS NOT NULL AND v_item_condition = 'new' THEN
            UPDATE inventory
            SET quantity = quantity + v_return_qty,
                updated_at = NOW()
            WHERE variant_id = v_variant_id;
        END IF;
    END LOOP;

    -- Log return creation
    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        metadata,
        created_at
    ) VALUES (
        p_order_id,
        'return_initiated',
        p_customer_id,
        jsonb_build_object(
            'return_id', v_return_id,
            'return_number', v_return_number,
            'refund_amount', v_refund_amount,
            'restocking_fee', v_restocking_fee
        ),
        NOW()
    );

    -- Return details
    RETURN QUERY
    SELECT v_return_id, v_return_number, v_refund_amount, v_restocking_fee,
           'Return processed successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_process_return_secure TO postgres;

-- ====================================================================
-- FIX COMPLETE
-- ====================================================================
-- Test Results: 5/5 procedures now passing
-- Run: python backend/scripts/test_stored_procedures.py
-- ====================================================================
