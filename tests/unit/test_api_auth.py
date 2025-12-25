"""Test authentication API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user, get_db
from app.main import app
from app.models.user import User
from app.services.auth_service import AuthenticationService


class TestAuthAPI:
    """Test authentication API endpoints."""

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
    def sample_user(self):
        """Create sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
        )

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service."""
        service = MagicMock(spec=AuthenticationService)
        service.register_with_email = AsyncMock(
            return_value=(
                User(id=1, email="test@example.com", username="testuser", is_active=True),
                {"access_token": "token", "refresh_token": "refresh"},
            )
        )
        service.login_with_email = AsyncMock(
            return_value=(
                User(id=1, email="test@example.com", username="testuser", is_active=True),
                {"access_token": "token", "refresh_token": "refresh"},
            )
        )
        service.refresh_access_token = AsyncMock(
            return_value={"access_token": "new_token", "refresh_token": "refresh"}
        )
        service.handle_provider_authentication = AsyncMock(
            return_value=(
                User(id=1, email="test@example.com", username="testuser", is_active=True),
                {"access_token": "token", "refresh_token": "refresh"},
            )
        )
        return service

    def test_register_success(self, client, mock_auth_service):
        """Test successful user registration."""
        from app.api.v1.auth import auth_service

        app.dependency_overrides[auth_service] = lambda: mock_auth_service

        try:
            with patch("app.api.v1.auth.auth_service", mock_auth_service):
                response = client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "test@example.com",
                        "password": "password123",
                        "username": "testuser",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
        finally:
            app.dependency_overrides.clear()

    def test_login_success(self, client, mock_auth_service):
        """Test successful user login."""
        from app.api.v1.auth import auth_service

        app.dependency_overrides[auth_service] = lambda: mock_auth_service

        try:
            with patch("app.api.v1.auth.auth_service", mock_auth_service):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@example.com", "password": "password123"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
        finally:
            app.dependency_overrides.clear()

    def test_refresh_token_success(self, client, mock_auth_service):
        """Test successful token refresh."""
        from app.api.v1.auth import auth_service

        app.dependency_overrides[auth_service] = lambda: mock_auth_service

        try:
            with patch("app.api.v1.auth.auth_service", mock_auth_service):
                response = client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": "refresh_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
        finally:
            app.dependency_overrides.clear()

    def test_provider_login_success(self, client, mock_auth_service):
        """Test successful provider login."""
        from app.api.v1.auth import auth_service

        app.dependency_overrides[auth_service] = lambda: mock_auth_service

        try:
            with patch("app.api.v1.auth.auth_service", mock_auth_service):
                response = client.post(
                    "/api/v1/auth/provider/login",
                    json={"access_token": "provider_token", "provider": "privy"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
        finally:
            app.dependency_overrides.clear()

    def test_logout_success(self, client, sample_user):
        """Test successful logout."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            response = client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
        finally:
            app.dependency_overrides.clear()

