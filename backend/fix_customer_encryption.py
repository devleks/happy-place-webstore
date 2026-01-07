"""
Fix Customer Encryption Mismatch
Re-encrypt customer data with current encryption keys
"""

import sys
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.database_models import db, Customer
from services.encryption import encrypt_customer, hash_email

def fix_customer_encryption(customer_id: int, email: str, first_name: str, last_name: str):
    """
    Update customer record with properly encrypted data using current keys

    Args:
        customer_id: Customer ID to update
        email: Plain text email address
        first_name: Plain text first name
        last_name: Plain text last name
    """

    app = create_app()

    with app.app_context():
        print('=' * 60)
        print('FIXING CUSTOMER ENCRYPTION')
        print('=' * 60)

        # Get customer
        customer = Customer.query.get(customer_id)

        if not customer:
            print(f'\n❌ Customer ID {customer_id} not found')
            return False

        print(f'\n📋 Customer ID: {customer_id}')
        print(f'   Created: {customer.created_at}')

        # Encrypt data with current keys
        print(f'\n🔐 Encrypting data with current keys...')

        email_encrypted = encrypt_customer(email)
        first_name_encrypted = encrypt_customer(first_name)
        last_name_encrypted = encrypt_customer(last_name)
        email_hash_new = hash_email(email)

        # Update customer record
        customer.email_encrypted = email_encrypted
        customer.first_name_encrypted = first_name_encrypted
        customer.last_name_encrypted = last_name_encrypted
        customer.email_hash = email_hash_new

        db.session.commit()

        print(f'\n✅ SUCCESS! Customer data re-encrypted')
        print(f'\n📧 Updated customer:')
        print(f'   Name: {first_name} {last_name}')
        print(f'   Email: {email}')
        print(f'   Email Hash: {email_hash_new[:30]}...')
        print(f'   Encryption: Using current CUSTOMER_ENCRYPTION_KEYS')

        print(f'\n✨ Customer can now be decrypted with current keys!')

        return True

def list_customers():
    """List all customers with their IDs and creation dates"""

    app = create_app()

    with app.app_context():
        customers = Customer.query.order_by(Customer.created_at.desc()).all()

        print('=' * 60)
        print('ALL CUSTOMERS')
        print('=' * 60)
        print(f'\nTotal: {len(customers)} customers\n')

        for customer in customers:
            print(f'Customer ID: {customer.id}')
            print(f'  Created: {customer.created_at}')
            print(f'  Email Verified: {customer.email_verified}')
            print(f'  Has encrypted data: {bool(customer.email_encrypted)}')
            print()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage:')
        print('  List customers:')
        print('    python fix_customer_encryption.py list')
        print()
        print('  Fix customer encryption:')
        print('    python fix_customer_encryption.py <customer_id> <email> <first_name> <last_name>')
        print()
        print('Example:')
        print('    python fix_customer_encryption.py 2 wraps@example.com Wraps Somber')
        sys.exit(1)

    if sys.argv[1] == 'list':
        list_customers()
    else:
        if len(sys.argv) < 5:
            print('❌ Error: Missing arguments')
            print('Usage: python fix_customer_encryption.py <customer_id> <email> <first_name> <last_name>')
            sys.exit(1)

        customer_id = int(sys.argv[1])
        email = sys.argv[2]
        first_name = sys.argv[3]
        last_name = ' '.join(sys.argv[4:])  # Allow last name with spaces

        fix_customer_encryption(customer_id, email, first_name, last_name)
