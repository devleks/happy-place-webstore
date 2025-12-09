-- ====================================================================
-- ROLLBACK SCRIPT FOR PRIORITY 3 BUSINESS PROCEDURES
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Safely rollback Priority 3 stored procedures
--
-- WARNING: Only run this if you need to revert to application-level
--          business logic processing.
-- ====================================================================

-- Drop stored procedures
DROP FUNCTION IF EXISTS sp_calculate_shipping_for_cart(INTEGER, VARCHAR(100));
DROP FUNCTION IF EXISTS sp_calculate_cart_weight(INTEGER);
DROP FUNCTION IF EXISTS sp_create_product_with_variants(VARCHAR(255), VARCHAR(255), TEXT, NUMERIC(10,2), NUMERIC(10,2), INTEGER, VARCHAR(100), NUMERIC(10,2), BOOLEAN, BOOLEAN, BOOLEAN, JSONB, INTEGER);
DROP FUNCTION IF EXISTS sp_calculate_shipping(VARCHAR(100), NUMERIC(10,2));

-- ====================================================================
-- ROLLBACK COMPLETE
-- ====================================================================
-- All Priority 3 business logic stored procedures have been removed.
-- Application will fall back to Python-based business logic.
-- ====================================================================
