"""
Seed script for Happy Place Boutique - Products with Variants (V3.2)
Creates sample products, variants, and inventory for testing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Product, ProductVariant, ProductImage, Inventory, Category
from datetime import datetime, timedelta

def seed_products_with_variants():
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Happy Place Boutique - Products & Variants Seeding")
        print("=" * 60)
        print()

        # Get categories
        womens_tops = Category.query.filter_by(slug='women-tops').first()
        womens_bottoms = Category.query.filter_by(slug='women-bottoms').first()
        womens_dresses = Category.query.filter_by(slug='women-dresses').first()
        maternity_tops = Category.query.filter_by(slug='maternity-tops').first()
        maternity_bottoms = Category.query.filter_by(slug='maternity-bottoms').first()
        maternity_dresses = Category.query.filter_by(slug='maternity-dresses').first()

        print("=== Creating Products ===")

        # Product 1: Classic Cotton T-Shirt (Regular Price)
        product1 = Product(
            name="Classic Cotton T-Shirt",
            slug="classic-cotton-tshirt",
            description="Soft, breathable cotton t-shirt perfect for everyday wear. Made from 100% organic cotton with a relaxed fit.",
            price=2999.00,  # KSh 2,999
            category_id=womens_tops.id if womens_tops else None,
            is_active=True,
            weight=0.2
        )
        db.session.add(product1)
        db.session.flush()

        # Add image
        img1 = ProductImage(
            product_id=product1.id,
            image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=600&fit=crop",
            alt_text="Classic Cotton T-Shirt",
            is_primary=True
        )
        db.session.add(img1)

        # Create variants for Product 1
        sizes = ['XS', 'S', 'M', 'L', 'XL']
        colors = ['White', 'Black', 'Navy', 'Pink']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product1.id,
                    sku=f"COTTEE-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                # Add inventory
                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=50 if size in ['S', 'M', 'L'] else 30,
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product1.name} (20 variants)")

        # Product 2: Elegant Blouse (ON SALE)
        product2 = Product(
            name="Elegant Silk Blouse",
            slug="elegant-silk-blouse",
            description="Sophisticated silk blouse perfect for work or special occasions. Features pearl buttons and French cuffs.",
            price=4999.00,  # Original: KSh 4,999
            sale_price=3499.00,  # Sale: KSh 3,499 (30% off)
            category_id=womens_tops.id if womens_tops else None,
            is_active=True,
            weight=0.15
        )
        db.session.add(product2)
        db.session.flush()

        img2 = ProductImage(
            product_id=product2.id,
            image_url="https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=400&h=600&fit=crop",
            alt_text="Elegant Silk Blouse",
            is_primary=True
        )
        db.session.add(img2)

        sizes = ['XS', 'S', 'M', 'L', 'XL']
        colors = ['White', 'Cream', 'Light Blue']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product2.id,
                    sku=f"SILKBL-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=8 if size == 'M' else 25,  # Low stock on M
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product2.name} (15 variants) - ON SALE 30% OFF")

        # Product 3: Skinny Jeans (CLEARANCE - FINAL SALE)
        product3 = Product(
            name="High-Waisted Skinny Jeans",
            slug="high-waisted-skinny-jeans",
            description="Flattering high-waisted skinny jeans with stretch fabric. Perfect fit and all-day comfort.",
            price=6999.00,  # Original: KSh 6,999
            sale_price=2999.00,  # Clearance: KSh 2,999 (57% off)
            is_clearance=True,
            category_id=womens_bottoms.id if womens_bottoms else None,
            is_active=True,
            weight=0.5
        )
        db.session.add(product3)
        db.session.flush()

        img3 = ProductImage(
            product_id=product3.id,
            image_url="https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=600&fit=crop",
            alt_text="High-Waisted Skinny Jeans",
            is_primary=True
        )
        db.session.add(img3)

        sizes = ['24', '26', '28', '30', '32']
        colors = ['Dark Blue', 'Black']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product3.id,
                    sku=f"SKJEAN-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=15,
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product3.name} (10 variants) - CLEARANCE (FINAL SALE)")

        # Product 4: Summer Maxi Dress (Regular Price)
        product4 = Product(
            name="Flowy Summer Maxi Dress",
            slug="flowy-summer-maxi-dress",
            description="Beautiful flowing maxi dress perfect for summer evenings. Lightweight and breathable fabric.",
            price=7999.00,  # KSh 7,999
            category_id=womens_dresses.id if womens_dresses else None,
            is_active=True,
            weight=0.3
        )
        db.session.add(product4)
        db.session.flush()

        img4 = ProductImage(
            product_id=product4.id,
            image_url="https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=600&fit=crop",
            alt_text="Flowy Summer Maxi Dress",
            is_primary=True
        )
        db.session.add(img4)

        sizes = ['XS', 'S', 'M', 'L', 'XL']
        colors = ['Floral Print', 'Solid Navy', 'Red']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product4.id,
                    sku=f"MAXIDR-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=20,
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product4.name} (15 variants)")

        # Product 5: Maternity Basic Tee (Regular Price)
        product5 = Product(
            name="Maternity Essential T-Shirt",
            slug="maternity-essential-tshirt",
            description="Soft stretchy tee that grows with your bump. Made with bamboo blend fabric for ultimate comfort.",
            price=3499.00,  # KSh 3,499
            category_id=maternity_tops.id if maternity_tops else None,
            is_active=True,
            weight=0.2
        )
        db.session.add(product5)
        db.session.flush()

        img5 = ProductImage(
            product_id=product5.id,
            image_url="https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=400&h=600&fit=crop",
            alt_text="Maternity Essential T-Shirt",
            is_primary=True
        )
        db.session.add(img5)

        sizes = ['S', 'M', 'L', 'XL']
        colors = ['White', 'Black', 'Gray', 'Pink']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product5.id,
                    sku=f"MATTEE-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=35,
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product5.name} (16 variants)")

        # Product 6: Maternity Jeans (ON SALE)
        product6 = Product(
            name="Maternity Comfort Jeans",
            slug="maternity-comfort-jeans",
            description="Supportive maternity jeans with over-bump panel. Premium denim with 4-way stretch.",
            price=8999.00,  # Original: KSh 8,999
            sale_price=6299.00,  # Sale: KSh 6,299 (30% off)
            category_id=maternity_bottoms.id if maternity_bottoms else None,
            is_active=True,
            weight=0.6
        )
        db.session.add(product6)
        db.session.flush()

        img6 = ProductImage(
            product_id=product6.id,
            image_url="https://images.unsplash.com/photo-1582418702059-97ebafb35d09?w=400&h=600&fit=crop",
            alt_text="Maternity Comfort Jeans",
            is_primary=True
        )
        db.session.add(img6)

        sizes = ['XS', 'S', 'M', 'L', 'XL']
        colors = ['Dark Wash', 'Light Wash']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product6.id,
                    sku=f"MATJEA-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=6 if size == 'L' else 18,  # Low stock on L
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product6.name} (10 variants) - ON SALE 30% OFF")

        # Product 7: Maternity Dress (CLEARANCE - FINAL SALE)
        product7 = Product(
            name="Maternity Wrap Dress",
            slug="maternity-wrap-dress",
            description="Elegant wrap dress with adjustable tie. Flattering silhouette for all trimesters.",
            price=9999.00,  # Original: KSh 9,999
            sale_price=3999.00,  # Clearance: KSh 3,999 (60% off)
            is_clearance=True,
            category_id=maternity_dresses.id if maternity_dresses else None,
            is_active=True,
            weight=0.4
        )
        db.session.add(product7)
        db.session.flush()

        img7 = ProductImage(
            product_id=product7.id,
            image_url="https://images.unsplash.com/photo-1596783074918-c84cb06531ca?w=400&h=600&fit=crop",
            alt_text="Maternity Wrap Dress",
            is_primary=True
        )
        db.session.add(img7)

        sizes = ['S', 'M', 'L', 'XL']
        colors = ['Navy', 'Burgundy', 'Forest Green']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product7.id,
                    sku=f"MATWRAP-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=12,
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product7.name} (12 variants) - CLEARANCE (FINAL SALE)")

        # Product 8: Yoga Pants (Regular Price, Some Out of Stock)
        product8 = Product(
            name="High-Performance Yoga Pants",
            slug="high-performance-yoga-pants",
            description="Premium yoga pants with moisture-wicking fabric. Perfect for workouts or casual wear.",
            price=4499.00,  # KSh 4,499
            category_id=womens_bottoms.id if womens_bottoms else None,
            is_active=True,
            weight=0.3
        )
        db.session.add(product8)
        db.session.flush()

        img8 = ProductImage(
            product_id=product8.id,
            image_url="https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400&h=600&fit=crop",
            alt_text="High-Performance Yoga Pants",
            is_primary=True
        )
        db.session.add(img8)

        sizes = ['XS', 'S', 'M', 'L', 'XL']
        colors = ['Black', 'Gray', 'Navy']
        for size in sizes:
            for color in colors:
                variant = ProductVariant(
                    product_id=product8.id,
                    sku=f"YOGAPANT-{size}-{color[:3].upper()}",
                    size=size,
                    color=color,
                    is_active=True
                )
                db.session.add(variant)
                db.session.flush()

                # Some variants out of stock
                qty = 0 if (size == 'S' and color == 'Black') else 30
                inventory = Inventory(
                    variant_id=variant.id,
                    quantity=qty,
                    reserved_quantity=0,
                    low_stock_threshold=10
                )
                db.session.add(inventory)

        print(f"✓ Created: {product8.name} (15 variants) - Some variants out of stock")

        # Commit all changes
        db.session.commit()

        print()
        print("=" * 60)
        print("✅ PRODUCTS SEEDING COMPLETE!")
        print("=" * 60)
        print()
        print("Seeded data:")
        print("  - 8 products")
        print("  - 113 product variants total")
        print("  - 113 inventory records")
        print("  - 8 product images")
        print()
        print("Product Types:")
        print("  - Regular Price: 4 products")
        print("  - On Sale (FINAL SALE): 2 products")
        print("  - Clearance (FINAL SALE): 2 products")
        print()

if __name__ == '__main__':
    seed_products_with_variants()
