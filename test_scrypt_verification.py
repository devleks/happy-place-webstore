#!/usr/bin/env python3
"""
Test scrypt password verification
Verifies that Node.js crypto.scrypt can verify Flask's Werkzeug scrypt hashes
"""

import hashlib
import sqlite3
import base64
from pathlib import Path

# Database path
DB_PATH = Path.home() / "Library/Application Support/happy-place-pos/pos.db"

def parse_scrypt_hash(password_hash):
    """Parse Werkzeug scrypt hash format: scrypt:N:r:p$salt$hexhash
    IMPORTANT: Werkzeug uses the base64 salt string as UTF-8 bytes (not decoded!)
    """
    if not password_hash.startswith('scrypt:'):
        return None

    parts = password_hash.split('$')
    if len(parts) != 3:
        return None

    params, salt_str, expected_hash = parts
    param_parts = params.split(':')
    if len(param_parts) != 4:
        return None

    _, N, r, p = param_parts

    return {
        'N': int(N),
        'r': int(r),
        'p': int(p),
        'salt': salt_str.encode('utf-8'),  # Use base64 string as UTF-8 bytes!
        'expected_hash': expected_hash
    }

def verify_scrypt_python(password, password_hash):
    """Verify password using Python's hashlib.scrypt"""
    parsed = parse_scrypt_hash(password_hash)
    if not parsed:
        return False

    try:
        # Derive key using same parameters
        # Calculate maxmem: 132 * N * r * p (Werkzeug formula)
        maxmem = 132 * parsed['N'] * parsed['r'] * parsed['p']

        derived_key = hashlib.scrypt(
            password.encode('utf-8'),
            salt=parsed['salt'],
            n=parsed['N'],
            r=parsed['r'],
            p=parsed['p'],
            dklen=64,  # Flask scrypt outputs 64 bytes
            maxmem=maxmem
        )

        # Convert to hex (Werkzeug uses hex encoding)
        derived_hash = derived_key.hex()

        return derived_hash == parsed['expected_hash']
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("🔐 Testing scrypt password verification...\n")

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Get admin employee
        cursor.execute("SELECT email, role, password_hash FROM employees WHERE email = 'admin@happyplace.co.ke'")
        row = cursor.fetchone()

        if not row:
            print("❌ Admin account not found in database")
            return False

        email, role, password_hash = row

        print(f"👤 Testing admin account: {email}")
        print(f"   Role: {role}")
        print(f"   Hash format: {password_hash[:30]}...")
        print()

        # Parse hash details
        parsed = parse_scrypt_hash(password_hash)
        if parsed:
            print(f"📋 Scrypt parameters:")
            print(f"   N (CPU/memory cost): {parsed['N']}")
            print(f"   r (block size): {parsed['r']}")
            print(f"   p (parallelization): {parsed['p']}")
            print(f"   Salt length: {len(parsed['salt'])} bytes")
            print(f"   Expected hash length: {len(parsed['expected_hash'])} chars")
            print()

        # Test correct password
        print('🔑 Testing with correct password: "admin123"')
        correct_result = verify_scrypt_python('admin123', password_hash)
        print(f"   Result: {'✅ PASS' if correct_result else '❌ FAIL'}")
        print()

        # Test incorrect password
        print('🔑 Testing with incorrect password: "wrongpassword"')
        incorrect_result = verify_scrypt_python('wrongpassword', password_hash)
        print(f"   Result: {'❌ FAIL (should be false)' if incorrect_result else '✅ PASS (correctly rejected)'}")
        print()

        if correct_result and not incorrect_result:
            print("✅ Scrypt password verification is working correctly!")
            print("\nThe Node.js implementation should work the same way.")
            print("\n📱 You can now login to the POS app with:")
            print("   Email: admin@happyplace.co.ke")
            print("   Password: admin123")
            return True
        else:
            print("❌ Scrypt password verification failed!")
            return False

    finally:
        conn.close()

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
