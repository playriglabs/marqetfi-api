"""Test health API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.health import health_check


@pytest.mark.asyncio
async def test_health_check_healthy():
    """Test health check with healthy database."""
    mock_db = MagicMock(spec=AsyncSession)
    mock_db.execute = AsyncMock()

    result = await health_check(mock_db)
    assert result.status == "healthy"
    assert result.database == "healthy"
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_unhealthy():
    """Test health check with unhealthy database."""
    mock_db = MagicMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

    result = await health_check(mock_db)
    assert result.status == "healthy"
    assert result.database == "unhealthy"

