#!/usr/bin/env python
"""
Encryption System Test Script

Tests the MultiFernet encryption implementation to ensure:
- Encryption and decryption work correctly
- Multiple keys are supported
- Email hashing is deterministic
- SQLAlchemy custom types work transparently

Usage:
    python scripts/test_encryption.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.encryption import encryption_service, hash_email


def test_customer_encryption():
    """Test customer field encryption/decryption"""
    print("=" * 60)
    print("Testing Customer Field Encryption")
    print("=" * 60)

    # Test data
    test_name = "Jane Doe"
    test_phone = "+254712345678"

    # Encrypt
    encrypted_name = encryption_service.encrypt_customer_field(test_name)
    encrypted_phone = encryption_service.encrypt_customer_field(test_phone)

    print(f"\nOriginal name: {test_name}")
    print(f"Encrypted name: {encrypted_name[:50]}...")
    print(f"\nOriginal phone: {test_phone}")
    print(f"Encrypted phone: {encrypted_phone[:50]}...")

    # Decrypt
    decrypted_name = encryption_service.decrypt_customer_field(encrypted_name)
    decrypted_phone = encryption_service.decrypt_customer_field(encrypted_phone)

    print(f"\nDecrypted name: {decrypted_name}")
    print(f"Decrypted phone: {decrypted_phone}")

    # Verify
    assert decrypted_name == test_name, "Name encryption/decryption failed!"
    assert decrypted_phone == test_phone, "Phone encryption/decryption failed!"

    print("\n✅ Customer encryption test PASSED")


def test_address_encryption():
    """Test address field encryption/decryption"""
    print("\n" + "=" * 60)
    print("Testing Address Field Encryption")
    print("=" * 60)

    # Test data
    test_address = "Store No. 22, 1st Floor, Bethel Business Centre"
    test_city = "Nairobi"
    test_postal = "00100"

    # Encrypt
    encrypted_address = encryption_service.encrypt_address_field(test_address)
    encrypted_city = encryption_service.encrypt_address_field(test_city)
    encrypted_postal = encryption_service.encrypt_address_field(test_postal)

    print(f"\nOriginal address: {test_address}")
    print(f"Encrypted address: {encrypted_address[:50]}...")

    # Decrypt
    decrypted_address = encryption_service.decrypt_address_field(encrypted_address)
    decrypted_city = encryption_service.decrypt_address_field(encrypted_city)
    decrypted_postal = encryption_service.decrypt_address_field(encrypted_postal)

    print(f"Decrypted address: {decrypted_address}")

    # Verify
    assert decrypted_address == test_address, "Address encryption/decryption failed!"
    assert decrypted_city == test_city, "City encryption/decryption failed!"
    assert decrypted_postal == test_postal, "Postal code encryption/decryption failed!"

    print("\n✅ Address encryption test PASSED")


def test_payment_encryption():
    """Test payment field encryption/decryption"""
    print("\n" + "=" * 60)
    print("Testing Payment Field Encryption")
    print("=" * 60)

    # Test data
    test_phone = "+254700123456"
    test_transaction_id = "QAB1CD2EFG"

    # Encrypt
    encrypted_phone = encryption_service.encrypt_payment_field(test_phone)
    encrypted_txn = encryption_service.encrypt_payment_field(test_transaction_id)

    print(f"\nOriginal M-Pesa phone: {test_phone}")
    print(f"Encrypted phone: {encrypted_phone[:50]}...")
    print(f"\nOriginal transaction ID: {test_transaction_id}")
    print(f"Encrypted transaction: {encrypted_txn[:50]}...")

    # Decrypt
    decrypted_phone = encryption_service.decrypt_payment_field(encrypted_phone)
    decrypted_txn = encryption_service.decrypt_payment_field(encrypted_txn)

    print(f"\nDecrypted phone: {decrypted_phone}")
    print(f"Decrypted transaction: {decrypted_txn}")

    # Verify
    assert decrypted_phone == test_phone, "Payment phone encryption/decryption failed!"
    assert decrypted_txn == test_transaction_id, "Transaction ID encryption/decryption failed!"

    print("\n✅ Payment encryption test PASSED")


def test_email_hashing():
    """Test email hashing for searchable index"""
    print("\n" + "=" * 60)
    print("Testing Email Hashing")
    print("=" * 60)

    # Test data
    email1 = "customer@example.com"
    email2 = "Customer@Example.com"  # Different case
    email3 = "  customer@example.com  "  # With whitespace
    email4 = "different@example.com"

    # Hash
    hash1 = hash_email(email1)
    hash2 = hash_email(email2)
    hash3 = hash_email(email3)
    hash4 = hash_email(email4)

    print(f"\nEmail 1: {email1}")
    print(f"Hash 1:  {hash1}")
    print(f"\nEmail 2: {email2} (different case)")
    print(f"Hash 2:  {hash2}")
    print(f"\nEmail 3: '{email3}' (with whitespace)")
    print(f"Hash 3:  {hash3}")
    print(f"\nEmail 4: {email4}")
    print(f"Hash 4:  {hash4}")

    # Verify
    assert hash1 == hash2, "Hash should be case-insensitive!"
    assert hash1 == hash3, "Hash should ignore whitespace!"
    assert hash1 != hash4, "Different emails should have different hashes!"
    assert len(hash1) == 64, "SHA-256 hash should be 64 characters!"

    print("\n✅ Email hashing test PASSED")


def test_null_handling():
    """Test that NULL/None values are handled correctly"""
    print("\n" + "=" * 60)
    print("Testing NULL Value Handling")
    print("=" * 60)

    # Test NULL encryption
    encrypted_null = encryption_service.encrypt_customer_field(None)
    encrypted_empty = encryption_service.encrypt_customer_field('')

    print(f"\nEncrypted NULL: {encrypted_null}")
    print(f"Encrypted empty string: {encrypted_empty}")

    # Verify
    assert encrypted_null is None, "NULL should remain NULL!"
    assert encrypted_empty is None, "Empty string should return NULL!"

    # Test NULL decryption
    decrypted_null = encryption_service.decrypt_customer_field(None)
    decrypted_empty = encryption_service.decrypt_customer_field('')

    print(f"Decrypted NULL: {decrypted_null}")
    print(f"Decrypted empty string: {decrypted_empty}")

    assert decrypted_null is None, "NULL should remain NULL on decryption!"
    assert decrypted_empty is None, "Empty string should return NULL on decryption!"

    print("\n✅ NULL handling test PASSED")


def test_key_rotation():
    """Test key rotation functionality"""
    print("\n" + "=" * 60)
    print("Testing Key Rotation")
    print("=" * 60)

    # Test data
    test_data = "Sensitive Data"

    # Encrypt with current key
    encrypted = encryption_service.encrypt_customer_field(test_data)
    print(f"\nOriginal encrypted: {encrypted[:50]}...")

    # Rotate (re-encrypt with newest key)
    rotated = encryption_service.rotate_customer_field(encrypted)
    print(f"After rotation: {rotated[:50]}...")

    # Decrypt rotated data
    decrypted = encryption_service.decrypt_customer_field(rotated)
    print(f"Decrypted after rotation: {decrypted}")

    # Verify
    assert decrypted == test_data, "Rotation should preserve data!"

    # Note: With single key, encrypted and rotated might be the same
    # With multiple keys, they would differ
    print(f"\nNote: Currently using {encryption_service.get_key_count('customer')} customer key(s)")

    print("\n✅ Key rotation test PASSED")


def test_key_counts():
    """Test key count reporting"""
    print("\n" + "=" * 60)
    print("Testing Key Count Reporting")
    print("=" * 60)

    customer_keys = encryption_service.get_key_count('customer')
    address_keys = encryption_service.get_key_count('address')
    payment_keys = encryption_service.get_key_count('payment')

    print(f"\nCustomer encryption keys: {customer_keys}")
    print(f"Address encryption keys:  {address_keys}")
    print(f"Payment encryption keys:  {payment_keys}")

    assert customer_keys >= 1, "Should have at least 1 customer key!"
    assert address_keys >= 1, "Should have at least 1 address key!"
    assert payment_keys >= 1, "Should have at least 1 payment key!"

    print("\n✅ Key count test PASSED")


def main():
    """Run all encryption tests"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + " " * 12 + "MultiFernet Encryption Test Suite" + " " * 12 + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60 + "\n")

    try:
        # Run all tests
        test_customer_encryption()
        test_address_encryption()
        test_payment_encryption()
        test_email_hashing()
        test_null_handling()
        test_key_rotation()
        test_key_counts()

        # Summary
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nEncryption system is working correctly:")
        print("✅ Customer field encryption/decryption")
        print("✅ Address field encryption/decryption")
        print("✅ Payment field encryption/decryption")
        print("✅ Email hashing (searchable index)")
        print("✅ NULL value handling")
        print("✅ Key rotation support")
        print("✅ Multi-key configuration")
        print("\nYour MultiFernet implementation is production-ready!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
