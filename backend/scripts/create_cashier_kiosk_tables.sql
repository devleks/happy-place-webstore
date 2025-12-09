-- Cashier Kiosk Enhancement Tables
-- Optimized for fast checkout workflow

-- Held Transactions (for serving multiple customers)
CREATE TABLE IF NOT EXISTS held_transactions (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    shift_id INTEGER REFERENCES pos_shifts(id),
    hold_reference VARCHAR(20) UNIQUE NOT NULL, -- Quick recall code (e.g., H001, H002)
    items JSONB NOT NULL, -- Cart snapshot with all items
    subtotal DECIMAL(12,2),
    tax DECIMAL(12,2),
    total DECIMAL(12,2),
    customer_note VARCHAR(200),
    held_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '2 hours'),
    status VARCHAR(20) DEFAULT 'held', -- held, recalled, expired, cancelled
    CONSTRAINT valid_hold_status CHECK (status IN ('held', 'recalled', 'expired', 'cancelled'))
);

CREATE INDEX idx_held_employee ON held_transactions(employee_id);
CREATE INDEX idx_held_shift ON held_transactions(shift_id);
CREATE INDEX idx_held_reference ON held_transactions(hold_reference);
CREATE INDEX idx_held_status ON held_transactions(status);

-- Quick Access Products (frequently used items for fast access)
CREATE TABLE IF NOT EXISTS pos_quick_access (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id), -- NULL = store-wide favorites
    store_location_id INTEGER REFERENCES store_locations(id),
    product_id INTEGER REFERENCES products(id),
    variant_id INTEGER REFERENCES product_variants(id),
    access_type VARCHAR(20) DEFAULT 'favorite', -- favorite, frequent, recent
    access_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0,
    CONSTRAINT valid_access_type CHECK (access_type IN ('favorite', 'frequent', 'recent'))
);

CREATE INDEX idx_quick_access_employee ON pos_quick_access(employee_id);
CREATE INDEX idx_quick_access_store ON pos_quick_access(store_location_id);
CREATE INDEX idx_quick_access_type ON pos_quick_access(access_type);
CREATE INDEX idx_quick_access_sort ON pos_quick_access(sort_order);

-- Cashier Performance Metrics
CREATE TABLE IF NOT EXISTS cashier_metrics (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    shift_id INTEGER REFERENCES pos_shifts(id),
    metric_date DATE DEFAULT CURRENT_DATE,
    transactions_count INTEGER DEFAULT 0,
    items_scanned INTEGER DEFAULT 0,
    items_per_minute DECIMAL(5,2),
    average_transaction_seconds INTEGER,
    fastest_transaction_seconds INTEGER,
    total_sales DECIMAL(12,2) DEFAULT 0,
    void_count INTEGER DEFAULT 0,
    discount_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, shift_id, metric_date)
);

CREATE INDEX idx_metrics_employee ON cashier_metrics(employee_id);
CREATE INDEX idx_metrics_shift ON cashier_metrics(shift_id);
CREATE INDEX idx_metrics_date ON cashier_metrics(metric_date);

-- Product Barcode Mapping (for scanner integration)
CREATE TABLE IF NOT EXISTS product_barcodes (
    id SERIAL PRIMARY KEY,
    variant_id INTEGER REFERENCES product_variants(id) ON DELETE CASCADE,
    barcode VARCHAR(50) UNIQUE NOT NULL,
    barcode_type VARCHAR(20) DEFAULT 'EAN13', -- EAN13, UPC, CODE128, QR
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_barcode_type CHECK (barcode_type IN ('EAN13', 'UPC', 'CODE128', 'QR', 'OTHER'))
);

CREATE INDEX idx_barcode_lookup ON product_barcodes(barcode);
CREATE INDEX idx_barcode_variant ON product_barcodes(variant_id);

-- Kiosk Configuration (per device settings)
CREATE TABLE IF NOT EXISTS kiosk_config (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) UNIQUE NOT NULL,
    store_location_id INTEGER REFERENCES store_locations(id),
    device_name VARCHAR(100),
    kiosk_mode_enabled BOOLEAN DEFAULT TRUE,
    auto_reset_seconds INTEGER DEFAULT 10,
    scan_beep_enabled BOOLEAN DEFAULT TRUE,
    quick_keys_enabled BOOLEAN DEFAULT TRUE,
    customer_display_enabled BOOLEAN DEFAULT FALSE,
    receipt_auto_print BOOLEAN DEFAULT TRUE,
    config_json JSONB, -- Additional settings
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kiosk_device ON kiosk_config(device_id);
CREATE INDEX idx_kiosk_store ON kiosk_config(store_location_id);

-- Comments
COMMENT ON TABLE held_transactions IS 'Temporarily held sales for serving multiple customers';
COMMENT ON TABLE pos_quick_access IS 'Frequently accessed products for cashier quick selection';
COMMENT ON TABLE cashier_metrics IS 'Performance tracking for cashier efficiency';
COMMENT ON TABLE product_barcodes IS 'Barcode mappings for scanner integration';
COMMENT ON TABLE kiosk_config IS 'Per-device kiosk configuration settings';

COMMENT ON COLUMN held_transactions.hold_reference IS 'Quick recall code (H001-H999)';
COMMENT ON COLUMN held_transactions.expires_at IS 'Auto-expire after 2 hours';
COMMENT ON COLUMN pos_quick_access.access_type IS 'favorite=manual, frequent=auto-tracked, recent=last 10';
COMMENT ON COLUMN cashier_metrics.items_per_minute IS 'Scan rate performance metric';
COMMENT ON COLUMN product_barcodes.barcode_type IS 'EAN13, UPC, CODE128, QR, OTHER';

-- Function to auto-generate hold reference
CREATE OR REPLACE FUNCTION generate_hold_reference()
RETURNS VARCHAR AS $$
DECLARE
    next_num INTEGER;
    reference VARCHAR(20);
BEGIN
    -- Get next available number for today
    SELECT COALESCE(MAX(CAST(SUBSTRING(hold_reference FROM 2) AS INTEGER)), 0) + 1
    INTO next_num
    FROM held_transactions
    WHERE DATE(held_at) = CURRENT_DATE;

    -- Format as H001, H002, etc.
    reference := 'H' || LPAD(next_num::TEXT, 3, '0');

    RETURN reference;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-set hold reference if not provided
CREATE OR REPLACE FUNCTION set_hold_reference()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.hold_reference IS NULL OR NEW.hold_reference = '' THEN
        NEW.hold_reference := generate_hold_reference();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_hold_reference
    BEFORE INSERT ON held_transactions
    FOR EACH ROW
    EXECUTE FUNCTION set_hold_reference();

-- Function to cleanup expired held transactions
CREATE OR REPLACE FUNCTION cleanup_expired_holds()
RETURNS INTEGER AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    UPDATE held_transactions
    SET status = 'expired'
    WHERE status = 'held'
      AND expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

-- Seed some barcodes for existing products (example)
-- In production, these would be set during product creation or imported
INSERT INTO product_barcodes (variant_id, barcode, barcode_type, is_primary)
SELECT
    id,
    'HP' || LPAD(id::TEXT, 10, '0'), -- Generate simple barcode from variant ID
    'CODE128',
    TRUE
FROM product_variants
WHERE NOT EXISTS (
    SELECT 1 FROM product_barcodes WHERE variant_id = product_variants.id
)
LIMIT 50; -- Add barcodes for first 50 variants

-- Initial quick access items (most popular products)
INSERT INTO pos_quick_access (employee_id, store_location_id, variant_id, access_type, access_count, sort_order)
SELECT
    NULL as employee_id, -- Store-wide
    1 as store_location_id,
    pv.id as variant_id,
    'frequent' as access_type,
    0 as access_count,
    ROW_NUMBER() OVER (ORDER BY p.id) as sort_order
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
WHERE p.is_active = TRUE
  AND pv.is_active = TRUE
LIMIT 20;
