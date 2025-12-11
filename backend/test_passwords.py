import requests

# Test common passwords
test_accounts = [
    ("admin@happyplace.co.ke", ["admin123", "password123", "Admin123", "admin", "password"]),
    ("manager@happyplace.co.ke", ["manager123", "password123", "Manager123", "manager", "password"]),
    ("cashier1@happyplace.co.ke", ["cashier123", "password123", "Cashier123", "cashier", "password"]),
]

print("\n🔑 Testing credentials...\n")
print("=" * 80)

for email, passwords in test_accounts:
    print(f"\nTesting: {email}")
    for pwd in passwords:
        response = requests.post(
            'http://localhost:5001/api/auth/employee/login',
            json={'email': email, 'password': pwd}
        )
        data = response.json()
        if data.get('success'):
            print(f"  ✅ SUCCESS! Password: {pwd}")
            print(f"     Token: {data['access_token'][:50]}...")
            break
        else:
            print(f"  ❌ Failed: {pwd}")
    print("-" * 80)
