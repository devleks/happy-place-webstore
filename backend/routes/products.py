"""
Products API routes with variant support.
"""

from flask import request, jsonify
from routes import api
from models import db, Product, ProductImage, ProductVariant, Inventory, Category, CategoryClosure
from middleware import manager_required
from sqlalchemy import and_
from logging_utils import get_logger, safe_auth_context
from flask_jwt_extended import get_jwt_identity

# Initialize logger
logger = get_logger(__name__)


@api.route('/products', methods=['GET'])
def get_products():
    """
    Get all products with pagination and filtering.

    Query params:
    - page (int, default: 1)
    - per_page (int, default: 20)
    - category (str): slug of specific category
    - parent_category (str): slug of parent category (returns all descendants)
    - category_id (int)
    - featured (boolean)
    - on_sale (boolean)
    """
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    query = Product.query.filter_by(is_active=True)

    # Apply filters
    # Handle parent category (e.g., women-clothing or maternity-clothing)
    if request.args.get('parent_category'):
        parent_slug = request.args['parent_category']
        parent_cat = Category.query.filter_by(slug=parent_slug).first()
        if parent_cat:
            # Get all descendant category IDs using closure table
            descendant_ids = db.session.query(CategoryClosure.descendant_id).filter(
                CategoryClosure.ancestor_id == parent_cat.id
            ).all()
            category_ids = [parent_cat.id] + [d[0] for d in descendant_ids]
            query = query.filter(Product.category_id.in_(category_ids))

    # Handle specific category (subcategory like women-tops)
    elif request.args.get('category'):
        cat_slug = request.args['category']
        cat = Category.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    elif request.args.get('category_id'):
        query = query.filter_by(category_id=int(request.args['category_id']))

    if request.args.get('featured', '').lower() == 'true':
        query = query.filter_by(is_featured=True)

    if request.args.get('on_sale', '').lower() == 'true':
        query = query.filter(Product.sale_price.isnot(None))

    # Add search filter for product name and SKU
    if request.args.get('search'):
        search_term = f"%{request.args['search']}%"
        query = query.outerjoin(ProductVariant).filter(
            db.or_(
                Product.name.ilike(search_term),
                ProductVariant.sku.ilike(search_term)
            )
        ).distinct()

    # Paginate
    products_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    products_list = []
    for product in products_paginated.items:
        # Get primary image
        primary_image = None
        if product.images:
            for img in product.images:
                if img.is_primary:
                    primary_image = img.image_url
                    break
            if not primary_image and product.images:
                primary_image = product.images[0].image_url

        # Get available colors from variants
        available_colors = list(set([v.color for v in product.variants if v.is_active])) if product.variants else []

        products_list.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'sale_price': float(product.sale_price) if product.sale_price else None,
            'is_on_sale': product.sale_price and product.sale_price < product.price,
            'is_clearance': product.is_clearance if hasattr(product, 'is_clearance') else False,
            'category': product.category.name if product.category else None,
            'category_name': product.category.name if product.category else None,
            'is_featured': product.is_featured,
            'variants_count': len(product.variants) if hasattr(product, 'variants') else 0,
            'image_url': primary_image,
            'available_colors': available_colors
        })

    return jsonify({
        'products': products_list,
        'total': products_paginated.total,
        'page': page,
        'per_page': per_page,
        'total_pages': products_paginated.pages
    }), 200


@api.route('/products/<slug>', methods=['GET'])
def get_product_by_slug(slug):
    """
    Get product details by slug (with variants and images).
    """
    product = Product.query.filter_by(slug=slug, is_active=True).first()

    if not product:
        return jsonify({
            'error': 'Product not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    # Get all variants with inventory
    variants_list = []
    available_sizes = set()
    available_colors = set()

    for variant in product.variants:
        if variant.is_active:
            available_sizes.add(variant.size)
            available_colors.add(variant.color)

            inventory_data = {}
            if variant.inventory:
                available_qty = variant.inventory.quantity - variant.inventory.reserved_quantity
                inventory_data = {
                    'quantity': variant.inventory.quantity,
                    'available_quantity': available_qty,
                    'is_low_stock': variant.inventory.is_low_stock,
                    'is_out_of_stock': available_qty == 0
                }

            variants_list.append({
                'id': variant.id,
                'sku': variant.sku,
                'size': variant.size,
                'color': variant.color,
                'is_active': variant.is_active,
                'inventory': inventory_data
            })

    # Get images
    images_list = []
    for image in product.images:
        images_list.append({
            'id': image.id,
            'image_url': image.image_url,
            'alt_text': image.alt_text,
            'is_primary': image.is_primary
        })

    return jsonify({
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'price': float(product.price),
        'sale_price': float(product.sale_price) if product.sale_price else None,
        'category_id': product.category_id,
        'category_name': product.category.name if product.category else None,
        'sku': product.sku,
        'is_clearance': product.is_clearance if hasattr(product, 'is_clearance') else False,
        'weight': float(product.weight) if hasattr(product, 'weight') and product.weight else None,
        'is_active': product.is_active,
        'is_featured': product.is_featured,
        'is_on_sale': product.sale_price and product.sale_price < product.price,
        'can_be_returned': not (product.is_clearance if hasattr(product, 'is_clearance') else False) and not (product.sale_price and product.sale_price < product.price),
        'images': images_list,
        'variants': variants_list,
        'available_sizes': sorted(list(available_sizes)),
        'available_colors': sorted(list(available_colors)),
        'created_at': product.created_at.isoformat() if product.created_at else None,
        'updated_at': product.updated_at.isoformat() if product.updated_at else None
    }), 200


@api.route('/products/with-variants', methods=['GET'])
def get_products_with_variants():
    """
    Get all products with full variant details and stock for POS.
    Includes: variants, prices, stock levels, SKUs
    """
    try:
        products = Product.query.filter_by(is_active=True).all()

        products_list = []
        for product in products:
            # Get all active variants with inventory
            variants_list = []
            for variant in product.variants:
                if variant.is_active:
                    inventory_data = {
                        'quantity': 0,
                        'available': 0
                    }

                    if variant.inventory:
                        available = variant.inventory.quantity - variant.inventory.reserved_quantity
                        inventory_data = {
                            'quantity': variant.inventory.quantity,
                            'available': available
                        }

                    variants_list.append({
                        'id': variant.id,
                        'sku': variant.sku,
                        'size': variant.size,
                        'color': variant.color,
                        'price': float(product.sale_price) if product.sale_price else float(product.price),
                        'pos_stock': inventory_data['available']
                    })

            # Get primary image
            primary_image = None
            if product.images:
                for img in product.images:
                    if img.is_primary:
                        primary_image = img.image_url
                        break
                if not primary_image and product.images:
                    primary_image = product.images[0].image_url

            products_list.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'category': product.category.name if product.category else None,
                'price': float(product.price),
                'sale_price': float(product.sale_price) if product.sale_price else None,
                'image_url': primary_image,
                'variants': variants_list
            })

        return jsonify({
            'success': True,
            'products': products_list,
            'count': len(products_list)
        }), 200

    except Exception as e:
        logger.error(
            "Products with variants operation failed",
            extra={"context": safe_auth_context(
                user_type='public',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )},
            exc_info=True,
        )
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@api.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """
    Get product details by ID (with variants and images).
    """
    product = Product.query.get(product_id)

    if not product or not product.is_active:
        return jsonify({
            'error': 'Product not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    # Redirect to slug endpoint for consistency
    return get_product_by_slug(product.slug)


@api.route('/admin/products', methods=['POST'])
@manager_required
def create_product(current_employee):
    """
    Create a new product with variants.
    Requires manager or admin role.
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ['name', 'slug', 'price', 'category_id', 'sku']
    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'code': 'VALIDATION_ERROR',
            'details': {'missing_fields': missing_fields}
        }), 400

    # Check if slug already exists
    existing_product = Product.query.filter_by(slug=data['slug']).first()
    if existing_product:
        return jsonify({
            'error': 'Product slug already exists',
            'code': 'DUPLICATE_RESOURCE'
        }), 409

    try:
        # Create product
        product = Product(
            name=data['name'],
            slug=data['slug'],
            description=data.get('description'),
            price=data['price'],
            sale_price=data.get('sale_price'),
            category_id=data['category_id'],
            sku=data['sku'],
            is_active=data.get('is_active', True),
            is_featured=data.get('is_featured', False)
        )

        # Add optional fields
        if 'is_clearance' in data:
            product.is_clearance = data['is_clearance']
        if 'weight' in data:
            product.weight = data['weight']

        db.session.add(product)
        db.session.flush()  # Get product ID

        # Create variants if provided
        variants_created = 0
        total_inventory = 0

        if data.get('variants'):
            for variant_data in data['variants']:
                variant = ProductVariant(
                    product_id=product.id,
                    sku=variant_data['sku'],
                    size=variant_data['size'],
                    color=variant_data['color'],
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                # Create inventory
                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=variant_data.get('initial_quantity', 0),
                    reserved_quantity=0
                )
                db.session.add(inventory)

                variants_created += 1
                total_inventory += variant_data.get('initial_quantity', 0)

        db.session.commit()

        return jsonify({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'variants_created': variants_created,
            'total_inventory': total_inventory,
            'message': 'Product and variants created successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(
            "Create product operation failed",
            extra={"context": safe_auth_context(
                user_type='employee',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                extra={"employee_id": int(get_jwt_identity()) if get_jwt_identity() else None}
            )},
            exc_info=True,
        )
        return jsonify({
            'error': 'Failed to create product',
            'code': 'INTERNAL_ERROR'
        }), 500
