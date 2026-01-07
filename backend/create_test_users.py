"""
Create Test Users from TEST_CREDENTIALS.md
Happy Place Boutique - E-commerce Platform
"""

from app import create_app
from models.database_models import db, Employee, Customer, Category, StoreLocation
from werkzeug.security import generate_password_hash
import hashlib
from datetime import datetime

def create_test_employees():
    """Create all test employee accounts"""

    employees = [
        {
            'email': 'admin@happyplace.com',
            'password': 'Admin123!',
            'full_name': 'Admin User',
            'role': 'admin',
            'is_active': True
        },
        {
            'email': 'manager@happyplace.com',
            'password': 'Manager123!',
            'full_name': 'Manager Sarah',
            'role': 'manager',
            'is_active': True
        },
        {
            'email': 'cashier@happyplace.com',
            'password': 'Cashier123!',
            'full_name': 'Cashier John',
            'role': 'cashier',
            'is_active': True
        },
        {
            'email': 'staff@happyplace.com',
            'password': 'Staff123!',
            'full_name': 'Staff Mary',
            'role': 'staff',
            'is_active': True
        },
        {
            'email': 'packer@happyplace.com',
            'password': 'Packer123!',
            'full_name': 'Packer David',
            'role': 'fulfillment',  # Using 'fulfillment' as per database schema
            'is_active': True
        },
        {
            'email': 'shipper@happyplace.com',
            'password': 'Shipper123!',
            'full_name': 'Shipper Lisa',
            'role': 'fulfillment',
            'is_active': True
        }
    ]

    print("Creating test employees...")
    for emp_data in employees:
        # Check if employee already exists
        existing = Employee.query.filter_by(email=emp_data['email']).first()
        if existing:
            print(f"  ⚠️  Employee {emp_data['email']} already exists, skipping...")
            continue

        employee = Employee(
            email=emp_data['email'],
            password_hash=generate_password_hash(emp_data['password']),
            full_name=emp_data['full_name'],
            role=emp_data['role'],
            is_active=emp_data['is_active'],
            created_at=datetime.utcnow()
        )
        db.session.add(employee)
        print(f"  ✅ Created {emp_data['role']}: {emp_data['email']}")

    db.session.commit()
    print(f"✅ Employees created successfully!\n")


def create_test_customer():
    """Create test customer account with encrypted PII"""

    print("Creating test customer...")

    # Check if customer already exists
    email = 'customer@test.com'
    email_hash = hashlib.sha256(email.encode()).hexdigest()

    existing = Customer.query.filter_by(email_hash=email_hash).first()
    if existing:
        print(f"  ⚠️  Customer {email} already exists, skipping...")
        return

    customer = Customer(
        email=email,  # Property setter will handle encryption
        first_name='Test',
        last_name='Customer',
        phone='+254712345678',
        password_hash=generate_password_hash('Customer123!'),
        gdpr_consent=True,
        marketing_consent=False,
        is_active=True,
        email_verified=False,
        created_at=datetime.utcnow()
    )

    db.session.add(customer)
    db.session.commit()
    print(f"  ✅ Created customer: {email}")
    print(f"✅ Customer created successfully!\n")


def create_categories():
    """Create product categories"""

    categories = [
        {
            'name': "Women's Tops",
            'slug': 'womens-tops',
            'description': 'Stylish tops for modern women'
        },
        {
            'name': "Women's Bottoms",
            'slug': 'womens-bottoms',
            'description': 'Comfortable and fashionable bottoms'
        },
        {
            'name': "Women's Dresses",
            'slug': 'womens-dresses',
            'description': 'Beautiful dresses for every occasion'
        },
        {
            'name': 'Maternity Tops',
            'slug': 'maternity-tops',
            'description': 'Comfortable tops for expecting mothers'
        },
        {
            'name': 'Maternity Bottoms',
            'slug': 'maternity-bottoms',
            'description': 'Stylish and comfortable maternity bottoms'
        },
        {
            'name': 'Maternity Dresses',
            'slug': 'maternity-dresses',
            'description': 'Elegant dresses for pregnancy'
        },
        {
            'name': 'Nursing Wear',
            'slug': 'nursing-wear',
            'description': 'Practical and beautiful nursing wear'
        }
    ]

    print("Creating product categories...")
    for cat_data in categories:
        # Check if category already exists
        existing = Category.query.filter_by(slug=cat_data['slug']).first()
        if existing:
            print(f"  ⚠️  Category '{cat_data['name']}' already exists, skipping...")
            continue

        category = Category(
            name=cat_data['name'],
            slug=cat_data['slug'],
            description=cat_data['description']
        )
        db.session.add(category)
        print(f"  ✅ Created category: {cat_data['name']}")

    db.session.commit()
    print(f"✅ Categories created successfully!\n")


def create_store_location():
    """Create main store location"""

    print("Creating store location...")

    # Check if store already exists
    existing = StoreLocation.query.filter_by(name='Happy Place Main Store').first()
    if existing:
        print(f"  ⚠️  Store location already exists, skipping...")
        return

    store = StoreLocation(
        name='Happy Place Main Store',
        address='123 Main Street',
        city='Nairobi',
        state='Nairobi County',
        zip_code='00100',
        phone='+254700000000',
        email='store@happyplace.com',
        is_active=True
    )

    db.session.add(store)
    db.session.commit()
    print(f"  ✅ Created store: Happy Place Main Store")
    print(f"✅ Store location created successfully!\n")


def verify_creation():
    """Verify all test data was created"""

    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    employee_count = Employee.query.count()
    customer_count = Customer.query.count()
    category_count = Category.query.count()
    store_count = StoreLocation.query.count()

    print(f"📊 Employees:  {employee_count}")
    print(f"📊 Customers:  {customer_count}")
    print(f"📊 Categories: {category_count}")
    print(f"📊 Stores:     {store_count}")
    print("="*60)

    if employee_count >= 6 and customer_count >= 1 and category_count >= 7 and store_count >= 1:
        print("✅ All test data created successfully!")
    else:
        print("⚠️  Some test data may be missing. Please check the output above.")

    print("\n📝 TEST CREDENTIALS:")
    print("-"*60)
    print("Admin:    admin@happyplace.com / Admin123!")
    print("Manager:  manager@happyplace.com / Manager123!")
    print("Cashier:  cashier@happyplace.com / Cashier123!")
    print("Customer: customer@test.com / Customer123!")
    print("-"*60)


if __name__ == '__main__':
    app = create_app()

    with app.app_context():
        print("\n" + "="*60)
        print("CREATING TEST USERS - HAPPY PLACE BOUTIQUE")
        print("="*60 + "\n")

        # Create all test data
        create_test_employees()
        create_test_customer()
        create_categories()
        create_store_location()

        # Verify creation
        verify_creation()

        print("\n✅ Setup complete! You can now log in with the test credentials.\n")
