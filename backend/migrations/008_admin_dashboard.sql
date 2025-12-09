-- =====================================================
-- MIGRATION 008: ADMIN DASHBOARD & MANAGEMENT SYSTEM
-- =====================================================
-- Phase 11: Admin Dashboard
-- Created: December 3, 2025
-- Description: Creates tables for promotions, system settings,
--              and adds promotion tracking to orders/POS transactions
-- =====================================================

-- ==============================
-- 1. CREATE NEW TABLES
-- ==============================

-- ------------------------------
-- 1.1 PROMOTIONS TABLE
-- ------------------------------
-- Stores promotional campaigns and discount codes

CREATE TABLE IF NOT EXISTS promotions (
    id SERIAL PRIMARY KEY,

    -- Basic Information
    name VARCHAR(200) NOT NULL,
    description TEXT,
    code VARCHAR(50) UNIQUE NOT NULL,

    -- Discount Configuration
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed_amount')),
    discount_value NUMERIC(10,2) NOT NULL CHECK (discount_value >= 0),

    -- Duration
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,

    -- Usage Limits
    max_uses INTEGER DEFAULT 0 CHECK (max_uses >= 0),              -- 0 = unlimited
    max_uses_per_customer INTEGER DEFAULT 0 CHECK (max_uses_per_customer >= 0), -- 0 = unlimited
    min_order_amount NUMERIC(10,2) DEFAULT 0 CHECK (min_order_amount >= 0),
    current_uses INTEGER DEFAULT 0 CHECK (current_uses >= 0),

    -- Applicability
    applicable_to VARCHAR(20) DEFAULT 'all' CHECK (applicable_to IN ('all', 'categories', 'products')),
    applicable_ids TEXT,                     -- Comma-separated category/product IDs

    -- Channels
    enabled_online BOOLEAN DEFAULT TRUE NOT NULL,
    enabled_pos BOOLEAN DEFAULT TRUE NOT NULL,

    -- Status & Tracking
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_by INTEGER REFERENCES employees(id),
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT valid_date_range CHECK (end_date > start_date)
);

-- Indexes for promotions
CREATE INDEX idx_promotions_code ON promotions(code);
CREATE INDEX idx_promotions_active ON promotions(is_active);
CREATE INDEX idx_promotions_dates ON promotions(start_date, end_date);
CREATE INDEX idx_promotions_created_by ON promotions(created_by);

-- ------------------------------
-- 1.2 PROMOTION_USAGE TABLE
-- ------------------------------
-- Tracks promotion usage for analytics and usage limits

CREATE TABLE IF NOT EXISTS promotion_usage (
    id SERIAL PRIMARY KEY,

    -- References
    promotion_id INTEGER NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    pos_transaction_id INTEGER REFERENCES pos_transactions(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,

    -- Usage Details
    discount_amount NUMERIC(10,2) NOT NULL CHECK (discount_amount >= 0),
    used_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT promotion_usage_source_check CHECK (
        (order_id IS NOT NULL AND pos_transaction_id IS NULL) OR
        (order_id IS NULL AND pos_transaction_id IS NOT NULL)
    )
);

-- Indexes for promotion_usage
CREATE INDEX idx_promotion_usage_promotion ON promotion_usage(promotion_id);
CREATE INDEX idx_promotion_usage_order ON promotion_usage(order_id);
CREATE INDEX idx_promotion_usage_pos ON promotion_usage(pos_transaction_id);
CREATE INDEX idx_promotion_usage_customer ON promotion_usage(customer_id);
CREATE INDEX idx_promotion_usage_date ON promotion_usage(used_at);

-- ------------------------------
-- 1.3 SYSTEM_SETTINGS TABLE
-- ------------------------------
-- Stores system-wide configuration settings

CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,

    -- Setting Information
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string' NOT NULL CHECK (setting_type IN ('string', 'integer', 'boolean', 'json', 'float')),
    description TEXT,

    -- Tracking
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_by INTEGER REFERENCES employees(id)
);

-- Index for system_settings
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);

-- ==============================
-- 2. MODIFY EXISTING TABLES
-- ==============================

-- ------------------------------
-- 2.1 ORDERS - Add promotion tracking
-- ------------------------------

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS promotion_id INTEGER REFERENCES promotions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
ADD COLUMN IF NOT EXISTS discount_code VARCHAR(50);

-- Index for orders promotion tracking
CREATE INDEX IF NOT EXISTS idx_orders_promotion ON orders(promotion_id);
CREATE INDEX IF NOT EXISTS idx_orders_discount_code ON orders(discount_code);

-- ------------------------------
-- 2.2 POS_TRANSACTIONS - Add promotion tracking
-- ------------------------------

ALTER TABLE pos_transactions
ADD COLUMN IF NOT EXISTS promotion_id INTEGER REFERENCES promotions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
ADD COLUMN IF NOT EXISTS discount_code VARCHAR(50);

-- Index for pos_transactions promotion tracking
CREATE INDEX IF NOT EXISTS idx_pos_transactions_promotion ON pos_transactions(promotion_id);
CREATE INDEX IF NOT EXISTS idx_pos_transactions_discount_code ON pos_transactions(discount_code);

-- ==============================
-- 3. SEED DEFAULT DATA
-- ==============================

-- ------------------------------
-- 3.1 Seed System Settings
-- ------------------------------

INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
    -- Store Information
    ('store_name', 'Happy Place Boutique', 'string', 'Store name displayed to customers'),
    ('store_email', 'info@happyplace.com', 'string', 'Store contact email'),
    ('store_phone', '+254-XXX-XXXXXX', 'string', 'Store contact phone number'),
    ('store_website', 'www.happyplace.com', 'string', 'Store website URL'),
    ('store_address', '123 Kimathi Street, Nairobi, Kenya, 00100', 'string', 'Physical store address'),

    -- Business Hours (JSON format)
    ('business_hours', '{"monday":{"open":"09:00","close":"18:00","closed":false},"tuesday":{"open":"09:00","close":"18:00","closed":false},"wednesday":{"open":"09:00","close":"18:00","closed":false},"thursday":{"open":"09:00","close":"18:00","closed":false},"friday":{"open":"09:00","close":"18:00","closed":false},"saturday":{"open":"09:00","close":"16:00","closed":false},"sunday":{"open":"","close":"","closed":true}}', 'json', 'Business hours by day of week'),

    -- Tax & Fees
    ('vat_rate', '16', 'integer', 'VAT rate percentage'),
    ('restocking_fee', '10', 'integer', 'Restocking fee percentage for returns'),

    -- Return Policy
    ('return_window_days', '30', 'integer', 'Number of days customers can return items'),
    ('clearance_items_returnable', 'false', 'boolean', 'Whether clearance items can be returned'),
    ('sale_items_returnable', 'false', 'boolean', 'Whether sale items can be returned'),

    -- Inventory
    ('low_stock_threshold', '10', 'integer', 'Inventory level that triggers low stock alert'),
    ('out_of_stock_threshold', '0', 'integer', 'Inventory level considered out of stock'),

    -- Email Configuration
    ('smtp_server', 'smtp.gmail.com', 'string', 'SMTP server for sending emails'),
    ('smtp_port', '587', 'string', 'SMTP server port'),
    ('smtp_email', 'noreply@happyplace.com', 'string', 'Email address for sending emails'),
    ('smtp_password', '', 'string', 'SMTP password (encrypted)'),
    ('smtp_use_tls', 'true', 'boolean', 'Whether to use TLS for SMTP'),

    -- Payment Methods
    ('payment_cod_enabled', 'true', 'boolean', 'Enable Cash on Delivery'),
    ('payment_mpesa_enabled', 'true', 'boolean', 'Enable M-Pesa payments'),
    ('payment_card_enabled', 'false', 'boolean', 'Enable card payments'),

    -- Shipping Settings
    ('shipping_standard_cost', '300', 'integer', 'Standard shipping cost in KSh'),
    ('shipping_express_cost', '500', 'integer', 'Express shipping cost in KSh'),
    ('shipping_free_threshold', '5000', 'integer', 'Order amount for free shipping in KSh'),

    -- Currency
    ('currency_code', 'KSh', 'string', 'Currency code'),
    ('currency_symbol', 'KSh', 'string', 'Currency symbol'),

    -- Orders
    ('order_prefix', 'ORD', 'string', 'Prefix for order numbers'),
    ('order_auto_complete_days', '7', 'integer', 'Days after which delivered orders auto-complete'),

    -- Notifications
    ('notifications_order_confirmation', 'true', 'boolean', 'Send order confirmation emails'),
    ('notifications_order_shipped', 'true', 'boolean', 'Send order shipped emails'),
    ('notifications_low_stock', 'true', 'boolean', 'Send low stock alerts to admin'),

    -- Analytics
    ('analytics_enabled', 'true', 'boolean', 'Enable analytics tracking'),
    ('analytics_retention_days', '365', 'integer', 'Days to retain analytics data')
ON CONFLICT (setting_key) DO NOTHING;

-- ------------------------------
-- 3.2 Seed Sample Promotions (for testing)
-- ------------------------------

-- Get the first admin/manager employee for created_by
DO $$
DECLARE
    admin_id INTEGER;
BEGIN
    -- Find the first admin or manager employee
    SELECT id INTO admin_id FROM employees
    WHERE role IN ('admin', 'manager')
    ORDER BY id ASC
    LIMIT 1;

    -- Only insert if we found an admin
    IF admin_id IS NOT NULL THEN
        INSERT INTO promotions (
            name, description, code, discount_type, discount_value,
            start_date, end_date, max_uses, max_uses_per_customer,
            min_order_amount, applicable_to, enabled_online, enabled_pos,
            is_active, created_by
        ) VALUES
            (
                'Welcome Discount',
                'Welcome discount for new customers',
                'WELCOME10',
                'percentage',
                10.00,
                '2025-01-01 00:00:00',
                '2025-12-31 23:59:59',
                0,  -- unlimited uses
                1,  -- once per customer
                1000.00,  -- minimum KSh 1,000 order
                'all',
                true,
                false,
                true,
                admin_id
            ),
            (
                'Holiday Sale',
                'Holiday season discount on all items',
                'HOLIDAY20',
                'percentage',
                20.00,
                '2025-12-15 00:00:00',
                '2025-12-31 23:59:59',
                500,  -- limited to 500 uses
                3,    -- up to 3 uses per customer
                2000.00,  -- minimum KSh 2,000 order
                'all',
                true,
                true,
                true,
                admin_id
            ),
            (
                'Clearance Discount',
                'Fixed discount on clearance items',
                'CLEARANCE500',
                'fixed_amount',
                500.00,
                '2025-01-01 00:00:00',
                '2025-06-30 23:59:59',
                0,
                0,
                3000.00,  -- minimum KSh 3,000 order
                'all',
                true,
                true,
                false,  -- inactive by default
                admin_id
            )
        ON CONFLICT (code) DO NOTHING;
    END IF;
END $$;

-- ==============================
-- 4. CREATE VIEWS (for reporting)
-- ==============================

-- ------------------------------
-- 4.1 Active Promotions View
-- ------------------------------
-- Shows only currently active and valid promotions

CREATE OR REPLACE VIEW active_promotions AS
SELECT
    p.*,
    e.full_name AS created_by_name,
    COUNT(DISTINCT pu.id) AS total_uses,
    COUNT(DISTINCT pu.customer_id) AS unique_customers,
    COALESCE(SUM(pu.discount_amount), 0) AS total_discount_given
FROM promotions p
LEFT JOIN employees e ON p.created_by = e.id
LEFT JOIN promotion_usage pu ON p.id = pu.promotion_id
WHERE p.is_active = true
  AND p.start_date <= NOW()
  AND p.end_date >= NOW()
  AND (p.max_uses = 0 OR p.current_uses < p.max_uses)
GROUP BY p.id, e.full_name;

-- ------------------------------
-- 4.2 Promotion Performance View
-- ------------------------------
-- Analytics view for promotion performance

CREATE OR REPLACE VIEW promotion_performance AS
SELECT
    p.id,
    p.name,
    p.code,
    p.discount_type,
    p.discount_value,
    p.start_date,
    p.end_date,
    p.max_uses,
    p.current_uses,
    COUNT(DISTINCT pu.id) AS total_uses,
    COUNT(DISTINCT pu.customer_id) AS unique_customers,
    COALESCE(SUM(pu.discount_amount), 0) AS total_discount_given,
    COALESCE(SUM(o.total_amount), 0) + COALESCE(SUM(pt.total_amount), 0) AS total_revenue_generated,
    CASE
        WHEN p.max_uses > 0 THEN ROUND((p.current_uses::NUMERIC / p.max_uses::NUMERIC * 100), 2)
        ELSE 0
    END AS usage_percentage,
    CASE
        WHEN NOW() < p.start_date THEN 'scheduled'
        WHEN NOW() > p.end_date THEN 'expired'
        WHEN p.is_active = false THEN 'disabled'
        WHEN p.max_uses > 0 AND p.current_uses >= p.max_uses THEN 'exhausted'
        ELSE 'active'
    END AS status
FROM promotions p
LEFT JOIN promotion_usage pu ON p.id = pu.promotion_id
LEFT JOIN orders o ON pu.order_id = o.id
LEFT JOIN pos_transactions pt ON pu.pos_transaction_id = pt.id
GROUP BY p.id;

-- ==============================
-- 5. CREATE FUNCTIONS
-- ==============================

-- ------------------------------
-- 5.1 Function to validate promotion
-- ------------------------------
-- Validates if a promotion can be applied to an order

CREATE OR REPLACE FUNCTION validate_promotion(
    promo_code VARCHAR,
    order_total NUMERIC,
    customer_id_param INTEGER DEFAULT NULL
) RETURNS TABLE(
    valid BOOLEAN,
    promotion_id INTEGER,
    discount_amount NUMERIC,
    error_message TEXT
) AS $$
DECLARE
    promo RECORD;
    customer_usage_count INTEGER;
    calculated_discount NUMERIC;
BEGIN
    -- Find the promotion by code
    SELECT * INTO promo FROM promotions
    WHERE code = promo_code
    AND is_active = true
    LIMIT 1;

    -- Promotion not found
    IF promo IS NULL THEN
        RETURN QUERY SELECT false, NULL::INTEGER, 0::NUMERIC, 'Invalid promotion code'::TEXT;
        RETURN;
    END IF;

    -- Check if promotion has started
    IF NOW() < promo.start_date THEN
        RETURN QUERY SELECT false, NULL::INTEGER, 0::NUMERIC, 'Promotion has not started yet'::TEXT;
        RETURN;
    END IF;

    -- Check if promotion has expired
    IF NOW() > promo.end_date THEN
        RETURN QUERY SELECT false, NULL::INTEGER, 0::NUMERIC, 'Promotion has expired'::TEXT;
        RETURN;
    END IF;

    -- Check if promotion usage limit is reached
    IF promo.max_uses > 0 AND promo.current_uses >= promo.max_uses THEN
        RETURN QUERY SELECT false, NULL::INTEGER, 0::NUMERIC, 'Promotion usage limit reached'::TEXT;
        RETURN;
    END IF;

    -- Check minimum order amount
    IF order_total < promo.min_order_amount THEN
        RETURN QUERY SELECT false, NULL::INTEGER, 0::NUMERIC,
            'Minimum order amount of ' || promo.min_order_amount || ' required'::TEXT;
        RETURN;
    END IF;

    -- Check customer usage limit (if customer_id provided)
    IF customer_id_param IS NOT NULL AND promo.max_uses_per_customer > 0 THEN
        SELECT COUNT(*) INTO customer_usage_count
        FROM promotion_usage
        WHERE promotion_id = promo.id
        AND customer_id = customer_id_param;

        IF customer_usage_count >= promo.max_uses_per_customer THEN
            RETURN QUERY SELECT false, NULL::INTEGER, 0::NUMERIC,
                'You have already used this promotion the maximum number of times'::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Calculate discount amount
    IF promo.discount_type = 'percentage' THEN
        calculated_discount := ROUND(order_total * (promo.discount_value / 100), 2);
    ELSE
        calculated_discount := promo.discount_value;
    END IF;

    -- Ensure discount doesn't exceed order total
    IF calculated_discount > order_total THEN
        calculated_discount := order_total;
    END IF;

    -- Promotion is valid
    RETURN QUERY SELECT true, promo.id, calculated_discount, NULL::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------
-- 5.2 Function to apply promotion
-- ------------------------------
-- Records promotion usage and increments counter

CREATE OR REPLACE FUNCTION apply_promotion(
    promo_id INTEGER,
    discount_amt NUMERIC,
    order_id_param INTEGER DEFAULT NULL,
    pos_transaction_id_param INTEGER DEFAULT NULL,
    customer_id_param INTEGER DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    -- Insert promotion usage record
    INSERT INTO promotion_usage (
        promotion_id,
        order_id,
        pos_transaction_id,
        customer_id,
        discount_amount
    ) VALUES (
        promo_id,
        order_id_param,
        pos_transaction_id_param,
        customer_id_param,
        discount_amt
    );

    -- Increment current_uses counter
    UPDATE promotions
    SET current_uses = current_uses + 1,
        updated_at = NOW()
    WHERE id = promo_id;

    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------
-- 5.3 Function to get setting value
-- ------------------------------
-- Helper function to retrieve setting values with type casting

CREATE OR REPLACE FUNCTION get_setting(
    setting_key_param VARCHAR,
    default_value TEXT DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    setting_value_result TEXT;
BEGIN
    SELECT setting_value INTO setting_value_result
    FROM system_settings
    WHERE setting_key = setting_key_param;

    IF setting_value_result IS NULL THEN
        RETURN default_value;
    ELSE
        RETURN setting_value_result;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ==============================
-- 6. CREATE TRIGGERS
-- ==============================

-- ------------------------------
-- 6.1 Update updated_at timestamp on promotions
-- ------------------------------

CREATE OR REPLACE FUNCTION update_promotion_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_promotion_timestamp
    BEFORE UPDATE ON promotions
    FOR EACH ROW
    EXECUTE FUNCTION update_promotion_timestamp();

-- ------------------------------
-- 6.2 Update updated_at timestamp on system_settings
-- ------------------------------

CREATE OR REPLACE FUNCTION update_system_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_system_settings_timestamp
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_timestamp();

-- ==============================
-- 7. GRANT PERMISSIONS
-- ==============================

-- Grant select on views to application user (if exists)
-- Note: Adjust the username as needed for your setup

-- GRANT SELECT ON active_promotions TO happy_place_app;
-- GRANT SELECT ON promotion_performance TO happy_place_app;

-- ==============================
-- 8. VERIFICATION QUERIES
-- ==============================

-- Verify tables were created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('promotions', 'promotion_usage', 'system_settings');

    IF table_count = 3 THEN
        RAISE NOTICE 'SUCCESS: All 3 new tables created';
    ELSE
        RAISE WARNING 'WARNING: Expected 3 tables, found %', table_count;
    END IF;
END $$;

-- Verify columns were added to orders
DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_name = 'orders'
    AND column_name IN ('promotion_id', 'discount_amount', 'discount_code');

    IF column_count = 3 THEN
        RAISE NOTICE 'SUCCESS: All 3 columns added to orders table';
    ELSE
        RAISE WARNING 'WARNING: Expected 3 columns in orders, found %', column_count;
    END IF;
END $$;

-- Verify columns were added to pos_transactions
DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_name = 'pos_transactions'
    AND column_name IN ('promotion_id', 'discount_amount', 'discount_code');

    IF column_count = 3 THEN
        RAISE NOTICE 'SUCCESS: All 3 columns added to pos_transactions table';
    ELSE
        RAISE WARNING 'WARNING: Expected 3 columns in pos_transactions, found %', column_count;
    END IF;
END $$;

-- Verify system_settings were seeded
DO $$
DECLARE
    settings_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO settings_count FROM system_settings;

    IF settings_count > 0 THEN
        RAISE NOTICE 'SUCCESS: % system settings seeded', settings_count;
    ELSE
        RAISE WARNING 'WARNING: No system settings found';
    END IF;
END $$;

-- Display summary
SELECT
    'Migration 008 completed successfully!' AS status,
    NOW() AS completed_at;

-- =====================================================
-- END OF MIGRATION 008
-- =====================================================
