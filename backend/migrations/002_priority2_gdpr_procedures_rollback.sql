-- ====================================================================
-- ROLLBACK SCRIPT FOR PRIORITY 2 GDPR PROCEDURES
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Safely rollback Priority 2 GDPR stored procedures
--
-- WARNING: Only run this if you need to revert to application-level
--          GDPR processing.
-- ====================================================================

-- Drop stored procedures
DROP FUNCTION IF EXISTS sp_gdpr_check_request_status(INTEGER, VARCHAR(20));
DROP FUNCTION IF EXISTS sp_gdpr_delete_customer(INTEGER, INTEGER, TEXT, VARCHAR(10));
DROP FUNCTION IF EXISTS sp_gdpr_anonymize_customer(INTEGER, INTEGER, TEXT);
DROP FUNCTION IF EXISTS sp_gdpr_export_customer_data(INTEGER, INTEGER, TEXT);

-- ====================================================================
-- ROLLBACK COMPLETE
-- ====================================================================
-- All Priority 2 GDPR stored procedures have been removed.
-- Application will fall back to ORM-based GDPR processing.
-- ====================================================================
