"""Test health API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestHealthAPI:
    """Test health API endpoints."""

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

    @pytest.mark.asyncio
    async def test_health_check_success(self, client, db_session):
        """Test successful health check."""
        db_session.execute = AsyncMock(return_value=MagicMock())

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_database_unhealthy(self, client, db_session):
        """Test health check with database error."""
        db_session.execute = AsyncMock(side_effect=Exception("Database error"))

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "unhealthy"
