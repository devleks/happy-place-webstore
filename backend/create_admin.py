#!/usr/bin/env python
"""Quick script to create or list admin users"""
from app import create_app
from models import db, Employee
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # List existing admin users
    print("\n=== Existing Admin Users ===")
    admins = Employee.query.filter_by(role='admin').all()
    for admin in admins:
        print(f"ID: {admin.id}, Email: {admin.email}, Name: {admin.full_name}")

    if not admins:
        print("No admin users found. Creating default admin...")
        # Create default admin
        admin = Employee(
            email='admin@happyplace.com',
            password_hash=generate_password_hash('Admin@123'),
            full_name='Admin User',
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Created admin user: {admin.email} / Admin@123")
    else:
        print(f"\nTotal admins: {len(admins)}")
        print("\nTo login, use one of the emails above with its password.")
        print("If you don't know the password, you can reset it manually in the database.")
