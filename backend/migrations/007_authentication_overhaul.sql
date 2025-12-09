-- =====================================================
-- MIGRATION 007: AUTHENTICATION OVERHAUL
-- =====================================================
-- Description: Separate customer and employee authentication
--              Add Google OAuth for customers
--              Add 2FA (TOTP) for employees
--              Implement refresh tokens and token blacklist
--              Add granular permissions system
--              Add authentication audit logging
--
-- Author: Development Team
-- Date: December 3, 2025
-- Dependencies: Migration 006
-- =====================================================

BEGIN;

-- =====================================================
-- 1. REFRESH TOKENS TABLE
-- =====================================================
-- Stores refresh tokens for both customers and employees
-- Allows 30-day sessions with auto-refresh

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,

    -- User identification
    user_id INTEGER NOT NULL,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('customer', 'employee')),

    -- Token details
    token_jti VARCHAR(36) UNIQUE NOT NULL,  -- JWT ID (unique identifier)

    -- Device/session tracking
    device_name VARCHAR(100),
    ip_address VARCHAR(50),
    user_agent TEXT,

    -- Lifecycle
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE NOT NULL,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(100)
);

CREATE INDEX idx_refresh_jti ON refresh_tokens(token_jti);
CREATE INDEX idx_refresh_user ON refresh_tokens(user_id, user_type);
CREATE INDEX idx_refresh_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_revoked ON refresh_tokens(revoked);

COMMENT ON TABLE refresh_tokens IS 'Refresh tokens for maintaining long-lived sessions (30 days)';

-- =====================================================
-- 2. TOKEN BLACKLIST TABLE
-- =====================================================
-- Stores revoked access and refresh tokens
-- Enables proper logout functionality

CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,

    -- Token identification
    jti VARCHAR(36) UNIQUE NOT NULL,  -- JWT ID
    token_type VARCHAR(20) NOT NULL CHECK (token_type IN ('access', 'refresh')),

    -- Revocation details
    revoked_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP NOT NULL,  -- Original token expiration
    reason VARCHAR(100),  -- logout, logout_all, security_breach, etc.

    -- User context (for auditing)
    user_id INTEGER,
    user_type VARCHAR(20) CHECK (user_type IN ('customer', 'employee'))
);

CREATE INDEX idx_blacklist_jti ON token_blacklist(jti);
CREATE INDEX idx_blacklist_expires ON token_blacklist(expires_at);
CREATE INDEX idx_blacklist_user ON token_blacklist(user_id, user_type);

COMMENT ON TABLE token_blacklist IS 'Blacklisted JWTs that should be rejected (for logout functionality)';

-- =====================================================
-- 3. AUTH AUDIT LOG TABLE
-- =====================================================
-- Comprehensive logging of all authentication events

CREATE TABLE IF NOT EXISTS auth_audit_log (
    id SERIAL PRIMARY KEY,

    -- User identification
    user_id INTEGER,
    user_type VARCHAR(20) CHECK (user_type IN ('customer', 'employee')),
    email VARCHAR(255),

    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- login, logout, login_failed, 2fa_failed, password_reset, etc.
    auth_method VARCHAR(50),  -- password, google_oauth, 2fa, pin, etc.

    -- Result
    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_message TEXT,

    -- Context
    ip_address VARCHAR(50),
    user_agent TEXT,
    device_info JSONB,  -- Additional device details

    -- Metadata
    metadata JSONB,  -- Flexible field for additional context
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_audit_event ON auth_audit_log(event_type);
CREATE INDEX idx_audit_user ON auth_audit_log(user_id, user_type);
CREATE INDEX idx_audit_created ON auth_audit_log(created_at DESC);
CREATE INDEX idx_audit_success ON auth_audit_log(success);
CREATE INDEX idx_audit_email ON auth_audit_log(email);

COMMENT ON TABLE auth_audit_log IS 'Audit trail of all authentication events';

-- =====================================================
-- 4. PERMISSIONS TABLE
-- =====================================================
-- Granular permissions beyond basic roles

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,

    -- Permission details
    name VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'pos.create_sale', 'inventory.update'
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- pos, inventory, reports, admin, etc.

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_permission_name ON permissions(name);
CREATE INDEX idx_permission_category ON permissions(category);
CREATE INDEX idx_permission_active ON permissions(is_active);

COMMENT ON TABLE permissions IS 'Granular permissions for fine-grained access control';

-- =====================================================
-- 5. ROLE PERMISSIONS TABLE
-- =====================================================
-- Maps roles to permissions (many-to-many)

CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,

    role VARCHAR(20) NOT NULL,  -- admin, manager, cashier, staff
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,

    -- Audit
    granted_at TIMESTAMP DEFAULT NOW() NOT NULL,
    granted_by INTEGER REFERENCES employees(id),

    UNIQUE(role, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);

COMMENT ON TABLE role_permissions IS 'Maps roles to their granted permissions';

-- =====================================================
-- 6. EMPLOYEE SESSIONS TABLE
-- =====================================================
-- Track active employee sessions (for security monitoring)

CREATE TABLE IF NOT EXISTS employee_sessions (
    id SERIAL PRIMARY KEY,

    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    -- Session details
    session_token VARCHAR(255) UNIQUE NOT NULL,
    session_type VARCHAR(20) NOT NULL,  -- web, pos, mobile

    -- Device info
    ip_address VARCHAR(50),
    user_agent TEXT,
    device_name VARCHAR(100),

    -- Lifecycle
    started_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_activity_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX idx_employee_sessions_employee ON employee_sessions(employee_id);
CREATE INDEX idx_employee_sessions_token ON employee_sessions(session_token);
CREATE INDEX idx_employee_sessions_active ON employee_sessions(is_active);
CREATE INDEX idx_employee_sessions_expires ON employee_sessions(expires_at);

COMMENT ON TABLE employee_sessions IS 'Active employee sessions for monitoring and security';

-- =====================================================
-- 7. MODIFY CUSTOMERS TABLE
-- =====================================================
-- Add OAuth fields and enhanced security features

ALTER TABLE customers
    -- OAuth fields
    ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(20),  -- google, facebook, etc.
    ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS oauth_access_token TEXT,
    ADD COLUMN IF NOT EXISTS oauth_refresh_token TEXT,
    ADD COLUMN IF NOT EXISTS oauth_token_expires_at TIMESTAMP,

    -- Email verification
    ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(64),
    ADD COLUMN IF NOT EXISTS email_verification_sent_at TIMESTAMP,

    -- Password reset
    ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(64),
    ADD COLUMN IF NOT EXISTS password_reset_expires_at TIMESTAMP,

    -- Login tracking
    ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(50),
    ADD COLUMN IF NOT EXISTS last_login_user_agent TEXT;

-- Add unique constraint for OAuth
CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_oauth ON customers(oauth_provider, oauth_id)
    WHERE oauth_provider IS NOT NULL AND oauth_id IS NOT NULL;

-- Add indexes for tokens
CREATE INDEX IF NOT EXISTS idx_customers_email_verification ON customers(email_verification_token)
    WHERE email_verification_token IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_password_reset ON customers(password_reset_token)
    WHERE password_reset_token IS NOT NULL;

COMMENT ON COLUMN customers.oauth_provider IS 'OAuth provider (google, facebook)';
COMMENT ON COLUMN customers.oauth_id IS 'Unique ID from OAuth provider';

-- =====================================================
-- 8. MODIFY EMPLOYEES TABLE
-- =====================================================
-- Add 2FA, PIN, and security features for employees

ALTER TABLE employees
    -- 2FA (TOTP) fields
    ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(32),  -- Base32-encoded secret
    ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    ADD COLUMN IF NOT EXISTS totp_enabled_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS backup_codes TEXT[],  -- Array of backup codes

    -- PIN for quick POS login
    ADD COLUMN IF NOT EXISTS pin_hash VARCHAR(255),  -- 6-digit PIN (hashed)
    ADD COLUMN IF NOT EXISTS pin_enabled BOOLEAN DEFAULT FALSE NOT NULL,

    -- Account security
    ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP,
    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE NOT NULL,

    -- Login tracking
    ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(50),
    ADD COLUMN IF NOT EXISTS last_login_user_agent TEXT;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_employees_totp_enabled ON employees(totp_enabled);
CREATE INDEX IF NOT EXISTS idx_employees_pin_enabled ON employees(pin_enabled);
CREATE INDEX IF NOT EXISTS idx_employees_account_locked ON employees(account_locked_until)
    WHERE account_locked_until IS NOT NULL;

COMMENT ON COLUMN employees.totp_secret IS 'TOTP secret for Google Authenticator';
COMMENT ON COLUMN employees.totp_enabled IS 'Whether 2FA is enabled';
COMMENT ON COLUMN employees.backup_codes IS 'Emergency backup codes for 2FA';
COMMENT ON COLUMN employees.pin_hash IS 'Hashed 6-digit PIN for quick POS login';
COMMENT ON COLUMN employees.account_locked_until IS 'Account locked until this timestamp (after failed attempts)';

-- =====================================================
-- 9. SEED PERMISSIONS
-- =====================================================
-- Insert 20 predefined permissions

INSERT INTO permissions (name, display_name, description, category) VALUES
    -- POS Permissions (4)
    ('pos.create_sale', 'Create Sales', 'Process sales transactions at POS', 'pos'),
    ('pos.void_transaction', 'Void Transactions', 'Void/cancel completed transactions', 'pos'),
    ('pos.view_transactions', 'View Transactions', 'View POS transaction history', 'pos'),
    ('pos.print_receipt', 'Print Receipts', 'Print/reprint receipts', 'pos'),

    -- Shift Permissions (3)
    ('shift.open', 'Open Shift', 'Open a new shift', 'shift'),
    ('shift.close', 'Close Shift', 'Close current shift', 'shift'),
    ('shift.view_all', 'View All Shifts', 'View shifts from all employees', 'shift'),

    -- Inventory Permissions (3)
    ('inventory.view', 'View Inventory', 'View inventory levels', 'inventory'),
    ('inventory.update', 'Update Inventory', 'Update stock quantities', 'inventory'),
    ('inventory.transfer', 'Transfer Stock', 'Transfer stock between locations', 'inventory'),

    -- Customer Permissions (3)
    ('customer.view', 'View Customers', 'View customer information', 'customer'),
    ('customer.edit', 'Edit Customers', 'Edit customer information', 'customer'),
    ('customer.delete', 'Delete Customers', 'Delete/anonymize customers', 'customer'),

    -- Report Permissions (4)
    ('reports.sales', 'Sales Reports', 'View sales reports', 'reports'),
    ('reports.inventory', 'Inventory Reports', 'View inventory reports', 'reports'),
    ('reports.employee', 'Employee Reports', 'View employee performance reports', 'reports'),
    ('reports.financial', 'Financial Reports', 'View financial reports', 'reports'),

    -- Admin Permissions (3)
    ('admin.employees', 'Manage Employees', 'Add/edit/remove employees', 'admin'),
    ('admin.roles', 'Manage Roles', 'Assign roles and permissions', 'admin'),
    ('admin.settings', 'System Settings', 'Modify system settings', 'admin')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- 10. SEED ROLE PERMISSIONS
-- =====================================================
-- Assign permissions to each role

-- Admin: All permissions (20)
INSERT INTO role_permissions (role, permission_id)
SELECT 'admin', id FROM permissions
ON CONFLICT (role, permission_id) DO NOTHING;

-- Manager: All except admin.* (17 permissions)
INSERT INTO role_permissions (role, permission_id)
SELECT 'manager', id FROM permissions
WHERE category != 'admin'
ON CONFLICT (role, permission_id) DO NOTHING;

-- Cashier: POS, shift, inventory view, customer view (7 permissions)
INSERT INTO role_permissions (role, permission_id)
SELECT 'cashier', id FROM permissions
WHERE name IN (
    'pos.create_sale',
    'pos.view_transactions',
    'pos.print_receipt',
    'shift.open',
    'shift.close',
    'inventory.view',
    'customer.view'
)
ON CONFLICT (role, permission_id) DO NOTHING;

-- Staff: View only (2 permissions)
INSERT INTO role_permissions (role, permission_id)
SELECT 'staff', id FROM permissions
WHERE name IN (
    'inventory.view',
    'customer.view'
)
ON CONFLICT (role, permission_id) DO NOTHING;

-- =====================================================
-- 11. CREATE HELPER FUNCTIONS
-- =====================================================

-- Function to check if a token is blacklisted
CREATE OR REPLACE FUNCTION is_token_blacklisted(token_jti VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM token_blacklist
        WHERE jti = token_jti
        AND expires_at > NOW()
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION is_token_blacklisted IS 'Check if a JWT token is blacklisted';

-- Function to check if employee has permission
CREATE OR REPLACE FUNCTION employee_has_permission(emp_id INTEGER, perm_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    emp_role VARCHAR(20);
BEGIN
    -- Get employee role
    SELECT role INTO emp_role FROM employees WHERE id = emp_id AND is_active = TRUE;

    IF emp_role IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check if role has permission
    RETURN EXISTS (
        SELECT 1 FROM role_permissions rp
        JOIN permissions p ON rp.permission_id = p.id
        WHERE rp.role = emp_role
        AND p.name = perm_name
        AND p.is_active = TRUE
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION employee_has_permission IS 'Check if employee has a specific permission';

-- Function to clean up expired tokens (for cron job)
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired tokens from blacklist (keep for 30 days after expiration)
    DELETE FROM token_blacklist
    WHERE expires_at < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Mark expired refresh tokens as revoked
    UPDATE refresh_tokens
    SET revoked = TRUE,
        revoked_at = NOW(),
        revoked_reason = 'expired'
    WHERE expires_at < NOW()
    AND revoked = FALSE;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_tokens IS 'Clean up expired tokens (run daily via cron)';

-- Function to log authentication event
CREATE OR REPLACE FUNCTION log_auth_event(
    p_user_id INTEGER,
    p_user_type VARCHAR,
    p_email VARCHAR,
    p_event_type VARCHAR,
    p_auth_method VARCHAR,
    p_success BOOLEAN,
    p_error_message TEXT,
    p_ip_address VARCHAR,
    p_user_agent TEXT,
    p_metadata JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO auth_audit_log (
        user_id, user_type, email, event_type, auth_method,
        success, error_message, ip_address, user_agent, metadata
    ) VALUES (
        p_user_id, p_user_type, p_email, p_event_type, p_auth_method,
        p_success, p_error_message, p_ip_address, p_user_agent, p_metadata
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_auth_event IS 'Log an authentication event to audit log';

-- =====================================================
-- 12. CREATE TRIGGERS
-- =====================================================

-- Trigger to update last_activity_at on employee_sessions
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_session_activity
    BEFORE UPDATE ON employee_sessions
    FOR EACH ROW
    WHEN (OLD.last_activity_at IS DISTINCT FROM NEW.last_activity_at)
    EXECUTE FUNCTION update_session_activity();

-- =====================================================
-- 13. GRANT PERMISSIONS
-- =====================================================

-- Grant permissions to application user (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'happy_place_app') THEN
        GRANT ALL ON refresh_tokens TO happy_place_app;
        GRANT ALL ON token_blacklist TO happy_place_app;
        GRANT ALL ON auth_audit_log TO happy_place_app;
        GRANT ALL ON permissions TO happy_place_app;
        GRANT ALL ON role_permissions TO happy_place_app;
        GRANT ALL ON employee_sessions TO happy_place_app;

        GRANT ALL ON SEQUENCE refresh_tokens_id_seq TO happy_place_app;
        GRANT ALL ON SEQUENCE token_blacklist_id_seq TO happy_place_app;
        GRANT ALL ON SEQUENCE auth_audit_log_id_seq TO happy_place_app;
        GRANT ALL ON SEQUENCE permissions_id_seq TO happy_place_app;
        GRANT ALL ON SEQUENCE role_permissions_id_seq TO happy_place_app;
        GRANT ALL ON SEQUENCE employee_sessions_id_seq TO happy_place_app;
    END IF;
END $$;

-- =====================================================
-- 14. VERIFICATION QUERIES
-- =====================================================

-- Verify all tables created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'refresh_tokens',
        'token_blacklist',
        'auth_audit_log',
        'permissions',
        'role_permissions',
        'employee_sessions'
    );

    IF table_count != 6 THEN
        RAISE EXCEPTION 'Not all tables were created. Expected 6, found %', table_count;
    END IF;

    RAISE NOTICE 'All 6 new tables created successfully';
END $$;

-- Verify columns added to existing tables
DO $$
DECLARE
    customer_columns INTEGER;
    employee_columns INTEGER;
BEGIN
    SELECT COUNT(*) INTO customer_columns
    FROM information_schema.columns
    WHERE table_name = 'customers'
    AND column_name IN (
        'oauth_provider', 'oauth_id', 'email_verification_token',
        'password_reset_token', 'login_count'
    );

    SELECT COUNT(*) INTO employee_columns
    FROM information_schema.columns
    WHERE table_name = 'employees'
    AND column_name IN (
        'totp_secret', 'totp_enabled', 'pin_hash', 'pin_enabled',
        'failed_login_attempts', 'account_locked_until'
    );

    IF customer_columns < 5 THEN
        RAISE EXCEPTION 'Not all columns added to customers table. Expected 5+, found %', customer_columns;
    END IF;

    IF employee_columns < 6 THEN
        RAISE EXCEPTION 'Not all columns added to employees table. Expected 6+, found %', employee_columns;
    END IF;

    RAISE NOTICE 'All columns added to customers and employees tables successfully';
END $$;

-- Verify permissions seeded
DO $$
DECLARE
    permission_count INTEGER;
    role_permission_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO permission_count FROM permissions;
    SELECT COUNT(*) INTO role_permission_count FROM role_permissions;

    IF permission_count < 20 THEN
        RAISE EXCEPTION 'Not all permissions seeded. Expected 20, found %', permission_count;
    END IF;

    IF role_permission_count < 46 THEN
        RAISE WARNING 'Expected ~46 role_permissions, found %', role_permission_count;
    END IF;

    RAISE NOTICE 'Permissions seeded: % permissions, % role_permissions', permission_count, role_permission_count;
END $$;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

COMMIT;

-- Print summary
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION 007: AUTHENTICATION OVERHAUL';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'New Tables: 6';
    RAISE NOTICE '  - refresh_tokens';
    RAISE NOTICE '  - token_blacklist';
    RAISE NOTICE '  - auth_audit_log';
    RAISE NOTICE '  - permissions';
    RAISE NOTICE '  - role_permissions';
    RAISE NOTICE '  - employee_sessions';
    RAISE NOTICE '';
    RAISE NOTICE 'Modified Tables: 2';
    RAISE NOTICE '  - customers (added OAuth & security fields)';
    RAISE NOTICE '  - employees (added 2FA & security fields)';
    RAISE NOTICE '';
    RAISE NOTICE 'Permissions: 20 seeded';
    RAISE NOTICE 'Role Permissions: ~46 seeded';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions: 4 created';
    RAISE NOTICE 'Triggers: 1 created';
    RAISE NOTICE '';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '========================================';
END $$;
