"""Test OAuth API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user, get_db
from app.main import app
from app.models.user import User
from app.services.oauth_service import OAuthService


class TestOAuthAPI:
    """Test OAuth API endpoints."""

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
    def mock_oauth_service(self):
        """Create mock OAuth service."""
        service = MagicMock(spec=OAuthService)
        service.get_oauth_authorization_url = AsyncMock(
            return_value=("https://auth0.com/authorize", "state123")
        )
        service.handle_oauth_callback = AsyncMock(
            return_value=(
                User(id=1, email="test@example.com", username="testuser", is_active=True),
                {"access_token": "token", "refresh_token": "refresh", "token_type": "bearer"},
            )
        )
        service.link_oauth_account = AsyncMock(
            return_value=MagicMock(
                id=1,
                provider="google",
                provider_user_id="google_123",
                created_at=None,
            )
        )
        service.unlink_oauth_account = AsyncMock()
        return service

    def test_authorize_oauth_success(self, client, mock_oauth_service):
        """Test successful OAuth authorization."""
        from app.api.v1.auth.oauth import oauth_service

        with patch("app.api.v1.auth.oauth.oauth_service", mock_oauth_service):
            response = client.get("/api/v1/auth/oauth/authorize/google")

            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert "state" in data

    def test_oauth_callback_success(self, client, mock_oauth_service):
        """Test successful OAuth callback."""
        from app.api.v1.auth.oauth import oauth_service

        with patch("app.api.v1.auth.oauth.oauth_service", mock_oauth_service):
            response = client.get(
                "/api/v1/auth/oauth/callback?code=auth_code&state=state123"
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    def test_google_oauth_callback_success(self, client, mock_oauth_service):
        """Test successful Google OAuth callback."""
        from app.api.v1.auth.oauth import oauth_service

        with patch("app.api.v1.auth.oauth.oauth_service", mock_oauth_service):
            response = client.get(
                "/api/v1/auth/oauth/google/callback?code=auth_code&state=state123"
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    def test_apple_oauth_callback_success(self, client, mock_oauth_service):
        """Test successful Apple OAuth callback."""
        from app.api.v1.auth.oauth import oauth_service

        with patch("app.api.v1.auth.oauth.oauth_service", mock_oauth_service):
            response = client.get(
                "/api/v1/auth/oauth/apple/callback?code=auth_code&state=state123"
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    def test_link_oauth_account_success(self, client, sample_user, mock_oauth_service):
        """Test successful OAuth account linking."""
        from app.api.v1.auth.oauth import oauth_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            with patch("app.api.v1.auth.oauth.oauth_service", mock_oauth_service):
                response = client.post(
                    "/api/v1/auth/oauth/link",
                    json={"code": "auth_code", "redirect_uri": "https://app.com/callback"},
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["provider"] == "google"
        finally:
            app.dependency_overrides.clear()

    def test_unlink_oauth_account_success(self, client, sample_user, mock_oauth_service):
        """Test successful OAuth account unlinking."""
        from app.api.v1.auth.oauth import oauth_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            with patch("app.api.v1.auth.oauth.oauth_service", mock_oauth_service):
                response = client.delete(
                    "/api/v1/auth/oauth/unlink/google",
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "message" in data
        finally:
            app.dependency_overrides.clear()

