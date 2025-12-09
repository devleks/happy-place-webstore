-- ====================================================================
-- MIGRATION 007: FIX STORED PROCEDURES AFTER SCHEMA OPTIMIZATION
-- ====================================================================
-- Purpose: Remove performed_by references from stored procedures
-- Date: 2025-12-05
-- ====================================================================

BEGIN;

-- --------------------------------------------------------------------
-- Fix sp_start_shift - Remove performed_by from cash movement insert
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_start_shift(
    p_employee_id INTEGER,
    p_store_location_id INTEGER,
    p_opening_float NUMERIC(10,2)
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_shift_id INTEGER;
    v_shift_number VARCHAR(50);
    v_open_shift INTEGER;
    v_today VARCHAR(8);
    v_today_count INTEGER;
BEGIN
    -- Check if employee already has an open shift
    SELECT id INTO v_open_shift
    FROM pos_shifts
    WHERE employee_id = p_employee_id
      AND status = 'open';

    IF v_open_shift IS NOT NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Employee already has an open shift',
            'shift_id', v_open_shift
        );
    END IF;

    -- Generate smart shift number: YYYYMMDD-LOC{id}-EMP{id}-{seq}
    v_today := TO_CHAR(NOW(), 'YYYYMMDD');

    SELECT COUNT(*) INTO v_today_count
    FROM pos_shifts
    WHERE employee_id = p_employee_id
      AND DATE(start_time) = CURRENT_DATE;

    v_shift_number := v_today || '-LOC' || p_store_location_id || '-EMP' || p_employee_id || '-' || LPAD((v_today_count + 1)::TEXT, 3, '0');

    -- Create shift
    INSERT INTO pos_shifts (
        employee_id,
        store_location_id,
        shift_number,
        start_time,
        opening_float,
        status,
        created_at
    ) VALUES (
        p_employee_id,
        p_store_location_id,
        v_shift_number,
        NOW(),
        p_opening_float,
        'open',
        NOW()
    ) RETURNING id INTO v_shift_id;

    -- Log opening float (NO performed_by column)
    INSERT INTO pos_cash_movements (
        shift_id,
        movement_type,
        amount,
        reason,
        created_at
    ) VALUES (
        v_shift_id,
        'starting_float',
        p_opening_float,
        'Shift opening float',
        NOW()
    );

    RETURN jsonb_build_object(
        'success', true,
        'shift_id', v_shift_id,
        'shift_number', v_shift_number,
        'opening_float', p_opening_float,
        'start_time', NOW()
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$;

-- --------------------------------------------------------------------
-- Fix sp_close_shift - Remove performed_by from cash movement insert
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_close_shift(
    p_shift_id INTEGER,
    p_closing_cash NUMERIC(10,2),
    p_notes TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_employee_id INTEGER;
    v_opening_float NUMERIC(10,2);
    v_cash_sales NUMERIC(10,2) := 0;
    v_cash_in NUMERIC(10,2) := 0;
    v_cash_out NUMERIC(10,2) := 0;
    v_expected_cash NUMERIC(10,2);
    v_variance NUMERIC(10,2);
BEGIN
    -- Get shift details
    SELECT employee_id, opening_float
    INTO v_employee_id, v_opening_float
    FROM pos_shifts
    WHERE id = p_shift_id AND status = 'open';

    IF v_employee_id IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Shift not found or already closed'
        );
    END IF;

    -- Calculate cash sales (only completed, non-voided cash transactions)
    SELECT COALESCE(SUM(total), 0) INTO v_cash_sales
    FROM pos_transactions
    WHERE shift_id = p_shift_id
      AND payment_method = 'cash'
      AND status = 'completed';

    -- Calculate cash movements
    SELECT 
        COALESCE(SUM(CASE WHEN movement_type = 'cash_in' THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN movement_type = 'cash_out' THEN amount ELSE 0 END), 0)
    INTO v_cash_in, v_cash_out
    FROM pos_cash_movements
    WHERE shift_id = p_shift_id
      AND movement_type IN ('cash_in', 'cash_out');

    -- Calculate expected cash
    v_expected_cash := v_opening_float + v_cash_sales + v_cash_in - v_cash_out;
    v_variance := p_closing_cash - v_expected_cash;

    -- Log closing count (NO performed_by column)
    INSERT INTO pos_cash_movements (
        shift_id,
        movement_type,
        amount,
        reason,
        created_at
    ) VALUES (
        p_shift_id,
        'closing_count',
        p_closing_cash,
        'Shift closing count',
        NOW()
    );

    -- Update shift
    UPDATE pos_shifts
    SET 
        end_time = NOW(),
        closing_cash = p_closing_cash,
        expected_cash = v_expected_cash,
        cash_variance = v_variance,
        notes = p_notes,
        status = 'closed',
        updated_at = NOW()
    WHERE id = p_shift_id;

    RETURN jsonb_build_object(
        'success', true,
        'shift_id', p_shift_id,
        'opening_float', v_opening_float,
        'cash_sales', v_cash_sales,
        'cash_in', v_cash_in,
        'cash_out', v_cash_out,
        'expected_cash', v_expected_cash,
        'closing_cash', p_closing_cash,
        'variance', v_variance
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$;

-- --------------------------------------------------------------------
-- Verify procedures updated
-- --------------------------------------------------------------------
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION 007 COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Updated stored procedures:';
    RAISE NOTICE '  • sp_start_shift - Removed performed_by';
    RAISE NOTICE '  • sp_close_shift - Removed performed_by';
    RAISE NOTICE '';
    RAISE NOTICE 'All procedures now compatible with optimized schema';
END $$;

COMMIT;
