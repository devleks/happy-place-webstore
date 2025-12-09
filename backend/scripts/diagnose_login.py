#!/usr/bin/env python3
"""
Diagnose admin login issues - check password hashes and test authentication
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models.database_models import db, Employee
from werkzeug.security import check_password_hash, generate_password_hash

def diagnose_login():
    """Diagnose login issues"""
    app = create_app()

    with app.app_context():
        print("\n" + "="*70)
        print("ADMIN LOGIN DIAGNOSTIC TOOL")
        print("="*70 + "\n")

        # Get admin and manager accounts
        admin = Employee.query.filter_by(email='admin@happyplace.co.ke').first()
        manager = Employee.query.filter_by(email='manager@happyplace.co.ke').first()

        if not admin:
            print("❌ Admin account not found!")
            return

        if not manager:
            print("❌ Manager account not found!")
            return

        print("✅ Both accounts found in database\n")

        # Test admin
        print("-" * 70)
        print("ADMIN ACCOUNT DIAGNOSTICS")
        print("-" * 70)
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Full Name: {admin.full_name}")
        print(f"Role: {admin.role}")
        print(f"Is Active: {admin.is_active}")
        print(f"Has Password Hash: {admin.password_hash is not None}")

        if admin.password_hash:
            print(f"Password Hash (first 30 chars): {admin.password_hash[:30]}...")

            # Test password verification
            test_passwords = ['admin123', 'Admin123', 'admin', 'password']
            print(f"\nTesting password verification:")
            for pwd in test_passwords:
                result = check_password_hash(admin.password_hash, pwd)
                status = "✅ MATCH" if result else "❌ NO MATCH"
                print(f"  '{pwd}': {status}")

        print(f"\nAccount Locked: {admin.account_locked_until is not None}")
        if admin.account_locked_until:
            print(f"  Locked Until: {admin.account_locked_until}")
        print(f"Failed Login Attempts: {admin.failed_login_attempts}")

        # Test manager
        print("\n" + "-" * 70)
        print("MANAGER ACCOUNT DIAGNOSTICS")
        print("-" * 70)
        print(f"ID: {manager.id}")
        print(f"Email: {manager.email}")
        print(f"Full Name: {manager.full_name}")
        print(f"Role: {manager.role}")
        print(f"Is Active: {manager.is_active}")
        print(f"Has Password Hash: {manager.password_hash is not None}")

        if manager.password_hash:
            print(f"Password Hash (first 30 chars): {manager.password_hash[:30]}...")

            # Test password verification
            test_passwords = ['manager123', 'Manager123', 'manager', 'password']
            print(f"\nTesting password verification:")
            for pwd in test_passwords:
                result = check_password_hash(manager.password_hash, pwd)
                status = "✅ MATCH" if result else "❌ NO MATCH"
                print(f"  '{pwd}': {status}")

        print(f"\nAccount Locked: {manager.account_locked_until is not None}")
        if manager.account_locked_until:
            print(f"  Locked Until: {manager.account_locked_until}")
        print(f"Failed Login Attempts: {manager.failed_login_attempts}")

        # Generate fresh hashes for comparison
        print("\n" + "-" * 70)
        print("HASH VALIDATION")
        print("-" * 70)
        fresh_admin_hash = generate_password_hash('admin123')
        fresh_manager_hash = generate_password_hash('manager123')

        print(f"\nFresh admin123 hash: {fresh_admin_hash[:50]}...")
        print(f"Current admin hash: {admin.password_hash[:50]}...")
        print(f"Hash formats match: {admin.password_hash.startswith(('pbkdf2:', 'scrypt:', 'argon2:', 'bcrypt'))}")

        print(f"\nFresh manager123 hash: {fresh_manager_hash[:50]}...")
        print(f"Current manager hash: {manager.password_hash[:50]}...")
        print(f"Hash formats match: {manager.password_hash.startswith(('pbkdf2:', 'scrypt:', 'argon2:', 'bcrypt'))}")

        # Check for account lock issues
        print("\n" + "-" * 70)
        print("RECOMMENDATIONS")
        print("-" * 70)

        issues = []
        if not admin.is_active:
            issues.append("Admin account is not active")
        if admin.account_locked_until:
            issues.append("Admin account is locked")
        if admin.failed_login_attempts >= 5:
            issues.append(f"Admin has {admin.failed_login_attempts} failed login attempts")

        if not manager.is_active:
            issues.append("Manager account is not active")
        if manager.account_locked_until:
            issues.append("Manager account is locked")
        if manager.failed_login_attempts >= 5:
            issues.append(f"Manager has {manager.failed_login_attempts} failed login attempts")

        if issues:
            print("\n⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")

            print("\n🔧 FIX:")
            print("  Run: python scripts/reset_admin_passwords.py")
            print("  This will reset passwords and clear any locks")
        else:
            print("\n✅ No issues found. Accounts should be working.")
            print("\nTest credentials:")
            print("  Admin:   admin@happyplace.co.ke / admin123")
            print("  Manager: manager@happyplace.co.ke / manager123")

        print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    diagnose_login()
