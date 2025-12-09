-- ====================================================================
-- PRIORITY 2 GDPR COMPLIANCE STORED PROCEDURES
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Implement GDPR compliance at database level
--
-- This migration implements 3 Priority 2 GDPR operations:
-- 1. Data Export (GDPR Right to Access - Article 15)
-- 2. Data Anonymization (GDPR Right to be Forgotten - Article 17)
-- 3. Data Deletion (Complete removal for closed accounts)
-- ====================================================================

-- ====================================================================
-- 1. CUSTOMER DATA EXPORT (GDPR Right to Access)
-- ====================================================================
-- Purpose: Export all personal data for a customer in machine-readable format
-- GDPR Article 15: Right of access by the data subject
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_gdpr_export_customer_data(
    p_customer_id INTEGER,
    p_requested_by INTEGER DEFAULT NULL,  -- Employee ID or NULL for self-service
    p_reason TEXT DEFAULT 'customer_request'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_customer_data JSONB;
    v_addresses JSONB;
    v_orders JSONB;
    v_consent_log JSONB;
    v_result JSONB;
BEGIN
    -- 1. Validate customer exists
    IF NOT EXISTS (SELECT 1 FROM customers WHERE id = p_customer_id) THEN
        RAISE EXCEPTION 'Customer not found: %', p_customer_id;
    END IF;

    -- 2. Export customer personal data
    SELECT jsonb_build_object(
        'customer_id', id,
        'email', email_encrypted,
        'first_name', first_name_encrypted,
        'last_name', last_name_encrypted,
        'phone', phone_encrypted,
        'gdpr_consent', gdpr_consent,
        'marketing_consent', marketing_consent,
        'email_verified', email_verified,
        'is_active', is_active,
        'anonymized', anonymized,
        'anonymized_at', anonymized_at,
        'created_at', created_at,
        'updated_at', updated_at,
        'last_login', last_login
    )
    INTO v_customer_data
    FROM customers
    WHERE id = p_customer_id;

    -- 3. Export addresses
    SELECT COALESCE(jsonb_agg(jsonb_build_object(
        'address_id', id,
        'address_type', address_type,
        'street_encrypted', street_encrypted,
        'city', city,
        'state', state,
        'zip_code', zip_code,
        'country', country,
        'is_default', is_default,
        'created_at', created_at
    )), '[]'::jsonb)
    INTO v_addresses
    FROM customer_addresses
    WHERE customer_id = p_customer_id;

    -- 4. Export order history (summary only, not full details)
    SELECT COALESCE(jsonb_agg(jsonb_build_object(
        'order_id', id,
        'order_number', order_number,
        'status', status,
        'subtotal', subtotal,
        'tax', tax,
        'shipping_cost', shipping_cost,
        'total', total,
        'created_at', created_at,
        'shipped_at', shipped_at,
        'delivered_at', delivered_at
    )), '[]'::jsonb)
    INTO v_orders
    FROM orders
    WHERE customer_id = p_customer_id;

    -- 5. Export GDPR consent history
    SELECT COALESCE(jsonb_agg(jsonb_build_object(
        'consent_id', id,
        'consent_type', consent_type,
        'consent_given', consent_given,
        'ip_address', ip_address,
        'consented_at', consented_at
    )), '[]'::jsonb)
    INTO v_consent_log
    FROM gdpr_consent_log
    WHERE customer_id = p_customer_id;

    -- 6. Build complete export
    v_result := jsonb_build_object(
        'export_date', NOW(),
        'customer', v_customer_data,
        'addresses', v_addresses,
        'orders', v_orders,
        'consent_history', v_consent_log,
        'notes', 'Encrypted fields require decryption key for viewing'
    );

    -- 7. Log GDPR data export request
    INSERT INTO gdpr_data_requests (
        customer_id,
        request_type,
        status,
        requested_at,
        processed_at,
        notes
    ) VALUES (
        p_customer_id,
        'export',
        'completed',
        NOW(),
        NOW(),
        p_reason
    );

    -- 8. Log data access (if requested by employee)
    IF p_requested_by IS NOT NULL THEN
        INSERT INTO data_access_log (
            employee_id,
            customer_id,
            accessed_table,
            accessed_record_id,
            action,
            reason,
            timestamp
        ) VALUES (
            p_requested_by,
            p_customer_id,
            'customers',
            p_customer_id,
            'gdpr_export',
            p_reason,
            NOW()
        );
    END IF;

    RETURN v_result;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_gdpr_export_customer_data TO postgres;

-- ====================================================================
-- 2. CUSTOMER ANONYMIZATION (GDPR Right to be Forgotten)
-- ====================================================================
-- Purpose: Anonymize customer data while preserving order history
-- GDPR Article 17: Right to erasure ('right to be forgotten')
-- Business Rule: Keep order records for accounting, anonymize PII
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_gdpr_anonymize_customer(
    p_customer_id INTEGER,
    p_requested_by INTEGER DEFAULT NULL,  -- Employee ID or NULL for self-service
    p_reason TEXT DEFAULT 'customer_request'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_outstanding_orders INTEGER;
    v_addresses_deleted INTEGER;
    v_cart_items_deleted INTEGER;
    v_wishlist_items_deleted INTEGER;
    v_result JSONB;
BEGIN
    -- 1. Validate customer exists and not already anonymized
    IF NOT EXISTS (SELECT 1 FROM customers WHERE id = p_customer_id AND anonymized = FALSE) THEN
        RAISE EXCEPTION 'Customer not found or already anonymized: %', p_customer_id;
    END IF;

    -- 2. Business Rule: Check for outstanding orders
    SELECT COUNT(*) INTO v_outstanding_orders
    FROM orders
    WHERE customer_id = p_customer_id
      AND status IN ('pending', 'processing', 'shipped');

    IF v_outstanding_orders > 0 THEN
        RAISE EXCEPTION 'Cannot anonymize customer with % outstanding orders. Complete or cancel orders first.', v_outstanding_orders;
    END IF;

    -- 3. Anonymize customer personal data (ATOMIC)
    UPDATE customers
    SET email_hash = encode(digest('anonymized_' || id || '@deleted.local', 'sha256'), 'hex'),
        email_encrypted = 'anonymized_' || id || '@deleted.local',
        first_name_encrypted = 'ANONYMIZED',
        last_name_encrypted = 'ANONYMIZED',
        phone_encrypted = NULL,
        marketing_consent = FALSE,
        anonymized = TRUE,
        anonymized_at = NOW(),
        is_active = FALSE,
        updated_at = NOW()
    WHERE id = p_customer_id;

    -- 4. Delete customer addresses (PII)
    DELETE FROM customer_addresses WHERE customer_id = p_customer_id;
    GET DIAGNOSTICS v_addresses_deleted = ROW_COUNT;

    -- 5. Clear shopping cart
    DELETE FROM cart_items WHERE cart_id IN (
        SELECT id FROM carts WHERE customer_id = p_customer_id
    );
    GET DIAGNOSTICS v_cart_items_deleted = ROW_COUNT;

    DELETE FROM carts WHERE customer_id = p_customer_id;

    -- 6. Clear wishlist
    DELETE FROM wishlist_items WHERE wishlist_id IN (
        SELECT id FROM wishlists WHERE customer_id = p_customer_id
    );
    GET DIAGNOSTICS v_wishlist_items_deleted = ROW_COUNT;

    DELETE FROM wishlists WHERE customer_id = p_customer_id;

    -- 7. Anonymize order shipping addresses (keep for records, but anonymize PII)
    UPDATE orders
    SET shipping_address_encrypted = 'ANONYMIZED - Customer requested data deletion',
        billing_address_encrypted = 'ANONYMIZED - Customer requested data deletion',
        updated_at = NOW()
    WHERE customer_id = p_customer_id;

    -- 8. Log GDPR anonymization request
    INSERT INTO gdpr_data_requests (
        customer_id,
        request_type,
        status,
        requested_at,
        processed_at,
        notes
    ) VALUES (
        p_customer_id,
        'anonymization',
        'completed',
        NOW(),
        NOW(),
        p_reason
    );

    -- 9. Log data access (if requested by employee)
    IF p_requested_by IS NOT NULL THEN
        INSERT INTO data_access_log (
            employee_id,
            customer_id,
            accessed_table,
            accessed_record_id,
            action,
            reason,
            timestamp
        ) VALUES (
            p_requested_by,
            p_customer_id,
            'customers',
            p_customer_id,
            'gdpr_anonymize',
            p_reason,
            NOW()
        );
    END IF;

    -- 10. Build result
    v_result := jsonb_build_object(
        'success', TRUE,
        'customer_id', p_customer_id,
        'anonymized_at', NOW(),
        'addresses_deleted', v_addresses_deleted,
        'cart_items_cleared', v_cart_items_deleted,
        'wishlist_items_cleared', v_wishlist_items_deleted,
        'orders_anonymized', (SELECT COUNT(*) FROM orders WHERE customer_id = p_customer_id),
        'message', 'Customer data anonymized. Order history preserved for accounting.'
    );

    RETURN v_result;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_gdpr_anonymize_customer TO postgres;

-- ====================================================================
-- 3. CUSTOMER DATA DELETION (Complete Removal)
-- ====================================================================
-- Purpose: Completely delete customer and all related data
-- Use Case: For test accounts, closed accounts with no order history
-- WARNING: This is irreversible and deletes all data including orders
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_gdpr_delete_customer(
    p_customer_id INTEGER,
    p_requested_by INTEGER,  -- Employee ID REQUIRED for deletion
    p_reason TEXT,
    p_confirmation_code VARCHAR(10)  -- Safety mechanism
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_email TEXT;
    v_orders_count INTEGER;
    v_result JSONB;
BEGIN
    -- 1. Validate employee has permission (deletion requires authorization)
    IF NOT EXISTS (
        SELECT 1 FROM employees
        WHERE id = p_requested_by
          AND is_active = TRUE
          AND role IN ('admin', 'super_admin')
    ) THEN
        RAISE EXCEPTION 'Insufficient permissions. Only admins can delete customer data.';
    END IF;

    -- 2. Validate customer exists
    SELECT email_encrypted, (SELECT COUNT(*) FROM orders WHERE customer_id = p_customer_id)
    INTO v_email, v_orders_count
    FROM customers
    WHERE id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer not found: %', p_customer_id;
    END IF;

    -- 3. Safety check: Require confirmation code
    IF p_confirmation_code != 'DELETE' THEN
        RAISE EXCEPTION 'Invalid confirmation code. Must be "DELETE" to proceed.';
    END IF;

    -- 4. Business Rule: Warn if customer has order history
    IF v_orders_count > 0 THEN
        RAISE NOTICE 'WARNING: Deleting customer with % orders. Consider anonymization instead.', v_orders_count;
    END IF;

    -- 5. Delete in cascade order (foreign keys will handle most)
    -- Log GDPR deletion request FIRST (before deletion)
    INSERT INTO gdpr_data_requests (
        customer_id,
        request_type,
        status,
        requested_at,
        processed_at,
        notes
    ) VALUES (
        p_customer_id,
        'deletion',
        'completed',
        NOW(),
        NOW(),
        p_reason
    );

    -- Log data access
    INSERT INTO data_access_log (
        employee_id,
        customer_id,
        accessed_table,
        accessed_record_id,
        action,
        reason,
        timestamp
    ) VALUES (
        p_requested_by,
        p_customer_id,
        'customers',
        p_customer_id,
        'gdpr_delete',
        p_reason,
        NOW()
    );

    -- Delete customer (CASCADE will handle related records)
    DELETE FROM customers WHERE id = p_customer_id;

    -- 6. Build result
    v_result := jsonb_build_object(
        'success', TRUE,
        'customer_id', p_customer_id,
        'deleted_at', NOW(),
        'email', v_email,
        'orders_deleted', v_orders_count,
        'message', 'Customer and all related data permanently deleted.'
    );

    RETURN v_result;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_gdpr_delete_customer TO postgres;

-- ====================================================================
-- HELPER: Check GDPR Data Request Status
-- ====================================================================
-- Purpose: Check if customer has pending/recent GDPR requests
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_gdpr_check_request_status(
    p_customer_id INTEGER,
    p_request_type VARCHAR(20) DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_pending_requests INTEGER;
    v_recent_requests JSONB;
    v_result JSONB;
BEGIN
    -- Count pending requests
    SELECT COUNT(*) INTO v_pending_requests
    FROM gdpr_data_requests
    WHERE customer_id = p_customer_id
      AND status = 'pending'
      AND (p_request_type IS NULL OR request_type = p_request_type);

    -- Get recent requests (last 30 days)
    SELECT COALESCE(jsonb_agg(jsonb_build_object(
        'request_id', id,
        'request_type', request_type,
        'status', status,
        'requested_at', requested_at,
        'processed_at', processed_at,
        'notes', notes
    )), '[]'::jsonb)
    INTO v_recent_requests
    FROM gdpr_data_requests
    WHERE customer_id = p_customer_id
      AND requested_at > NOW() - INTERVAL '30 days'
      AND (p_request_type IS NULL OR request_type = p_request_type)
    ORDER BY requested_at DESC
    LIMIT 10;

    v_result := jsonb_build_object(
        'customer_id', p_customer_id,
        'pending_requests', v_pending_requests,
        'recent_requests', v_recent_requests,
        'checked_at', NOW()
    );

    RETURN v_result;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_gdpr_check_request_status TO postgres;

-- ====================================================================
-- MIGRATION COMPLETE
-- ====================================================================
-- All Priority 2 GDPR stored procedures have been created.
--
-- Next steps:
-- 1. Create gdpr_service.py to call these procedures
-- 2. Add GDPR endpoints to API
-- 3. Test with comprehensive test suite
--
-- Rollback: See 002_priority2_gdpr_procedures_rollback.sql
-- ====================================================================
