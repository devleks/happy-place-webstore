-- ====================================================================
-- ROLLBACK 006: RESTORE REDUNDANT COLUMNS
-- ====================================================================
-- Purpose: Rollback schema optimization if needed
-- Date: 2025-12-05
-- ====================================================================

BEGIN;

RAISE NOTICE '========================================';
RAISE NOTICE 'ROLLBACK 006: Restoring Original Schema';
RAISE NOTICE '========================================';

-- ====================================================================
-- PART 1: RESTORE pos_transactions COLUMNS
-- ====================================================================

RAISE NOTICE 'Part 1: Restoring pos_transactions columns...';

-- Add columns back
ALTER TABLE pos_transactions
    ADD COLUMN IF NOT EXISTS employee_id INTEGER,
    ADD COLUMN IF NOT EXISTS store_location_id INTEGER;

-- Populate from shifts
UPDATE pos_transactions t
SET employee_id = s.employee_id,
    store_location_id = s.store_location_id
FROM pos_shifts s
WHERE s.id = t.shift_id;

-- Make NOT NULL
ALTER TABLE pos_transactions
    ALTER COLUMN employee_id SET NOT NULL,
    ALTER COLUMN store_location_id SET NOT NULL;

-- Restore foreign keys
ALTER TABLE pos_transactions
    ADD CONSTRAINT pos_transactions_employee_id_fkey 
        FOREIGN KEY (employee_id) REFERENCES employees(id),
    ADD CONSTRAINT pos_transactions_store_location_id_fkey 
        FOREIGN KEY (store_location_id) REFERENCES store_locations(id);

RAISE NOTICE '✓ Restored employee_id and store_location_id to pos_transactions';

-- ====================================================================
-- PART 2: RESTORE pos_cash_movements COLUMNS
-- ====================================================================

RAISE NOTICE 'Part 2: Restoring pos_cash_movements columns...';

-- Add column back
ALTER TABLE pos_cash_movements
    ADD COLUMN IF NOT EXISTS performed_by INTEGER;

-- Populate from shifts
UPDATE pos_cash_movements cm
SET performed_by = s.employee_id
FROM pos_shifts s
WHERE s.id = cm.shift_id;

-- Make NOT NULL
ALTER TABLE pos_cash_movements
    ALTER COLUMN performed_by SET NOT NULL;

-- Restore foreign key
ALTER TABLE pos_cash_movements
    ADD CONSTRAINT pos_cash_movements_performed_by_fkey 
        FOREIGN KEY (performed_by) REFERENCES employees(id);

RAISE NOTICE '✓ Restored performed_by to pos_cash_movements';

-- ====================================================================
-- PART 3: DROP VIEWS
-- ====================================================================

RAISE NOTICE 'Part 3: Dropping compatibility views...';

DROP VIEW IF EXISTS v_pos_transactions_detailed;
DROP VIEW IF EXISTS v_pos_cash_movements_detailed;

RAISE NOTICE '✓ Dropped compatibility views';

-- ====================================================================
-- ROLLBACK COMPLETE
-- ====================================================================

RAISE NOTICE '========================================';
RAISE NOTICE 'ROLLBACK 006 COMPLETED SUCCESSFULLY!';
RAISE NOTICE '========================================';
RAISE NOTICE '';
RAISE NOTICE 'Schema restored to original state';

COMMIT;
