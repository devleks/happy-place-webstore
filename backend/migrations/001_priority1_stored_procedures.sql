-- ====================================================================
-- PRIORITY 1 STORED PROCEDURES MIGRATION
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Migrate critical business operations to database level
--          for security-by-design and atomicity guarantees
--
-- This migration implements 5 Priority 1 operations:
-- 1. Order Creation (sp_create_order_secure)
-- 2. Inventory Reservation (sp_reserve_inventory_atomic)
-- 3. Payment Processing (sp_process_payment_secure)
-- 4. Return Processing (sp_process_return_secure)
-- 5. Promotion Validation (sp_validate_promotion_secure)
-- ====================================================================

-- ====================================================================
-- 1. ORDER CREATION STORED PROCEDURE
-- ====================================================================
-- Purpose: Create orders atomically with race condition prevention
-- Security: Prevents order number collisions, ensures ACID guarantees
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_create_order_secure(
    p_customer_id INTEGER,
    p_shipping_address_encrypted TEXT,
    p_billing_address_encrypted TEXT,
    p_payment_method VARCHAR(20),
    p_cart_items JSONB,
    p_shipping_method_id INTEGER DEFAULT NULL,
    p_is_nairobi BOOLEAN DEFAULT FALSE,
    p_shipping_cost NUMERIC(10,2) DEFAULT 0.00
)
RETURNS TABLE(
    order_id INTEGER,
    order_number VARCHAR(50),
    payment_id INTEGER,
    total_amount NUMERIC(10,2)
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_order_id INTEGER;
    v_order_number VARCHAR(50);
    v_payment_id INTEGER;
    v_subtotal NUMERIC(10,2) := 0;
    v_tax NUMERIC(10,2) := 0;
    v_total NUMERIC(10,2) := 0;
    v_item JSONB;
    v_variant_id INTEGER;
    v_quantity INTEGER;
    v_unit_price NUMERIC(10,2);
    v_product_id INTEGER;
    v_available_qty INTEGER;
BEGIN
    -- Lock order number generation to prevent race conditions
    LOCK TABLE orders IN EXCLUSIVE MODE;

    -- Generate unique order number with collision prevention
    SELECT 'ORD-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
           LPAD((
               SELECT COALESCE(COUNT(*), 0) + 1
               FROM orders
               WHERE DATE(created_at) = CURRENT_DATE
           )::TEXT, 5, '0')
    INTO v_order_number;

    -- Validate cart items exist and calculate subtotal
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_cart_items)
    LOOP
        v_variant_id := (v_item->>'variant_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;
        v_unit_price := (v_item->>'unit_price')::NUMERIC(10,2);

        -- Get product_id and verify variant exists
        SELECT pv.product_id INTO v_product_id
        FROM product_variants pv
        WHERE pv.id = v_variant_id AND pv.is_active = TRUE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Invalid or inactive variant_id: %', v_variant_id;
        END IF;

        -- Check inventory availability
        SELECT (quantity - reserved_quantity) INTO v_available_qty
        FROM inventory
        WHERE variant_id = v_variant_id;

        IF v_available_qty < v_quantity THEN
            RAISE EXCEPTION 'Insufficient inventory for variant_id: % (available: %, requested: %)',
                v_variant_id, v_available_qty, v_quantity;
        END IF;

        -- Add to subtotal
        v_subtotal := v_subtotal + (v_unit_price * v_quantity);
    END LOOP;

    -- Calculate tax (VAT 16% - already included in prices)
    -- Extract VAT component: VAT = Subtotal - (Subtotal / 1.16)
    v_tax := v_subtotal - (v_subtotal / 1.16);

    -- Calculate total
    v_total := v_subtotal + p_shipping_cost;

    -- Create order record
    INSERT INTO orders (
        customer_id,
        order_number,
        status,
        subtotal,
        tax,
        shipping_cost,
        total,
        shipping_method_id,
        is_nairobi,
        shipping_address_encrypted,
        billing_address_encrypted,
        created_at,
        updated_at
    ) VALUES (
        p_customer_id,
        v_order_number,
        'pending',
        v_subtotal,
        v_tax,
        p_shipping_cost,
        v_total,
        p_shipping_method_id,
        p_is_nairobi,
        p_shipping_address_encrypted,
        p_billing_address_encrypted,
        NOW(),
        NOW()
    )
    RETURNING id INTO v_order_id;

    -- Create order items
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_cart_items)
    LOOP
        v_variant_id := (v_item->>'variant_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;
        v_unit_price := (v_item->>'unit_price')::NUMERIC(10,2);

        -- Get product_id
        SELECT product_id INTO v_product_id
        FROM product_variants
        WHERE id = v_variant_id;

        -- Insert order item
        INSERT INTO order_items (
            order_id,
            product_id,
            variant_id,
            quantity,
            unit_price,
            total_price
        ) VALUES (
            v_order_id,
            v_product_id,
            v_variant_id,
            v_quantity,
            v_unit_price,
            v_unit_price * v_quantity
        );

        -- Reserve inventory atomically
        UPDATE inventory
        SET reserved_quantity = reserved_quantity + v_quantity,
            updated_at = NOW()
        WHERE variant_id = v_variant_id;
    END LOOP;

    -- Create payment record
    INSERT INTO payments (
        order_id,
        payment_method,
        amount,
        status,
        created_at
    ) VALUES (
        v_order_id,
        p_payment_method,
        v_total,
        CASE
            WHEN p_payment_method = 'cod' THEN 'pending'
            ELSE 'pending'
        END,
        NOW()
    )
    RETURNING id INTO v_payment_id;

    -- Log order creation in audit trail
    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        performed_at,
        details
    ) VALUES (
        v_order_id,
        'order_created',
        p_customer_id,
        NOW(),
        jsonb_build_object(
            'order_number', v_order_number,
            'payment_method', p_payment_method,
            'total', v_total,
            'items_count', jsonb_array_length(p_cart_items)
        )
    );

    -- Return order details
    RETURN QUERY
    SELECT v_order_id, v_order_number, v_payment_id, v_total;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION sp_create_order_secure TO postgres;

-- ====================================================================
-- 2. INVENTORY RESERVATION STORED PROCEDURE
-- ====================================================================
-- Purpose: Reserve inventory atomically with TOCTOU prevention
-- Security: Prevents overselling through database-level locks
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_reserve_inventory_atomic(
    p_variant_id INTEGER,
    p_quantity INTEGER
)
RETURNS TABLE(
    success BOOLEAN,
    available_quantity INTEGER,
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_current_qty INTEGER;
    v_reserved_qty INTEGER;
    v_available INTEGER;
BEGIN
    -- Lock the inventory row for update to prevent race conditions
    SELECT quantity, reserved_quantity INTO v_current_qty, v_reserved_qty
    FROM inventory
    WHERE variant_id = p_variant_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 0::INTEGER, 'Variant not found in inventory'::TEXT;
        RETURN;
    END IF;

    -- Calculate available quantity
    v_available := v_current_qty - v_reserved_qty;

    -- Check if sufficient inventory
    IF v_available < p_quantity THEN
        RETURN QUERY
        SELECT FALSE, v_available,
               format('Insufficient inventory. Available: %s, Requested: %s', v_available, p_quantity)::TEXT;
        RETURN;
    END IF;

    -- Reserve inventory atomically
    UPDATE inventory
    SET reserved_quantity = reserved_quantity + p_quantity,
        updated_at = NOW()
    WHERE variant_id = p_variant_id;

    -- Return success
    RETURN QUERY
    SELECT TRUE, v_available - p_quantity, 'Inventory reserved successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_reserve_inventory_atomic TO postgres;

-- ====================================================================
-- 3. INVENTORY RELEASE STORED PROCEDURE
-- ====================================================================
-- Purpose: Release reserved inventory (e.g., when order cancelled)
-- Security: Ensures reservations are properly released
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_release_inventory_atomic(
    p_variant_id INTEGER,
    p_quantity INTEGER
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_reserved_qty INTEGER;
BEGIN
    -- Lock the inventory row for update
    SELECT reserved_quantity INTO v_reserved_qty
    FROM inventory
    WHERE variant_id = p_variant_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Variant not found in inventory'::TEXT;
        RETURN;
    END IF;

    -- Check if we have enough reserved to release
    IF v_reserved_qty < p_quantity THEN
        RETURN QUERY
        SELECT FALSE,
               format('Cannot release %s units. Only %s units are reserved', p_quantity, v_reserved_qty)::TEXT;
        RETURN;
    END IF;

    -- Release inventory atomically
    UPDATE inventory
    SET reserved_quantity = reserved_quantity - p_quantity,
        updated_at = NOW()
    WHERE variant_id = p_variant_id;

    -- Return success
    RETURN QUERY
    SELECT TRUE, 'Inventory released successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_release_inventory_atomic TO postgres;

-- ====================================================================
-- 4. PAYMENT PROCESSING STORED PROCEDURE
-- ====================================================================
-- Purpose: Process payments atomically with inventory finalization
-- Security: Ensures payment completion triggers inventory deduction
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_process_payment_secure(
    p_payment_id INTEGER,
    p_transaction_id_encrypted TEXT DEFAULT NULL,
    p_mpesa_phone_encrypted TEXT DEFAULT NULL
)
RETURNS TABLE(
    success BOOLEAN,
    order_id INTEGER,
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_order_id INTEGER;
    v_payment_status VARCHAR(20);
    v_order_status VARCHAR(20);
    v_item RECORD;
BEGIN
    -- Lock payment for update
    SELECT p.order_id, p.status INTO v_order_id, v_payment_status
    FROM payments p
    WHERE p.id = p_payment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, NULL::INTEGER, 'Payment not found'::TEXT;
        RETURN;
    END IF;

    -- Check if already completed
    IF v_payment_status = 'completed' THEN
        RETURN QUERY
        SELECT FALSE, v_order_id, 'Payment already completed'::TEXT;
        RETURN;
    END IF;

    -- Update payment status
    UPDATE payments
    SET status = 'completed',
        completed_at = NOW(),
        transaction_id_encrypted = p_transaction_id_encrypted,
        mpesa_phone_encrypted = p_mpesa_phone_encrypted
    WHERE id = p_payment_id;

    -- Update order status
    UPDATE orders
    SET status = 'processing',
        updated_at = NOW()
    WHERE id = v_order_id;

    -- Convert reserved inventory to actual deduction
    FOR v_item IN
        SELECT oi.variant_id, oi.quantity
        FROM order_items oi
        WHERE oi.order_id = v_order_id
    LOOP
        -- Deduct from actual quantity and remove from reserved
        UPDATE inventory
        SET quantity = quantity - v_item.quantity,
            reserved_quantity = reserved_quantity - v_item.quantity,
            updated_at = NOW()
        WHERE variant_id = v_item.variant_id;
    END LOOP;

    -- Log payment completion
    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        performed_at,
        details
    )
    SELECT
        v_order_id,
        'payment_completed',
        o.customer_id,
        NOW(),
        jsonb_build_object(
            'payment_id', p_payment_id,
            'transaction_id', CASE WHEN p_transaction_id_encrypted IS NOT NULL THEN 'encrypted' ELSE NULL END
        )
    FROM orders o
    WHERE o.id = v_order_id;

    -- Return success
    RETURN QUERY
    SELECT TRUE, v_order_id, 'Payment processed successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_process_payment_secure TO postgres;

-- ====================================================================
-- 5. RETURN PROCESSING STORED PROCEDURE
-- ====================================================================
-- Purpose: Process product returns with business rules enforcement
-- Security: Enforces return window, restocking fees, inventory restoration
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_process_return_secure(
    p_order_id INTEGER,
    p_customer_id INTEGER,
    p_reason VARCHAR(100),
    p_reason_description TEXT,
    p_return_items JSONB, -- [{order_item_id, quantity, condition}]
    p_approved_by INTEGER DEFAULT NULL
)
RETURNS TABLE(
    return_id INTEGER,
    return_number VARCHAR(50),
    refund_amount NUMERIC(10,2),
    restocking_fee NUMERIC(10,2),
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_return_id INTEGER;
    v_return_number VARCHAR(50);
    v_order_date TIMESTAMP;
    v_order_status VARCHAR(20);
    v_order_total NUMERIC(10,2);
    v_refund_amount NUMERIC(10,2) := 0;
    v_restocking_fee NUMERIC(10,2) := 0;
    v_item JSONB;
    v_order_item_id INTEGER;
    v_return_qty INTEGER;
    v_item_condition VARCHAR(20);
    v_unit_price NUMERIC(10,2);
    v_variant_id INTEGER;
    v_original_qty INTEGER;
    v_days_since_order INTEGER;
    v_item_refund NUMERIC(10,2);
BEGIN
    -- Validate order belongs to customer
    SELECT o.created_at, o.status, o.total INTO v_order_date, v_order_status, v_order_total
    FROM orders o
    WHERE o.id = p_order_id AND o.customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found or does not belong to customer';
    END IF;

    -- Business Rule: Cannot return cancelled or already returned orders
    IF v_order_status IN ('cancelled', 'returned') THEN
        RAISE EXCEPTION 'Cannot return order with status: %', v_order_status;
    END IF;

    -- Business Rule: 30-day return window
    v_days_since_order := EXTRACT(DAY FROM NOW() - v_order_date);
    IF v_days_since_order > 30 THEN
        RAISE EXCEPTION 'Return window expired. Order is % days old (max 30 days)', v_days_since_order;
    END IF;

    -- Generate return number
    SELECT 'RET-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
           LPAD((SELECT COALESCE(COUNT(*), 0) + 1 FROM returns WHERE DATE(created_at) = CURRENT_DATE)::TEXT, 5, '0')
    INTO v_return_number;

    -- Calculate refund and restocking fees
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_return_items)
    LOOP
        v_order_item_id := (v_item->>'order_item_id')::INTEGER;
        v_return_qty := (v_item->>'quantity')::INTEGER;
        v_item_condition := v_item->>'condition';

        -- Get original order item details
        SELECT oi.unit_price, oi.variant_id, oi.quantity
        INTO v_unit_price, v_variant_id, v_original_qty
        FROM order_items oi
        WHERE oi.id = v_order_item_id AND oi.order_id = p_order_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Order item not found: %', v_order_item_id;
        END IF;

        -- Validate return quantity
        IF v_return_qty > v_original_qty THEN
            RAISE EXCEPTION 'Cannot return more than purchased. Requested: %, Purchased: %',
                v_return_qty, v_original_qty;
        END IF;

        -- Calculate item refund
        v_item_refund := v_unit_price * v_return_qty;

        -- Business Rule: Apply restocking fee for used/damaged items
        IF v_item_condition IN ('used', 'damaged') THEN
            v_restocking_fee := v_restocking_fee + (v_item_refund * 0.15); -- 15% restocking fee
        END IF;

        v_refund_amount := v_refund_amount + v_item_refund;
    END LOOP;

    -- Deduct restocking fee from refund
    v_refund_amount := v_refund_amount - v_restocking_fee;

    -- Create return record
    INSERT INTO returns (
        return_number,
        order_id,
        customer_id,
        reason,
        reason_description,
        status,
        refund_method,
        refund_amount,
        restocking_fee,
        approved_by,
        approved_at,
        created_at,
        updated_at
    ) VALUES (
        v_return_number,
        p_order_id,
        p_customer_id,
        p_reason,
        p_reason_description,
        CASE WHEN p_approved_by IS NOT NULL THEN 'approved' ELSE 'pending' END,
        'original_payment_method',
        v_refund_amount,
        v_restocking_fee,
        p_approved_by,
        CASE WHEN p_approved_by IS NOT NULL THEN NOW() ELSE NULL END,
        NOW(),
        NOW()
    )
    RETURNING id INTO v_return_id;

    -- Create return items
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_return_items)
    LOOP
        v_order_item_id := (v_item->>'order_item_id')::INTEGER;
        v_return_qty := (v_item->>'quantity')::INTEGER;
        v_item_condition := v_item->>'condition';

        -- Get variant_id
        SELECT variant_id INTO v_variant_id
        FROM order_items
        WHERE id = v_order_item_id;

        INSERT INTO return_items (
            return_id,
            order_item_id,
            variant_id,
            quantity,
            condition,
            refund_amount
        ) VALUES (
            v_return_id,
            v_order_item_id,
            v_variant_id,
            v_return_qty,
            v_item_condition,
            (SELECT unit_price * v_return_qty FROM order_items WHERE id = v_order_item_id)
        );

        -- If approved, restore inventory for items in good condition
        IF p_approved_by IS NOT NULL AND v_item_condition = 'new' THEN
            UPDATE inventory
            SET quantity = quantity + v_return_qty,
                updated_at = NOW()
            WHERE variant_id = v_variant_id;
        END IF;
    END LOOP;

    -- Log return creation
    INSERT INTO order_audit_log (
        order_id,
        action,
        performed_by,
        performed_at,
        details
    ) VALUES (
        p_order_id,
        'return_initiated',
        p_customer_id,
        NOW(),
        jsonb_build_object(
            'return_id', v_return_id,
            'return_number', v_return_number,
            'refund_amount', v_refund_amount,
            'restocking_fee', v_restocking_fee
        )
    );

    -- Return details
    RETURN QUERY
    SELECT v_return_id, v_return_number, v_refund_amount, v_restocking_fee,
           'Return processed successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_process_return_secure TO postgres;

-- ====================================================================
-- 6. PROMOTION VALIDATION STORED PROCEDURE
-- ====================================================================
-- Purpose: Validate promotion codes with concurrent usage prevention
-- Security: Prevents promotion code abuse through atomic validation
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_validate_promotion_secure(
    p_promotion_code VARCHAR(50),
    p_customer_id INTEGER,
    p_order_subtotal NUMERIC(10,2),
    p_category_id INTEGER DEFAULT NULL,
    p_product_id INTEGER DEFAULT NULL
)
RETURNS TABLE(
    valid BOOLEAN,
    promotion_id INTEGER,
    discount_amount NUMERIC(10,2),
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_promotion_id INTEGER;
    v_discount_type VARCHAR(20);
    v_discount_value NUMERIC(10,2);
    v_minimum_order NUMERIC(10,2);
    v_maximum_discount NUMERIC(10,2);
    v_applies_to VARCHAR(20);
    v_promo_category_id INTEGER;
    v_promo_product_id INTEGER;
    v_usage_limit INTEGER;
    v_usage_per_customer INTEGER;
    v_current_usage INTEGER;
    v_customer_usage INTEGER;
    v_start_date TIMESTAMP;
    v_end_date TIMESTAMP;
    v_is_active BOOLEAN;
    v_discount_amount NUMERIC(10,2);
BEGIN
    -- Lock promotion for update to prevent race conditions
    SELECT
        id, discount_type, discount_value, minimum_order_amount,
        maximum_discount_amount, applies_to, category_id, product_id,
        usage_limit, usage_per_customer, current_usage_count,
        start_date, end_date, is_active
    INTO
        v_promotion_id, v_discount_type, v_discount_value, v_minimum_order,
        v_maximum_discount, v_applies_to, v_promo_category_id, v_promo_product_id,
        v_usage_limit, v_usage_per_customer, v_current_usage,
        v_start_date, v_end_date, v_is_active
    FROM promotions
    WHERE code = p_promotion_code
    FOR UPDATE;

    -- Validation: Promotion exists
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, NULL::INTEGER, 0::NUMERIC(10,2), 'Invalid promotion code'::TEXT;
        RETURN;
    END IF;

    -- Validation: Is active
    IF NOT v_is_active THEN
        RETURN QUERY
        SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2), 'Promotion is not active'::TEXT;
        RETURN;
    END IF;

    -- Validation: Date range
    IF NOW() < v_start_date THEN
        RETURN QUERY
        SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2), 'Promotion has not started yet'::TEXT;
        RETURN;
    END IF;

    IF NOW() > v_end_date THEN
        RETURN QUERY
        SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2), 'Promotion has expired'::TEXT;
        RETURN;
    END IF;

    -- Validation: Minimum order amount
    IF v_minimum_order IS NOT NULL AND p_order_subtotal < v_minimum_order THEN
        RETURN QUERY
        SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2),
               format('Minimum order amount not met. Required: KSh %s', v_minimum_order)::TEXT;
        RETURN;
    END IF;

    -- Validation: Usage limit
    IF v_usage_limit IS NOT NULL AND v_current_usage >= v_usage_limit THEN
        RETURN QUERY
        SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2), 'Promotion usage limit reached'::TEXT;
        RETURN;
    END IF;

    -- Validation: Per-customer usage limit
    IF v_usage_per_customer IS NOT NULL THEN
        SELECT COUNT(*) INTO v_customer_usage
        FROM order_promotions op
        JOIN orders o ON op.order_id = o.id
        WHERE op.promotion_id = v_promotion_id
        AND o.customer_id = p_customer_id;

        IF v_customer_usage >= v_usage_per_customer THEN
            RETURN QUERY
            SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2),
                   'You have reached the usage limit for this promotion'::TEXT;
            RETURN;
        END IF;
    END IF;

    -- Validation: Category/Product applicability
    IF v_applies_to = 'category' AND v_promo_category_id != p_category_id THEN
        RETURN QUERY
        SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2),
               'Promotion does not apply to this category'::TEXT;
        RETURN;
    END IF;

    IF v_applies_to = 'product' AND v_promo_product_id != p_product_id THEN
        RETURN QUERY
        SELECT FALSE, v_promotion_id, 0::NUMERIC(10,2),
               'Promotion does not apply to this product'::TEXT;
        RETURN;
    END IF;

    -- Calculate discount amount
    IF v_discount_type = 'percentage' THEN
        v_discount_amount := p_order_subtotal * (v_discount_value / 100);
    ELSIF v_discount_type = 'fixed' THEN
        v_discount_amount := v_discount_value;
    ELSE
        v_discount_amount := 0;
    END IF;

    -- Apply maximum discount cap if exists
    IF v_maximum_discount IS NOT NULL AND v_discount_amount > v_maximum_discount THEN
        v_discount_amount := v_maximum_discount;
    END IF;

    -- Increment usage count (will be committed when order completes)
    UPDATE promotions
    SET current_usage_count = current_usage_count + 1
    WHERE id = v_promotion_id;

    -- Return success
    RETURN QUERY
    SELECT TRUE, v_promotion_id, v_discount_amount, 'Promotion applied successfully'::TEXT;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_validate_promotion_secure TO postgres;

-- ====================================================================
-- MIGRATION COMPLETE
-- ====================================================================
-- All Priority 1 stored procedures have been created.
--
-- Next steps:
-- 1. Update application services to call these procedures
-- 2. Run comprehensive tests
-- 3. Monitor performance and security improvements
--
-- Rollback: See 001_priority1_stored_procedures_rollback.sql
-- ====================================================================
