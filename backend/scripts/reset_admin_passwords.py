#!/usr/bin/env python3
"""
Reset admin and manager passwords to known test values
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models.database_models import db, Employee
from werkzeug.security import generate_password_hash

def reset_passwords():
    """Reset admin and manager passwords"""
    app = create_app()

    with app.app_context():
        # Admin account
        admin = Employee.query.filter_by(email='admin@happyplace.co.ke').first()
        if admin:
            admin.password_hash = generate_password_hash('admin123')
            print(f"✅ Reset password for: {admin.email} (role: {admin.role})")
        else:
            print("❌ Admin account not found")

        # Manager account
        manager = Employee.query.filter_by(email='manager@happyplace.co.ke').first()
        if manager:
            manager.password_hash = generate_password_hash('manager123')
            print(f"✅ Reset password for: {manager.email} (role: {manager.role})")
        else:
            print("❌ Manager account not found")

        # Commit changes
        db.session.commit()
        print("\n✅ Password reset complete!")
        print("\nTest Credentials:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Admin Login:")
        print("  Email: admin@happyplace.co.ke")
        print("  Password: admin123")
        print("\nManager Login:")
        print("  Email: manager@happyplace.co.ke")
        print("  Password: manager123")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == '__main__':
    reset_passwords()
