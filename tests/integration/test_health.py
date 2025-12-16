"""Test health check endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.skip(reason="Requires database connection, tested in unit tests")
def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    # Database status can be healthy or unhealthy depending on connection
    assert data["database"] in ["healthy", "unhealthy"]

