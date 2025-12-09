#!/usr/bin/env python
"""
Seed Data for Extended Tables

Creates initial data for:
1. Category hierarchy (Women Clothing, Maternity Clothing + subcategories)
2. Category closure table (for fast hierarchical queries)
3. Shipping methods (Nairobi free, Upcountry variable)
4. Sample promotions (referral code 5%)
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import Config
from extensions import db


def create_app():
    """Create Flask app for database access"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def seed_categories_with_closure():
    """
    Seed category hierarchy and closure table.

    Category Structure:
    - Women Clothing (id=1)
      - Tops (id=2)
      - Bottoms (id=3)
      - Dresses (id=4)
      - Accessories (id=5)
    - Maternity Clothing (id=6)
      - Maternity Tops (id=7)
      - Maternity Bottoms (id=8)
      - Maternity Dresses (id=9)
    """
    from models.database_models import Category
    from models.extended_models import CategoryClosure

    print("\n=== Seeding Categories ===")

    # Delete existing categories and closure
    CategoryClosure.query.delete()
    Category.query.delete()
    db.session.commit()

    categories = []

    # Parent Categories
    women = Category(
        id=1,
        name="Women Clothing",
        slug="women-clothing",
        description="Fashion and clothing for women",
        parent_id=None,
        is_active=True
    )
    categories.append(women)

    maternity = Category(
        id=6,
        name="Maternity Clothing",
        slug="maternity-clothing",
        description="Comfortable and stylish maternity wear",
        parent_id=None,
        is_active=True
    )
    categories.append(maternity)

    # Women Clothing Subcategories
    women_tops = Category(
        id=2,
        name="Tops",
        slug="women-tops",
        description="Blouses, shirts, and tops for women",
        parent_id=1,
        is_active=True
    )
    categories.append(women_tops)

    women_bottoms = Category(
        id=3,
        name="Bottoms",
        slug="women-bottoms",
        description="Pants, skirts, and shorts for women",
        parent_id=1,
        is_active=True
    )
    categories.append(women_bottoms)

    women_dresses = Category(
        id=4,
        name="Dresses",
        slug="women-dresses",
        description="Beautiful dresses for all occasions",
        parent_id=1,
        is_active=True
    )
    categories.append(women_dresses)

    women_accessories = Category(
        id=5,
        name="Accessories",
        slug="women-accessories",
        description="Accessories to complete your look",
        parent_id=1,
        is_active=True
    )
    categories.append(women_accessories)

    # Maternity Clothing Subcategories
    maternity_tops = Category(
        id=7,
        name="Maternity Tops",
        slug="maternity-tops",
        description="Comfortable tops for expecting mothers",
        parent_id=6,
        is_active=True
    )
    categories.append(maternity_tops)

    maternity_bottoms = Category(
        id=8,
        name="Maternity Bottoms",
        slug="maternity-bottoms",
        description="Maternity pants and leggings",
        parent_id=6,
        is_active=True
    )
    categories.append(maternity_bottoms)

    maternity_dresses = Category(
        id=9,
        name="Maternity Dresses",
        slug="maternity-dresses",
        description="Elegant maternity dresses",
        parent_id=6,
        is_active=True
    )
    categories.append(maternity_dresses)

    # Add all categories
    db.session.add_all(categories)
    db.session.flush()  # Get IDs without committing

    print(f"Created {len(categories)} categories")

    # Build closure table
    print("\n=== Building Category Closure Table ===")
    closure_entries = []

    # For each category, create closure entries
    for category in categories:
        # Self-reference (depth 0)
        closure_entries.append(CategoryClosure(
            ancestor_id=category.id,
            descendant_id=category.id,
            depth=0
        ))

        # If category has parent, create ancestor paths
        if category.parent_id:
            parent = next((c for c in categories if c.id == category.parent_id), None)
            if parent:
                # Direct parent (depth 1)
                closure_entries.append(CategoryClosure(
                    ancestor_id=parent.id,
                    descendant_id=category.id,
                    depth=1
                ))

                # Grandparents (depth 2+) - not needed in this 2-level hierarchy
                # but would be added here for deeper trees

    db.session.add_all(closure_entries)
    db.session.commit()

    print(f"Created {len(closure_entries)} closure table entries")
    print("\nCategory Hierarchy:")
    print("- Women Clothing")
    print("  - Tops")
    print("  - Bottoms")
    print("  - Dresses")
    print("  - Accessories")
    print("- Maternity Clothing")
    print("  - Maternity Tops")
    print("  - Maternity Bottoms")
    print("  - Maternity Dresses")


def seed_shipping_methods():
    """
    Seed shipping methods.

    Business Rules:
    - Nairobi: Free shipping
    - Outside Nairobi: Variable cost
    """
    from models.extended_models import ShippingMethod

    print("\n=== Seeding Shipping Methods ===")

    ShippingMethod.query.delete()
    db.session.commit()

    shipping_methods = []

    # Nairobi Free Delivery
    nairobi_free = ShippingMethod(
        name="Nairobi Free Delivery",
        description="Free delivery within Nairobi (2-3 business days)",
        base_cost=0,
        cost_per_kg=0,
        estimated_days_min=2,
        estimated_days_max=3,
        available_for_nairobi=True,
        available_outside_nairobi=False,
        is_active=True,
        display_order=1
    )
    shipping_methods.append(nairobi_free)

    # Upcountry Standard Delivery
    upcountry_standard = ShippingMethod(
        name="Upcountry Standard Delivery",
        description="Delivery outside Nairobi (3-7 business days)",
        base_cost=300,  # Base KSh 300
        cost_per_kg=50,  # Additional KSh 50 per kg
        estimated_days_min=3,
        estimated_days_max=7,
        available_for_nairobi=False,
        available_outside_nairobi=True,
        free_shipping_threshold=5000,  # Free if order > KSh 5000
        is_active=True,
        display_order=2
    )
    shipping_methods.append(upcountry_standard)

    # Store Pickup (Free)
    store_pickup = ShippingMethod(
        name="Store Pickup",
        description="Pickup at our Bethel Business Centre location (Same day)",
        base_cost=0,
        cost_per_kg=0,
        estimated_days_min=0,
        estimated_days_max=0,
        available_for_nairobi=True,
        available_outside_nairobi=False,
        is_active=True,
        display_order=3
    )
    shipping_methods.append(store_pickup)

    db.session.add_all(shipping_methods)
    db.session.commit()

    print(f"Created {len(shipping_methods)} shipping methods:")
    for method in shipping_methods:
        print(f"  - {method.name} (KSh {method.base_cost})")


def seed_promotions():
    """
    Seed sample promotions.

    Business Rules:
    - Referral codes: 5% discount
    """
    from models.extended_models import Promotion

    print("\n=== Seeding Promotions ===")

    Promotion.query.delete()
    db.session.commit()

    promotions = []

    # Referral Code (5% discount)
    referral = Promotion(
        code="REFER5",
        name="Referral Discount",
        description="5% discount for referrals",
        discount_type='percentage',
        discount_value=5,
        applies_to='all',
        usage_per_customer=1,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=365),  # Valid for 1 year
        is_active=True
    )
    promotions.append(referral)

    # Welcome Discount (10% for first purchase)
    welcome = Promotion(
        code="WELCOME10",
        name="Welcome Discount",
        description="10% off your first purchase",
        discount_type='percentage',
        discount_value=10,
        maximum_discount_amount=500,  # Max KSh 500 discount
        applies_to='all',
        usage_per_customer=1,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=365),
        is_active=True
    )
    promotions.append(welcome)

    # Free Shipping Promo
    free_shipping = Promotion(
        code="FREESHIP",
        name="Free Shipping",
        description="Free shipping on all orders",
        discount_type='free_shipping',
        discount_value=0,
        minimum_order_amount=2000,  # On orders > KSh 2000
        applies_to='all',
        usage_per_customer=1,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    promotions.append(free_shipping)

    db.session.add_all(promotions)
    db.session.commit()

    print(f"Created {len(promotions)} promotions:")
    for promo in promotions:
        print(f"  - {promo.code}: {promo.name} ({promo.discount_value}% off)")


def main():
    """Seed all extended data"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Happy Place Boutique - Extended Data Seeding")
        print("=" * 60)

        try:
            seed_categories_with_closure()
            seed_shipping_methods()
            seed_promotions()

            print("\n" + "=" * 60)
            print("✅ SEEDING COMPLETE!")
            print("=" * 60)
            print("\nSeeded data:")
            print("  - 9 categories with hierarchical closure table")
            print("  - 3 shipping methods (Nairobi free, Upcountry, Store pickup)")
            print("  - 3 sample promotions (Referral 5%, Welcome 10%, Free shipping)")

        except Exception as e:
            print(f"\n❌ SEEDING FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    main()
