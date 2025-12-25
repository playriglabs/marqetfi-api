"""Test API dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
    get_price_feed_service,
    get_settlement_service,
    get_trading_service,
    require_feature_access,
    require_full_access,
    require_mpc_wallet,
)
from app.models.enums import FeatureAccessLevel, WalletType
from app.models.user import User


class TestAPIDependencies:
    """Test API dependencies."""

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_superuser=False,
            wallet_type=WalletType.MPC,
            feature_access_level=FeatureAccessLevel.FULL,
        )

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return User(
            id=2,
            email="admin@example.com",
            username="admin",
            is_active=True,
            is_superuser=True,
            wallet_type=WalletType.MPC,
            feature_access_level=FeatureAccessLevel.FULL,
        )

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, db_session, sample_user):
        """Test successful user retrieval."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        with patch("app.api.dependencies.decode_token", return_value={"sub": "1", "type": "access"}), patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute"
        ) as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_execute.return_value = mock_result

            user = await get_current_user(mock_credentials, db_session)

            assert user.id == 1

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Test user retrieval with invalid token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"

        with patch("app.api.dependencies.decode_token", return_value=None):
            with pytest.raises(HTTPException, match="Invalid authentication"):
                await get_current_user(mock_credentials, db_session)

    @pytest.mark.asyncio
    async def test_get_current_user_wrong_token_type(self, db_session):
        """Test user retrieval with wrong token type."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "refresh_token"

        with patch("app.api.dependencies.decode_token", return_value={"sub": "1", "type": "refresh"}):
            with pytest.raises(HTTPException, match="Invalid token type"):
                await get_current_user(mock_credentials, db_session)

    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, sample_user):
        """Test successful active user retrieval."""
        user = await get_current_active_user(current_user=sample_user)

        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test active user retrieval with inactive user."""
        inactive_user = User(
            id=1,
            email="test@example.com",
            is_active=False,
        )

        with pytest.raises(HTTPException, match="Inactive user"):
            await get_current_active_user(current_user=inactive_user)

    @pytest.mark.asyncio
    async def test_get_current_admin_user_success(self, db_session, admin_user):
        """Test successful admin user retrieval."""
        with patch("app.api.dependencies.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get = AsyncMock(return_value=admin_user)
            mock_repo_class.return_value = mock_repo

            result = await get_current_admin_user(current_user={"id": 2}, db=db_session)

            assert result["is_superuser"] is True

    @pytest.mark.asyncio
    async def test_get_current_admin_user_not_superuser(self, db_session, sample_user):
        """Test admin user retrieval with non-superuser."""
        with patch("app.api.dependencies.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get = AsyncMock(return_value=sample_user)
            mock_repo_class.return_value = mock_repo

            with pytest.raises(HTTPException, match="Admin access required"):
                await get_current_admin_user(current_user={"id": 1}, db=db_session)

    @pytest.mark.asyncio
    async def test_get_trading_service(self, db_session):
        """Test getting trading service."""
        service = await get_trading_service(db=db_session)

        assert service is not None
        assert service.db is db_session

    @pytest.mark.asyncio
    async def test_get_settlement_service(self):
        """Test getting settlement service."""
        service = await get_settlement_service()

        assert service is not None

    @pytest.mark.asyncio
    async def test_get_price_feed_service(self):
        """Test getting price feed service."""
        service = await get_price_feed_service()

        assert service is not None

    @pytest.mark.asyncio
    async def test_require_feature_access_success(self, sample_user):
        """Test requiring feature access successfully."""
        user = await require_feature_access(feature="view_prices", current_user=sample_user)

        assert user.id == 1

    @pytest.mark.asyncio
    async def test_require_feature_access_denied(self):
        """Test requiring feature access when denied."""
        limited_user = User(
            id=1,
            email="test@example.com",
            is_active=True,
            wallet_type=WalletType.EXTERNAL,
            feature_access_level=FeatureAccessLevel.LIMITED,
        )

        with pytest.raises(HTTPException, match="Access denied"):
            await require_feature_access(feature="batch_operations", current_user=limited_user)

    @pytest.mark.asyncio
    async def test_require_mpc_wallet_success(self, sample_user):
        """Test requiring MPC wallet successfully."""
        user = await require_mpc_wallet(current_user=sample_user)

        assert user.wallet_type == WalletType.MPC

    @pytest.mark.asyncio
    async def test_require_mpc_wallet_failure(self):
        """Test requiring MPC wallet when user doesn't have one."""
        external_user = User(
            id=1,
            email="test@example.com",
            is_active=True,
            wallet_type=WalletType.EXTERNAL,
        )

        with pytest.raises(HTTPException, match="MPC wallet required"):
            await require_mpc_wallet(current_user=external_user)

    @pytest.mark.asyncio
    async def test_require_full_access_success(self, sample_user):
        """Test requiring full access successfully."""
        user = await require_full_access(current_user=sample_user)

        assert user.feature_access_level == FeatureAccessLevel.FULL

    @pytest.mark.asyncio
    async def test_require_full_access_failure(self):
        """Test requiring full access when user doesn't have it."""
        limited_user = User(
            id=1,
            email="test@example.com",
            is_active=True,
            feature_access_level=FeatureAccessLevel.LIMITED,
        )

        with pytest.raises(HTTPException, match="Full access required"):
            await require_full_access(current_user=limited_user)

