"""Test Ostium admin API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_admin_user, get_db
from app.main import app
from app.services.ostium_admin_service import OstiumAdminService


class TestOstiumAdminAPI:
    """Test Ostium admin API endpoints."""

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
    def mock_ostium_service(self):
        """Create mock Ostium admin service."""
        service = MagicMock(spec=OstiumAdminService)
        service.settings_to_dict = MagicMock(
            return_value={"id": 1, "private_key": "0x123", "rpc_url": "https://rpc.example.com"}
        )
        service.create_settings = AsyncMock(return_value=MagicMock(id=1))
        service.update_settings = AsyncMock(return_value=MagicMock(id=1))
        return service

    def test_get_active_settings_success(self, client, mock_admin_user, db_session):
        """Test successful active settings retrieval."""
        from app.api.v1.admin.ostium import OstiumSettingsRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(OstiumSettingsRepository, "get_active", new_callable=AsyncMock) as mock_repo:
                mock_settings = MagicMock()
                mock_settings.id = 1
                mock_repo.return_value = mock_settings

                with patch("app.api.v1.admin.ostium.OstiumAdminService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.settings_to_dict = MagicMock(return_value={"id": 1})
                    mock_service_class.return_value = mock_service

                    response = client.get(
                        "/api/v1/admin/ostium/settings",
                        headers={"Authorization": "Bearer admin_token"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "id" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_active_settings_not_found(self, client, mock_admin_user, db_session):
        """Test active settings retrieval when not found."""
        from app.api.v1.admin.ostium import OstiumSettingsRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(OstiumSettingsRepository, "get_active", new_callable=AsyncMock, return_value=None):
                response = client.get(
                    "/api/v1/admin/ostium/settings",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_settings_history_success(self, client, mock_admin_user, db_session):
        """Test successful settings history retrieval."""
        from app.api.v1.admin.ostium import OstiumSettingsRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(OstiumSettingsRepository, "get_history", new_callable=AsyncMock) as mock_repo:
                mock_settings = MagicMock()
                mock_settings.id = 1
                mock_repo.return_value = [mock_settings]

                with patch("app.api.v1.admin.ostium.OstiumAdminService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.settings_to_dict = MagicMock(return_value={"id": 1})
                    mock_service_class.return_value = mock_service

                    response = client.get(
                        "/api/v1/admin/ostium/settings/history",
                        headers={"Authorization": "Bearer admin_token"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "items" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_settings_success(self, client, mock_admin_user, mock_ostium_service, db_session):
        """Test successful settings creation."""
        from app.api.v1.admin.ostium import OstiumAdminService

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch("app.api.v1.admin.ostium.OstiumAdminService", return_value=mock_ostium_service):
                response = client.post(
                    "/api/v1/admin/ostium/settings",
                    json={"private_key": "0x123", "rpc_url": "https://rpc.example.com", "activate": True},
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 201
                data = response.json()
                assert "id" in data
        finally:
            app.dependency_overrides.clear()

    def test_activate_settings_success(self, client, mock_admin_user, db_session):
        """Test successful settings activation."""
        from app.api.v1.admin.ostium import OstiumSettingsRepository

        app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user

        try:
            with patch.object(OstiumSettingsRepository, "activate", new_callable=AsyncMock) as mock_repo:
                mock_settings = MagicMock()
                mock_settings.id = 1
                mock_repo.return_value = mock_settings

                with patch("app.api.v1.admin.ostium.OstiumAdminService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.settings_to_dict = MagicMock(return_value={"id": 1})
                    mock_service_class.return_value = mock_service

                    response = client.post(
                        "/api/v1/admin/ostium/settings/1/activate",
                        headers={"Authorization": "Bearer admin_token"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "id" in data
        finally:
            app.dependency_overrides.clear()

