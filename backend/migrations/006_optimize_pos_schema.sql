-- ====================================================================
-- MIGRATION 006: OPTIMIZE POS SCHEMA - REMOVE REDUNDANT FKs
-- ====================================================================
-- Purpose: Remove redundant foreign keys from pos_transactions and pos_cash_movements
-- Impact: Improves normalization (3NF), reduces data redundancy
-- Date: 2025-12-05
-- 
-- Changes:
-- 1. Remove employee_id and store_location_id from pos_transactions
-- 2. Remove performed_by from pos_cash_movements
-- 3. Both can be derived from pos_shifts via shift_id
-- ====================================================================

BEGIN;

-- ====================================================================
-- PART 1: OPTIMIZE pos_transactions
-- ====================================================================

-- Step 1.1: Verify data integrity
DO $$
DECLARE
    v_orphaned_count INTEGER;
    v_inconsistent_count INTEGER;
BEGIN
    -- Check for orphaned transactions (transactions without shifts)
    SELECT COUNT(*) INTO v_orphaned_count
    FROM pos_transactions 
    WHERE shift_id IS NULL;
    
    IF v_orphaned_count > 0 THEN
        RAISE EXCEPTION 'Found % transactions without shift_id. Cannot proceed.', v_orphaned_count;
    END IF;
    
    -- Check for data inconsistencies
    SELECT COUNT(*) INTO v_inconsistent_count
    FROM pos_transactions t
    JOIN pos_shifts s ON s.id = t.shift_id
    WHERE t.employee_id != s.employee_id 
       OR t.store_location_id != s.store_location_id;
    
    IF v_inconsistent_count > 0 THEN
        RAISE WARNING 'Found % inconsistent transactions. Correcting...', v_inconsistent_count;
        
        -- Fix inconsistencies by using shift data as source of truth
        UPDATE pos_transactions t
        SET employee_id = s.employee_id,
            store_location_id = s.store_location_id
        FROM pos_shifts s
        WHERE s.id = t.shift_id
          AND (t.employee_id != s.employee_id OR t.store_location_id != s.store_location_id);
          
        RAISE NOTICE 'Corrected % inconsistent records', v_inconsistent_count;
    END IF;
    
    RAISE NOTICE '✓ pos_transactions data integrity verified';
END $$;

-- Step 1.2: Make shift_id NOT NULL
ALTER TABLE pos_transactions
    ALTER COLUMN shift_id SET NOT NULL;

-- Step 1.3: Drop redundant foreign key constraints
ALTER TABLE pos_transactions
    DROP CONSTRAINT IF EXISTS pos_transactions_employee_id_fkey;

ALTER TABLE pos_transactions
    DROP CONSTRAINT IF EXISTS pos_transactions_store_location_id_fkey;

-- Step 1.4: Drop redundant columns
ALTER TABLE pos_transactions
    DROP COLUMN IF EXISTS employee_id;

ALTER TABLE pos_transactions
    DROP COLUMN IF EXISTS store_location_id;

-- ====================================================================
-- PART 2: OPTIMIZE pos_cash_movements
-- ====================================================================

-- Step 2.1: Verify data integrity
DO $$
DECLARE
    v_inconsistent_count INTEGER;
BEGIN
    -- Check for data inconsistencies
    SELECT COUNT(*) INTO v_inconsistent_count
    FROM pos_cash_movements cm
    JOIN pos_shifts s ON s.id = cm.shift_id
    WHERE cm.performed_by != s.employee_id;
    
    IF v_inconsistent_count > 0 THEN
        RAISE WARNING 'Found % inconsistent cash movements. Correcting...', v_inconsistent_count;
        
        -- Fix inconsistencies by using shift data as source of truth
        UPDATE pos_cash_movements cm
        SET performed_by = s.employee_id
        FROM pos_shifts s
        WHERE s.id = cm.shift_id
          AND cm.performed_by != s.employee_id;
          
        RAISE NOTICE 'Corrected % inconsistent records', v_inconsistent_count;
    END IF;
    
    RAISE NOTICE '✓ pos_cash_movements data integrity verified';
END $$;

-- Step 2.2: Drop redundant foreign key constraint
ALTER TABLE pos_cash_movements
    DROP CONSTRAINT IF EXISTS pos_cash_movements_performed_by_fkey;

-- Step 2.3: Drop redundant column
ALTER TABLE pos_cash_movements
    DROP COLUMN IF EXISTS performed_by;

-- ====================================================================
-- PART 3: CREATE VIEWS FOR BACKWARD COMPATIBILITY
-- ====================================================================

-- View 1: Detailed transactions view
CREATE OR REPLACE VIEW v_pos_transactions_detailed AS
SELECT 
    t.id,
    t.transaction_number,
    t.shift_id,
    s.employee_id,
    s.store_location_id,
    t.customer_id,
    t.payment_method,
    t.subtotal,
    t.tax,
    t.total,
    t.cash_tendered,
    t.change_given,
    t.status,
    t.receipt_printed,
    t.receipt_emailed,
    t.voided_at,
    t.voided_by,
    t.void_reason,
    t.promotion_id,
    t.discount_amount,
    t.discount_code,
    t.created_at,
    -- Denormalized fields from related tables
    e.full_name AS employee_name,
    e.email AS employee_email,
    e.role AS employee_role,
    COALESCE(sl.name, 'Unknown Location') AS store_name,
    sl.city AS store_city,
    s.shift_number,
    s.start_time AS shift_start_time,
    s.status AS shift_status
FROM pos_transactions t
JOIN pos_shifts s ON s.id = t.shift_id
JOIN employees e ON e.id = s.employee_id
LEFT JOIN store_locations sl ON sl.id = s.store_location_id;

COMMENT ON VIEW v_pos_transactions_detailed IS 
'Denormalized view of transactions with employee and location details derived from shifts. Use this for reporting and queries that need employee/location info.';

-- View 2: Detailed cash movements view
CREATE OR REPLACE VIEW v_pos_cash_movements_detailed AS
SELECT 
    cm.id,
    cm.shift_id,
    cm.movement_type,
    cm.amount,
    cm.reason,
    cm.created_at,
    s.employee_id AS performed_by,
    -- Denormalized fields
    e.full_name AS employee_name,
    e.email AS employee_email,
    s.shift_number,
    s.store_location_id,
    COALESCE(sl.name, 'Unknown Location') AS store_name
FROM pos_cash_movements cm
JOIN pos_shifts s ON s.id = cm.shift_id
JOIN employees e ON e.id = s.employee_id
LEFT JOIN store_locations sl ON sl.id = s.store_location_id;

COMMENT ON VIEW v_pos_cash_movements_detailed IS 
'Denormalized view of cash movements with employee details derived from shifts. Use this for reporting and audit trails.';

-- ====================================================================
-- PART 4: VERIFY MIGRATION
-- ====================================================================

DO $$
DECLARE
    v_txn_columns TEXT[];
    v_cm_columns TEXT[];
BEGIN
    -- Verify pos_transactions columns
    SELECT array_agg(column_name::TEXT) INTO v_txn_columns
    FROM information_schema.columns
    WHERE table_name = 'pos_transactions'
      AND column_name IN ('employee_id', 'store_location_id');
    
    IF v_txn_columns IS NOT NULL AND array_length(v_txn_columns, 1) > 0 THEN
        RAISE EXCEPTION 'Failed: Columns still exist in pos_transactions: %', v_txn_columns;
    END IF;
    
    -- Verify pos_cash_movements columns
    SELECT array_agg(column_name::TEXT) INTO v_cm_columns
    FROM information_schema.columns
    WHERE table_name = 'pos_cash_movements'
      AND column_name = 'performed_by';
    
    IF v_cm_columns IS NOT NULL AND array_length(v_cm_columns, 1) > 0 THEN
        RAISE EXCEPTION 'Failed: Column performed_by still exists in pos_cash_movements';
    END IF;
    
    -- Verify views exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'v_pos_transactions_detailed') THEN
        RAISE EXCEPTION 'Failed: View v_pos_transactions_detailed not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'v_pos_cash_movements_detailed') THEN
        RAISE EXCEPTION 'Failed: View v_pos_cash_movements_detailed not created';
    END IF;
    
    RAISE NOTICE '✓ All verifications passed';
END $$;

-- ====================================================================
-- MIGRATION COMPLETE
-- ====================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION 006 COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Summary of changes:';
    RAISE NOTICE '  • Removed employee_id from pos_transactions';
    RAISE NOTICE '  • Removed store_location_id from pos_transactions';
    RAISE NOTICE '  • Removed performed_by from pos_cash_movements';
    RAISE NOTICE '  • Created v_pos_transactions_detailed view';
    RAISE NOTICE '  • Created v_pos_cash_movements_detailed view';
    RAISE NOTICE '';
    RAISE NOTICE 'Benefits:';
    RAISE NOTICE '  • Improved normalization (3NF compliant)';
    RAISE NOTICE '  • Reduced data redundancy';
    RAISE NOTICE '  • Single source of truth via shift_id';
    RAISE NOTICE '  • Storage savings: ~12 bytes per transaction';
END $$;

COMMIT;
