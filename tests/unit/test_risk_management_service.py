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


@pytest.mark.asyncio
async def test_monitor_position_risk_margin_call(db_session):
    """Test risk alert generation for margin call."""
    from app.models.enums import PositionSide, TradeSide, TradeStatus
    from app.models.trading import Position, Trade
    from app.repositories.risk_repository import RiskLimitRepository

    # Create a risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": 1,
            "asset": "BTC",
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    # Create a trade
    from datetime import datetime

    trade = Trade(
        user_id=1,
        order_id=1,
        pair_id=1,
        trade_index=1,
        asset="BTC",
        quote="USDT",
        side=TradeSide.LONG,
        entry_price=Decimal("50000"),
        quantity=Decimal("1.0"),
        leverage=10,
        collateral=Decimal("5000"),
        status=TradeStatus.OPEN,
        provider="ostium",
        provider_trade_id="test-trade-1",
        opened_at=datetime.utcnow(),
    )
    db_session.add(trade)
    await db_session.commit()
    await db_session.refresh(trade)

    # Create a position with low margin ratio (below 10% threshold)
    position = Position(
        user_id=1,
        trade_id=trade.id,
        asset="BTC",
        quote="USDT",
        side=PositionSide.LONG,
        size=Decimal("1.0"),
        entry_price=Decimal("50000"),
        current_price=Decimal("49000"),
        leverage=10,
        collateral=Decimal("5000"),
        unrealized_pnl=Decimal("-1000"),
        unrealized_pnl_percentage=Decimal("-2.0"),
        liquidation_price=Decimal("45000"),
        margin_ratio=Decimal("0.05"),  # 5% - below 10% threshold
        provider="ostium",
    )
    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)

    service = RiskManagementService(db_session)
    events = await service.monitor_position_risk(position)

    assert len(events) > 0
    assert any(event.event_type == "margin_call" for event in events)
    margin_call_event = next(e for e in events if e.event_type == "margin_call")
    assert margin_call_event.severity == "critical"
    assert margin_call_event.user_id == 1
    assert margin_call_event.position_id == position.id


@pytest.mark.asyncio
async def test_monitor_position_risk_liquidation_risk(db_session):
    """Test risk alert generation for liquidation risk."""
    from app.models.enums import PositionSide, TradeSide, TradeStatus
    from app.models.trading import Position, Trade
    from app.repositories.risk_repository import RiskLimitRepository

    # Create a risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": 1,
            "asset": "BTC",
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    # Create a trade
    from datetime import datetime

    trade = Trade(
        user_id=1,
        order_id=1,
        pair_id=1,
        trade_index=1,
        asset="BTC",
        quote="USDT",
        side=TradeSide.LONG,
        entry_price=Decimal("50000"),
        quantity=Decimal("1.0"),
        leverage=10,
        collateral=Decimal("5000"),
        status=TradeStatus.OPEN,
        provider="ostium",
        provider_trade_id="test-trade-2",
        opened_at=datetime.utcnow(),
    )
    db_session.add(trade)
    await db_session.commit()
    await db_session.refresh(trade)

    # Create a position close to liquidation (within 5%)
    position = Position(
        user_id=1,
        trade_id=trade.id,
        asset="BTC",
        quote="USDT",
        side=PositionSide.LONG,
        size=Decimal("1.0"),
        entry_price=Decimal("50000"),
        current_price=Decimal("45200"),  # Within 4% of liquidation (45000)
        leverage=10,
        collateral=Decimal("5000"),
        unrealized_pnl=Decimal("-4800"),
        unrealized_pnl_percentage=Decimal("-9.6"),
        liquidation_price=Decimal("45000"),
        margin_ratio=Decimal("0.15"),
        provider="ostium",
    )
    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)

    service = RiskManagementService(db_session)
    events = await service.monitor_position_risk(position)

    assert len(events) > 0
    assert any(event.event_type == "liquidation_risk" for event in events)
    liquidation_event = next(e for e in events if e.event_type == "liquidation_risk")
    assert liquidation_event.severity == "critical"
    assert liquidation_event.user_id == 1
    assert liquidation_event.position_id == position.id


@pytest.mark.asyncio
async def test_get_risk_limit_user_specific_asset(db_session):
    """Test getting user-specific risk limit for asset."""
    from app.repositories.risk_repository import RiskLimitRepository

    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": 1,
            "asset": "BTC",
            "max_leverage": 20,
            "max_position_size": Decimal("2000000"),
            "min_margin": Decimal("200"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    limit = await service.get_risk_limit(user_id=1, asset="BTC")

    assert limit.max_leverage == 20
    assert limit.user_id == 1
    assert limit.asset == "BTC"


@pytest.mark.asyncio
async def test_get_risk_limit_user_global(db_session):
    """Test getting user-specific global risk limit."""
    from app.repositories.risk_repository import RiskLimitRepository

    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": 1,
            "asset": None,
            "max_leverage": 15,
            "max_position_size": Decimal("1500000"),
            "min_margin": Decimal("150"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    limit = await service.get_risk_limit(user_id=1, asset="ETH")

    assert limit.max_leverage == 15
    assert limit.user_id == 1


@pytest.mark.asyncio
async def test_get_risk_limit_asset_global(db_session):
    """Test getting asset-specific global risk limit."""
    from app.repositories.risk_repository import RiskLimitRepository

    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": None,
            "asset": "BTC",
            "max_leverage": 12,
            "max_position_size": Decimal("1200000"),
            "min_margin": Decimal("120"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    limit = await service.get_risk_limit(user_id=999, asset="BTC")

    assert limit.max_leverage == 12
    assert limit.asset == "BTC"


@pytest.mark.asyncio
async def test_get_risk_limit_global_default(db_session):
    """Test getting global default risk limit."""
    from app.repositories.risk_repository import RiskLimitRepository

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
    limit = await service.get_risk_limit(user_id=999, asset="UNKNOWN")

    assert limit.max_leverage == 10


@pytest.mark.asyncio
async def test_get_risk_limit_no_config(db_session):
    """Test getting risk limit when no config exists."""
    service = RiskManagementService(db_session)
    limit = await service.get_risk_limit(user_id=999, asset="UNKNOWN")

    # Should return default values
    assert limit.max_leverage == 10
    assert limit.max_position_size == Decimal("1000000")
    assert limit.min_margin == Decimal("100")


@pytest.mark.asyncio
async def test_validate_position_size_within_limit(db_session):
    """Test position size validation when within limit."""
    from app.repositories.risk_repository import RiskLimitRepository

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
    is_valid, error = await service.validate_position_size(
        user_id=1, new_position_size=Decimal("500000"), asset=None
    )

    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_position_size_exceeds_limit(db_session):
    """Test position size validation when exceeds limit."""
    from app.repositories.risk_repository import RiskLimitRepository

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
    is_valid, error = await service.validate_position_size(
        user_id=1, new_position_size=Decimal("1500000"), asset=None
    )

    assert is_valid is False
    assert "exceeds maximum" in error.lower()


@pytest.mark.asyncio
async def test_validate_position_size_with_existing_positions(db_session):
    """Test position size validation with existing positions."""
    from app.repositories.risk_repository import RiskLimitRepository
    from app.repositories.position_repository import PositionRepository

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

    # Create existing position
    from app.models.trading import Position
    from app.models.enums import PositionSide

    from datetime import datetime

    existing_position = Position(
        user_id=1,
        trade_id=1,
        asset="BTC",
        quote="USDT",
        side=PositionSide.LONG,
        size=Decimal("600000"),
        entry_price=Decimal("50000"),
        current_price=Decimal("50000"),
        leverage=10,
        collateral=Decimal("60000"),
        provider="ostium",
        created_at=datetime.utcnow(),
    )
    db_session.add(existing_position)
    await db_session.commit()
    await db_session.refresh(existing_position)

    service = RiskManagementService(db_session)
    # New position would make total exceed limit (600000 + 500000 = 1100000 > 1000000)
    is_valid, error = await service.validate_position_size(
        user_id=1, new_position_size=Decimal("500000"), asset=None
    )

    assert is_valid is False
    assert "exceeds maximum" in error.lower()


@pytest.mark.asyncio
async def test_validate_margin_below_minimum(db_session):
    """Test margin validation when below minimum."""
    from app.repositories.risk_repository import RiskLimitRepository

    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": None,
            "asset": None,
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("1000"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    is_valid, error = await service.validate_margin(
        user_id=1,
        collateral=Decimal("50"),  # Would result in margin of 500, below 1000
        leverage=10,
        available_balance=Decimal("10000"),
        asset=None,
    )

    assert is_valid is False
    assert "below minimum" in error.lower()


@pytest.mark.asyncio
async def test_validate_pre_trade_leverage_fails(db_session):
    """Test pre-trade validation when leverage check fails."""
    from app.repositories.risk_repository import RiskLimitRepository

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
        leverage=15,  # Exceeds max leverage
        position_size=Decimal("5000"),
        available_balance=Decimal("20000"),
        asset=None,
    )

    assert is_valid is False
    assert "leverage" in error.lower()


@pytest.mark.asyncio
async def test_validate_pre_trade_position_size_fails(db_session):
    """Test pre-trade validation when position size check fails."""
    from app.repositories.risk_repository import RiskLimitRepository

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
        position_size=Decimal("2000000"),  # Exceeds max position size
        available_balance=Decimal("20000"),
        asset=None,
    )

    assert is_valid is False
    assert "position size" in error.lower()


@pytest.mark.asyncio
async def test_validate_pre_trade_margin_fails(db_session):
    """Test pre-trade validation when margin check fails."""
    from app.repositories.risk_repository import RiskLimitRepository

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
        leverage=10,
        position_size=Decimal("5000"),
        available_balance=Decimal("5000"),  # Insufficient
        asset=None,
    )

    assert is_valid is False
    assert "insufficient" in error.lower() or "balance" in error.lower()


@pytest.mark.asyncio
async def test_get_user_risk_metrics(db_session):
    """Test getting user risk metrics."""
    from app.repositories.risk_repository import RiskLimitRepository, RiskEventRepository
    from app.repositories.position_repository import PositionRepository

    # Create risk limit
    risk_limit_repo = RiskLimitRepository()
    await risk_limit_repo.create(
        db_session,
        {
            "user_id": 1,
            "asset": None,
            "max_leverage": 10,
            "max_position_size": Decimal("1000000"),
            "min_margin": Decimal("100"),
            "is_active": True,
        },
    )

    service = RiskManagementService(db_session)
    metrics = await service.get_user_risk_metrics(user_id=1)

    assert "user_id" in metrics
    assert "total_positions" in metrics
    assert "aggregate_leverage" in metrics
    assert "total_position_size" in metrics
    assert "total_collateral" in metrics
    assert "recent_risk_events" in metrics


@pytest.mark.asyncio
async def test_get_platform_risk_metrics(db_session):
    """Test getting platform risk metrics."""
    service = RiskManagementService(db_session)
    metrics = await service.get_platform_risk_metrics()

    assert "total_positions" in metrics
    assert "aggregate_leverage" in metrics
    assert "total_position_size" in metrics
    assert "total_collateral" in metrics
    assert "total_notional" in metrics
