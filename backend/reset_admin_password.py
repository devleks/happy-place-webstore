#!/usr/bin/env python
"""Reset admin password to a known value"""
from app import create_app
from models import db, Employee
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    admin = Employee.query.filter_by(email='admin@happyplace.co.ke').first()

    if admin:
        new_password = 'Admin@123'
        admin.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print("✅ Password reset successful!")
        print(f"Email: {admin.email}")
        print(f"Password: {new_password}")
    else:
        print("❌ Admin user not found")
