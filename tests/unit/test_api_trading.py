"""Test trading API endpoints."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user, get_trading_service
from app.main import app
from app.models.enums import WalletType
from app.models.user import User
from app.services.trading_service import TradingService


class TestTradingAPI:
    """Test trading API endpoints."""

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
    def mock_trading_service(self):
        """Create mock trading service."""
        service = MagicMock(spec=TradingService)
        service.open_trade = AsyncMock(
            return_value={
                "transaction_hash": "0x123",
                "pair_id": 1,
                "trade_index": 0,
                "status": "success",
            }
        )
        service.close_trade = AsyncMock(return_value={"transaction_hash": "0x456", "status": "closed"})
        service.update_tp = AsyncMock(return_value={"status": "updated"})
        service.update_sl = AsyncMock(return_value={"status": "updated"})
        service.get_open_trades = AsyncMock(return_value=[])
        service.get_open_trade_metrics = AsyncMock(return_value={})
        service.get_orders = AsyncMock(return_value=[])
        service.cancel_limit_order = AsyncMock(return_value={"status": "cancelled"})
        service.update_limit_order = AsyncMock(return_value={"status": "updated"})
        service.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])
        return service

    @pytest.mark.asyncio
    async def test_open_trade_success(self, client, sample_user, mock_trading_service, db_session):
        """Test successful trade opening."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.post(
                "/api/v1/trading/trades",
                json={
                    "collateral": 1000.0,
                    "leverage": 10,
                    "asset_type": 1,
                    "direction": True,
                    "order_type": "MARKET",
                    "asset": "BTC",
                },
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["transaction_hash"] == "0x123"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_open_trade_validation_error(self, client, sample_user, mock_trading_service):
        """Test trade opening with validation error."""
        mock_trading_service.open_trade = AsyncMock(side_effect=ValueError("Invalid leverage"))

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.post(
                "/api/v1/trading/trades",
                json={
                    "collateral": 1000.0,
                    "leverage": 100,  # Invalid
                    "asset_type": 1,
                    "direction": True,
                    "order_type": "MARKET",
                },
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_close_trade_success(self, client, sample_user, mock_trading_service):
        """Test successful trade closing."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.delete(
                "/api/v1/trading/trades/1/0",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "closed"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_take_profit_success(self, client, sample_user, mock_trading_service):
        """Test successful take profit update."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.patch(
                "/api/v1/trading/trades/1/0/tp?tp_price=55000.0",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_stop_loss_success(self, client, sample_user, mock_trading_service):
        """Test successful stop loss update."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.patch(
                "/api/v1/trading/trades/1/0/sl?sl_price=45000.0",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_open_trades_success(self, client, sample_user, mock_trading_service):
        """Test getting open trades."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.get(
                "/api/v1/trading/trades",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "trades" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_pairs_success(self, client, sample_user, mock_trading_service):
        """Test getting trading pairs."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.get(
                "/api/v1/trading/pairs",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_trade_metrics_success(self, client, sample_user, mock_trading_service):
        """Test getting trade metrics."""
        mock_trading_service.get_open_trade_metrics = AsyncMock(
            return_value={"pnl": 100.0, "leverage": 10, "collateral": 1000.0}
        )

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.get(
                "/api/v1/trading/trades/1/0/metrics",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["pnl"] == 100.0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_orders_success(self, client, sample_user, mock_trading_service):
        """Test getting orders."""
        mock_trading_service.get_orders = AsyncMock(return_value=[{"order_id": "123", "status": "pending"}])

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.get(
                "/api/v1/trading/orders?trader_address=0x123",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["order_id"] == "123"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_orders_missing_address(self, client, sample_user, mock_trading_service):
        """Test getting orders without trader address."""
        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.get(
                "/api/v1/trading/orders",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_limit_order_success(self, client, sample_user, mock_trading_service):
        """Test cancelling limit order."""
        mock_trading_service.cancel_limit_order = AsyncMock(
            return_value={"transaction_hash": "0x789", "status": "cancelled"}
        )

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.delete(
                "/api/v1/trading/orders/1/0",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_limit_order_success(self, client, sample_user, mock_trading_service):
        """Test updating limit order."""
        mock_trading_service.update_limit_order = AsyncMock(
            return_value={"transaction_hash": "0xabc", "status": "updated"}
        )

        app.dependency_overrides[get_current_active_user] = lambda: sample_user
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        try:
            response = client.patch(
                "/api/v1/trading/orders/1/0?at_price=45000.0",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
        finally:
            app.dependency_overrides.clear()

