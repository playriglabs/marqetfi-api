"""Test deposit API endpoints."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user, get_db
from app.main import app
from app.models.deposit import Deposit
from app.models.enums import WalletType
from app.models.user import User
from app.services.deposit_service import DepositService


class TestDepositAPI:
    """Test deposit API endpoints."""

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
            wallet_type=WalletType.MPC,
            is_active=True,
        )

    @pytest.fixture
    def mock_deposit_service(self):
        """Create mock deposit service."""
        service = MagicMock(spec=DepositService)
        mock_deposit = MagicMock(spec=Deposit)
        mock_deposit.id = 1
        mock_deposit.user_id = 1
        mock_deposit.token_address = "0x123"
        mock_deposit.token_symbol = "USDC"
        mock_deposit.chain = "arbitrum"
        mock_deposit.amount = Decimal("100.0")
        mock_deposit.status = "completed"
        mock_deposit.provider = "ostium"
        mock_deposit.transaction_hash = "0xabc"
        from datetime import datetime

        mock_deposit.created_at = datetime.utcnow()
        mock_deposit.updated_at = datetime.utcnow()

        service.process_deposit = AsyncMock(return_value=mock_deposit)
        service.get_deposit = AsyncMock(return_value=mock_deposit)
        service.list_deposits = AsyncMock(return_value=[mock_deposit])
        service.get_swap_status = AsyncMock(
            return_value={"deposit_id": 1, "swap_needed": False, "swaps": []}
        )
        return service

    def test_create_deposit_success(self, client, sample_user, mock_deposit_service):
        """Test successful deposit creation."""
        from app.api.v1.deposits import get_deposit_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_deposit_service] = lambda: mock_deposit_service

        try:
            response = client.post(
                "/api/v1/deposits/deposits",
                json={
                    "token_address": "0x123",
                    "token_symbol": "USDC",
                    "chain": "arbitrum",
                    "amount": "100.0",
                    "provider": "ostium",
                    "transaction_hash": "0xabc",
                },
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 1
            assert data["token_symbol"] == "USDC"
        finally:
            app.dependency_overrides.clear()

    def test_list_deposits_success(self, client, sample_user, mock_deposit_service):
        """Test successful deposit listing."""
        from app.api.v1.deposits import get_deposit_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_deposit_service] = lambda: mock_deposit_service

        try:
            response = client.get(
                "/api/v1/deposits/deposits",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "deposits" in data
            assert len(data["deposits"]) == 1
        finally:
            app.dependency_overrides.clear()

    def test_get_deposit_success(self, client, sample_user, mock_deposit_service):
        """Test successful deposit retrieval."""
        from app.api.v1.deposits import get_deposit_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_deposit_service] = lambda: mock_deposit_service

        try:
            response = client.get(
                "/api/v1/deposits/deposits/1",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()

    def test_get_deposit_not_found(self, client, sample_user, mock_deposit_service):
        """Test deposit retrieval when not found."""
        from app.api.v1.deposits import get_deposit_service

        mock_deposit_service.get_deposit = AsyncMock(return_value=None)

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_deposit_service] = lambda: mock_deposit_service

        try:
            response = client.get(
                "/api/v1/deposits/deposits/999",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_swap_status_success(self, client, sample_user, mock_deposit_service):
        """Test successful swap status retrieval."""
        from app.api.v1.deposits import get_deposit_service

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_deposit_service] = lambda: mock_deposit_service

        try:
            response = client.get(
                "/api/v1/deposits/deposits/1/swap-status",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["deposit_id"] == 1
        finally:
            app.dependency_overrides.clear()

