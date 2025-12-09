-- Migration: Fix POS Transaction to respect normalized schema
-- Date: 2025-12-08
-- Purpose: Remove employee_id from pos_transactions INSERT (get it from shift instead)

CREATE OR REPLACE FUNCTION sp_create_pos_transaction(
    p_employee_id INTEGER,  -- Still passed for validation, but not inserted
    p_store_location_id INTEGER,
    p_shift_id INTEGER,
    p_payment_method VARCHAR(20),
    p_items JSONB,
    p_customer_id INTEGER DEFAULT NULL,
    p_cash_tendered NUMERIC(10,2) DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_transaction_id INTEGER;
    v_transaction_number VARCHAR(50);
    v_item JSONB;
    v_variant_id INTEGER;
    v_product_id INTEGER;
    v_inventory_id INTEGER;
    v_quantity INTEGER;
    v_price NUMERIC(10,2);
    v_subtotal NUMERIC(10,2);
    v_total NUMERIC(10,2) := 0;
    v_change_given NUMERIC(10,2) := 0;
    v_shift_employee_id INTEGER;
BEGIN
    -- Verify shift exists and belongs to employee
    SELECT employee_id INTO v_shift_employee_id
    FROM pos_shifts
    WHERE id = p_shift_id AND status = 'open';
    
    IF v_shift_employee_id IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Shift not found or not open'
        );
    END IF;
    
    -- Verify employee matches shift (security check)
    IF v_shift_employee_id != p_employee_id THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Employee does not match shift'
        );
    END IF;
    
    -- Generate transaction number
    v_transaction_number := 'TXN-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || 
                           LPAD(nextval('pos_transaction_number_seq')::TEXT, 6, '0');
    
    -- Create transaction (WITHOUT employee_id and store_location_id - both come from shift)
    INSERT INTO pos_transactions (
        transaction_number,
        shift_id,
        customer_id,
        payment_method,
        subtotal,
        tax,
        total,
        cash_tendered,
        change_given,
        status,
        created_at
    ) VALUES (
        v_transaction_number,
        p_shift_id,
        p_customer_id,
        p_payment_method,
        0,  -- Will be updated
        0,  -- Will be updated
        0,  -- Will be updated
        p_cash_tendered,
        0,  -- Will be calculated
        'completed',
        NOW()
    ) RETURNING id INTO v_transaction_id;
    
    -- Process each item
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_variant_id := (v_item->>'variant_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;
        
        -- Get product_id and inventory_id from variant, and price from product
        SELECT pv.product_id, i.id, p.price 
        INTO v_product_id, v_inventory_id, v_price
        FROM product_variants pv
        JOIN products p ON p.id = pv.product_id
        JOIN inventory i ON i.variant_id = pv.id
        WHERE pv.id = v_variant_id;
        
        IF v_price IS NULL THEN
            RAISE EXCEPTION 'Variant % not found', v_variant_id;
        END IF;
        
        v_subtotal := v_price * v_quantity;
        v_total := v_total + v_subtotal;
        
        -- Insert transaction item (using product_id and inventory_id, not variant_id)
        INSERT INTO pos_transaction_items (
            transaction_id,
            product_id,
            inventory_id,
            quantity,
            unit_price,
            total_price
        ) VALUES (
            v_transaction_id,
            v_product_id,
            v_inventory_id,
            v_quantity,
            v_price,
            v_subtotal
        );
        
        -- Deduct inventory
        UPDATE inventory
        SET quantity = quantity - v_quantity
        WHERE id = v_inventory_id;
        
    END LOOP;
    
    -- Calculate change if cash payment
    IF p_payment_method = 'cash' AND p_cash_tendered IS NOT NULL THEN
        v_change_given := p_cash_tendered - v_total;
        IF v_change_given < 0 THEN
            RAISE EXCEPTION 'Insufficient cash tendered';
        END IF;
    END IF;
    
    -- Update transaction totals (no updated_at column in this table)
    UPDATE pos_transactions
    SET subtotal = v_total,
        total = v_total,
        change_given = v_change_given
    WHERE id = v_transaction_id;
    
    -- Return success
    RETURN jsonb_build_object(
        'success', true,
        'transaction_id', v_transaction_id,
        'transaction_number', v_transaction_number,
        'total', v_total,
        'change_given', v_change_given
    );
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$;

-- Create sequence if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS pos_transaction_number_seq;

COMMENT ON FUNCTION sp_create_pos_transaction IS 'Create POS transaction with normalized schema (employee_id comes from shift)';
