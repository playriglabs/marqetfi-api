"""Test encryption utilities."""

from unittest.mock import MagicMock, patch

import pytest

from app.utils.encryption import decrypt_value, encrypt_value


class TestEncryption:
    """Test encryption utilities."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.SECRET_KEY = "test_secret_key_12345678901234567890"
        return settings

    @pytest.mark.asyncio
    async def test_encrypt_value_success(self, mock_settings):
        """Test successful value encryption."""
        with patch("app.utils.encryption.settings", mock_settings):
            plaintext = "sensitive_data_123"

            encrypted = encrypt_value(plaintext)

            assert encrypted is not None
            assert encrypted != plaintext
            assert len(encrypted) > 0

    @pytest.mark.asyncio
    async def test_encrypt_value_empty(self, mock_settings):
        """Test encrypting empty value."""
        with patch("app.utils.encryption.settings", mock_settings):
            result = encrypt_value("")

            assert result == ""

    @pytest.mark.asyncio
    async def test_encrypt_value_none(self, mock_settings):
        """Test encrypting None value."""
        with patch("app.utils.encryption.settings", mock_settings):
            # None is falsy, so should return empty string
            result = encrypt_value(None)  # type: ignore
            assert result == ""

    @pytest.mark.asyncio
    async def test_decrypt_value_success(self, mock_settings):
        """Test successful value decryption."""
        with patch("app.utils.encryption.settings", mock_settings):
            plaintext = "sensitive_data_123"
            encrypted = encrypt_value(plaintext)

            decrypted = decrypt_value(encrypted)

            assert decrypted == plaintext

    @pytest.mark.asyncio
    async def test_decrypt_value_empty(self, mock_settings):
        """Test decrypting empty value."""
        with patch("app.utils.encryption.settings", mock_settings):
            result = decrypt_value("")

            assert result == ""

    @pytest.mark.asyncio
    async def test_decrypt_value_invalid_token(self, mock_settings):
        """Test decrypting invalid token."""
        with patch("app.utils.encryption.settings", mock_settings):
            with pytest.raises(ValueError, match="Invalid token or wrong key"):
                decrypt_value("invalid_encrypted_data")

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip(self, mock_settings):
        """Test encrypt/decrypt roundtrip."""
        with patch("app.utils.encryption.settings", mock_settings):
            test_values = [
                "simple",
                "data_with_123_numbers",
                "data-with-special-chars!@#$%",
                "unicode_测试_データ",
                "very_long_string_" * 100,
            ]

            for plaintext in test_values:
                encrypted = encrypt_value(plaintext)
                decrypted = decrypt_value(encrypted)
                assert decrypted == plaintext, f"Failed for: {plaintext}"

    @pytest.mark.asyncio
    async def test_encrypt_value_exception(self):
        """Test encryption with exception."""
        with patch("app.utils.encryption.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test"
            with patch("app.utils.encryption._get_encryption_key", side_effect=Exception("Error")):
                with pytest.raises(ValueError, match="Failed to encrypt value"):
                    encrypt_value("test")

    @pytest.mark.asyncio
    async def test_decrypt_value_exception(self):
        """Test decryption with exception."""
        with patch("app.utils.encryption.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test"
            with patch("app.utils.encryption._get_encryption_key", side_effect=Exception("Error")):
                with pytest.raises(ValueError, match="Failed to decrypt value"):
                    decrypt_value("test")

