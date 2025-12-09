-- ====================================================================
-- ROLLBACK SCRIPT FOR PRIORITY 1 STORED PROCEDURES
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Safely rollback Priority 1 stored procedures migration
--
-- WARNING: Only run this if you need to revert to application-level
--          order processing. Ensure all in-flight transactions using
--          these procedures have completed before rolling back.
-- ====================================================================

-- Drop stored procedures in reverse order of dependencies
DROP FUNCTION IF EXISTS sp_validate_promotion_secure(VARCHAR(50), INTEGER, NUMERIC(10,2), INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_process_return_secure(INTEGER, INTEGER, VARCHAR(100), TEXT, JSONB, INTEGER);
DROP FUNCTION IF EXISTS sp_process_payment_secure(INTEGER, TEXT, TEXT);
DROP FUNCTION IF EXISTS sp_release_inventory_atomic(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_reserve_inventory_atomic(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_create_order_secure(INTEGER, TEXT, TEXT, VARCHAR(20), JSONB, INTEGER, BOOLEAN, NUMERIC(10,2));

-- ====================================================================
-- ROLLBACK COMPLETE
-- ====================================================================
-- All Priority 1 stored procedures have been removed.
-- Application will fall back to ORM-based order processing.
-- ====================================================================
