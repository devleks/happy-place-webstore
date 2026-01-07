"""
Seed Products Database - Happy Place Boutique
Creates sample products for women's clothing and maternity wear with stock images
"""

from app import create_app
from models.database_models import db, Category, Product, ProductImage, Inventory
from models.extended_models import ProductVariant
from datetime import datetime
import random

# Free stock image sources for product images
# Using placeholder service for demonstration
def get_product_image(category, index):
    """Generate placeholder image URL for products"""
    # Using picsum.photos for random high-quality images
    seed = f"{category}-{index}"
    return f"https://picsum.photos/seed/{seed}/800/1000"


# Product data organized by category
PRODUCTS_DATA = {
    "Women's Tops": [
        {
            'name': 'Classic White Cotton Blouse',
            'description': 'Elegant white cotton blouse perfect for office or casual wear. Features button-down front and long sleeves.',
            'price': 2499.00,
            'sale_price': None,
            'sku_prefix': 'WTP-BLS',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['White', 'Cream', 'Light Blue'],
            'weight': 0.3,
            'is_featured': True
        },
        {
            'name': 'Floral Print Chiffon Top',
            'description': 'Lightweight chiffon top with beautiful floral print. Perfect for spring and summer.',
            'price': 2199.00,
            'sale_price': 1899.00,
            'sku_prefix': 'WTP-FLR',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Pink Floral', 'Blue Floral', 'Purple Floral'],
            'weight': 0.2,
            'is_featured': False
        },
        {
            'name': 'Striped V-Neck T-Shirt',
            'description': 'Casual striped t-shirt with flattering v-neck design. Made from soft cotton blend.',
            'price': 1599.00,
            'sale_price': None,
            'sku_prefix': 'WTP-VNK',
            'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['Navy/White', 'Black/White', 'Red/White'],
            'weight': 0.25,
            'is_featured': False
        },
        {
            'name': 'Silk Camisole Top',
            'description': 'Luxurious silk camisole with delicate lace trim. Perfect for layering or wearing alone.',
            'price': 3299.00,
            'sale_price': None,
            'sku_prefix': 'WTP-CMI',
            'sizes': ['XS', 'S', 'M', 'L'],
            'colors': ['Black', 'Champagne', 'Rose'],
            'weight': 0.15,
            'is_featured': True
        },
        {
            'name': 'Oversized Linen Shirt',
            'description': 'Relaxed fit linen shirt for effortless style. Breathable and comfortable.',
            'price': 2799.00,
            'sale_price': 2299.00,
            'sku_prefix': 'WTP-LIN',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Natural', 'White', 'Sage Green'],
            'weight': 0.35,
            'is_featured': False
        }
    ],

    "Women's Bottoms": [
        {
            'name': 'High-Waist Skinny Jeans',
            'description': 'Classic skinny jeans with high waist and stretch denim. Flattering fit for all body types.',
            'price': 3499.00,
            'sale_price': None,
            'sku_prefix': 'WBT-SKJ',
            'sizes': ['24', '26', '28', '30', '32', '34'],
            'colors': ['Dark Wash', 'Light Wash', 'Black'],
            'weight': 0.6,
            'is_featured': True
        },
        {
            'name': 'Wide Leg Palazzo Pants',
            'description': 'Flowing palazzo pants for elegant comfort. Perfect for work or evening wear.',
            'price': 2999.00,
            'sale_price': 2499.00,
            'sku_prefix': 'WBT-PLZ',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Black', 'Navy', 'Burgundy', 'Cream'],
            'weight': 0.4,
            'is_featured': False
        },
        {
            'name': 'Pleated Midi Skirt',
            'description': 'Feminine pleated midi skirt with elastic waist. Versatile and easy to style.',
            'price': 2499.00,
            'sale_price': None,
            'sku_prefix': 'WBT-PLT',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Blush Pink', 'Emerald', 'Camel', 'Black'],
            'weight': 0.35,
            'is_featured': True
        },
        {
            'name': 'Tailored Ankle Pants',
            'description': 'Professional tailored pants with ankle length. Perfect for office wear.',
            'price': 3199.00,
            'sale_price': None,
            'sku_prefix': 'WBT-TAL',
            'sizes': ['24', '26', '28', '30', '32'],
            'colors': ['Black', 'Charcoal', 'Beige'],
            'weight': 0.45,
            'is_featured': False
        }
    ],

    "Women's Dresses": [
        {
            'name': 'Floral Maxi Dress',
            'description': 'Flowing maxi dress with beautiful floral print. Perfect for summer occasions.',
            'price': 4299.00,
            'sale_price': None,
            'sku_prefix': 'WDR-MXI',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Garden Floral', 'Sunset Floral', 'Ocean Floral'],
            'weight': 0.5,
            'is_featured': True
        },
        {
            'name': 'Little Black Dress',
            'description': 'Classic LBD with flattering silhouette. A wardrobe essential for every woman.',
            'price': 3999.00,
            'sale_price': 3299.00,
            'sku_prefix': 'WDR-LBD',
            'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['Black'],
            'weight': 0.4,
            'is_featured': True
        },
        {
            'name': 'Wrap Midi Dress',
            'description': 'Versatile wrap dress that flatters all figures. Adjustable tie waist.',
            'price': 3499.00,
            'sale_price': None,
            'sku_prefix': 'WDR-WRP',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Red', 'Navy', 'Emerald', 'Leopard Print'],
            'weight': 0.45,
            'is_featured': False
        },
        {
            'name': 'Casual T-Shirt Dress',
            'description': 'Comfortable t-shirt dress for everyday wear. Soft jersey fabric.',
            'price': 1999.00,
            'sale_price': 1599.00,
            'sku_prefix': 'WDR-TSD',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Grey', 'Black', 'Navy', 'Olive'],
            'weight': 0.35,
            'is_featured': False
        }
    ],

    "Maternity Tops": [
        {
            'name': 'Maternity Empire Waist Tunic',
            'description': 'Comfortable empire waist tunic that grows with you. Soft stretchy fabric.',
            'price': 2299.00,
            'sale_price': None,
            'sku_prefix': 'MTP-EMP',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Blush', 'Navy', 'Grey'],
            'weight': 0.3,
            'is_featured': True
        },
        {
            'name': 'Nursing-Friendly Wrap Top',
            'description': 'Stylish wrap top with easy nursing access. Versatile for pregnancy and postpartum.',
            'price': 2499.00,
            'sale_price': None,
            'sku_prefix': 'MTP-NUR',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Black', 'Burgundy', 'Forest Green'],
            'weight': 0.35,
            'is_featured': True
        },
        {
            'name': 'Maternity Striped Tee',
            'description': 'Classic striped tee with room for your growing bump. Soft cotton blend.',
            'price': 1799.00,
            'sale_price': 1499.00,
            'sku_prefix': 'MTP-STR',
            'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['Navy/White', 'Black/White', 'Grey/White'],
            'weight': 0.25,
            'is_featured': False
        }
    ],

    "Maternity Bottoms": [
        {
            'name': 'Over-Bump Maternity Jeans',
            'description': 'Comfortable maternity jeans with over-bump panel. Classic skinny fit.',
            'price': 3799.00,
            'sale_price': None,
            'sku_prefix': 'MBT-OBJ',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Dark Wash', 'Medium Wash', 'Black'],
            'weight': 0.65,
            'is_featured': True
        },
        {
            'name': 'Maternity Leggings',
            'description': 'Super comfortable full-panel maternity leggings. Perfect for everyday wear.',
            'price': 1999.00,
            'sale_price': None,
            'sku_prefix': 'MBT-LEG',
            'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['Black', 'Navy', 'Charcoal', 'Burgundy'],
            'weight': 0.3,
            'is_featured': True
        },
        {
            'name': 'Maternity Joggers',
            'description': 'Casual maternity joggers with soft waistband. Comfortable and stylish.',
            'price': 2299.00,
            'sale_price': 1899.00,
            'sku_prefix': 'MBT-JOG',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Grey', 'Black', 'Navy'],
            'weight': 0.4,
            'is_featured': False
        }
    ],

    "Maternity Dresses": [
        {
            'name': 'Maternity Maxi Dress',
            'description': 'Elegant maternity maxi dress with empire waist. Perfect for special occasions.',
            'price': 4499.00,
            'sale_price': None,
            'sku_prefix': 'MDR-MXI',
            'sizes': ['XS', 'S', 'M', 'L', 'XL'],
            'colors': ['Navy', 'Burgundy', 'Forest Green', 'Dusty Rose'],
            'weight': 0.55,
            'is_featured': True
        },
        {
            'name': 'Maternity Wrap Dress',
            'description': 'Flattering wrap dress designed for pregnancy. Adjustable fit throughout all trimesters.',
            'price': 3799.00,
            'sale_price': 3199.00,
            'sku_prefix': 'MDR-WRP',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Black', 'Floral Navy', 'Polka Dot'],
            'weight': 0.5,
            'is_featured': True
        },
        {
            'name': 'Casual Maternity Dress',
            'description': 'Comfortable everyday maternity dress. Soft jersey fabric with pockets.',
            'price': 2499.00,
            'sale_price': None,
            'sku_prefix': 'MDR-CAS',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Grey', 'Navy', 'Black', 'Olive'],
            'weight': 0.4,
            'is_featured': False
        }
    ],

    "Nursing Wear": [
        {
            'name': 'Nursing Sleep Bra',
            'description': 'Ultra-comfortable wireless nursing bra for day and night. Easy clip-down access.',
            'price': 1499.00,
            'sale_price': None,
            'sku_prefix': 'NUR-BRA',
            'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['Black', 'Nude', 'White'],
            'weight': 0.1,
            'is_featured': True
        },
        {
            'name': 'Nursing Tank Top',
            'description': 'Built-in shelf bra nursing tank with easy access. Perfect for layering.',
            'price': 1799.00,
            'sale_price': 1499.00,
            'sku_prefix': 'NUR-TNK',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Black', 'White', 'Grey', 'Navy'],
            'weight': 0.2,
            'is_featured': False
        },
        {
            'name': 'Nursing Nightgown',
            'description': 'Comfortable nightgown with discreet nursing access. Soft and breathable.',
            'price': 2299.00,
            'sale_price': None,
            'sku_prefix': 'NUR-NGT',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Pink', 'Blue', 'Grey'],
            'weight': 0.35,
            'is_featured': True
        }
    ]
}


def create_slug(name):
    """Create URL-friendly slug from product name"""
    return name.lower().replace(' ', '-').replace("'", '')


def seed_products():
    """Seed all products with variants and inventory"""

    app = create_app()

    with app.app_context():
        print("\n" + "="*60)
        print("SEEDING PRODUCTS - HAPPY PLACE BOUTIQUE")
        print("="*60 + "\n")

        # Get all categories
        categories = {cat.name: cat for cat in Category.query.all()}

        if not categories:
            print("❌ Error: No categories found. Please run create_test_users.py first.")
            return

        print(f"📦 Found {len(categories)} categories")
        print("-"*60 + "\n")

        total_products = 0
        total_variants = 0
        total_inventory = 0

        # Create products for each category
        for category_name, products in PRODUCTS_DATA.items():
            category = categories.get(category_name)

            if not category:
                print(f"⚠️  Category '{category_name}' not found, skipping...")
                continue

            print(f"\n📂 Category: {category_name}")
            print("-"*60)

            for idx, product_data in enumerate(products, 1):
                # Check if product already exists
                slug = create_slug(product_data['name'])
                existing = Product.query.filter_by(slug=slug).first()

                if existing:
                    print(f"  ⚠️  '{product_data['name']}' already exists, skipping...")
                    continue

                # Create product
                product = Product(
                    name=product_data['name'],
                    slug=slug,
                    description=product_data['description'],
                    price=product_data['price'],
                    sale_price=product_data['sale_price'],
                    category_id=category.id,
                    sku=f"{product_data['sku_prefix']}-001",
                    weight=product_data['weight'],
                    is_featured=product_data['is_featured'],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(product)
                db.session.flush()  # Get product ID

                # Create product images (3 images per product)
                for img_idx in range(1, 4):
                    image = ProductImage(
                        product_id=product.id,
                        image_url=get_product_image(slug, img_idx),
                        alt_text=f"{product_data['name']} - Image {img_idx}",
                        display_order=img_idx,
                        is_primary=(img_idx == 1)
                    )
                    db.session.add(image)

                # Create variants (size + color combinations)
                variant_count = 0
                for color in product_data['colors']:
                    for size in product_data['sizes']:
                        # Create variant
                        sku = f"{product_data['sku_prefix']}-{color[:3].upper()}-{size}"
                        variant = ProductVariant(
                            product_id=product.id,
                            size=size,
                            color=color,
                            sku=sku,
                            is_active=True
                        )
                        db.session.add(variant)
                        db.session.flush()  # Get variant ID

                        # Create inventory for this variant
                        # Random stock between 10-50 items
                        stock_quantity = random.randint(10, 50)

                        inventory = Inventory(
                            variant_id=variant.id,
                            quantity=stock_quantity,
                            low_stock_threshold=5,
                            last_restocked_at=datetime.utcnow()
                        )
                        db.session.add(inventory)

                        variant_count += 1
                        total_inventory += 1

                total_variants += variant_count
                total_products += 1

                price_display = f"KES {product_data['price']:,.2f}"
                if product_data['sale_price']:
                    price_display += f" (Sale: KES {product_data['sale_price']:,.2f})"

                print(f"  ✅ {product_data['name']}")
                print(f"     {price_display}")
                print(f"     {variant_count} variants ({len(product_data['sizes'])} sizes × {len(product_data['colors'])} colors)")

        # Commit all changes
        db.session.commit()

        print("\n" + "="*60)
        print("SEEDING COMPLETE!")
        print("="*60)
        print(f"✅ Products created:  {total_products}")
        print(f"✅ Variants created:  {total_variants}")
        print(f"✅ Inventory records: {total_inventory}")
        print(f"✅ Images created:    {total_products * 3}")
        print("="*60)

        # Show some statistics
        print("\n📊 PRODUCT STATISTICS BY CATEGORY:")
        print("-"*60)
        for cat_name in PRODUCTS_DATA.keys():
            cat = categories.get(cat_name)
            if cat:
                count = Product.query.filter_by(category_id=cat.id).count()
                print(f"  {cat_name}: {count} products")

        print("\n✅ Database seeded successfully!")
        print("🌐 You can now browse products in the customer portal!")
        print("-"*60 + "\n")


if __name__ == '__main__':
    seed_products()
