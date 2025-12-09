-- ====================================================================
-- ROLLBACK SCRIPT FOR MIGRATION 005: POS SYSTEM ENHANCEMENTS
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Safely rollback POS enhancements migration
-- ====================================================================

-- Drop views
DROP VIEW IF EXISTS v_pos_shift_summary;

-- Drop stored procedures
DROP FUNCTION IF EXISTS sp_get_shift_summary(INTEGER);
DROP FUNCTION IF EXISTS sp_close_shift(INTEGER, NUMERIC, TEXT);
DROP FUNCTION IF EXISTS sp_start_shift(INTEGER, INTEGER, NUMERIC);
DROP FUNCTION IF EXISTS sp_void_pos_transaction(INTEGER, INTEGER, TEXT);
DROP FUNCTION IF EXISTS sp_create_pos_transaction(INTEGER, INTEGER, INTEGER, VARCHAR, JSONB, INTEGER, NUMERIC);

-- Remove columns from pos_transactions
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS void_reason;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS voided_by;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS voided_at;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS receipt_emailed;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS receipt_printed;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS customer_id;
ALTER TABLE pos_transactions DROP COLUMN IF EXISTS shift_id;

-- Drop tables (CASCADE to remove foreign keys)
DROP TABLE IF EXISTS pos_cash_movements CASCADE;
DROP TABLE IF EXISTS pos_shifts CASCADE;

-- ====================================================================
-- ROLLBACK COMPLETE
-- ====================================================================

DO $$
BEGIN
    RAISE NOTICE 'Rollback of migration 005 complete';
    RAISE NOTICE 'POS enhancements have been removed';
END $$;
