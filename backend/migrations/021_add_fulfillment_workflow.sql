-- ============================================================================
-- Migration 021: Add Fulfillment Workflow
-- Phase 1, Task 1.2.1 - Fulfillment Database
-- ============================================================================
-- Description: Add fulfillment roles and order assignment tracking
-- Author: Phase 1 Implementation
-- Date: 2025-12-09
-- ============================================================================

-- Add new fulfillment roles to employees table
-- Note: The role column already exists, we're just documenting the new values
COMMENT ON COLUMN employees.role IS 'Employee role: admin, manager, cashier, packer, shipper, customer_service';

-- Create order_assignments table for tracking fulfillment workflow
CREATE TABLE IF NOT EXISTS order_assignments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    assigned_by INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('packer', 'shipper')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    assigned_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(order_id, role)
);

-- Create indexes for performance
CREATE INDEX idx_order_assignments_order_id ON order_assignments(order_id);
CREATE INDEX idx_order_assignments_assigned_to ON order_assignments(assigned_to);
CREATE INDEX idx_order_assignments_status ON order_assignments(status);
CREATE INDEX idx_order_assignments_role ON order_assignments(role);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_order_assignments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_assignments_updated_at
    BEFORE UPDATE ON order_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_order_assignments_updated_at();

-- Insert sample packer and shipper employees for testing
-- Check if they don't already exist
DO $$
BEGIN
    -- Add packer if not exists
    IF NOT EXISTS (SELECT 1 FROM employees WHERE email = 'packer@happyplace.co.ke') THEN
        INSERT INTO employees (
            email, 
            password_hash, 
            full_name, 
            role, 
            phone, 
            is_active,
            created_at
        ) VALUES (
            'packer@happyplace.co.ke',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qL0Yw.Kiq', -- Password: Packer@123
            'John Packer',
            'packer',
            '+254712345678',
            true,
            NOW()
        );
    END IF;

    -- Add shipper if not exists
    IF NOT EXISTS (SELECT 1 FROM employees WHERE email = 'shipper@happyplace.co.ke') THEN
        INSERT INTO employees (
            email, 
            password_hash, 
            full_name, 
            role, 
            phone, 
            is_active,
            created_at
        ) VALUES (
            'shipper@happyplace.co.ke',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qL0Yw.Kiq', -- Password: Shipper@123
            'Jane Shipper',
            'shipper',
            '+254712345679',
            true,
            NOW()
        );
    END IF;
END $$;

-- Verification queries (commented out - run manually if needed)
-- SELECT * FROM order_assignments;
-- SELECT id, email, full_name, role FROM employees WHERE role IN ('packer', 'shipper');
-- SELECT COUNT(*) as assignment_count FROM order_assignments;

COMMENT ON TABLE order_assignments IS 'Tracks order assignments to fulfillment staff (packers and shippers)';
COMMENT ON COLUMN order_assignments.order_id IS 'Reference to the order being fulfilled';
COMMENT ON COLUMN order_assignments.assigned_to IS 'Employee assigned to this fulfillment task';
COMMENT ON COLUMN order_assignments.assigned_by IS 'Manager/admin who made the assignment';
COMMENT ON COLUMN order_assignments.role IS 'Fulfillment role: packer or shipper';
COMMENT ON COLUMN order_assignments.status IS 'Assignment status: pending, in_progress, completed, cancelled';
COMMENT ON COLUMN order_assignments.started_at IS 'When the employee started working on this task';
COMMENT ON COLUMN order_assignments.completed_at IS 'When the task was completed';
