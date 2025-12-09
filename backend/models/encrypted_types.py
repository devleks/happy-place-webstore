"""
SQLAlchemy Custom Encrypted Column Types

Provides transparent encryption/decryption for PII fields using MultiFernet.
These custom types automatically encrypt data on INSERT/UPDATE and decrypt
on SELECT, making encryption transparent to application code.

Usage:
    from models.encrypted_types import EncryptedCustomerString

    class Customer(db.Model):
        first_name = Column(EncryptedCustomerString)
        last_name = Column(EncryptedCustomerString)
        phone = Column(EncryptedCustomerString)

Features:
- Transparent encryption/decryption
- MultiFernet support (zero-downtime key rotation)
- Separate key sets for customer, address, payment data
- Handles NULL values correctly
- Type annotations for IDE support
"""

from sqlalchemy.types import TypeDecorator, Text
from typing import Optional
import logging

# Import encryption service
from services.encryption import encryption_service

logger = logging.getLogger(__name__)


class EncryptedCustomerString(TypeDecorator):
    """
    SQLAlchemy type for encrypted customer PII fields.

    Automatically encrypts on write and decrypts on read using
    the customer encryption keys from MultiFernet.

    Fields: first_name, last_name, phone, etc.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Encrypt value before storing in database.

        Args:
            value: Plaintext string to encrypt
            dialect: SQLAlchemy dialect (unused)

        Returns:
            Encrypted string or None
        """
        if value is None or value == '':
            return None

        try:
            encrypted = encryption_service.encrypt_customer_field(value)
            return encrypted
        except Exception as e:
            logger.error(f"Failed to encrypt customer field: {str(e)}")
            raise

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Decrypt value after retrieving from database.

        Args:
            value: Encrypted string from database
            dialect: SQLAlchemy dialect (unused)

        Returns:
            Decrypted plaintext string or None
        """
        if value is None or value == '':
            return None

        try:
            decrypted = encryption_service.decrypt_customer_field(value, log_access=True)
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt customer field: {str(e)}")
            # Return None instead of raising to prevent cascading failures
            # In production, you might want to raise an exception instead
            return None


class EncryptedAddressString(TypeDecorator):
    """
    SQLAlchemy type for encrypted address fields.

    Automatically encrypts on write and decrypts on read using
    the address encryption keys from MultiFernet.

    Fields: address_line1, address_line2, city, postal_code, etc.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Encrypt value before storing in database.

        Args:
            value: Plaintext string to encrypt
            dialect: SQLAlchemy dialect (unused)

        Returns:
            Encrypted string or None
        """
        if value is None or value == '':
            return None

        try:
            encrypted = encryption_service.encrypt_address_field(value)
            return encrypted
        except Exception as e:
            logger.error(f"Failed to encrypt address field: {str(e)}")
            raise

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Decrypt value after retrieving from database.

        Args:
            value: Encrypted string from database
            dialect: SQLAlchemy dialect (unused)

        Returns:
            Decrypted plaintext string or None
        """
        if value is None or value == '':
            return None

        try:
            decrypted = encryption_service.decrypt_address_field(value, log_access=True)
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt address field: {str(e)}")
            return None


class EncryptedPaymentString(TypeDecorator):
    """
    SQLAlchemy type for encrypted payment fields.

    Automatically encrypts on write and decrypts on read using
    the payment encryption keys from MultiFernet.

    Fields: mpesa_phone, transaction_id, etc.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Encrypt value before storing in database.

        Args:
            value: Plaintext string to encrypt
            dialect: SQLAlchemy dialect (unused)

        Returns:
            Encrypted string or None
        """
        if value is None or value == '':
            return None

        try:
            encrypted = encryption_service.encrypt_payment_field(value)
            return encrypted
        except Exception as e:
            logger.error(f"Failed to encrypt payment field: {str(e)}")
            raise

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Decrypt value after retrieving from database.

        Args:
            value: Encrypted string from database
            dialect: SQLAlchemy dialect (unused)

        Returns:
            Decrypted plaintext string or None
        """
        if value is None or value == '':
            return None

        try:
            decrypted = encryption_service.decrypt_payment_field(value, log_access=True)
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt payment field: {str(e)}")
            return None


# Example usage in models:
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from models.encrypted_types import EncryptedCustomerString, EncryptedAddressString
from services.encryption import hash_email

class Customer(db.Model):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True)

    # Dual email storage: hash for search, encrypted for privacy
    email_hash = Column(String(64), unique=True, index=True, nullable=False)
    email_encrypted = Column(EncryptedCustomerString, nullable=False)

    # Encrypted PII fields
    first_name_encrypted = Column(EncryptedCustomerString)
    last_name_encrypted = Column(EncryptedCustomerString)
    phone_encrypted = Column(EncryptedCustomerString)

    # Password (one-way hash, NOT encrypted)
    password_hash = Column(String(255), nullable=False)

    # GDPR fields
    gdpr_consent = Column(Boolean, default=False)
    anonymized = Column(Boolean, default=False)

    @property
    def email(self):
        '''Get decrypted email'''
        return self.email_encrypted

    @email.setter
    def email(self, value):
        '''Set email (both hash and encrypted)'''
        self.email_hash = hash_email(value)
        self.email_encrypted = value

    @property
    def first_name(self):
        '''Get decrypted first name'''
        return self.first_name_encrypted

    @first_name.setter
    def first_name(self, value):
        '''Set encrypted first name'''
        self.first_name_encrypted = value


class CustomerAddress(db.Model):
    __tablename__ = 'customer_addresses'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)

    # Encrypted address fields
    address_line1_encrypted = Column(EncryptedAddressString, nullable=False)
    address_line2_encrypted = Column(EncryptedAddressString)
    city_encrypted = Column(EncryptedAddressString, nullable=False)
    postal_code_encrypted = Column(EncryptedAddressString)

    # Non-sensitive fields (not encrypted)
    country = Column(String(100), nullable=False, default='Kenya')
    is_default = Column(Boolean, default=False)

    @property
    def address_line1(self):
        return self.address_line1_encrypted

    @address_line1.setter
    def address_line1(self, value):
        self.address_line1_encrypted = value
"""
