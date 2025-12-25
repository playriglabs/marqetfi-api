"""Test ConfigurationAdminService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.app_configuration import AppConfiguration, ProviderConfiguration
from app.services.configuration_admin_service import ConfigurationAdminService


class TestConfigurationAdminService:
    """Test ConfigurationAdminService class."""

    @pytest.fixture
    def config_service(self):
        """Create ConfigurationAdminService instance."""
        return ConfigurationAdminService()

    @pytest.fixture
    def sample_app_config(self):
        """Create sample app configuration."""
        return MagicMock(spec=AppConfiguration)

    @pytest.mark.asyncio
    async def test_create_app_config_success(self, config_service, db_session):
        """Test successful app config creation."""
        config_data = {
            "config_key": "test_key",
            "config_value": "test_value",
            "category": "general",
            "is_encrypted": False,
        }

        with patch.object(config_service.app_config_repo, "create", new_callable=AsyncMock) as mock_create:
            mock_config = MagicMock(spec=AppConfiguration)
            mock_config.id = 1
            mock_create.return_value = mock_config

            result = await config_service.create_app_config(
                db=db_session, config_data=config_data, created_by=1
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_create_app_config_encrypted(self, config_service, db_session):
        """Test creating encrypted app config."""
        config_data = {
            "config_key": "secret_key",
            "config_value": "secret_value",
            "category": "security",
            "is_encrypted": True,
        }

        with patch("app.services.configuration_admin_service.encrypt_value", return_value="encrypted_value"), patch.object(
            config_service.app_config_repo, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_config = MagicMock(spec=AppConfiguration)
            mock_config.id = 1
            mock_create.return_value = mock_config

            result = await config_service.create_app_config(
                db=db_session, config_data=config_data, created_by=1
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_update_app_config_success(self, config_service, db_session, sample_app_config):
        """Test successful app config update."""
        config_data = {"config_value": "updated_value"}

        with patch.object(config_service.app_config_repo, "get", new_callable=AsyncMock, return_value=sample_app_config), patch.object(
            config_service.app_config_repo, "update", new_callable=AsyncMock, return_value=sample_app_config
        ):
            sample_app_config.is_encrypted = False

            result = await config_service.update_app_config(
                db=db_session, config_id=1, config_data=config_data
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_update_app_config_not_found(self, config_service, db_session):
        """Test updating app config when not found."""
        with patch.object(config_service.app_config_repo, "get", new_callable=AsyncMock, return_value=None):
            with pytest.raises(ValueError, match="Configuration not found"):
                await config_service.update_app_config(
                    db=db_session, config_id=999, config_data={"config_value": "value"}
                )

    @pytest.mark.asyncio
    async def test_create_provider_config_success(self, config_service, db_session):
        """Test successful provider config creation."""
        config_data = {
            "provider_name": "ostium",
            "provider_type": "trading",
            "config_data": {"key": "value"},
        }

        with patch.object(
            config_service.provider_config_repo, "create", new_callable=AsyncMock
        ) as mock_create, patch.object(
            config_service.provider_config_repo, "deactivate_all", new_callable=AsyncMock
        ) as mock_deactivate, patch.object(
            config_service.provider_config_repo, "activate", new_callable=AsyncMock
        ) as mock_activate:
            mock_config = MagicMock(spec=ProviderConfiguration)
            mock_config.id = 1
            mock_create.return_value = mock_config
            mock_activate.return_value = mock_config

            result = await config_service.create_provider_config(
                db=db_session, config_data=config_data, created_by=1, activate=True
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_activate_provider_config_success(self, config_service, db_session):
        """Test successful provider config activation."""
        with patch.object(
            config_service.provider_config_repo, "get", new_callable=AsyncMock
        ) as mock_get, patch.object(
            config_service.provider_config_repo, "deactivate_all", new_callable=AsyncMock
        ) as mock_deactivate, patch.object(
            config_service.provider_config_repo, "activate", new_callable=AsyncMock
        ) as mock_activate:
            mock_config = MagicMock(spec=ProviderConfiguration)
            mock_config.id = 1
            mock_config.provider_name = "ostium"
            mock_get.return_value = mock_config
            mock_activate.return_value = mock_config

            result = await config_service.activate_provider_config(db=db_session, config_id=1)

            assert result is not None

    @pytest.mark.asyncio
    async def test_activate_provider_config_not_found(self, config_service, db_session):
        """Test activating provider config when not found."""
        with patch.object(config_service.provider_config_repo, "get", new_callable=AsyncMock, return_value=None):
            with pytest.raises(ValueError, match="Configuration not found"):
                await config_service.activate_provider_config(db=db_session, config_id=999)

    def test_config_to_dict_app_config(self, config_service, sample_app_config):
        """Test converting app config to dict."""
        sample_app_config.id = 1
        sample_app_config.config_key = "test_key"
        sample_app_config.config_value = "test_value"
        sample_app_config.category = "general"
        sample_app_config.is_encrypted = False
        sample_app_config.is_active = True
        sample_app_config.created_by = 1
        sample_app_config.created_at = None
        sample_app_config.updated_at = None

        with patch("app.services.configuration_admin_service.decrypt_value", return_value="decrypted_value"):
            result = config_service.config_to_dict(sample_app_config, include_private_key=False)

            assert result["id"] == 1
            assert result["config_key"] == "test_key"

