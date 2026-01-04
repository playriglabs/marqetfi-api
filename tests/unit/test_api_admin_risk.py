"""Test risk admin API endpoints."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_admin_user
from app.main import app
from app.models.risk import RiskEvent, RiskLimit
from app.services.risk_management_service import RiskManagementService


class TestRiskAdminAPI:
    """Test risk admin API endpoints."""

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
    def mock_risk_service(self):
        """Create mock risk management service."""
        service = MagicMock(spec=RiskManagementService)
        service.get_user_risk_metrics = AsyncMock(
            return_value={
                "user_id": 1,
                "total_positions": 5,
                "aggregate_leverage": 2.5,
                "total_position_size": 1000.0,
                "total_collateral": 500.0,
                "recent_risk_events": [],
            }
        )
        service.get_platform_risk_metrics = AsyncMock(
            return_value={
                "total_positions": 100,
                "aggregate_leverage": 3.0,
                "total_position_size": 100000.0,
                "total_collateral": 50000.0,
                "total_notional": 150000.0,
            }
        )
        return service

    def test_create_risk_limit_success(self, client, mock_admin_user, db_session):
        """Test successful risk limit creation."""
        from app.api.dependencies import get_current_user
        from app.repositories.risk_repository import RiskLimitRepository

        async def override_get_current_user():
            # Return a dict-like object that get_current_admin_user expects
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            with patch.object(RiskLimitRepository, "create", new_callable=AsyncMock) as mock_repo:
                mock_limit = MagicMock(spec=RiskLimit)
                mock_limit.id = 1
                mock_limit.user_id = 1
                mock_limit.asset = "BTC"
                mock_limit.max_leverage = 10
                mock_limit.max_position_size = Decimal("1000.0")
                mock_limit.min_margin = Decimal("100.0")
                mock_limit.is_active = True
                mock_repo.return_value = mock_limit

                response = client.post(
                    "/api/v1/admin/risk/limits",
                    json={
                        "user_id": 1,
                        "asset": "BTC",
                        "max_leverage": 10,
                        "max_position_size": "1000.0",
                        "min_margin": "100.0",
                        "is_active": True,
                    },
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 201
                data = response.json()
                assert data["id"] == 1
        finally:
            app.dependency_overrides.clear()

    def test_list_risk_limits_success(self, client, mock_admin_user, db_session):
        """Test successful risk limits listing."""
        from app.api.dependencies import get_current_user
        from app.repositories.risk_repository import RiskLimitRepository

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            with patch.object(
                RiskLimitRepository, "get_all_active", new_callable=AsyncMock
            ) as mock_repo:
                mock_limit = MagicMock(spec=RiskLimit)
                mock_limit.id = 1
                mock_limit.user_id = 1
                mock_limit.asset = "BTC"
                mock_limit.max_leverage = 10
                mock_limit.max_position_size = Decimal("1000.0")
                mock_limit.min_margin = Decimal("100.0")
                mock_limit.is_active = True
                mock_repo.return_value = [mock_limit]

                response = client.get(
                    "/api/v1/admin/risk/limits",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "items" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_user_risk_metrics_success(self, client, mock_admin_user, mock_risk_service):
        """Test successful user risk metrics retrieval."""
        from app.api.dependencies import get_current_user
        from app.api.v1.admin.risk import get_risk_service

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user
        app.dependency_overrides[get_risk_service] = lambda: mock_risk_service

        try:
            response = client.get(
                "/api/v1/admin/risk/metrics/users/1",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "total_positions" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_platform_risk_metrics_success(self, client, mock_admin_user, mock_risk_service):
        """Test successful platform risk metrics retrieval."""
        from app.api.dependencies import get_current_user
        from app.api.v1.admin.risk import get_risk_service

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        # The dependency function takes db as parameter
        def override_get_risk_service(db=None):
            return mock_risk_service

        app.dependency_overrides[get_risk_service] = override_get_risk_service

        try:
            response = client.get(
                "/api/v1/admin/risk/metrics/platform",
                headers={"Authorization": "Bearer admin_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "total_positions" in data
            assert "aggregate_leverage" in data
            assert "total_position_size" in data
            assert "total_collateral" in data
            assert "total_notional" in data
        finally:
            app.dependency_overrides.clear()

    def test_list_risk_events_success(self, client, mock_admin_user, db_session):
        """Test successful risk events listing."""
        from app.api.dependencies import get_current_user

        async def override_get_current_user():
            return {"id": mock_admin_user["id"]}

        async def override_get_current_admin_user():
            return mock_admin_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user

        try:
            # Patch where the repository is instantiated in the endpoint
            with patch("app.repositories.risk_repository.RiskEventRepository") as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_event = MagicMock(spec=RiskEvent)
                mock_event.id = 1
                mock_event.user_id = 1
                mock_event.event_type = "leverage_exceeded"
                mock_event.severity = "warning"
                mock_event.threshold = Decimal("1000.0")
                mock_event.current_value = Decimal("1100.0")
                mock_event.current_value = Decimal("1100.0")
                mock_event.message = "Limit exceeded"
                mock_event.created_at = datetime.utcnow()
                mock_event.updated_at = datetime.utcnow()
                mock_repo_instance.get_by_user = AsyncMock(return_value=[mock_event])
                mock_repo_class.return_value = mock_repo_instance

                response = client.get(
                    "/api/v1/admin/risk/events?user_id=1",
                    headers={"Authorization": "Bearer admin_token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "items" in data
        finally:
            app.dependency_overrides.clear()
