#!/usr/bin/env python3
"""Test script for admin dashboard endpoints"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Employee
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset admin password for testing"""
    app = create_app()
    with app.app_context():
        admin = Employee.query.filter_by(email='admin@happyplace.co.ke').first()
        if admin:
            admin.password_hash = generate_password_hash('Admin@123')
            admin.is_active = True
            admin.failed_login_attempts = 0
            admin.account_locked_until = None
            db.session.commit()
            print("✅ Admin password reset to: Admin@123")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role}")
        else:
            print("❌ Admin user not found")

if __name__ == '__main__':
    reset_admin_password()
