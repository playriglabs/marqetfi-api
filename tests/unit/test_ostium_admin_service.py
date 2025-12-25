"""Test OstiumAdminService."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.ostium_settings import OstiumSettings
from app.services.ostium_admin_service import OstiumAdminService


class TestOstiumAdminService:
    """Test OstiumAdminService class."""

    @pytest.fixture
    def ostium_service(self):
        """Create OstiumAdminService instance."""
        return OstiumAdminService()

    @pytest.fixture
    def sample_settings(self):
        """Create sample Ostium settings."""
        return MagicMock(spec=OstiumSettings)

    def test_validate_settings_success(self, ostium_service):
        """Test successful settings validation."""
        settings_data = {
            "slippage_percentage": 1.0,
            "default_fee_percentage": 0.1,
            "min_fee": 0.01,
            "max_fee": 0.1,
            "network": "mainnet",
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "rpc_url": "https://rpc.example.com",
            "private_key": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        }

        # Should not raise
        ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_slippage(self, ostium_service):
        """Test settings validation with invalid slippage."""
        settings_data = {"slippage_percentage": 150.0}

        with pytest.raises(ValueError, match="slippage_percentage must be between"):
            ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_fee(self, ostium_service):
        """Test settings validation with invalid fee."""
        settings_data = {"default_fee_percentage": -1.0}

        with pytest.raises(ValueError, match="default_fee_percentage must be between"):
            ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_fee_relationship(self, ostium_service):
        """Test settings validation with invalid min/max fee relationship."""
        settings_data = {"min_fee": 0.1, "max_fee": 0.05}

        with pytest.raises(ValueError, match="min_fee must be less than max_fee"):
            ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_network(self, ostium_service):
        """Test settings validation with invalid network."""
        settings_data = {"network": "invalid"}

        with pytest.raises(ValueError, match="network must be"):
            ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_timeout(self, ostium_service):
        """Test settings validation with invalid timeout."""
        settings_data = {"timeout": 500}

        with pytest.raises(ValueError, match="timeout must be <="):
            ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_retry_attempts(self, ostium_service):
        """Test settings validation with invalid retry attempts."""
        settings_data = {"retry_attempts": 20}

        with pytest.raises(ValueError, match="retry_attempts must be <="):
            ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_rpc_url(self, ostium_service):
        """Test settings validation with invalid RPC URL."""
        settings_data = {"rpc_url": "invalid_url"}

        with pytest.raises(ValueError, match="rpc_url must be a valid"):
            ostium_service.validate_settings(settings_data)

    def test_validate_settings_invalid_private_key(self, ostium_service):
        """Test settings validation with invalid private key."""
        settings_data = {"private_key": "invalid_key"}

        with pytest.raises(ValueError, match="private_key must be a valid hex"):
            ostium_service.validate_settings(settings_data)

    @pytest.mark.asyncio
    async def test_create_settings_success(self, ostium_service, db_session):
        """Test successful settings creation."""
        settings_data = {
            "private_key": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "rpc_url": "https://rpc.example.com",
            "network": "mainnet",
        }

        with patch.object(ostium_service.repository, "deactivate_all", new_callable=AsyncMock), patch.object(
            ostium_service.repository, "create", new_callable=AsyncMock
        ) as mock_create, patch.object(
            ostium_service.repository, "activate", new_callable=AsyncMock
        ) as mock_activate, patch(
            "app.services.ostium_admin_service.encrypt_value", return_value="encrypted_key"
        ):
            mock_settings = MagicMock(spec=OstiumSettings)
            mock_settings.id = 1
            mock_create.return_value = mock_settings
            mock_activate.return_value = mock_settings

            result = await ostium_service.create_settings(
                db=db_session, settings_data=settings_data, created_by=1, activate=True
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_update_settings_success(self, ostium_service, db_session, sample_settings):
        """Test successful settings update."""
        settings_data = {"rpc_url": "https://new-rpc.example.com"}

        with patch.object(ostium_service.repository, "get", new_callable=AsyncMock, return_value=sample_settings), patch.object(
            ostium_service.repository, "update", new_callable=AsyncMock, return_value=sample_settings
        ):
            sample_settings.is_encrypted = False

            result = await ostium_service.update_settings(
                db=db_session, settings_id=1, settings_data=settings_data
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_get_active_config_success(self, ostium_service, db_session):
        """Test successful active config retrieval."""
        mock_settings = MagicMock(spec=OstiumSettings)
        mock_settings.private_key = "0x123"
        mock_settings.rpc_url = "https://rpc.example.com"
        mock_settings.network = "mainnet"
        mock_settings.slippage_percentage = Decimal("1.0")
        mock_settings.timeout = 30
        mock_settings.retry_attempts = 3
        mock_settings.retry_delay = Decimal("1.0")
        mock_settings.is_encrypted = False

        with patch.object(ostium_service.repository, "get_active", new_callable=AsyncMock, return_value=mock_settings), patch(
            "app.services.ostium_admin_service.decrypt_value", return_value="decrypted_key"
        ):
            config = await ostium_service.get_active_config(db_session)

            assert config is not None

    @pytest.mark.asyncio
    async def test_get_active_config_not_found(self, ostium_service, db_session):
        """Test active config retrieval when not found."""
        with patch.object(ostium_service.repository, "get_active", new_callable=AsyncMock, return_value=None):
            config = await ostium_service.get_active_config(db_session)

            assert config is None

    def test_settings_to_dict_success(self, ostium_service, sample_settings):
        """Test converting settings to dict."""
        sample_settings.id = 1
        sample_settings.private_key = "0x123"
        sample_settings.rpc_url = "https://rpc.example.com"
        sample_settings.network = "mainnet"
        sample_settings.slippage_percentage = Decimal("1.0")
        sample_settings.timeout = 30
        sample_settings.retry_attempts = 3
        sample_settings.retry_delay = Decimal("1.0")
        sample_settings.is_encrypted = False
        sample_settings.is_active = True
        sample_settings.created_by = 1
        sample_settings.created_at = None
        sample_settings.updated_at = None

        with patch("app.services.ostium_admin_service.decrypt_value", return_value="decrypted_key"):
            result = ostium_service.settings_to_dict(sample_settings, include_private_key=False)

            assert result["id"] == 1
            assert "private_key" not in result or result.get("private_key") is None

    def test_settings_to_dict_with_private_key(self, ostium_service, sample_settings):
        """Test converting settings to dict with private key."""
        sample_settings.id = 1
        sample_settings.private_key = "0x123"
        sample_settings.is_encrypted = False

        with patch("app.services.ostium_admin_service.decrypt_value", return_value="decrypted_key"):
            result = ostium_service.settings_to_dict(sample_settings, include_private_key=True)

            assert "private_key" in result

