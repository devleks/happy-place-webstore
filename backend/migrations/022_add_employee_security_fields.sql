-- Migration: Add security fields to employees table
-- Date: 2025-12-09
-- Purpose: Add failed_login_attempts, account_locked_until, login_count for auth_service

-- Add security tracking columns
ALTER TABLE employees 
ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP,
ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0 NOT NULL;

-- Add 2FA columns
ALTER TABLE employees
ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(32),
ADD COLUMN IF NOT EXISTS backup_codes TEXT;

-- Update existing employees to have default values
UPDATE employees 
SET failed_login_attempts = 0,
    login_count = 0,
    totp_enabled = FALSE
WHERE failed_login_attempts IS NULL 
   OR login_count IS NULL 
   OR totp_enabled IS NULL;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_employees_account_locked ON employees(account_locked_until) 
WHERE account_locked_until IS NOT NULL;

-- Verify changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'employees'
AND column_name IN ('failed_login_attempts', 'account_locked_until', 'login_count', 'totp_enabled', 'totp_secret', 'backup_codes')
ORDER BY column_name;
