"""Test admin API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_admin_user, get_db
from app.main import app
from app.services.configuration_admin_service import ConfigurationAdminService


class TestAdminAPI:
    """Test admin API endpoints."""

    @pytest.fixture
    def client(self, db_session):
        """Create test client."""
        from app.core.database import get_db

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        return {"id": 1, "email": "admin@example.com", "is_admin": True}

    @pytest.fixture
    def mock_config_service(self):
        """Create mock configuration admin service."""
        service = MagicMock(spec=ConfigurationAdminService)
        service.config_to_dict = MagicMock(return_value={"id": 1, "key": "test", "value": "value"})
        service.create_app_config = AsyncMock(return_value=MagicMock(id=1, key="test", value="value"))
        service.update_app_config = AsyncMock(return_value=MagicMock(id=1, key="test", value="updated"))
        service.create_provider_config = AsyncMock(
            return_value=MagicMock(
                id=1,
                provider_name="ostium",
                provider_type="trading",
                config_data={},
                is_active=True,
                version=1,
                created_by=1,
                created_at=None,
                updated_at=None,
            )
        )
        service.activate_provider_config = AsyncMock(
            return_value=MagicMock(
                id=1,
                provider_name="ostium",
                provider_type="trading",
                config_data={},
                is_active=True,
                version=1,
                created_by=1,
                created_at=None,
                updated_at=None,
            )
        )
        return service

    def test_list_app_configs_success(self, client, mock_admin_user, db_session):
        """Test successful app config listing."""
        from app.api.v1.admin.configuration import AppConfigurationRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(AppConfigurationRepository, "get_all_active", new_callable=AsyncMock) as mock_repo:
                mock_config = MagicMock()
                mock_config.id = 1
                mock_config.key = "test"
                mock_config.value = "value"
                mock_config.category = "general"
                mock_config.is_active = True
                mock_repo.return_value = [mock_config]

                response = client.get(
                    "/api/v1/admin/config/app-configs",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "items" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_app_config_success(self, client, mock_admin_user, db_session):
        """Test successful app config retrieval."""
        from app.api.v1.admin.configuration import AppConfigurationRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(AppConfigurationRepository, "get", new_callable=AsyncMock) as mock_repo:
                mock_config = MagicMock()
                mock_config.id = 1
                mock_config.key = "test"
                mock_config.value = "value"
                mock_repo.return_value = mock_config

                response = client.get(
                    "/api/v1/admin/config/app-configs/1",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()

    def test_get_app_config_not_found(self, client, mock_admin_user, db_session):
        """Test app config retrieval when not found."""
        from app.api.v1.admin.configuration import AppConfigurationRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(AppConfigurationRepository, "get", new_callable=AsyncMock, return_value=None):
                response = client.get(
                    "/api/v1/admin/config/app-configs/999",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_create_app_config_success(self, client, mock_admin_user, mock_config_service, db_session):
        """Test successful app config creation."""
        from app.api.v1.admin.configuration import ConfigurationAdminService

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch("app.api.v1.admin.configuration.ConfigurationAdminService", return_value=mock_config_service):
                response = client.post(
                    "/api/v1/admin/config/app-configs",
                    json={"key": "test", "value": "value", "category": "general"},
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 201
                data = response.json()
                assert "id" in data
        finally:
            app.dependency_overrides.clear()

    def test_list_provider_configs_success(self, client, mock_admin_user, db_session):
        """Test successful provider config listing."""
        from app.api.v1.admin.configuration import ProviderConfigurationRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(ProviderConfigurationRepository, "get_all", new_callable=AsyncMock) as mock_repo:
                mock_config = MagicMock()
                mock_config.id = 1
                mock_config.provider_name = "ostium"
                mock_config.provider_type = "trading"
                mock_config.config_data = {}
                mock_config.is_active = True
                mock_config.version = 1
                mock_config.created_by = 1
                mock_config.created_at = None
                mock_config.updated_at = None
                mock_repo.return_value = [mock_config]

                response = client.get(
                    "/api/v1/admin/config/provider-configs",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "items" in data
        finally:
            app.dependency_overrides.clear()

    def test_activate_provider_config_success(self, client, mock_admin_user, mock_config_service, db_session):
        """Test successful provider config activation."""
        from app.api.v1.admin.configuration import ConfigurationAdminService

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch("app.api.v1.admin.configuration.ConfigurationAdminService", return_value=mock_config_service):
                response = client.post(
                    "/api/v1/admin/config/provider-configs/1/activate",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["is_active"] is True
        finally:
            app.dependency_overrides.clear()

