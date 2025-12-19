"""API dependencies."""

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.services.price_feed_service import PriceFeedService
from app.services.providers.base import (
    BasePriceProvider,
    BaseSettlementProvider,
    BaseTradingProvider,
)
from app.services.providers.factory import ProviderFactory
from app.services.settlement_service import SettlementService
from app.services.trading_service import TradingService

if TYPE_CHECKING:
    from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> "User":
    """Get current authenticated user."""
    from sqlalchemy import select

    from app.models.user import User

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # Check token type (for custom tokens)
    token_type = payload.get("type")
    if token_type and token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Get user ID from payload
    user_id: int | None = None
    auth0_user_id: str | None = None

    # Check if it's an Auth0 token (has 'sub' with auth0 format) or custom token
    sub = payload.get("sub")
    if isinstance(sub, str) and "|" in sub:
        # Auth0 user ID format: "auth0|..." or "google-oauth2|..."
        auth0_user_id = sub
    elif isinstance(sub, int | str):
        # Custom token with user ID
        try:
            user_id = int(sub)
        except (ValueError, TypeError):
            pass

    if not user_id and not auth0_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Fetch user from database
    if auth0_user_id:
        result = await db.execute(select(User).where(User.auth0_user_id == auth0_user_id))
    else:
        result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Get current active user."""

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return current_user


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current admin user (superuser only).

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User dictionary with admin privileges

    Raises:
        HTTPException: If user is not a superuser
    """
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository()
    user = await user_repo.get(db, current_user["id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "is_superuser": user.is_superuser,
    }


async def get_trading_provider() -> BaseTradingProvider:
    """Get configured trading provider."""
    return await ProviderFactory.get_trading_provider()


async def get_price_provider() -> BasePriceProvider:
    """Get configured price provider."""
    return await ProviderFactory.get_price_provider()


async def get_settlement_provider() -> BaseSettlementProvider:
    """Get configured settlement provider."""
    return await ProviderFactory.get_settlement_provider()


async def get_trading_service() -> TradingService:
    """Get trading service instance with multi-provider routing."""
    # Pass None to enable multi-provider routing via ProviderRouter
    return TradingService(trading_provider=None)


async def get_settlement_service() -> SettlementService:
    """Get settlement service instance with multi-provider routing."""
    # Pass None to enable multi-provider routing via ProviderRouter
    return SettlementService(settlement_provider=None)


async def get_price_feed_service() -> PriceFeedService:
    """Get price feed service instance with multi-provider routing."""
    # Pass None to enable multi-provider routing via ProviderRouter
    return PriceFeedService(price_provider=None)


async def require_feature_access(
    feature: str,
    current_user: "User" = Depends(get_current_active_user),
) -> "User":
    """Require feature access for current user.

    Args:
        feature: Feature name
        current_user: Current authenticated user

    Returns:
        User instance

    Raises:
        HTTPException: If user doesn't have access to the feature
    """
    from app.services.feature_access_service import FeatureAccessService

    if not FeatureAccessService.check_feature_access(current_user, feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for feature: {feature}",
        )

    return current_user


async def require_mpc_wallet(
    current_user: "User" = Depends(get_current_active_user),
) -> "User":
    """Require MPC wallet for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance

    Raises:
        HTTPException: If user doesn't have MPC wallet
    """
    from app.models.enums import WalletType

    if current_user.wallet_type != WalletType.MPC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MPC wallet required for this operation",
        )

    return current_user


async def require_full_access(
    current_user: "User" = Depends(get_current_active_user),
) -> "User":
    """Require full feature access for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance

    Raises:
        HTTPException: If user doesn't have full access
    """
    from app.models.enums import FeatureAccessLevel

    if current_user.feature_access_level != FeatureAccessLevel.FULL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full access required for this operation",
        )

    return current_user
