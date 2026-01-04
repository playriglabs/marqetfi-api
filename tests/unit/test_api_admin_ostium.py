"""Test Ostium admin API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_admin_user, get_current_user
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

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            # Patch the repository where it's instantiated in the endpoint
            with patch("app.api.v1.admin.ostium.OstiumSettingsRepository") as mock_repo_class:
                mock_settings = MagicMock()
                mock_settings.id = 1
                mock_settings.enabled = True
                mock_settings.rpc_url = "https://rpc.example.com"
                mock_settings.network = "mainnet"
                mock_settings.verbose = False
                mock_settings.slippage_percentage = 0.5
                mock_settings.default_fee_percentage = 0.1
                mock_settings.min_fee = 0.0
                mock_settings.max_fee = 1.0
                mock_settings.timeout = 30
                mock_settings.retry_attempts = 3
                mock_settings.retry_delay = 1.0
                mock_settings.is_active = True
                mock_settings.version = 1
                mock_settings.created_by = 1
                from datetime import datetime

                mock_settings.created_at = datetime.now()
                mock_settings.updated_at = datetime.now()

                mock_repo_instance = MagicMock()
                mock_repo_instance.get_active = AsyncMock(return_value=mock_settings)
                mock_repo_class.return_value = mock_repo_instance

                # Patch the service where it's instantiated
                with patch("app.api.v1.admin.ostium.OstiumAdminService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.settings_to_dict = MagicMock(
                        return_value={
                            "id": 1,
                            "enabled": True,
                            "rpc_url": "https://rpc.example.com",
                            "network": "mainnet",
                            "verbose": False,
                            "slippage_percentage": 0.5,
                            "default_fee_percentage": 0.1,
                            "min_fee": 0.0,
                            "max_fee": 1.0,
                            "timeout": 30,
                            "retry_attempts": 3,
                            "retry_delay": 1.0,
                            "is_active": True,
                            "version": 1,
                            "created_by": 1,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
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

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            with patch.object(
                OstiumSettingsRepository, "get_active", new_callable=AsyncMock, return_value=None
            ):
                response = client.get(
                    "/api/v1/admin/ostium/settings",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_settings_history_success(self, client, mock_admin_user, db_session):
        """Test successful settings history retrieval."""

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            # Patch the repository where it's instantiated in the endpoint
            with patch("app.api.v1.admin.ostium.OstiumSettingsRepository") as mock_repo_class:
                from datetime import datetime

                mock_settings = MagicMock()
                mock_settings.id = 1
                mock_settings.enabled = True
                mock_settings.rpc_url = "https://rpc.example.com"
                mock_settings.network = "mainnet"
                mock_settings.verbose = False
                mock_settings.slippage_percentage = 0.5
                mock_settings.default_fee_percentage = 0.1
                mock_settings.min_fee = 0.0
                mock_settings.max_fee = 1.0
                mock_settings.timeout = 30
                mock_settings.retry_attempts = 3
                mock_settings.retry_delay = 1.0
                mock_settings.is_active = True
                mock_settings.version = 1
                mock_settings.created_by = 1
                mock_settings.created_at = datetime.now()
                mock_settings.updated_at = datetime.now()

                mock_repo_instance = MagicMock()
                mock_repo_instance.get_history = AsyncMock(return_value=[mock_settings])
                mock_repo_class.return_value = mock_repo_instance

                # Patch the service where it's instantiated
                with patch("app.api.v1.admin.ostium.OstiumAdminService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.settings_to_dict = MagicMock(
                        return_value={
                            "id": 1,
                            "enabled": True,
                            "rpc_url": "https://rpc.example.com",
                            "network": "mainnet",
                            "verbose": False,
                            "slippage_percentage": 0.5,
                            "default_fee_percentage": 0.1,
                            "min_fee": 0.0,
                            "max_fee": 1.0,
                            "timeout": 30,
                            "retry_attempts": 3,
                            "retry_delay": 1.0,
                            "is_active": True,
                            "version": 1,
                            "created_by": 1,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
                    mock_service_class.return_value = mock_service

                    response = client.get(
                        "/api/v1/admin/ostium/settings/history",
                        headers={"Authorization": "Bearer admin_token"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "items" in data
                    assert "total" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_settings_success(
        self, client, mock_admin_user, mock_ostium_service, db_session
    ):
        """Test successful settings creation."""

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            from datetime import datetime

            # Create a mock settings object that will be returned
            mock_settings = MagicMock()
            mock_settings.id = 1
            mock_settings.enabled = True
            mock_settings.rpc_url = "https://rpc.example.com"
            mock_settings.network = "mainnet"
            mock_settings.verbose = False
            mock_settings.slippage_percentage = 1.0
            mock_settings.default_fee_percentage = 0.1
            mock_settings.min_fee = 0.01
            mock_settings.max_fee = 10.0
            mock_settings.timeout = 30
            mock_settings.retry_attempts = 3
            mock_settings.retry_delay = 1.0
            mock_settings.is_active = True
            mock_settings.version = 1
            mock_settings.created_by = 1
            mock_settings.created_at = datetime.now()
            mock_settings.updated_at = datetime.now()

            # Mock the service's create_settings method
            mock_ostium_service.create_settings = AsyncMock(return_value=mock_settings)
            mock_ostium_service.settings_to_dict = MagicMock(
                return_value={
                    "id": 1,
                    "enabled": True,
                    "rpc_url": "https://rpc.example.com",
                    "network": "mainnet",
                    "verbose": False,
                    "slippage_percentage": 1.0,
                    "default_fee_percentage": 0.1,
                    "min_fee": 0.01,
                    "max_fee": 10.0,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "retry_delay": 1.0,
                    "is_active": True,
                    "version": 1,
                    "created_by": 1,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            )

            with patch(
                "app.api.v1.admin.ostium.OstiumAdminService", return_value=mock_ostium_service
            ):
                response = client.post(
                    "/api/v1/admin/ostium/settings",
                    json={
                        "private_key": "0x123",
                        "rpc_url": "https://rpc.example.com",
                        "activate": True,
                    },
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 201
                data = response.json()
                assert "id" in data
        finally:
            app.dependency_overrides.clear()

    def test_activate_settings_success(self, client, mock_admin_user, db_session):
        """Test successful settings activation."""

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            from datetime import datetime

            # Patch the repository where it's instantiated
            with patch("app.api.v1.admin.ostium.OstiumSettingsRepository") as mock_repo_class:
                mock_settings = MagicMock()
                mock_settings.id = 1
                mock_settings.enabled = True
                mock_settings.rpc_url = "https://rpc.example.com"
                mock_settings.network = "mainnet"
                mock_settings.verbose = False
                mock_settings.slippage_percentage = 0.5
                mock_settings.default_fee_percentage = 0.1
                mock_settings.min_fee = 0.0
                mock_settings.max_fee = 1.0
                mock_settings.timeout = 30
                mock_settings.retry_attempts = 3
                mock_settings.retry_delay = 1.0
                mock_settings.is_active = True
                mock_settings.version = 1
                mock_settings.created_by = 1
                mock_settings.created_at = datetime.now()
                mock_settings.updated_at = datetime.now()

                mock_repo_instance = MagicMock()
                mock_repo_instance.activate = AsyncMock(return_value=mock_settings)
                mock_repo_class.return_value = mock_repo_instance

                # Patch the service where it's instantiated
                with patch("app.api.v1.admin.ostium.OstiumAdminService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.settings_to_dict = MagicMock(
                        return_value={
                            "id": 1,
                            "enabled": True,
                            "rpc_url": "https://rpc.example.com",
                            "network": "mainnet",
                            "verbose": False,
                            "slippage_percentage": 0.5,
                            "default_fee_percentage": 0.1,
                            "min_fee": 0.0,
                            "max_fee": 1.0,
                            "timeout": 30,
                            "retry_attempts": 3,
                            "retry_delay": 1.0,
                            "is_active": True,
                            "version": 1,
                            "created_by": 1,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
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
