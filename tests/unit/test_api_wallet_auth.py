"""Test wallet authentication API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user, get_db
from app.main import app
from app.models.user import User
from app.models.auth import WalletConnection
from app.services.wallet_auth_service import WalletAuthService


class TestWalletAuthAPI:
    """Test wallet authentication API endpoints."""

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
    def mock_wallet_auth_service(self):
        """Create mock wallet auth service."""
        service = MagicMock(spec=WalletAuthService)
        service.generate_nonce = AsyncMock(return_value="nonce123")
        mock_conn = MagicMock()
        mock_conn.id = 1
        mock_conn.wallet_address = "0x123"
        mock_conn.wallet_type = "external"
        mock_conn.provider = "metamask"
        mock_conn.is_primary = True
        mock_conn.verified = True
        mock_conn.verified_at = None
        service.connect_wallet = AsyncMock(return_value=mock_conn)
        service.create_mpc_wallet = AsyncMock(
            return_value={
                "wallet_id": "wallet_123",
                "address": "0x123",
                "network": "mainnet",
                "provider": "privy",
            }
        )
        mock_conn2 = MagicMock()
        mock_conn2.id = 1
        mock_conn2.wallet_address = "0x123"
        mock_conn2.wallet_type = "external"
        mock_conn2.provider = "metamask"
        mock_conn2.provider_wallet_id = None
        mock_conn2.is_primary = True
        mock_conn2.verified = True
        mock_conn2.verified_at = None
        mock_conn2.last_used_at = None
        mock_conn2.created_at = None
        service.get_user_wallet_connections = AsyncMock(return_value=[mock_conn2])
        return service

    def test_get_wallet_nonce_success(self, client, mock_wallet_auth_service):
        """Test successful nonce generation."""
        from app.api.v1.auth.wallet import wallet_auth_service

        with patch("app.api.v1.auth.wallet.wallet_auth_service", mock_wallet_auth_service):
            response = client.post(
                "/api/v1/auth/wallet/nonce",
                json={"wallet_address": "0x123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "nonce" in data
            assert "message" in data

    def test_connect_wallet_success(self, client, sample_user, mock_wallet_auth_service):
        """Test successful wallet connection."""
        from app.api.v1.auth.wallet import wallet_auth_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            with patch("app.api.v1.auth.wallet.wallet_auth_service", mock_wallet_auth_service):
                response = client.post(
                    "/api/v1/auth/wallet/connect",
                    json={
                        "wallet_address": "0x123",
                        "signature": "0xsig",
                        "nonce": "nonce123",
                        "provider": "metamask",
                    },
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["wallet_address"] == "0x123"
        finally:
            app.dependency_overrides.clear()

    def test_create_mpc_wallet_success(self, client, sample_user, mock_wallet_auth_service):
        """Test successful MPC wallet creation."""
        from app.api.v1.auth.wallet import wallet_auth_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            with patch("app.api.v1.auth.wallet.wallet_auth_service", mock_wallet_auth_service):
                response = client.post(
                    "/api/v1/auth/wallet/create-mpc",
                    json={"provider": "privy", "network": "mainnet"},
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "wallet_id" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_wallet_connections_success(self, client, sample_user, mock_wallet_auth_service):
        """Test successful wallet connections retrieval."""
        from app.api.v1.auth.wallet import wallet_auth_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user

        try:
            with patch("app.api.v1.auth.wallet.wallet_auth_service", mock_wallet_auth_service):
                response = client.get(
                    "/api/v1/auth/wallet/connections",
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1
        finally:
            app.dependency_overrides.clear()

