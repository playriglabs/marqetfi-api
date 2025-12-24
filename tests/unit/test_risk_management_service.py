"""Unit tests for risk management service."""

from decimal import Decimal

import pytest

from app.services.risk_management_service import RiskManagementService


@pytest.mark.asyncio
async def test_validate_leverage_within_limit(db_session):
    """Test leverage validation when within limit."""
    from app.repositories.risk_repository import RiskLimitRepository

    # Create a risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": None,
            "asset": None,
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    is_valid, error = await service.validate_leverage(user_id=1, leverage=5, asset=None)

    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_leverage_exceeds_limit(db_session):
    """Test leverage validation when exceeds limit."""
    from app.repositories.risk_repository import RiskLimitRepository

    # Create a risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": None,
            "asset": None,
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    is_valid, error = await service.validate_leverage(user_id=1, leverage=15, asset=None)

    assert is_valid is False
    assert "exceeds maximum" in error.lower()


@pytest.mark.asyncio
async def test_calculate_required_margin(db_session):
    """Test margin calculation."""
    service = RiskManagementService(db_session)
    margin = await service.calculate_required_margin(collateral=Decimal("1000"), leverage=10)

    assert margin == Decimal("10000")


@pytest.mark.asyncio
async def test_validate_margin_sufficient_balance(db_session):
    """Test margin validation with sufficient balance."""
    from app.repositories.risk_repository import RiskLimitRepository

    # Create a risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": None,
            "asset": None,
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    is_valid, error = await service.validate_margin(
        user_id=1,
        collateral=Decimal("1000"),
        leverage=10,
        available_balance=Decimal("20000"),
        asset=None,
    )

    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_margin_insufficient_balance(db_session):
    """Test margin validation with insufficient balance."""
    from app.repositories.risk_repository import RiskLimitRepository

    # Create a risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": None,
            "asset": None,
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    is_valid, error = await service.validate_margin(
        user_id=1,
        collateral=Decimal("1000"),
        leverage=10,
        available_balance=Decimal("5000"),  # Less than required 10000
        asset=None,
    )

    assert is_valid is False
    assert "insufficient" in error.lower()


@pytest.mark.asyncio
async def test_pre_trade_validation_all_pass(db_session):
    """Test pre-trade validation when all checks pass."""
    from app.repositories.risk_repository import RiskLimitRepository

    # Create a risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": None,
            "asset": None,
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    is_valid, error = await service.validate_pre_trade(
        user_id=1,
        collateral=Decimal("1000"),
        leverage=5,
        position_size=Decimal("5000"),
        available_balance=Decimal("20000"),
        asset=None,
    )

    assert is_valid is True
    assert error is None
