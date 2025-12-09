-- ============================================================================
-- MIGRATION: 020_add_order_tracking.sql
-- Description: Add order tracking functionality
-- Author: Happy Place Development Team
-- Date: 2025-12-09
-- Phase: Phase 1 - Critical Fixes
-- Task: 1.1.1 - Database Schema Updates
-- ============================================================================

-- Add tracking fields to orders table
-- These fields store tracking information for shipped orders
ALTER TABLE orders 
ADD COLUMN tracking_number VARCHAR(100),
ADD COLUMN carrier VARCHAR(50),
ADD COLUMN tracking_url TEXT,
ADD COLUMN estimated_delivery_date DATE,
ADD COLUMN shipping_notes TEXT;

-- Add comments for documentation
COMMENT ON COLUMN orders.tracking_number IS 'Carrier tracking number (e.g., DHL123456789)';
COMMENT ON COLUMN orders.carrier IS 'Shipping carrier name (e.g., DHL Express)';
COMMENT ON COLUMN orders.tracking_url IS 'Full URL to track shipment on carrier website';
COMMENT ON COLUMN orders.estimated_delivery_date IS 'Expected delivery date';
COMMENT ON COLUMN orders.shipping_notes IS 'Additional shipping notes or instructions';

-- ============================================================================
-- Create shipment_updates table for tracking history
-- Stores timeline of shipment status updates
-- ============================================================================
CREATE TABLE shipment_updates (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    location VARCHAR(200),
    description TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_by INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_shipment_updates_order_id ON shipment_updates(order_id);
CREATE INDEX idx_shipment_updates_timestamp ON shipment_updates(timestamp);

-- Add comments
COMMENT ON TABLE shipment_updates IS 'Timeline of shipment status updates for order tracking';
COMMENT ON COLUMN shipment_updates.order_id IS 'Reference to the order being tracked';
COMMENT ON COLUMN shipment_updates.status IS 'Shipment status (e.g., shipped, in_transit, delivered)';
COMMENT ON COLUMN shipment_updates.location IS 'Current location of shipment';
COMMENT ON COLUMN shipment_updates.description IS 'Detailed description of status update';
COMMENT ON COLUMN shipment_updates.timestamp IS 'When this status update occurred';
COMMENT ON COLUMN shipment_updates.created_by IS 'Employee who created this update';

-- ============================================================================
-- Create shipping_carriers table
-- Stores configuration for supported shipping carriers
-- ============================================================================
CREATE TABLE shipping_carriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    tracking_url_template TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE shipping_carriers IS 'Configuration for supported shipping carriers';
COMMENT ON COLUMN shipping_carriers.name IS 'Carrier name (e.g., DHL Express)';
COMMENT ON COLUMN shipping_carriers.tracking_url_template IS 'URL template with {tracking_number} placeholder';
COMMENT ON COLUMN shipping_carriers.is_active IS 'Whether this carrier is currently available for selection';

-- ============================================================================
-- Insert Kenyan shipping carriers
-- These are the major carriers operating in Kenya
-- ============================================================================
INSERT INTO shipping_carriers (name, tracking_url_template) VALUES
('DHL Express', 'https://www.dhl.com/ke-en/home/tracking.html?tracking-id={tracking_number}'),
('Posta Kenya', 'https://www.posta.co.ke/track?number={tracking_number}'),
('G4S Courier', 'https://www.g4s.co.ke/track/{tracking_number}'),
('Sendy', 'https://sendy.co.ke/track/{tracking_number}'),
('Uber Direct', 'https://www.uber.com/ke/en/delivery/track/{tracking_number}');

-- ============================================================================
-- Verification queries (run these to verify migration)
-- ============================================================================

-- Verify orders table was altered
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'orders' AND column_name IN ('tracking_number', 'carrier', 'tracking_url');

-- Verify shipment_updates table was created
-- SELECT * FROM information_schema.tables WHERE table_name = 'shipment_updates';

-- Verify shipping_carriers table was created and populated
-- SELECT * FROM shipping_carriers;

-- ============================================================================
-- Rollback script (if needed)
-- ============================================================================

-- To rollback this migration, run:
-- ALTER TABLE orders 
-- DROP COLUMN IF EXISTS tracking_number,
-- DROP COLUMN IF EXISTS carrier,
-- DROP COLUMN IF EXISTS tracking_url,
-- DROP COLUMN IF EXISTS estimated_delivery_date,
-- DROP COLUMN IF EXISTS shipping_notes;
-- 
-- DROP TABLE IF EXISTS shipment_updates CASCADE;
-- DROP TABLE IF EXISTS shipping_carriers CASCADE;

-- ============================================================================
-- Migration Complete
-- ============================================================================
