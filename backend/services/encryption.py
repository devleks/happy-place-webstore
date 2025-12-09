"""
Encryption Service for Happy Place Boutique

Implements MultiFernet-based encryption for customer PII data with support for
zero-downtime key rotation.

Features:
- MultiFernet encryption (AES-128-CBC + HMAC-SHA256)
- Separate key sets for customer, address, and payment data
- Zero-downtime key rotation support
- SHA-256 email hashing for searchable indexes
- Audit logging of decryption operations

Usage:
    from services.encryption import encryption_service

    # Encrypt customer data
    encrypted = encryption_service.encrypt_customer_field("John Doe")

    # Decrypt customer data
    decrypted = encryption_service.decrypt_customer_field(encrypted)

    # Hash email for search
    email_hash = encryption_service.hash_email("customer@example.com")
"""

import os
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, MultiFernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Encryption service using MultiFernet for PII data protection.

    Supports multiple encryption keys per data type to enable zero-downtime
    key rotation. Always encrypts with the first (newest) key, but can
    decrypt with any key in the list.
    """

    def __init__(self):
        """Initialize MultiFernet ciphers for different data types."""
        self.customer_cipher = self._create_multi_cipher('CUSTOMER_ENCRYPTION_KEYS')
        self.address_cipher = self._create_multi_cipher('ADDRESS_ENCRYPTION_KEYS')
        self.payment_cipher = self._create_multi_cipher('PAYMENT_ENCRYPTION_KEYS')

        logger.info("EncryptionService initialized with MultiFernet support")

    def _load_multi_keys(self, env_var: str) -> list:
        """
        Load multiple encryption keys from environment variable.

        Args:
            env_var: Name of environment variable containing comma-separated keys

        Returns:
            List of Fernet key bytes

        Raises:
            ValueError: If no keys are found or keys are invalid
        """
        keys_str = os.environ.get(env_var)

        if not keys_str:
            # For development, generate a single key if none exists
            logger.warning(f"{env_var} not found. Generating temporary key for development.")
            key = Fernet.generate_key()
            return [key]

        # Split comma-separated keys and strip whitespace
        keys = [key.strip().encode() if isinstance(key.strip(), str) else key.strip()
                for key in keys_str.split(',')]

        if not keys:
            raise ValueError(f"No encryption keys found in {env_var}")

        # Validate all keys
        for i, key in enumerate(keys):
            try:
                # Test key validity by creating Fernet instance
                Fernet(key)
            except Exception as e:
                raise ValueError(f"Invalid encryption key at index {i} in {env_var}: {str(e)}")

        logger.info(f"Loaded {len(keys)} encryption key(s) from {env_var}")
        return keys

    def _create_multi_cipher(self, env_var: str) -> MultiFernet:
        """
        Create MultiFernet cipher from environment variable keys.

        Args:
            env_var: Name of environment variable containing keys

        Returns:
            MultiFernet instance
        """
        keys = self._load_multi_keys(env_var)
        fernet_instances = [Fernet(key) for key in keys]
        return MultiFernet(fernet_instances)

    # ========================
    # CUSTOMER DATA ENCRYPTION
    # ========================

    def encrypt_customer_field(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt customer PII field (name, phone, etc).

        Args:
            plaintext: The plaintext string to encrypt

        Returns:
            Base64-encoded encrypted string, or None if input is None
        """
        if plaintext is None or plaintext == '':
            return None

        try:
            encrypted_bytes = self.customer_cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Customer field encryption failed: {str(e)}")
            raise

    def decrypt_customer_field(self, ciphertext: Optional[str], log_access: bool = True) -> Optional[str]:
        """
        Decrypt customer PII field.

        MultiFernet will try all keys in order until one succeeds.

        Args:
            ciphertext: The encrypted string to decrypt
            log_access: Whether to log this decryption (for audit trail)

        Returns:
            Decrypted plaintext string, or None if input is None

        Raises:
            InvalidToken: If decryption fails with all keys
        """
        if ciphertext is None or ciphertext == '':
            return None

        try:
            decrypted_bytes = self.customer_cipher.decrypt(ciphertext.encode('utf-8'))

            if log_access:
                logger.info("Customer field decrypted (audit log entry should be created)")

            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            logger.error("Customer field decryption failed: Invalid token (all keys failed)")
            raise
        except Exception as e:
            logger.error(f"Customer field decryption failed: {str(e)}")
            raise

    def rotate_customer_field(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Rotate customer field encryption to newest key.

        Decrypts with any available key, then re-encrypts with the first (newest) key.

        Args:
            ciphertext: The encrypted string to rotate

        Returns:
            Re-encrypted string with newest key, or None if input is None
        """
        if ciphertext is None or ciphertext == '':
            return None

        try:
            rotated_bytes = self.customer_cipher.rotate(ciphertext.encode('utf-8'))
            return rotated_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Customer field rotation failed: {str(e)}")
            raise

    # ========================
    # ADDRESS DATA ENCRYPTION
    # ========================

    def encrypt_address_field(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt address field (street, city, postal code, etc).

        Args:
            plaintext: The plaintext string to encrypt

        Returns:
            Base64-encoded encrypted string, or None if input is None
        """
        if plaintext is None or plaintext == '':
            return None

        try:
            encrypted_bytes = self.address_cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Address field encryption failed: {str(e)}")
            raise

    def decrypt_address_field(self, ciphertext: Optional[str], log_access: bool = True) -> Optional[str]:
        """
        Decrypt address field.

        Args:
            ciphertext: The encrypted string to decrypt
            log_access: Whether to log this decryption (for audit trail)

        Returns:
            Decrypted plaintext string, or None if input is None
        """
        if ciphertext is None or ciphertext == '':
            return None

        try:
            decrypted_bytes = self.address_cipher.decrypt(ciphertext.encode('utf-8'))

            if log_access:
                logger.info("Address field decrypted (audit log entry should be created)")

            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            logger.error("Address field decryption failed: Invalid token (all keys failed)")
            raise
        except Exception as e:
            logger.error(f"Address field decryption failed: {str(e)}")
            raise

    def rotate_address_field(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Rotate address field encryption to newest key.

        Args:
            ciphertext: The encrypted string to rotate

        Returns:
            Re-encrypted string with newest key, or None if input is None
        """
        if ciphertext is None or ciphertext == '':
            return None

        try:
            rotated_bytes = self.address_cipher.rotate(ciphertext.encode('utf-8'))
            return rotated_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Address field rotation failed: {str(e)}")
            raise

    # ========================
    # PAYMENT DATA ENCRYPTION
    # ========================

    def encrypt_payment_field(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt payment field (M-Pesa phone, transaction ID, etc).

        Args:
            plaintext: The plaintext string to encrypt

        Returns:
            Base64-encoded encrypted string, or None if input is None
        """
        if plaintext is None or plaintext == '':
            return None

        try:
            encrypted_bytes = self.payment_cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Payment field encryption failed: {str(e)}")
            raise

    def decrypt_payment_field(self, ciphertext: Optional[str], log_access: bool = True) -> Optional[str]:
        """
        Decrypt payment field.

        Args:
            ciphertext: The encrypted string to decrypt
            log_access: Whether to log this decryption (for audit trail)

        Returns:
            Decrypted plaintext string, or None if input is None
        """
        if ciphertext is None or ciphertext == '':
            return None

        try:
            decrypted_bytes = self.payment_cipher.decrypt(ciphertext.encode('utf-8'))

            if log_access:
                logger.info("Payment field decrypted (audit log entry should be created)")

            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            logger.error("Payment field decryption failed: Invalid token (all keys failed)")
            raise
        except Exception as e:
            logger.error(f"Payment field decryption failed: {str(e)}")
            raise

    def rotate_payment_field(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Rotate payment field encryption to newest key.

        Args:
            ciphertext: The encrypted string to rotate

        Returns:
            Re-encrypted string with newest key, or None if input is None
        """
        if ciphertext is None or ciphertext == '':
            return None

        try:
            rotated_bytes = self.payment_cipher.rotate(ciphertext.encode('utf-8'))
            return rotated_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Payment field rotation failed: {str(e)}")
            raise

    # ========================
    # EMAIL HASHING
    # ========================

    @staticmethod
    def hash_email(email: str) -> str:
        """
        Create SHA-256 hash of email for searchable index.

        This enables fast email lookups during login without storing
        plaintext emails. The hash is deterministic (same email always
        produces same hash) and collision-resistant.

        Args:
            email: Email address to hash (will be lowercased)

        Returns:
            64-character hexadecimal SHA-256 hash
        """
        if not email:
            raise ValueError("Email cannot be empty")

        # Normalize email to lowercase for consistent hashing
        normalized_email = email.lower().strip()

        # Create SHA-256 hash
        hash_object = hashlib.sha256(normalized_email.encode('utf-8'))
        email_hash = hash_object.hexdigest()

        return email_hash

    # ========================
    # KEY MANAGEMENT
    # ========================

    @staticmethod
    def generate_fernet_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded Fernet key as string
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')

    def get_key_count(self, key_type: str = 'customer') -> int:
        """
        Get the number of active keys for a given data type.

        Args:
            key_type: Type of keys ('customer', 'address', or 'payment')

        Returns:
            Number of active encryption keys
        """
        if key_type == 'customer':
            return len(self.customer_cipher._fernets)
        elif key_type == 'address':
            return len(self.address_cipher._fernets)
        elif key_type == 'payment':
            return len(self.payment_cipher._fernets)
        else:
            raise ValueError(f"Invalid key_type: {key_type}")


# Singleton instance
encryption_service = EncryptionService()


# Convenience functions for direct import
def encrypt_customer(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt customer PII field."""
    return encryption_service.encrypt_customer_field(plaintext)


def decrypt_customer(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt customer PII field."""
    return encryption_service.decrypt_customer_field(ciphertext)


def encrypt_address(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt address field."""
    return encryption_service.encrypt_address_field(plaintext)


def decrypt_address(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt address field."""
    return encryption_service.decrypt_address_field(ciphertext)


def encrypt_payment(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt payment field."""
    return encryption_service.encrypt_payment_field(plaintext)


def decrypt_payment(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt payment field."""
    return encryption_service.decrypt_payment_field(ciphertext)


def hash_email(email: str) -> str:
    """Hash email for searchable index."""
    return encryption_service.hash_email(email)
