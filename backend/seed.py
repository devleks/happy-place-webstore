from app import create_app
from models import db, Category, Product, Inventory, StoreLocation
import json

def seed_database():
    app = create_app()

    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        print("Seeding categories...")

        # Create Categories
        categories = [
            Category(name="Women's Tops", slug="womens-tops", description="Stylish tops for every occasion"),
            Category(name="Women's Bottoms", slug="womens-bottoms", description="Comfortable and fashionable bottoms"),
            Category(name="Women's Dresses", slug="womens-dresses", description="Beautiful dresses for any event"),
            Category(name="Maternity Tops", slug="maternity-tops", description="Comfortable maternity tops"),
            Category(name="Maternity Bottoms", slug="maternity-bottoms", description="Stretchy and supportive maternity bottoms"),
            Category(name="Maternity Dresses", slug="maternity-dresses", description="Elegant maternity dresses"),
            Category(name="Nursing Wear", slug="nursing-wear", description="Convenient nursing-friendly clothing"),
        ]

        for cat in categories:
            db.session.add(cat)

        db.session.commit()

        print("Seeding products...")

        # Sample Products
        products = [
            # Women's Tops
            {
                'name': 'Classic Cotton T-Shirt',
                'slug': 'classic-cotton-tshirt',
                'description': 'Soft, breathable cotton t-shirt perfect for everyday wear',
                'price': 29.99,
                'category': 'womens-tops',
                'sizes': json.dumps(['XS', 'S', 'M', 'L', 'XL']),
                'colors': json.dumps(['White', 'Black', 'Navy', 'Pink']),
                'image_url': 'https://via.placeholder.com/400x600/FF69B4/FFFFFF?text=Cotton+T-Shirt'
            },
            {
                'name': 'Elegant Blouse',
                'slug': 'elegant-blouse',
                'description': 'Sophisticated blouse for work or special occasions',
                'price': 49.99,
                'category': 'womens-tops',
                'sizes': json.dumps(['XS', 'S', 'M', 'L', 'XL']),
                'colors': json.dumps(['White', 'Cream', 'Light Blue']),
                'image_url': 'https://via.placeholder.com/400x600/FFC0CB/FFFFFF?text=Elegant+Blouse'
            },
            # Women's Bottoms
            {
                'name': 'Skinny Jeans',
                'slug': 'skinny-jeans',
                'description': 'Flattering skinny jeans with stretch fabric',
                'price': 69.99,
                'category': 'womens-bottoms',
                'sizes': json.dumps(['24', '26', '28', '30', '32']),
                'colors': json.dumps(['Dark Blue', 'Black', 'Light Wash']),
                'image_url': 'https://via.placeholder.com/400x600/4169E1/FFFFFF?text=Skinny+Jeans'
            },
            {
                'name': 'Yoga Pants',
                'slug': 'yoga-pants',
                'description': 'Comfortable high-waisted yoga pants',
                'price': 44.99,
                'category': 'womens-bottoms',
                'sizes': json.dumps(['XS', 'S', 'M', 'L', 'XL']),
                'colors': json.dumps(['Black', 'Gray', 'Navy']),
                'image_url': 'https://via.placeholder.com/400x600/2F4F4F/FFFFFF?text=Yoga+Pants'
            },
            # Women's Dresses
            {
                'name': 'Summer Maxi Dress',
                'slug': 'summer-maxi-dress',
                'description': 'Flowing maxi dress perfect for summer',
                'price': 79.99,
                'category': 'womens-dresses',
                'sizes': json.dumps(['XS', 'S', 'M', 'L', 'XL']),
                'colors': json.dumps(['Floral Print', 'Solid Navy', 'Red']),
                'image_url': 'https://via.placeholder.com/400x600/FF1493/FFFFFF?text=Maxi+Dress'
            },
            # Maternity Tops
            {
                'name': 'Maternity Basic Tee',
                'slug': 'maternity-basic-tee',
                'description': 'Soft stretchy tee that grows with your bump',
                'price': 34.99,
                'category': 'maternity-tops',
                'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                'colors': json.dumps(['White', 'Black', 'Gray', 'Pink']),
                'image_url': 'https://via.placeholder.com/400x600/FFB6C1/FFFFFF?text=Maternity+Tee'
            },
            {
                'name': 'Maternity Wrap Top',
                'slug': 'maternity-wrap-top',
                'description': 'Flattering wrap top for pregnancy and beyond',
                'price': 54.99,
                'category': 'maternity-tops',
                'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                'colors': json.dumps(['Black', 'Navy', 'Burgundy']),
                'image_url': 'https://via.placeholder.com/400x600/BA55D3/FFFFFF?text=Wrap+Top'
            },
            # Maternity Bottoms
            {
                'name': 'Maternity Leggings',
                'slug': 'maternity-leggings',
                'description': 'Ultra-comfortable over-the-bump leggings',
                'price': 39.99,
                'category': 'maternity-bottoms',
                'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                'colors': json.dumps(['Black', 'Gray', 'Navy']),
                'image_url': 'https://via.placeholder.com/400x600/708090/FFFFFF?text=Maternity+Leggings'
            },
            {
                'name': 'Maternity Jeans',
                'slug': 'maternity-jeans',
                'description': 'Comfortable maternity jeans with belly panel',
                'price': 79.99,
                'category': 'maternity-bottoms',
                'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                'colors': json.dumps(['Dark Blue', 'Black']),
                'image_url': 'https://via.placeholder.com/400x600/191970/FFFFFF?text=Maternity+Jeans'
            },
            # Maternity Dresses
            {
                'name': 'Maternity Wrap Dress',
                'slug': 'maternity-wrap-dress',
                'description': 'Elegant wrap dress perfect for any occasion',
                'price': 89.99,
                'category': 'maternity-dresses',
                'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                'colors': json.dumps(['Black', 'Navy', 'Floral']),
                'image_url': 'https://via.placeholder.com/400x600/8B008B/FFFFFF?text=Wrap+Dress'
            },
            # Nursing Wear
            {
                'name': 'Nursing Tank Top',
                'slug': 'nursing-tank-top',
                'description': 'Convenient nursing tank with easy access',
                'price': 32.99,
                'category': 'nursing-wear',
                'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                'colors': json.dumps(['White', 'Black', 'Gray']),
                'image_url': 'https://via.placeholder.com/400x600/C0C0C0/000000?text=Nursing+Tank'
            },
        ]

        for product_data in products:
            category = Category.query.filter_by(slug=product_data['category']).first()
            product = Product(
                name=product_data['name'],
                slug=product_data['slug'],
                description=product_data['description'],
                price=product_data['price'],
                category_id=category.id,
                sizes=product_data['sizes'],
                colors=product_data['colors'],
                image_url=product_data['image_url']
            )
            db.session.add(product)

        db.session.commit()

        print("Seeding inventory...")

        # Add inventory for each product
        products = Product.query.all()
        for product in products:
            sizes = json.loads(product.sizes)
            colors = json.loads(product.colors)

            for size in sizes:
                for color in colors:
                    inventory = Inventory(
                        product_id=product.id,
                        size=size,
                        color=color,
                        quantity=50,
                        online_quantity=30,
                        store_quantity=20
                    )
                    db.session.add(inventory)

        db.session.commit()

        print("Seeding store location...")

        # Add store location
        store = StoreLocation(
            name="Happy Place Boutique",
            address="123 Main Street",
            city="San Francisco",
            state="CA",
            zip_code="94102",
            phone="(555) 123-4567",
            email="info@happyplaceboutique.com",
            latitude=37.7749,
            longitude=-122.4194,
            hours_of_operation=json.dumps({
                'Monday': '10:00 AM - 7:00 PM',
                'Tuesday': '10:00 AM - 7:00 PM',
                'Wednesday': '10:00 AM - 7:00 PM',
                'Thursday': '10:00 AM - 7:00 PM',
                'Friday': '10:00 AM - 8:00 PM',
                'Saturday': '10:00 AM - 8:00 PM',
                'Sunday': '11:00 AM - 6:00 PM'
            })
        )
        db.session.add(store)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
