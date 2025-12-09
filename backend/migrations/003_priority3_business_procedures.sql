-- ====================================================================
-- PRIORITY 3 BUSINESS LOGIC STORED PROCEDURES
-- ====================================================================
-- Created: 2025-11-26
-- Purpose: Implement medium-priority business operations at database level
--
-- This migration implements 2 Priority 3 operations:
-- 1. Shipping Cost Calculation
-- 2. Product Creation with Variants
-- ====================================================================

-- ====================================================================
-- 1. SHIPPING COST CALCULATION
-- ====================================================================
-- Purpose: Calculate shipping cost based on city and weight
-- Business Rules:
-- - Nairobi: Free shipping (KSh 0)
-- - Upcountry: KSh 300 base + KSh 50 per kg
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_calculate_shipping(
    p_city VARCHAR(100),
    p_total_weight_kg NUMERIC(10,2)
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_is_nairobi BOOLEAN := FALSE;
    v_cost NUMERIC(10,2) := 0;
    v_description TEXT;
    v_nairobi_variations TEXT[] := ARRAY['nairobi', 'nai', 'nairobi county', 'nairobi city'];
    v_city_lower TEXT;
BEGIN
    -- Validate inputs
    IF p_city IS NULL OR TRIM(p_city) = '' THEN
        RAISE EXCEPTION 'City is required for shipping calculation';
    END IF;

    IF p_total_weight_kg IS NULL OR p_total_weight_kg < 0 THEN
        RAISE EXCEPTION 'Valid weight is required (must be >= 0)';
    END IF;

    -- Normalize city name
    v_city_lower := LOWER(TRIM(p_city));

    -- Check if Nairobi (free shipping)
    IF v_city_lower = ANY(v_nairobi_variations) THEN
        v_is_nairobi := TRUE;
        v_cost := 0.00;
        v_description := 'Free shipping within Nairobi';
    ELSE
        -- Upcountry shipping: KSh 300 + (weight * KSh 50)
        v_is_nairobi := FALSE;
        v_cost := 300.00 + (p_total_weight_kg * 50.00);
        v_description := FORMAT(
            'Upcountry shipping: KSh 300 base + KSh 50/kg (%s kg)',
            p_total_weight_kg
        );
    END IF;

    -- Return shipping details
    RETURN jsonb_build_object(
        'cost', ROUND(v_cost, 2),
        'is_nairobi', v_is_nairobi,
        'description', v_description,
        'city', p_city,
        'weight_kg', p_total_weight_kg
    );
END;
$$;

GRANT EXECUTE ON FUNCTION sp_calculate_shipping TO postgres;

-- ====================================================================
-- 2. PRODUCT CREATION WITH VARIANTS
-- ====================================================================
-- Purpose: Atomically create product with multiple variants and inventory
-- Business Rules:
-- - Product slug must be unique
-- - SKU must be unique across products
-- - Variant SKUs must be unique
-- - Inventory created for each variant
-- - All operations atomic (all succeed or all rollback)
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_create_product_with_variants(
    p_name VARCHAR(255),
    p_slug VARCHAR(255),
    p_description TEXT,
    p_price NUMERIC(10,2),
    p_sale_price NUMERIC(10,2),
    p_category_id INTEGER,
    p_sku VARCHAR(100),
    p_weight NUMERIC(10,2),
    p_is_active BOOLEAN,
    p_is_featured BOOLEAN,
    p_is_clearance BOOLEAN,
    p_variants JSONB,  -- Array of variants with size, color, sku, initial_quantity
    p_created_by INTEGER  -- Employee ID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_product_id INTEGER;
    v_variant JSONB;
    v_variant_id INTEGER;
    v_variants_created INTEGER := 0;
    v_total_inventory INTEGER := 0;
    v_result JSONB;
BEGIN
    -- 1. Validate employee has permission
    IF NOT EXISTS (
        SELECT 1 FROM employees
        WHERE id = p_created_by
          AND is_active = TRUE
          AND role IN ('manager', 'admin', 'super_admin')
    ) THEN
        RAISE EXCEPTION 'Insufficient permissions. Only managers and admins can create products.';
    END IF;

    -- 2. Validate required fields
    IF p_name IS NULL OR TRIM(p_name) = '' THEN
        RAISE EXCEPTION 'Product name is required';
    END IF;

    IF p_slug IS NULL OR TRIM(p_slug) = '' THEN
        RAISE EXCEPTION 'Product slug is required';
    END IF;

    IF p_sku IS NULL OR TRIM(p_sku) = '' THEN
        RAISE EXCEPTION 'Product SKU is required';
    END IF;

    IF p_price IS NULL OR p_price < 0 THEN
        RAISE EXCEPTION 'Valid price is required (must be >= 0)';
    END IF;

    IF p_category_id IS NULL THEN
        RAISE EXCEPTION 'Category ID is required';
    END IF;

    -- 3. Check if category exists
    IF NOT EXISTS (SELECT 1 FROM categories WHERE id = p_category_id) THEN
        RAISE EXCEPTION 'Category not found: %', p_category_id;
    END IF;

    -- 4. Check if slug already exists
    IF EXISTS (SELECT 1 FROM products WHERE slug = p_slug) THEN
        RAISE EXCEPTION 'Product slug already exists: %', p_slug;
    END IF;

    -- 5. Check if SKU already exists
    IF EXISTS (SELECT 1 FROM products WHERE sku = p_sku) THEN
        RAISE EXCEPTION 'Product SKU already exists: %', p_sku;
    END IF;

    -- 6. Validate sale price if provided
    IF p_sale_price IS NOT NULL AND p_sale_price >= p_price THEN
        RAISE EXCEPTION 'Sale price must be less than regular price';
    END IF;

    -- 7. Create product
    INSERT INTO products (
        name,
        slug,
        description,
        price,
        sale_price,
        category_id,
        sku,
        weight,
        is_active,
        is_featured,
        is_clearance,
        created_at,
        updated_at
    ) VALUES (
        p_name,
        p_slug,
        p_description,
        p_price,
        p_sale_price,
        p_category_id,
        p_sku,
        COALESCE(p_weight, 0.0),
        COALESCE(p_is_active, TRUE),
        COALESCE(p_is_featured, FALSE),
        COALESCE(p_is_clearance, FALSE),
        NOW(),
        NOW()
    )
    RETURNING id INTO v_product_id;

    -- 8. Create variants if provided
    IF p_variants IS NOT NULL AND jsonb_array_length(p_variants) > 0 THEN
        FOR v_variant IN SELECT * FROM jsonb_array_elements(p_variants)
        LOOP
            -- Validate variant fields
            IF v_variant->>'sku' IS NULL OR TRIM(v_variant->>'sku') = '' THEN
                RAISE EXCEPTION 'Variant SKU is required';
            END IF;

            IF v_variant->>'size' IS NULL OR TRIM(v_variant->>'size') = '' THEN
                RAISE EXCEPTION 'Variant size is required';
            END IF;

            IF v_variant->>'color' IS NULL OR TRIM(v_variant->>'color') = '' THEN
                RAISE EXCEPTION 'Variant color is required';
            END IF;

            -- Check if variant SKU already exists
            IF EXISTS (SELECT 1 FROM product_variants WHERE sku = v_variant->>'sku') THEN
                RAISE EXCEPTION 'Variant SKU already exists: %', v_variant->>'sku';
            END IF;

            -- Create variant
            INSERT INTO product_variants (
                product_id,
                sku,
                size,
                color,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                v_product_id,
                v_variant->>'sku',
                v_variant->>'size',
                v_variant->>'color',
                TRUE,
                NOW(),
                NOW()
            )
            RETURNING id INTO v_variant_id;

            -- Create inventory for variant
            INSERT INTO inventory (
                variant_id,
                quantity,
                reserved_quantity,
                created_at,
                updated_at
            ) VALUES (
                v_variant_id,
                COALESCE((v_variant->>'initial_quantity')::INTEGER, 0),
                0,
                NOW(),
                NOW()
            );

            v_variants_created := v_variants_created + 1;
            v_total_inventory := v_total_inventory + COALESCE((v_variant->>'initial_quantity')::INTEGER, 0);
        END LOOP;
    END IF;

    -- 9. Log product creation in activity log
    INSERT INTO activity_logs (
        action,
        resource_type,
        resource_id,
        employee_id,
        ip_address,
        details,
        created_at
    ) VALUES (
        'product_created',
        'product',
        v_product_id,
        p_created_by,
        NULL,  -- IP address tracked at application level
        jsonb_build_object(
            'product_id', v_product_id,
            'name', p_name,
            'sku', p_sku,
            'variants_created', v_variants_created,
            'total_inventory', v_total_inventory
        ),
        NOW()
    );

    -- 10. Build result
    v_result := jsonb_build_object(
        'success', TRUE,
        'product_id', v_product_id,
        'name', p_name,
        'slug', p_slug,
        'sku', p_sku,
        'variants_created', v_variants_created,
        'total_inventory', v_total_inventory,
        'created_at', NOW(),
        'message', 'Product and variants created successfully'
    );

    RETURN v_result;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_create_product_with_variants TO postgres;

-- ====================================================================
-- HELPER: Calculate cart total weight
-- ====================================================================
-- Purpose: Calculate total weight from cart items for shipping
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_calculate_cart_weight(
    p_customer_id INTEGER
)
RETURNS NUMERIC(10,2)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_total_weight NUMERIC(10,2) := 0;
BEGIN
    -- Calculate total weight from cart items
    SELECT COALESCE(SUM(p.weight * ci.quantity), 0)
    INTO v_total_weight
    FROM carts c
    JOIN cart_items ci ON ci.cart_id = c.id
    JOIN product_variants pv ON pv.id = ci.variant_id
    JOIN products p ON p.id = pv.product_id
    WHERE c.customer_id = p_customer_id;

    RETURN ROUND(v_total_weight, 2);
END;
$$;

GRANT EXECUTE ON FUNCTION sp_calculate_cart_weight TO postgres;

-- ====================================================================
-- HELPER: Calculate shipping for customer's cart
-- ====================================================================
-- Purpose: Calculate shipping for customer's current cart
-- ====================================================================

CREATE OR REPLACE FUNCTION sp_calculate_shipping_for_cart(
    p_customer_id INTEGER,
    p_city VARCHAR(100)
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_total_weight NUMERIC(10,2);
    v_shipping_result JSONB;
BEGIN
    -- Get cart weight
    v_total_weight := sp_calculate_cart_weight(p_customer_id);

    -- Calculate shipping
    v_shipping_result := sp_calculate_shipping(p_city, v_total_weight);

    RETURN v_shipping_result;
END;
$$;

GRANT EXECUTE ON FUNCTION sp_calculate_shipping_for_cart TO postgres;

-- ====================================================================
-- MIGRATION COMPLETE
-- ====================================================================
-- All Priority 3 business logic stored procedures have been created.
--
-- Next steps:
-- 1. Create service layer to call these procedures
-- 2. Update API endpoints to use new procedures
-- 3. Test with comprehensive test suite
--
-- Rollback: See 003_priority3_business_procedures_rollback.sql
-- ====================================================================
