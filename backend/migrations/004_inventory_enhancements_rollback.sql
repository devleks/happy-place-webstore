-- ====================================================================
-- ROLLBACK SCRIPT FOR INVENTORY ENHANCEMENTS
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Safely rollback Phase 1 inventory enhancements
--
-- WARNING: This will remove inventory movement tracking and reservations.
--          Movement history will be lost!
-- ====================================================================

-- Drop views
DROP VIEW IF EXISTS v_inventory_movements_summary;
DROP VIEW IF EXISTS v_inventory_summary;

-- Drop stored procedures
DROP FUNCTION IF EXISTS sp_cleanup_expired_reservations();
DROP FUNCTION IF EXISTS sp_add_inventory(INTEGER, INTEGER, VARCHAR(20), VARCHAR(20), INTEGER, TEXT);
DROP FUNCTION IF EXISTS sp_deduct_inventory(INTEGER, INTEGER, VARCHAR(20), VARCHAR(30), INTEGER, INTEGER, INTEGER, TEXT);
DROP FUNCTION IF EXISTS sp_log_inventory_movement(INTEGER, VARCHAR(20), VARCHAR(20), INTEGER, VARCHAR(30), INTEGER, INTEGER, INTEGER, VARCHAR(100), VARCHAR(100), TEXT);
DROP FUNCTION IF EXISTS sp_get_available_inventory(INTEGER, VARCHAR(20));

-- Drop tables (CASCADE will handle foreign keys)
DROP TABLE IF EXISTS inventory_reservations CASCADE;
DROP TABLE IF EXISTS inventory_movements CASCADE;

-- Remove columns from inventory table
ALTER TABLE inventory DROP COLUMN IF EXISTS primary_location;
ALTER TABLE inventory DROP COLUMN IF EXISTS store_display_units;

-- ====================================================================
-- ROLLBACK COMPLETE
-- ====================================================================
-- All Phase 1 inventory enhancements have been removed.
-- System reverted to basic unified inventory model.
-- ====================================================================
