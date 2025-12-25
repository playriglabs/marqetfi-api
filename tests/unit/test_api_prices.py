"""Test price API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_price_feed_service
from app.main import app
from app.services.price_feed_service import PriceFeedService


class TestPriceAPI:
    """Test price API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_price_service(self):
        """Create mock price service."""
        service = MagicMock(spec=PriceFeedService)
        service.get_price_by_pair = AsyncMock(
            return_value=(100.0, 1234567890, "test_source", "BTC", "USDT")
        )
        service.get_prices_by_pairs = AsyncMock(
            return_value={
                "BTCUSDT": (100.0, 1234567890, "test_source", "BTC", "USDT"),
                "ETHUSDT": (200.0, 1234567890, "test_source", "ETH", "USDT"),
            }
        )
        service.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])
        return service

    @pytest.mark.asyncio
    async def test_get_price_success(self, client, mock_price_service):
        """Test successful price retrieval."""
        app.dependency_overrides[get_price_feed_service] = lambda: mock_price_service
        try:
            response = client.get("/api/v1/prices/BTCUSDT")

            assert response.status_code == 200
            data = response.json()
            assert data["price"] == 100.0
            assert data["asset"] == "BTC"
            assert data["quote"] == "USDT"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_price_error(self, client, mock_price_service):
        """Test price retrieval error."""
        mock_price_service.get_price_by_pair = AsyncMock(side_effect=Exception("Provider error"))
        app.dependency_overrides[get_price_feed_service] = lambda: mock_price_service
        try:
            response = client.get("/api/v1/prices/BTCUSDT")
            assert response.status_code == 500
            assert "Failed to get price" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_prices_success(self, client, mock_price_service):
        """Test successful multiple price retrieval."""
        app.dependency_overrides[get_price_feed_service] = lambda: mock_price_service
        try:
            response = client.get("/api/v1/prices?pairs=BTCUSDT,ETHUSDT")
            assert response.status_code == 200
            data = response.json()
            assert "prices" in data
            assert "BTCUSDT" in data["prices"]
            assert "ETHUSDT" in data["prices"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_prices_error(self, client, mock_price_service):
        """Test multiple price retrieval error."""
        mock_price_service.get_prices_by_pairs = AsyncMock(side_effect=Exception("Provider error"))
        app.dependency_overrides[get_price_feed_service] = lambda: mock_price_service
        try:
            response = client.get("/api/v1/prices?pairs=BTCUSDT,ETHUSDT")
            assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_pairs_success(self, client, mock_price_service):
        """Test successful pairs retrieval."""
        app.dependency_overrides[get_price_feed_service] = lambda: mock_price_service
        try:
            response = client.get("/api/v1/prices/pairs")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["pair_id"] == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_pairs_with_category(self, client, mock_price_service):
        """Test pairs retrieval with category."""
        app.dependency_overrides[get_price_feed_service] = lambda: mock_price_service
        try:
            response = client.get("/api/v1/prices/pairs?category=crypto")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_pairs_error(self, client, mock_price_service):
        """Test pairs retrieval error."""
        mock_price_service.get_pairs = AsyncMock(side_effect=Exception("Provider error"))
        app.dependency_overrides[get_price_feed_service] = lambda: mock_price_service
        try:
            response = client.get("/api/v1/prices/pairs")
            assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()

