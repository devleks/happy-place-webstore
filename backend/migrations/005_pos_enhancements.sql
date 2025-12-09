-- ====================================================================
-- MIGRATION 005: POS SYSTEM ENHANCEMENTS
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Add shift management, cash tracking, and enhance POS tables
-- Dependencies: Existing pos_transactions, pos_transaction_items tables
-- ====================================================================

-- ====================================================================
-- 1. CREATE NEW TABLES
-- ====================================================================

-- Table: pos_shifts
-- Purpose: Track employee shifts and cash management
CREATE TABLE IF NOT EXISTS pos_shifts (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    store_location_id INTEGER NOT NULL REFERENCES store_locations(id),
    shift_number VARCHAR(50) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP,
    opening_float NUMERIC(10,2) NOT NULL,
    closing_cash NUMERIC(10,2),
    expected_cash NUMERIC(10,2),
    variance NUMERIC(10,2),
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT pos_shifts_status_check CHECK (status IN ('open', 'closed'))
);

-- Indexes for pos_shifts
CREATE INDEX idx_pos_shifts_employee ON pos_shifts(employee_id);
CREATE INDEX idx_pos_shifts_store ON pos_shifts(store_location_id);
CREATE INDEX idx_pos_shifts_status ON pos_shifts(status);
CREATE INDEX idx_pos_shifts_start_time ON pos_shifts(start_time);

-- Table: pos_cash_movements
-- Purpose: Track all cash in/out activities during shifts
CREATE TABLE IF NOT EXISTS pos_cash_movements (
    id SERIAL PRIMARY KEY,
    shift_id INTEGER NOT NULL REFERENCES pos_shifts(id) ON DELETE CASCADE,
    movement_type VARCHAR(20) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    reason TEXT,
    performed_by INTEGER NOT NULL REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT pos_cash_movements_type_check CHECK (
        movement_type IN ('cash_in', 'cash_out', 'starting_float', 'closing_count', 'adjustment')
    )
);

-- Indexes for pos_cash_movements
CREATE INDEX idx_pos_cash_movements_shift ON pos_cash_movements(shift_id);
CREATE INDEX idx_pos_cash_movements_type ON pos_cash_movements(movement_type);

-- ====================================================================
-- 2. MODIFY EXISTING TABLES
-- ====================================================================

-- Add new columns to pos_transactions
ALTER TABLE pos_transactions
    ADD COLUMN IF NOT EXISTS shift_id INTEGER REFERENCES pos_shifts(id),
    ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(id),
    ADD COLUMN IF NOT EXISTS receipt_printed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS receipt_emailed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS voided_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS voided_by INTEGER REFERENCES employees(id),
    ADD COLUMN IF NOT EXISTS void_reason TEXT;

-- Indexes for new columns
CREATE INDEX IF NOT EXISTS idx_pos_transactions_shift ON pos_transactions(shift_id);
CREATE INDEX IF NOT EXISTS idx_pos_transactions_customer ON pos_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_pos_transactions_voided ON pos_transactions(voided_at) WHERE voided_at IS NOT NULL;

-- ====================================================================
-- 3. STORED PROCEDURES
-- ====================================================================

-- --------------------------------------------------------------------
-- Procedure: sp_create_pos_transaction
-- Purpose: Create a POS transaction with inventory deduction
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_create_pos_transaction(
    p_employee_id INTEGER,
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
    v_subtotal NUMERIC(10,2) := 0;
    v_tax NUMERIC(10,2) := 0;
    v_total NUMERIC(10,2) := 0;
    v_change_given NUMERIC(10,2) := 0;
    v_variant_id INTEGER;
    v_quantity INTEGER;
    v_unit_price NUMERIC(10,2);
    v_total_price NUMERIC(10,2);
    v_available INTEGER;
    v_product_id INTEGER;
    v_inventory_id INTEGER;
    v_today_count INTEGER;
    v_today VARCHAR(8);
BEGIN
    -- Validate shift is open
    IF NOT EXISTS (
        SELECT 1 FROM pos_shifts
        WHERE id = p_shift_id AND status = 'open'
    ) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Shift is not open'
        );
    END IF;

    -- Generate transaction number: POS-YYYYMMDD-NNNN
    v_today := TO_CHAR(NOW(), 'YYYYMMDD');

    SELECT COUNT(*) INTO v_today_count
    FROM pos_transactions
    WHERE DATE(created_at) = CURRENT_DATE;

    v_transaction_number := 'POS-' || v_today || '-' || LPAD((v_today_count + 1)::TEXT, 4, '0');

    -- Loop through items to calculate totals and validate inventory
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_variant_id := (v_item->>'variant_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;

        -- Get product_id and inventory_id for this variant
        SELECT pv.product_id, i.id, i.quantity
        INTO v_product_id, v_inventory_id, v_available
        FROM product_variants pv
        JOIN inventory i ON i.variant_id = pv.id
        WHERE pv.id = v_variant_id;

        IF v_product_id IS NULL THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'Variant not found: ' || v_variant_id
            );
        END IF;

        -- Check inventory availability (store channel sees all except reserved)
        SELECT sp_get_available_inventory(v_variant_id, 'store') INTO v_available;

        IF v_available < v_quantity THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'Insufficient inventory for variant: ' || v_variant_id,
                'available', v_available,
                'requested', v_quantity
            );
        END IF;

        -- Get unit price (check for sale price)
        SELECT COALESCE(p.sale_price, p.price) INTO v_unit_price
        FROM products p
        WHERE p.id = v_product_id;

        v_total_price := v_unit_price * v_quantity;
        v_subtotal := v_subtotal + v_total_price;
    END LOOP;

    -- Calculate tax (0% in Kenya for now)
    v_tax := 0;
    v_total := v_subtotal + v_tax;

    -- Calculate change if cash payment
    IF p_payment_method = 'cash' AND p_cash_tendered IS NOT NULL THEN
        v_change_given := p_cash_tendered - v_total;
        IF v_change_given < 0 THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'Insufficient cash tendered',
                'total', v_total,
                'tendered', p_cash_tendered
            );
        END IF;
    END IF;

    -- Create transaction
    INSERT INTO pos_transactions (
        transaction_number,
        employee_id,
        store_location_id,
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
        p_employee_id,
        p_store_location_id,
        p_shift_id,
        p_customer_id,
        p_payment_method,
        v_subtotal,
        v_tax,
        v_total,
        p_cash_tendered,
        v_change_given,
        'completed',
        NOW()
    ) RETURNING id INTO v_transaction_id;

    -- Add transaction items and deduct inventory
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_variant_id := (v_item->>'variant_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;

        -- Get product_id and inventory_id
        SELECT pv.product_id, i.id INTO v_product_id, v_inventory_id
        FROM product_variants pv
        JOIN inventory i ON i.variant_id = pv.id
        WHERE pv.id = v_variant_id;

        -- Get unit price
        SELECT COALESCE(p.sale_price, p.price) INTO v_unit_price
        FROM products p
        WHERE p.id = v_product_id;

        v_total_price := v_unit_price * v_quantity;

        -- Insert transaction item
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
            v_unit_price,
            v_total_price
        );

        -- Deduct inventory using InventoryService
        PERFORM sp_deduct_inventory(
            v_variant_id,
            v_quantity,
            'pos',
            'transaction',
            v_transaction_id,
            p_employee_id,
            p_customer_id,
            'POS Sale: ' || v_transaction_number
        );
    END LOOP;

    -- Return success
    RETURN jsonb_build_object(
        'success', true,
        'transaction_id', v_transaction_id,
        'transaction_number', v_transaction_number,
        'subtotal', v_subtotal,
        'tax', v_tax,
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

-- --------------------------------------------------------------------
-- Procedure: sp_void_pos_transaction
-- Purpose: Void a POS transaction and restore inventory
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_void_pos_transaction(
    p_transaction_id INTEGER,
    p_voided_by INTEGER,
    p_void_reason TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_transaction_number VARCHAR(50);
    v_item RECORD;
    v_employee_role VARCHAR(20);
BEGIN
    -- Check if transaction exists and is not already voided
    SELECT transaction_number INTO v_transaction_number
    FROM pos_transactions
    WHERE id = p_transaction_id
      AND voided_at IS NULL;

    IF v_transaction_number IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Transaction not found or already voided'
        );
    END IF;

    -- Check if user has manager/admin role
    SELECT role INTO v_employee_role
    FROM employees
    WHERE id = p_voided_by;

    IF v_employee_role NOT IN ('manager', 'admin') THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Only managers and admins can void transactions'
        );
    END IF;

    -- Restore inventory for each item
    FOR v_item IN
        SELECT pti.inventory_id, pti.quantity, pv.id as variant_id
        FROM pos_transaction_items pti
        JOIN inventory i ON i.id = pti.inventory_id
        JOIN product_variants pv ON pv.id = i.variant_id
        WHERE pti.transaction_id = p_transaction_id
    LOOP
        -- Add inventory back using InventoryService
        PERFORM sp_add_inventory(
            v_item.variant_id,
            v_item.quantity,
            'pos',
            'return',
            p_voided_by,
            'Voided transaction: ' || v_transaction_number
        );
    END LOOP;

    -- Mark transaction as voided
    UPDATE pos_transactions
    SET voided_at = NOW(),
        voided_by = p_voided_by,
        void_reason = p_void_reason,
        status = 'voided'
    WHERE id = p_transaction_id;

    RETURN jsonb_build_object(
        'success', true,
        'transaction_id', p_transaction_id,
        'transaction_number', v_transaction_number,
        'voided_at', NOW()
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$;

-- --------------------------------------------------------------------
-- Procedure: sp_start_shift
-- Purpose: Open a new shift for an employee
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
    v_today VARCHAR(8);
    v_today_count INTEGER;
    v_open_shift INTEGER;
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

    -- Generate shift number: SHIFT-YYYYMMDD-NNNN
    v_today := TO_CHAR(NOW(), 'YYYYMMDD');

    SELECT COUNT(*) INTO v_today_count
    FROM pos_shifts
    WHERE DATE(start_time) = CURRENT_DATE;

    v_shift_number := 'SHIFT-' || v_today || '-' || LPAD((v_today_count + 1)::TEXT, 4, '0');

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

    -- Log opening float
    INSERT INTO pos_cash_movements (
        shift_id,
        movement_type,
        amount,
        reason,
        performed_by,
        created_at
    ) VALUES (
        v_shift_id,
        'starting_float',
        p_opening_float,
        'Shift opening float',
        p_employee_id,
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
-- Procedure: sp_close_shift
-- Purpose: Close a shift with cash reconciliation
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
    v_shift_number VARCHAR(50);
    v_opening_float NUMERIC(10,2);
    v_cash_sales NUMERIC(10,2);
    v_cash_in NUMERIC(10,2);
    v_cash_out NUMERIC(10,2);
    v_expected_cash NUMERIC(10,2);
    v_variance NUMERIC(10,2);
    v_status VARCHAR(20);
BEGIN
    -- Get shift details
    SELECT shift_number, opening_float, status
    INTO v_shift_number, v_opening_float, v_status
    FROM pos_shifts
    WHERE id = p_shift_id;

    IF v_shift_number IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Shift not found'
        );
    END IF;

    IF v_status = 'closed' THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Shift is already closed'
        );
    END IF;

    -- Calculate total cash sales for this shift
    SELECT COALESCE(SUM(total), 0) INTO v_cash_sales
    FROM pos_transactions
    WHERE shift_id = p_shift_id
      AND payment_method = 'cash'
      AND voided_at IS NULL;

    -- Calculate cash in movements
    SELECT COALESCE(SUM(amount), 0) INTO v_cash_in
    FROM pos_cash_movements
    WHERE shift_id = p_shift_id
      AND movement_type = 'cash_in';

    -- Calculate cash out movements
    SELECT COALESCE(SUM(amount), 0) INTO v_cash_out
    FROM pos_cash_movements
    WHERE shift_id = p_shift_id
      AND movement_type = 'cash_out';

    -- Calculate expected cash
    v_expected_cash := v_opening_float + v_cash_sales + v_cash_in - v_cash_out;

    -- Calculate variance
    v_variance := p_closing_cash - v_expected_cash;

    -- Log closing count
    INSERT INTO pos_cash_movements (
        shift_id,
        movement_type,
        amount,
        reason,
        performed_by,
        created_at
    ) VALUES (
        p_shift_id,
        'closing_count',
        p_closing_cash,
        'Shift closing count',
        (SELECT employee_id FROM pos_shifts WHERE id = p_shift_id),
        NOW()
    );

    -- Update shift
    UPDATE pos_shifts
    SET end_time = NOW(),
        closing_cash = p_closing_cash,
        expected_cash = v_expected_cash,
        variance = v_variance,
        status = 'closed',
        notes = p_notes,
        updated_at = NOW()
    WHERE id = p_shift_id;

    RETURN jsonb_build_object(
        'success', true,
        'shift_id', p_shift_id,
        'shift_number', v_shift_number,
        'opening_float', v_opening_float,
        'cash_sales', v_cash_sales,
        'cash_in', v_cash_in,
        'cash_out', v_cash_out,
        'expected_cash', v_expected_cash,
        'closing_cash', p_closing_cash,
        'variance', v_variance,
        'end_time', NOW()
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$;

-- --------------------------------------------------------------------
-- Procedure: sp_get_shift_summary
-- Purpose: Get statistics for a shift
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_get_shift_summary(
    p_shift_id INTEGER
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSONB;
    v_shift RECORD;
    v_transaction_count INTEGER;
    v_total_sales NUMERIC(10,2);
    v_cash_sales NUMERIC(10,2);
    v_mpesa_sales NUMERIC(10,2);
    v_voided_count INTEGER;
    v_voided_amount NUMERIC(10,2);
BEGIN
    -- Get shift details
    SELECT * INTO v_shift
    FROM pos_shifts
    WHERE id = p_shift_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Shift not found'
        );
    END IF;

    -- Get transaction statistics
    SELECT
        COUNT(*) FILTER (WHERE voided_at IS NULL),
        COALESCE(SUM(total) FILTER (WHERE voided_at IS NULL), 0),
        COALESCE(SUM(total) FILTER (WHERE payment_method = 'cash' AND voided_at IS NULL), 0),
        COALESCE(SUM(total) FILTER (WHERE payment_method = 'mpesa' AND voided_at IS NULL), 0),
        COUNT(*) FILTER (WHERE voided_at IS NOT NULL),
        COALESCE(SUM(total) FILTER (WHERE voided_at IS NOT NULL), 0)
    INTO
        v_transaction_count,
        v_total_sales,
        v_cash_sales,
        v_mpesa_sales,
        v_voided_count,
        v_voided_amount
    FROM pos_transactions
    WHERE shift_id = p_shift_id;

    -- Build result
    v_result := jsonb_build_object(
        'success', true,
        'shift_id', v_shift.id,
        'shift_number', v_shift.shift_number,
        'employee_id', v_shift.employee_id,
        'store_location_id', v_shift.store_location_id,
        'start_time', v_shift.start_time,
        'end_time', v_shift.end_time,
        'status', v_shift.status,
        'opening_float', v_shift.opening_float,
        'closing_cash', v_shift.closing_cash,
        'expected_cash', v_shift.expected_cash,
        'variance', v_shift.variance,
        'transaction_count', v_transaction_count,
        'total_sales', v_total_sales,
        'cash_sales', v_cash_sales,
        'mpesa_sales', v_mpesa_sales,
        'voided_count', v_voided_count,
        'voided_amount', v_voided_amount,
        'notes', v_shift.notes
    );

    RETURN v_result;

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$;

-- ====================================================================
-- 4. VIEWS
-- ====================================================================

-- View: v_pos_shift_summary
-- Purpose: User-friendly shift summary
CREATE OR REPLACE VIEW v_pos_shift_summary AS
SELECT
    ps.id AS shift_id,
    ps.shift_number,
    e.first_name || ' ' || e.last_name AS employee_name,
    e.email AS employee_email,
    sl.name AS store_name,
    ps.start_time,
    ps.end_time,
    ps.status,
    ps.opening_float,
    ps.closing_cash,
    ps.expected_cash,
    ps.variance,
    COUNT(pt.id) FILTER (WHERE pt.voided_at IS NULL) AS transaction_count,
    COALESCE(SUM(pt.total) FILTER (WHERE pt.voided_at IS NULL), 0) AS total_sales,
    COALESCE(SUM(pt.total) FILTER (WHERE pt.payment_method = 'cash' AND pt.voided_at IS NULL), 0) AS cash_sales,
    COALESCE(SUM(pt.total) FILTER (WHERE pt.payment_method = 'mpesa' AND pt.voided_at IS NULL), 0) AS mpesa_sales,
    COUNT(pt.id) FILTER (WHERE pt.voided_at IS NOT NULL) AS voided_count,
    ps.notes,
    ps.created_at
FROM pos_shifts ps
JOIN employees e ON e.id = ps.employee_id
JOIN store_locations sl ON sl.id = ps.store_location_id
LEFT JOIN pos_transactions pt ON pt.shift_id = ps.id
GROUP BY ps.id, e.first_name, e.last_name, e.email, sl.name;

-- ====================================================================
-- MIGRATION COMPLETE
-- ====================================================================

-- Verify tables exist
DO $$
BEGIN
    RAISE NOTICE 'Verifying migration 005...';

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pos_shifts') THEN
        RAISE NOTICE '✓ pos_shifts table created';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pos_cash_movements') THEN
        RAISE NOTICE '✓ pos_cash_movements table created';
    END IF;

    RAISE NOTICE 'Migration 005 complete!';
END $$;
