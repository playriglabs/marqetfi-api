"""Encryption utilities for sensitive data."""

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings

settings = get_settings()


def _get_encryption_key() -> bytes:
    """Generate encryption key from application secret key.

    Uses PBKDF2 to derive a Fernet-compatible key from the SECRET_KEY.
    This ensures we can use the existing SECRET_KEY without storing a separate key.

    Returns:
        bytes: Fernet-compatible encryption key
    """
    # Use SECRET_KEY as password
    password = settings.SECRET_KEY.encode()

    # Use a fixed salt derived from the app name for consistency
    # In production, consider using a stored salt per encrypted value
    salt = b"marqetfi_ostium_encryption_salt"

    # Derive key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_value(value: str) -> str:
    """Encrypt a string value.

    Args:
        value: Plain text string to encrypt

    Returns:
        str: Encrypted string (base64 encoded)

    Raises:
        ValueError: If encryption fails
    """
    if not value:
        return ""

    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(value.encode())
        return str(encrypted.decode())
    except Exception as e:
        raise ValueError(f"Failed to encrypt value: {str(e)}") from e


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt an encrypted string value.

    Args:
        encrypted_value: Encrypted string to decrypt

    Returns:
        str: Decrypted plain text string

    Raises:
        ValueError: If decryption fails (invalid token, wrong key, etc.)
    """
    if not encrypted_value:
        return ""

    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_value.encode())
        return str(decrypted.decode())
    except InvalidToken as e:
        raise ValueError("Failed to decrypt value: Invalid token or wrong key") from e
    except Exception as e:
        raise ValueError(f"Failed to decrypt value: {str(e)}") from e
