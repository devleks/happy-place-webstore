#!/usr/bin/env python3
"""Direct test of admin login credentials"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import Employee
from werkzeug.security import check_password_hash

def test_admin_credentials():
    """Test admin credentials directly"""
    app = create_app()
    with app.app_context():
        admin = Employee.query.filter_by(email='admin@happyplace.co.ke').first()
        
        if not admin:
            print("❌ Admin user not found")
            return False
            
        print("✅ Admin user found:")
        print(f"   ID: {admin.id}")
        print(f"   Email: {admin.email}")
        print(f"   Full Name: {admin.full_name}")
        print(f"   Role: {admin.role}")
        print(f"   Is Active: {admin.is_active}")
        print(f"   Failed Login Attempts: {admin.failed_login_attempts}")
        print(f"   Account Locked: {admin.account_locked_until}")
        
        # Test password
        test_password = 'Admin@123'
        if check_password_hash(admin.password_hash, test_password):
            print(f"\n✅ Password '{test_password}' is CORRECT")
            return True
        else:
            print(f"\n❌ Password '{test_password}' is INCORRECT")
            return False

if __name__ == '__main__':
    test_admin_credentials()
