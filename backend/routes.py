from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Product, Category, Inventory, StoreLocation
from sqlalchemy import or_
import json

api = Blueprint('api', __name__)

# Authentication Routes
@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(
        email=data['email'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', '')
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id)

    return jsonify({
        'message': 'User registered successfully',
        'access_token': access_token,
        'user': user.to_dict()
    }), 201

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=user.id)

    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@api.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict()), 200

# Category Routes
@api.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([cat.to_dict() for cat in categories]), 200

@api.route('/categories/<slug>', methods=['GET'])
def get_category(slug):
    category = Category.query.filter_by(slug=slug).first()

    if not category:
        return jsonify({'error': 'Category not found'}), 404

    return jsonify(category.to_dict()), 200

# Product Routes
@api.route('/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = Product.query.filter_by(is_active=True)

    if category:
        # Support broader category filtering (e.g., "womens" matches all "womens-*" categories)
        if category in ['womens', 'maternity']:
            categories = Category.query.filter(Category.slug.like(f'{category}%')).all()
            if categories:
                category_ids = [cat.id for cat in categories]
                query = query.filter(Product.category_id.in_(category_ids))
        else:
            # Exact match for specific categories
            cat = Category.query.filter_by(slug=category).first()
            if cat:
                query = query.filter_by(category_id=cat.id)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'products': [product.to_dict() for product in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@api.route('/products/<slug>', methods=['GET'])
def get_product(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify(product.to_dict(include_inventory=True)), 200

# Inventory Routes
@api.route('/inventory/product/<int:product_id>', methods=['GET'])
def get_product_inventory(product_id):
    inventory_items = Inventory.query.filter_by(product_id=product_id).all()

    if not inventory_items:
        return jsonify({'error': 'No inventory found for this product'}), 404

    return jsonify([item.to_dict() for item in inventory_items]), 200

# Store Location Routes
@api.route('/store-locations', methods=['GET'])
def get_store_locations():
    locations = StoreLocation.query.filter_by(is_active=True).all()
    return jsonify([location.to_dict() for location in locations]), 200

@api.route('/store-locations/<int:location_id>', methods=['GET'])
def get_store_location(location_id):
    location = StoreLocation.query.get(location_id)

    if not location or not location.is_active:
        return jsonify({'error': 'Store location not found'}), 404

    return jsonify(location.to_dict()), 200

# Health check
@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200
