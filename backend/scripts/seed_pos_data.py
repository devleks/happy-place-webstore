"""
Seed Data for POS System
Creates employees and store location for Happy Place Boutique
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from werkzeug.security import generate_password_hash

app = create_app()


def seed_store_location():
    """Seed Happy Place Boutique store location"""
    print("\n" + "="*80)
    print("  SEEDING STORE LOCATION")
    print("="*80 + "\n")

    with app.app_context():
        # Check if store location already exists
        result = db.session.execute(
            db.text("SELECT COUNT(*) FROM store_locations")
        )
        count = result.scalar()

        if count > 0:
            print(f"⚠️  Store location already exists ({count} location(s))")
            print("   Skipping store location seeding...")
            return

        # Insert Happy Place Boutique store
        db.session.execute(
            db.text("""
                INSERT INTO store_locations (
                    name,
                    address,
                    city,
                    state,
                    zip_code,
                    phone,
                    email,
                    latitude,
                    longitude,
                    hours_of_operation,
                    is_active
                ) VALUES (
                    :name,
                    :address,
                    :city,
                    :state,
                    :zip_code,
                    :phone,
                    :email,
                    :latitude,
                    :longitude,
                    :hours,
                    :is_active
                )
            """),
            {
                'name': 'Happy Place Boutique - Nairobi',
                'address': 'Kimathi Street, City Centre',
                'city': 'Nairobi',
                'state': 'Nairobi County',
                'zip_code': '00100',
                'phone': '+254 700 123456',
                'email': 'store@happyplace.co.ke',
                'latitude': -1.286389,  # Nairobi coordinates
                'longitude': 36.817223,
                'hours': 'Monday-Saturday: 9:00 AM - 7:00 PM, Sunday: 10:00 AM - 6:00 PM',
                'is_active': True
            }
        )

        db.session.commit()
        print("✅ Store location created: Happy Place Boutique - Nairobi")
        print("   Address: Kimathi Street, City Centre")
        print("   Phone: +254 700 123456")


def seed_employees():
    """Seed test employees for POS system"""
    print("\n" + "="*80)
    print("  SEEDING EMPLOYEES")
    print("="*80 + "\n")

    with app.app_context():
        # Check if employees already exist
        result = db.session.execute(
            db.text("SELECT COUNT(*) FROM employees")
        )
        count = result.scalar()

        if count > 0:
            print(f"⚠️  Employees already exist ({count} employee(s))")
            print("   Skipping employee seeding...")
            return

        # Employees to create
        employees = [
            {
                'email': 'admin@happyplace.co.ke',
                'password': 'admin123',  # Change in production!
                'full_name': 'Admin User',
                'role': 'admin',
                'is_active': True
            },
            {
                'email': 'manager@happyplace.co.ke',
                'password': 'manager123',  # Change in production!
                'full_name': 'Jane Manager',
                'role': 'manager',
                'is_active': True
            },
            {
                'email': 'cashier1@happyplace.co.ke',
                'password': 'cashier123',  # Change in production!
                'full_name': 'Mary Cashier',
                'role': 'cashier',
                'is_active': True
            },
            {
                'email': 'cashier2@happyplace.co.ke',
                'password': 'cashier123',  # Change in production!
                'full_name': 'John Cashier',
                'role': 'cashier',
                'is_active': True
            },
            {
                'email': 'staff@happyplace.co.ke',
                'password': 'staff123',  # Change in production!
                'full_name': 'Alice Staff',
                'role': 'staff',
                'is_active': True
            }
        ]

        print("Creating employees...\n")

        for emp_data in employees:
            # Hash password
            password_hash = generate_password_hash(emp_data['password'])

            # Insert employee
            db.session.execute(
                db.text("""
                    INSERT INTO employees (
                        email,
                        password_hash,
                        full_name,
                        role,
                        is_active,
                        created_at
                    ) VALUES (
                        :email,
                        :password_hash,
                        :full_name,
                        :role,
                        :is_active,
                        NOW()
                    )
                """),
                {
                    'email': emp_data['email'],
                    'password_hash': password_hash,
                    'full_name': emp_data['full_name'],
                    'role': emp_data['role'],
                    'is_active': emp_data['is_active']
                }
            )

            print(f"✅ Created: {emp_data['full_name']} ({emp_data['role']})")
            print(f"   Email: {emp_data['email']}")
            print(f"   Password: {emp_data['password']}")
            print()

        db.session.commit()

        print(f"✅ Created {len(employees)} employees")
        print("\n⚠️  IMPORTANT: Change default passwords in production!")


def verify_seed():
    """Verify seeded data"""
    print("\n" + "="*80)
    print("  VERIFYING SEEDED DATA")
    print("="*80 + "\n")

    with app.app_context():
        # Count employees
        result = db.session.execute(
            db.text("SELECT COUNT(*), role FROM employees GROUP BY role ORDER BY role")
        )
        employees = result.fetchall()

        print("Employees by role:")
        total = 0
        for count, role in employees:
            print(f"   {role}: {count}")
            total += count
        print(f"   Total: {total}\n")

        # Get store location
        result = db.session.execute(
            db.text("SELECT name, city, phone FROM store_locations WHERE is_active = TRUE")
        )
        store = result.fetchone()

        if store:
            print("Active Store Location:")
            print(f"   {store[0]}")
            print(f"   {store[1]}")
            print(f"   {store[2]}\n")
        else:
            print("⚠️  No active store location found\n")


def main():
    """Main seeding function"""
    print("\n" + "🌱" * 40)
    print("POS SYSTEM DATA SEEDING")
    print("🌱" * 40)

    try:
        # Seed store location
        seed_store_location()

        # Seed employees
        seed_employees()

        # Verify
        verify_seed()

        print("\n" + "="*80)
        print("  ✅ POS DATA SEEDING COMPLETE")
        print("="*80 + "\n")

        print("Next steps:")
        print("1. Test employee login with credentials above")
        print("2. Update passwords for production use")
        print("3. Create POS backend services")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Error seeding data: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
