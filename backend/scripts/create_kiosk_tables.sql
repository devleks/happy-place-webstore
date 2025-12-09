-- Kiosk System Database Tables
-- Self-service kiosk for in-store product browsing and assistance requests

-- Kiosk Sessions Table
CREATE TABLE IF NOT EXISTS kiosk_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    store_location_id INTEGER REFERENCES store_locations(id),
    kiosk_device_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- active, assistance_requested, completed, abandoned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assistance_requested_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    CONSTRAINT valid_session_status CHECK (status IN ('active', 'assistance_requested', 'completed', 'abandoned'))
);

CREATE INDEX idx_kiosk_sessions_session_id ON kiosk_sessions(session_id);
CREATE INDEX idx_kiosk_sessions_status ON kiosk_sessions(status);
CREATE INDEX idx_kiosk_sessions_created_at ON kiosk_sessions(created_at);

-- Kiosk Cart Items Table
CREATE TABLE IF NOT EXISTS kiosk_cart_items (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES kiosk_sessions(session_id) ON DELETE CASCADE,
    variant_id INTEGER REFERENCES product_variants(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_quantity CHECK (quantity > 0)
);

CREATE INDEX idx_kiosk_cart_session_id ON kiosk_cart_items(session_id);
CREATE INDEX idx_kiosk_cart_variant_id ON kiosk_cart_items(variant_id);

-- Assistance Requests Table
CREATE TABLE IF NOT EXISTS assistance_requests (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES kiosk_sessions(session_id),
    request_type VARCHAR(50) NOT NULL, -- item_retrieval, size_help, general_question, checkout
    status VARCHAR(20) DEFAULT 'pending', -- pending, acknowledged, completed, cancelled
    priority INTEGER DEFAULT 1, -- 1=normal, 2=high, 3=urgent
    customer_location VARCHAR(100),
    message TEXT,
    assigned_to INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT valid_request_status CHECK (status IN ('pending', 'acknowledged', 'completed', 'cancelled')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 3)
);

CREATE INDEX idx_assistance_session_id ON assistance_requests(session_id);
CREATE INDEX idx_assistance_status ON assistance_requests(status);
CREATE INDEX idx_assistance_assigned_to ON assistance_requests(assigned_to);
CREATE INDEX idx_assistance_created_at ON assistance_requests(created_at);

-- Kiosk Analytics Table (optional for tracking usage patterns)
CREATE TABLE IF NOT EXISTS kiosk_analytics (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES kiosk_sessions(session_id),
    event_type VARCHAR(50) NOT NULL, -- session_start, product_view, add_to_cart, assistance_request, session_end
    product_id INTEGER REFERENCES products(id),
    variant_id INTEGER REFERENCES product_variants(id),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kiosk_analytics_session ON kiosk_analytics(session_id);
CREATE INDEX idx_kiosk_analytics_event_type ON kiosk_analytics(event_type);
CREATE INDEX idx_kiosk_analytics_created_at ON kiosk_analytics(created_at);

-- Comments
COMMENT ON TABLE kiosk_sessions IS 'Tracks customer sessions on self-service kiosks';
COMMENT ON TABLE kiosk_cart_items IS 'Items added to cart during kiosk session';
COMMENT ON TABLE assistance_requests IS 'Customer requests for staff assistance from kiosk';
COMMENT ON TABLE kiosk_analytics IS 'Analytics data for kiosk usage patterns';

COMMENT ON COLUMN kiosk_sessions.session_id IS 'Unique session identifier (UUID format)';
COMMENT ON COLUMN kiosk_sessions.kiosk_device_id IS 'Physical kiosk device identifier';
COMMENT ON COLUMN assistance_requests.request_type IS 'Type of assistance: item_retrieval, size_help, general_question, checkout';
COMMENT ON COLUMN assistance_requests.priority IS '1=normal, 2=high, 3=urgent';
