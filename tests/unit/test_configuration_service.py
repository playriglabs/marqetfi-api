"""Test ConfigurationService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.configuration_service import ConfigurationService


class TestConfigurationService:
    """Test ConfigurationService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_db):
        """Create ConfigurationService instance."""
        return ConfigurationService(db=mock_db)

    @pytest.fixture
    def service_no_db(self):
        """Create ConfigurationService without database."""
        return ConfigurationService(db=None)

    @pytest.mark.asyncio
    async def test_get_app_config_found(self, service, mock_db):
        """Test getting app config from database."""
        mock_config = MagicMock()
        mock_config.config_value = "test_value"
        mock_config.is_encrypted = False
        mock_config.config_type = "string"

        service.app_config_repo.get_by_key = AsyncMock(return_value=mock_config)

        result = await service.get_app_config("test_key")

        assert result == "test_value"
        service.app_config_repo.get_by_key.assert_called_once_with(mock_db, "test_key")

    @pytest.mark.asyncio
    async def test_get_app_config_encrypted(self, service, mock_db):
        """Test getting encrypted app config."""
        mock_config = MagicMock()
        mock_config.config_value = "encrypted_value"
        mock_config.is_encrypted = True
        mock_config.config_type = "string"

        service.app_config_repo.get_by_key = AsyncMock(return_value=mock_config)

        with patch("app.services.configuration_service.decrypt_value") as mock_decrypt:
            mock_decrypt.return_value = "decrypted_value"

            result = await service.get_app_config("test_key")

            assert result == "decrypted_value"
            mock_decrypt.assert_called_once_with("encrypted_value")

    @pytest.mark.asyncio
    async def test_get_app_config_not_found(self, service, mock_db):
        """Test getting app config when not found."""
        service.app_config_repo.get_by_key = AsyncMock(return_value=None)

        result = await service.get_app_config("test_key", default="default_value")

        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_get_app_config_no_db(self, service_no_db):
        """Test getting app config without database."""
        result = await service_no_db.get_app_config("test_key", default="default_value")

        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_get_provider_config_found(self, service, mock_db):
        """Test getting provider config from database."""
        mock_config = MagicMock()
        mock_config.config_data = {"key": "value"}

        service.provider_config_repo.get_active_config = AsyncMock(return_value=mock_config)

        result = await service.get_provider_config("ostium", "trading")

        assert result == {"key": "value"}
        service.provider_config_repo.get_active_config.assert_called_once_with(
            mock_db, "ostium", "trading"
        )

    @pytest.mark.asyncio
    async def test_get_provider_config_not_found(self, service, mock_db):
        """Test getting provider config when not found."""
        service.provider_config_repo.get_active_config = AsyncMock(return_value=None)

        result = await service.get_provider_config("ostium", "trading")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_app_configs(self, service, mock_db):
        """Test getting all app configs."""
        mock_config1 = MagicMock()
        mock_config1.config_key = "key1"
        mock_config1.config_value = "value1"
        mock_config1.is_encrypted = False
        mock_config1.config_type = "string"

        mock_config2 = MagicMock()
        mock_config2.config_key = "key2"
        mock_config2.config_value = "value2"
        mock_config2.is_encrypted = False
        mock_config2.config_type = "string"

        service.app_config_repo.get_all_active = AsyncMock(
            return_value=[mock_config1, mock_config2]
        )

        result = await service.get_all_app_configs()

        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_get_all_app_configs_with_category(self, service, mock_db):
        """Test getting app configs with category."""
        mock_config = MagicMock()
        mock_config.config_key = "key1"
        mock_config.config_value = "value1"
        mock_config.is_encrypted = False
        mock_config.config_type = "string"

        service.app_config_repo.get_by_category = AsyncMock(return_value=[mock_config])

        result = await service.get_all_app_configs(category="test_category")

        assert result == {"key1": "value1"}

    def test_convert_value_int(self, service):
        """Test converting value to int."""
        assert service._convert_value("123", "int") == 123
        assert service._convert_value("0", "int") == 0

    def test_convert_value_float(self, service):
        """Test converting value to float."""
        assert service._convert_value("123.45", "float") == 123.45
        assert service._convert_value("0.0", "float") == 0.0

    def test_convert_value_bool(self, service):
        """Test converting value to bool."""
        assert service._convert_value("true", "bool") is True
        assert service._convert_value("1", "bool") is True
        assert service._convert_value("yes", "bool") is True
        assert service._convert_value("false", "bool") is False
        assert service._convert_value("0", "bool") is False

    def test_convert_value_json(self, service):
        """Test converting value to JSON."""
        import json

        json_str = json.dumps({"key": "value"})
        result = service._convert_value(json_str, "json")
        assert result == {"key": "value"}

    def test_convert_value_string(self, service):
        """Test converting value to string."""
        assert service._convert_value("test", "string") == "test"

    def test_get_env_config(self):
        """Test getting config from environment."""
        with patch("app.services.configuration_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(test_key="env_value")

            result = ConfigurationService.get_env_config("test_key")

            assert result == "env_value"

    def test_get_env_config_default(self):
        """Test getting env config with default."""
        with patch("app.services.configuration_service.get_settings") as mock_settings:
            # Mock settings object without the key - getattr will use default
            mock_settings_obj = MagicMock()
            # Remove the attribute so getattr returns default
            del mock_settings_obj.nonexistent_key
            mock_settings.return_value = mock_settings_obj

            result = ConfigurationService.get_env_config("nonexistent_key", default="default")

            assert result == "default"

    @pytest.mark.asyncio
    async def test_get_config_with_fallback_db(self, service, mock_db):
        """Test getting config with database fallback."""
        mock_config = MagicMock()
        mock_config.config_value = "db_value"
        mock_config.is_encrypted = False
        mock_config.config_type = "string"

        service.app_config_repo.get_by_key = AsyncMock(return_value=mock_config)

        result = await service.get_config_with_fallback("test_key")

        assert result == "db_value"

    @pytest.mark.asyncio
    async def test_get_config_with_fallback_env(self, service, mock_db):
        """Test getting config with environment fallback."""
        service.app_config_repo.get_by_key = AsyncMock(return_value=None)

        with patch("app.services.configuration_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(test_key="env_value")

            result = await service.get_config_with_fallback("test_key")

            assert result == "env_value"

    @pytest.mark.asyncio
    async def test_get_config_with_fallback_default(self, service, mock_db):
        """Test getting config with default fallback."""
        service.app_config_repo.get_by_key = AsyncMock(return_value=None)

        with patch("app.services.configuration_service.get_settings") as mock_settings:
            # Mock settings object without the key - getattr will use default
            mock_settings_obj = MagicMock()
            # Remove the attribute so getattr returns default
            if hasattr(mock_settings_obj, "test_key"):
                del mock_settings_obj.test_key
            mock_settings.return_value = mock_settings_obj

            result = await service.get_config_with_fallback("test_key", default="default_value")

            assert result == "default_value"

