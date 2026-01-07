#!/usr/bin/env python
"""
Encryption Key Rotation Script

This script re-encrypts all PII data with the newest encryption key in MultiFernet.
Used for annual key rotation or after a security incident.

Usage:
    # Check rotation status
    python scripts/rotate_encryption_keys.py status

    # Rotate all customer fields
    python scripts/rotate_encryption_keys.py rotate --type customer

    # Rotate all address fields
    python scripts/rotate_encryption_keys.py rotate --type address

    # Rotate all payment fields
    python scripts/rotate_encryption_keys.py rotate --type payment

    # Rotate all fields (customer, address, payment)
    python scripts/rotate_encryption_keys.py rotate --all

    # Dry run (show what would be rotated without making changes)
    python scripts/rotate_encryption_keys.py rotate --all --dry-run

Key Rotation Process:
    1. Generate new Fernet key
    2. Prepend new key to CUSTOMER_ENCRYPTION_KEYS in .env (becomes first key)
    3. Restart application (picks up new key configuration)
    4. Run this script to re-encrypt all existing data with new key
    5. After verification, remove oldest key from .env (optional)

Safety Features:
    - Dry-run mode to preview changes
    - Transaction support (rollback on error)
    - Progress tracking
    - Detailed logging
    - Backup recommendations
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import Config
from extensions import db
from services.encryption import encryption_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'key_rotation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def create_app():
    """Create Flask app for database access."""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def rotate_customer_fields(dry_run=False):
    """
    Rotate encryption for all customer PII fields.

    Args:
        dry_run: If True, only count records without making changes

    Returns:
        Number of records rotated
    """
    from models.database_models import Customer

    logger.info("Starting customer fields rotation...")

    try:
        customers = Customer.query.all()
        total = len(customers)
        rotated = 0

        logger.info(f"Found {total} customer records to rotate")

        for i, customer in enumerate(customers, 1):
            try:
                if not dry_run:
                    # Rotate each encrypted field
                    if customer.email_encrypted:
                        customer.email_encrypted = encryption_service.rotate_customer_field(
                            customer.email_encrypted
                        )

                    if customer.first_name_encrypted:
                        customer.first_name_encrypted = encryption_service.rotate_customer_field(
                            customer.first_name_encrypted
                        )

                    if customer.last_name_encrypted:
                        customer.last_name_encrypted = encryption_service.rotate_customer_field(
                            customer.last_name_encrypted
                        )

                    if customer.phone_encrypted:
                        customer.phone_encrypted = encryption_service.rotate_customer_field(
                            customer.phone_encrypted
                        )

                    db.session.add(customer)

                    # Commit every 100 records
                    if i % 100 == 0:
                        db.session.commit()
                        logger.info(f"Rotated {i}/{total} customer records...")

                rotated += 1

            except Exception as e:
                logger.error(f"Failed to rotate customer {customer.id}: {str(e)}")
                if not dry_run:
                    db.session.rollback()
                continue

        if not dry_run:
            db.session.commit()
            logger.info(f"Successfully rotated {rotated} customer records")
        else:
            logger.info(f"DRY RUN: Would rotate {rotated} customer records")

        return rotated

    except Exception as e:
        logger.error(f"Customer rotation failed: {str(e)}")
        if not dry_run:
            db.session.rollback()
        raise


def rotate_address_fields(dry_run=False):
    """
    Rotate encryption for all address fields.

    Args:
        dry_run: If True, only count records without making changes

    Returns:
        Number of records rotated
    """
    from models.database_models import CustomerAddress

    logger.info("Starting address fields rotation...")

    try:
        addresses = CustomerAddress.query.all()
        total = len(addresses)
        rotated = 0

        logger.info(f"Found {total} address records to rotate")

        for i, address in enumerate(addresses, 1):
            try:
                if not dry_run:
                    # Rotate each encrypted field
                    if address.address_line1_encrypted:
                        address.address_line1_encrypted = encryption_service.rotate_address_field(
                            address.address_line1_encrypted
                        )

                    if address.address_line2_encrypted:
                        address.address_line2_encrypted = encryption_service.rotate_address_field(
                            address.address_line2_encrypted
                        )

                    if address.city_encrypted:
                        address.city_encrypted = encryption_service.rotate_address_field(
                            address.city_encrypted
                        )

                    if address.postal_code_encrypted:
                        address.postal_code_encrypted = encryption_service.rotate_address_field(
                            address.postal_code_encrypted
                        )

                    db.session.add(address)

                    # Commit every 100 records
                    if i % 100 == 0:
                        db.session.commit()
                        logger.info(f"Rotated {i}/{total} address records...")

                rotated += 1

            except Exception as e:
                logger.error(f"Failed to rotate address {address.id}: {str(e)}")
                if not dry_run:
                    db.session.rollback()
                continue

        if not dry_run:
            db.session.commit()
            logger.info(f"Successfully rotated {rotated} address records")
        else:
            logger.info(f"DRY RUN: Would rotate {rotated} address records")

        return rotated

    except Exception as e:
        logger.error(f"Address rotation failed: {str(e)}")
        if not dry_run:
            db.session.rollback()
        raise


def rotate_payment_fields(dry_run=False):
    """
    Rotate encryption for all payment fields.

    Args:
        dry_run: If True, only count records without making changes

    Returns:
        Number of records rotated
    """
    from models.database_models import Payment

    logger.info("Starting payment fields rotation...")

    try:
        payments = Payment.query.all()
        total = len(payments)
        rotated = 0

        logger.info(f"Found {total} payment records to rotate")

        for i, payment in enumerate(payments, 1):
            try:
                if not dry_run:
                    # Rotate each encrypted field
                    if payment.mpesa_phone_encrypted:
                        payment.mpesa_phone_encrypted = encryption_service.rotate_payment_field(
                            payment.mpesa_phone_encrypted
                        )

                    if payment.transaction_id_encrypted:
                        payment.transaction_id_encrypted = encryption_service.rotate_payment_field(
                            payment.transaction_id_encrypted
                        )

                    db.session.add(payment)

                    # Commit every 100 records
                    if i % 100 == 0:
                        db.session.commit()
                        logger.info(f"Rotated {i}/{total} payment records...")

                rotated += 1

            except Exception as e:
                logger.error(f"Failed to rotate payment {payment.id}: {str(e)}")
                if not dry_run:
                    db.session.rollback()
                continue

        if not dry_run:
            db.session.commit()
            logger.info(f"Successfully rotated {rotated} payment records")
        else:
            logger.info(f"DRY RUN: Would rotate {rotated} payment records")

        return rotated

    except Exception as e:
        logger.error(f"Payment rotation failed: {str(e)}")
        if not dry_run:
            db.session.rollback()
        raise


def show_status():
    """Display current encryption key configuration and record counts."""
    logger.info("=== Encryption Key Status ===")

    # Show key counts
    customer_key_count = encryption_service.get_key_count('customer')
    address_key_count = encryption_service.get_key_count('address')
    payment_key_count = encryption_service.get_key_count('payment')

    logger.info(f"Customer keys loaded: {customer_key_count}")
    logger.info(f"Address keys loaded: {address_key_count}")
    logger.info(f"Payment keys loaded: {payment_key_count}")

    # Show record counts (requires database models)
    try:
        from models.database_models import Customer, CustomerAddress, Payment

        customer_count = Customer.query.count()
        address_count = CustomerAddress.query.count()
        payment_count = Payment.query.count()

        logger.info("\n=== Record Counts ===")
        logger.info(f"Customer records: {customer_count}")
        logger.info(f"Address records: {address_count}")
        logger.info(f"Payment records: {payment_count}")

    except Exception as e:
        logger.warning(f"Could not retrieve record counts: {str(e)}")


def main():
    """Main entry point for key rotation script."""
    parser = argparse.ArgumentParser(description='Rotate encryption keys for PII data')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Status command
    subparsers.add_parser('status', help='Show current encryption key status')

    # Rotate command
    rotate_parser = subparsers.add_parser('rotate', help='Rotate encryption keys')
    rotate_parser.add_argument(
        '--type',
        choices=['customer', 'address', 'payment'],
        help='Type of fields to rotate'
    )
    rotate_parser.add_argument(
        '--all',
        action='store_true',
        help='Rotate all field types'
    )
    rotate_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be rotated without making changes'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create Flask app for database access
    app = create_app()

    with app.app_context():
        if args.command == 'status':
            show_status()

        elif args.command == 'rotate':
            if not args.type and not args.all:
                logger.error("Must specify --type or --all for rotation")
                sys.exit(1)

            if args.dry_run:
                logger.info("DRY RUN MODE - No changes will be made")

            logger.info("\n⚠️  WARNING: Encryption key rotation in progress")
            logger.info("Recommended: Create database backup before proceeding")

            if not args.dry_run:
                response = input("\nContinue with rotation? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Rotation cancelled")
                    sys.exit(0)

            total_rotated = 0

            try:
                if args.all or args.type == 'customer':
                    total_rotated += rotate_customer_fields(dry_run=args.dry_run)

                if args.all or args.type == 'address':
                    total_rotated += rotate_address_fields(dry_run=args.dry_run)

                if args.all or args.type == 'payment':
                    total_rotated += rotate_payment_fields(dry_run=args.dry_run)

                if args.dry_run:
                    logger.info(f"\n✅ DRY RUN COMPLETE: Would rotate {total_rotated} total records")
                else:
                    logger.info(f"\n✅ ROTATION COMPLETE: Successfully rotated {total_rotated} total records")

            except Exception as e:
                logger.error(f"\n❌ ROTATION FAILED: {str(e)}")
                sys.exit(1)


if __name__ == '__main__':
    main()
