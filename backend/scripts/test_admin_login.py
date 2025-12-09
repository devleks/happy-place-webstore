#!/usr/bin/env python3
"""
Test admin login credentials
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5001/api"

def test_login(email, password, role_name):
    """Test login with given credentials"""
    print(f"\n{'='*60}")
    print(f"Testing {role_name} Login")
    print(f"{'='*60}")
    print(f"Email: {email}")
    print(f"Password: {password}")

    try:
        response = requests.post(
            f"{BASE_URL}/auth/employee/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ LOGIN SUCCESSFUL!")
            print(f"\nEmployee Info:")
            if 'employee' in data:
                emp = data['employee']
                print(f"  ID: {emp.get('id')}")
                print(f"  Name: {emp.get('full_name')}")
                print(f"  Email: {emp.get('email')}")
                print(f"  Role: {emp.get('role')}")
            if 'access_token' in data:
                token = data['access_token']
                print(f"\nAccess Token (first 50 chars): {token[:50]}...")
        else:
            print("❌ LOGIN FAILED!")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("ADMIN DASHBOARD LOGIN TEST")
    print("="*60)

    # Test admin login
    test_login("admin@happyplace.co.ke", "admin123", "Admin")

    # Test manager login
    test_login("manager@happyplace.co.ke", "manager123", "Manager")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")
