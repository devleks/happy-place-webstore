"""
Product Service
Handles product and variant creation using stored procedures.
Implements business logic for product management.
"""

import json
from typing import Dict, List, Optional
from extensions import db


class ProductService:
    """Service for product management operations"""

    @staticmethod
    def create_product_with_variants(
        name: str,
        slug: str,
        price: float,
        category_id: int,
        sku: str,
        created_by: int,
        description: Optional[str] = None,
        sale_price: Optional[float] = None,
        weight: Optional[float] = None,
        is_active: bool = True,
        is_featured: bool = False,
        is_clearance: bool = False,
        variants: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Create a new product with variants using stored procedure.

        Features:
        - Atomic creation (all succeed or all rollback)
        - Unique slug validation
        - Unique SKU validation
        - Automatic inventory creation
        - Activity logging

        Args:
            name: Product name
            slug: URL-friendly product identifier
            price: Regular price
            category_id: Category ID
            sku: Stock keeping unit
            created_by: Employee ID creating the product
            description: Product description
            sale_price: Sale price (must be less than price)
            weight: Product weight in kg
            is_active: Whether product is active
            is_featured: Whether product is featured
            is_clearance: Whether product is clearance item
            variants: List of variants with size, color, sku, initial_quantity

        Returns:
            dict: Product creation result with product_id, variants_created, etc.

        Raises:
            ValueError: If validation fails or employee lacks permission
            RuntimeError: If creation fails

        Example:
            result = ProductService.create_product_with_variants(
                name='Floral Dress',
                slug='floral-dress-summer',
                price=2500.00,
                category_id=3,
                sku='FD-001',
                created_by=1,  # Employee ID
                variants=[
                    {
                        'size': 'S',
                        'color': 'Blue',
                        'sku': 'FD-001-S-BLU',
                        'initial_quantity': 10
                    },
                    {
                        'size': 'M',
                        'color': 'Blue',
                        'sku': 'FD-001-M-BLU',
                        'initial_quantity': 15
                    }
                ]
            )
        """
        try:
            # Convert variants to JSONB format
            variants_json = json.dumps(variants) if variants else None

            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_create_product_with_variants(
                        :name,
                        :slug,
                        :description,
                        :price,
                        :sale_price,
                        :category_id,
                        :sku,
                        :weight,
                        :is_active,
                        :is_featured,
                        :is_clearance,
                        CAST(:variants AS jsonb),
                        :created_by
                    )
                """),
                {
                    'name': name,
                    'slug': slug,
                    'description': description,
                    'price': price,
                    'sale_price': sale_price,
                    'category_id': category_id,
                    'sku': sku,
                    'weight': weight or 0.0,
                    'is_active': is_active,
                    'is_featured': is_featured,
                    'is_clearance': is_clearance,
                    'variants': variants_json,
                    'created_by': created_by
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Product creation procedure did not return result')

            product_data = row[0]  # JSONB result

            db.session.commit()

            return {
                'success': product_data.get('success', False),
                'product_id': product_data.get('product_id'),
                'name': product_data.get('name'),
                'slug': product_data.get('slug'),
                'sku': product_data.get('sku'),
                'variants_created': product_data.get('variants_created', 0),
                'total_inventory': product_data.get('total_inventory', 0),
                'created_at': product_data.get('created_at'),
                'message': product_data.get('message', 'Product created successfully')
            }

        except Exception as e:
            db.session.rollback()
            error_msg = str(e)

            # Check for validation/business rule errors
            if 'insufficient permissions' in error_msg.lower():
                raise ValueError('Insufficient permissions. Only managers and admins can create products.')
            if 'already exists' in error_msg.lower():
                raise ValueError(error_msg)
            if 'required' in error_msg.lower():
                raise ValueError(error_msg)
            if 'not found' in error_msg.lower():
                raise ValueError(error_msg)
            if 'sale price must be less' in error_msg.lower():
                raise ValueError(error_msg)

            raise RuntimeError(f'Product creation failed: {error_msg}')

    @staticmethod
    def validate_product_data(
        name: str,
        slug: str,
        price: float,
        sku: str,
        sale_price: Optional[float] = None
    ) -> Dict:
        """
        Validate product data before creation.

        Args:
            name: Product name
            slug: Product slug
            price: Regular price
            sku: Stock keeping unit
            sale_price: Sale price (optional)

        Returns:
            dict: {
                'valid': bool,
                'errors': List[str]
            }
        """
        errors = []

        # Validate name
        if not name or not name.strip():
            errors.append('Product name is required')
        elif len(name) > 255:
            errors.append('Product name must be 255 characters or less')

        # Validate slug
        if not slug or not slug.strip():
            errors.append('Product slug is required')
        elif len(slug) > 255:
            errors.append('Product slug must be 255 characters or less')

        # Validate SKU
        if not sku or not sku.strip():
            errors.append('Product SKU is required')
        elif len(sku) > 100:
            errors.append('Product SKU must be 100 characters or less')

        # Validate price
        if price is None or price < 0:
            errors.append('Valid price is required (must be >= 0)')

        # Validate sale price
        if sale_price is not None:
            if sale_price < 0:
                errors.append('Sale price must be >= 0')
            elif price and sale_price >= price:
                errors.append('Sale price must be less than regular price')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    @staticmethod
    def validate_variant_data(variants: List[Dict]) -> Dict:
        """
        Validate variant data before product creation.

        Args:
            variants: List of variant dictionaries

        Returns:
            dict: {
                'valid': bool,
                'errors': List[str]
            }
        """
        errors = []

        if not variants:
            return {'valid': True, 'errors': []}

        # Check for duplicate SKUs
        skus = [v.get('sku') for v in variants if v.get('sku')]
        if len(skus) != len(set(skus)):
            errors.append('Variant SKUs must be unique')

        # Validate each variant
        for i, variant in enumerate(variants):
            prefix = f'Variant {i + 1}: '

            if not variant.get('sku'):
                errors.append(f'{prefix}SKU is required')
            elif len(variant.get('sku', '')) > 100:
                errors.append(f'{prefix}SKU must be 100 characters or less')

            if not variant.get('size'):
                errors.append(f'{prefix}Size is required')

            if not variant.get('color'):
                errors.append(f'{prefix}Color is required')

            initial_qty = variant.get('initial_quantity', 0)
            if not isinstance(initial_qty, int) or initial_qty < 0:
                errors.append(f'{prefix}Initial quantity must be a non-negative integer')

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
