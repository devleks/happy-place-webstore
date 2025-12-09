"""
Categories API routes with closure table support.
Handles hierarchical category queries using O(1) lookups.
"""

from flask import request, jsonify
from sqlalchemy import and_
from routes import api
from models import db, Category, CategoryClosure, Product
from logging_utils import get_logger, safe_auth_context

# Initialize logger
logger = get_logger(__name__)


@api.route('/categories/tree', methods=['GET'])
def get_category_tree():
    """
    Get complete category tree with subcategories.
    Uses closure table for efficient hierarchical queries.
    """
    # Get all root categories (no parent)
    root_categories = Category.query.filter_by(parent_id=None, is_active=True).all()

    def build_tree(category):
        """Recursively build category tree."""
        # Get direct children using closure table
        children = db.session.query(Category).join(
            CategoryClosure,
            and_(
                CategoryClosure.descendant_id == Category.id,
                CategoryClosure.ancestor_id == category.id,
                CategoryClosure.depth == 1
            )
        ).filter(Category.is_active == True).all()

        return {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'parent_id': category.parent_id,
            'is_active': category.is_active,
            'subcategories': [build_tree(child) for child in children]
        }

    categories_tree = [build_tree(cat) for cat in root_categories]

    return jsonify({
        'categories': categories_tree
    }), 200


@api.route('/categories/<int:category_id>/descendants', methods=['GET'])
def get_category_descendants(category_id):
    """
    Get all descendants of a category (recursive).
    Uses closure table for O(1) query.
    """
    category = Category.query.get(category_id)

    if not category:
        return jsonify({
            'error': 'Category not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    # Get all descendants using closure table
    descendants = db.session.query(Category, CategoryClosure.depth).join(
        CategoryClosure,
        and_(
            CategoryClosure.descendant_id == Category.id,
            CategoryClosure.ancestor_id == category_id,
            CategoryClosure.depth > 0  # Exclude self
        )
    ).filter(Category.is_active == True).all()

    return jsonify({
        'category_id': category.id,
        'category_name': category.name,
        'descendants': [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'depth': depth
            }
            for cat, depth in descendants
        ],
        'total_descendants': len(descendants)
    }), 200


@api.route('/categories/<int:category_id>/products', methods=['GET'])
def get_category_products(category_id):
    """
    Get all products in a category (including subcategories).
    Uses closure table for efficient hierarchical product lookup.

    Query params:
    - include_subcategories (boolean, default: true)
    - page (int, default: 1)
    - per_page (int, default: 20)
    """
    category = Category.query.get(category_id)

    if not category:
        return jsonify({
            'error': 'Category not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404

    include_subcategories = request.args.get('include_subcategories', 'true').lower() == 'true'
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    if include_subcategories:
        # Get category IDs including descendants
        category_ids = [category_id]

        descendants = db.session.query(CategoryClosure.descendant_id).filter(
            CategoryClosure.ancestor_id == category_id,
            CategoryClosure.depth > 0
        ).all()

        category_ids.extend([desc[0] for desc in descendants])

        # Get subcategory names for response
        subcategories = db.session.query(Category.name).filter(
            Category.id.in_(category_ids),
            Category.id != category_id
        ).all()
        subcategories_included = [cat[0] for cat in subcategories]

        # Query products from all categories
        products_query = Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.is_active == True
        )
    else:
        # Query products from this category only
        products_query = Product.query.filter_by(
            category_id=category_id,
            is_active=True
        )
        subcategories_included = []

    # Paginate results
    products_paginated = products_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    products_list = []
    for product in products_paginated.items:
        # Count variants
        variants_count = len(product.variants) if hasattr(product, 'variants') else 0

        products_list.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'sale_price': float(product.sale_price) if product.sale_price else None,
            'category_id': product.category_id,
            'category_name': product.category.name if product.category else None,
            'variants_count': variants_count,
            'is_on_sale': product.sale_price and product.sale_price < product.price,
            'is_clearance': product.is_clearance if hasattr(product, 'is_clearance') else False
        })

    return jsonify({
        'category_id': category.id,
        'category_name': category.name,
        'include_subcategories': include_subcategories,
        'products': products_list,
        'total': products_paginated.total,
        'page': page,
        'per_page': per_page,
        'total_pages': products_paginated.pages,
        'subcategories_included': subcategories_included if include_subcategories else []
    }), 200


@api.route('/categories', methods=['GET'])
def get_all_categories():
    """
    Get all active categories (flat list).
    """
    categories = Category.query.filter_by(is_active=True).all()

    return jsonify({
        'categories': [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'parent_id': cat.parent_id,
                'is_active': cat.is_active
            }
            for cat in categories
        ]
    }), 200
