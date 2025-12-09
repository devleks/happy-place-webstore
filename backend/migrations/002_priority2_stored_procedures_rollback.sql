-- ====================================================================
-- ROLLBACK SCRIPT FOR PRIORITY 2 STORED PROCEDURES
-- ====================================================================
-- Created: 2025-12-04
-- Purpose: Safely rollback Priority 2 stored procedures migration
--          and restore application-layer processing
--
-- This script removes:
-- 1. Customer Registration stored procedure
-- 2. Customer Anonymization stored procedure
-- 3. Associated indexes and permissions
-- ====================================================================

-- ====================================================================
-- REMOVE STORED PROCEDURES
-- ====================================================================

-- Drop customer registration stored procedure
DROP FUNCTION IF EXISTS sp_register_customer_secure(
    p_email_hash VARCHAR(64),
    p_email_encrypted TEXT,
    p_password_hash VARCHAR(255),
    p_first_name_encrypted TEXT,
    p_last_name_encrypted TEXT,
    p_phone_encrypted TEXT,
    p_gdpr_consent BOOLEAN,
    p_marketing_consent BOOLEAN,
    p_ip_address VARCHAR(45),
    p_user_agent TEXT
);

-- Note: Customer anonymization uses existing sp_gdpr_anonymize_customer() 
-- from 002_priority2_gdpr_procedures.sql - no rollback needed here

-- ====================================================================
-- REMOVE INDEXES
-- ====================================================================

-- Remove performance indexes created for P2 procedures
DROP INDEX IF EXISTS idx_customers_email_hash_active;
DROP INDEX IF EXISTS idx_customers_anonymized;

-- ====================================================================
-- RESTORE APPLICATION LAYER
-- ====================================================================

-- Note: Application layer functions in routes/auth.py and models/database_models.py
-- should be restored from version control to their original implementations
-- that use direct ORM operations instead of stored procedure calls.

-- ====================================================================
-- VERIFICATION
-- ====================================================================

-- Verify procedures are removed
SELECT routine_name, routine_type 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name LIKE 'sp_%_secure' 
AND routine_name LIKE '%customer%';

-- Expected: No rows returned for P2 customer procedures

-- ====================================================================
-- ROLLBACK COMPLETE
-- ====================================================================

-- All Priority 2 stored procedures have been removed.
-- Application should be restarted to use restored ORM functions.
-- Verify customer registration and anonymization work correctly
-- through the application layer after rollback.
