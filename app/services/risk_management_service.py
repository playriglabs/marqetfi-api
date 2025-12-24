"""Risk management service."""

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk import RiskEvent, RiskLimit
from app.models.trading import Position
from app.repositories.position_repository import PositionRepository
from app.repositories.risk_repository import RiskEventRepository, RiskLimitRepository


class RiskManagementService:
    """Service for risk management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize risk management service.

        Args:
            db: Database session
        """
        self.db = db
        self.risk_limit_repo = RiskLimitRepository()
        self.risk_event_repo = RiskEventRepository()
        self.position_repo = PositionRepository()

    async def get_risk_limit(self, user_id: int, asset: str | None = None) -> RiskLimit:
        """Get effective risk limit for user and asset.

        Priority: user-specific > asset-specific > global default

        Args:
            user_id: User ID
            asset: Optional asset symbol

        Returns:
            Effective risk limit

        Raises:
            ValueError: If no risk limit found
        """
        # 1. Try user-specific limit for asset
        if asset:
            limit = await self.risk_limit_repo.get_by_user(self.db, user_id, asset)
            if limit:
                return limit

        # 2. Try user-specific global limit
        limit = await self.risk_limit_repo.get_by_user(self.db, user_id, None)
        if limit:
            return limit

        # 3. Try asset-specific global limit
        if asset:
            limit = await self.risk_limit_repo.get_by_asset(self.db, asset)
            if limit:
                return limit

        # 4. Try global default limit
        limit = await self.risk_limit_repo.get_global_default(self.db)
        if limit:
            return limit

        # 5. Return default values if no limit configured
        return RiskLimit(
            id=0,
            user_id=None,
            asset=None,
            max_leverage=10,  # Default max leverage
            max_position_size=Decimal("1000000"),  # Default max position size
            min_margin=Decimal("100"),  # Default min margin
            is_active=True,
        )

    async def validate_leverage(
        self, user_id: int, leverage: int, asset: str | None = None
    ) -> tuple[bool, str | None]:
        """Validate leverage against risk limits.

        Args:
            user_id: User ID
            leverage: Requested leverage
            asset: Optional asset symbol

        Returns:
            Tuple of (is_valid, error_message)
        """
        risk_limit = await self.get_risk_limit(user_id, asset)

        if leverage > risk_limit.max_leverage:
            return (
                False,
                f"Leverage {leverage} exceeds maximum allowed leverage of {risk_limit.max_leverage}",
            )

        return True, None

    async def validate_position_size(
        self,
        user_id: int,
        new_position_size: Decimal,
        asset: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validate position size against risk limits.

        Args:
            user_id: User ID
            new_position_size: Size of new position
            asset: Optional asset symbol

        Returns:
            Tuple of (is_valid, error_message)
        """
        risk_limit = await self.get_risk_limit(user_id, asset)

        # Get existing positions for user
        existing_positions = await self.position_repo.get_by_user(self.db, user_id)

        # Calculate aggregate position size
        total_position_size = sum(
            pos.size for pos in existing_positions if not asset or pos.asset == asset
        )
        total_position_size += new_position_size

        if total_position_size > risk_limit.max_position_size:
            return (
                False,
                f"Total position size {total_position_size} exceeds maximum allowed size of {risk_limit.max_position_size}",
            )

        return True, None

    async def calculate_required_margin(self, collateral: Decimal, leverage: int) -> Decimal:
        """Calculate required margin for trade.

        Args:
            collateral: Collateral amount
            leverage: Leverage multiplier

        Returns:
            Required margin
        """
        # Required margin = collateral * leverage
        return collateral * Decimal(leverage)

    async def validate_margin(
        self,
        user_id: int,
        collateral: Decimal,
        leverage: int,
        available_balance: Decimal,
        asset: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validate margin requirements.

        Args:
            user_id: User ID
            collateral: Collateral amount
            leverage: Leverage multiplier
            available_balance: User's available balance
            asset: Optional asset symbol

        Returns:
            Tuple of (is_valid, error_message)
        """
        risk_limit = await self.get_risk_limit(user_id, asset)
        required_margin = await self.calculate_required_margin(collateral, leverage)

        # Check minimum margin requirement
        if required_margin < risk_limit.min_margin:
            return (
                False,
                f"Required margin {required_margin} is below minimum margin requirement of {risk_limit.min_margin}",
            )

        # Check available balance
        if available_balance < required_margin:
            return (
                False,
                f"Insufficient balance. Required: {required_margin}, Available: {available_balance}",
            )

        return True, None

    async def validate_pre_trade(
        self,
        user_id: int,
        collateral: Decimal,
        leverage: int,
        position_size: Decimal,
        available_balance: Decimal,
        asset: str | None = None,
    ) -> tuple[bool, str | None]:
        """Perform comprehensive pre-trade risk validation.

        Args:
            user_id: User ID
            collateral: Collateral amount
            leverage: Leverage multiplier
            position_size: Position size
            available_balance: User's available balance
            asset: Optional asset symbol

        Returns:
            Tuple of (is_valid, error_message)
        """
        # 1. Validate leverage
        is_valid, error = await self.validate_leverage(user_id, leverage, asset)
        if not is_valid:
            return False, error

        # 2. Validate position size
        is_valid, error = await self.validate_position_size(user_id, position_size, asset)
        if not is_valid:
            return False, error

        # 3. Validate margin
        is_valid, error = await self.validate_margin(
            user_id, collateral, leverage, available_balance, asset
        )
        if not is_valid:
            return False, error

        return True, None

    async def monitor_position_risk(self, position: Position) -> list[RiskEvent]:
        """Monitor position for risk threshold breaches.

        Args:
            position: Position to monitor

        Returns:
            List of generated risk events
        """
        events: list[RiskEvent] = []

        # Check margin ratio
        if position.margin_ratio < Decimal("0.1"):  # 10% margin ratio threshold
            event = await self.risk_event_repo.create_event(
                self.db,
                user_id=position.user_id,
                event_type="margin_call",
                threshold=Decimal("0.1"),
                current_value=position.margin_ratio,
                severity="critical",
                message=f"Margin ratio {position.margin_ratio} is below 10%",
                position_id=position.id,
            )
            events.append(event)

        # Check liquidation risk
        if position.liquidation_price:
            # Calculate distance to liquidation (simplified)
            # Handle both enum and string values
            side_value = (
                position.side.value if hasattr(position.side, "value") else str(position.side)
            )
            if side_value == "long":
                distance = (
                    (position.current_price - position.liquidation_price)
                    / position.current_price
                    * 100
                )
            else:
                distance = (
                    (position.liquidation_price - position.current_price)
                    / position.current_price
                    * 100
                )

            if distance < 5:  # Within 5% of liquidation
                event = await self.risk_event_repo.create_event(
                    self.db,
                    user_id=position.user_id,
                    event_type="liquidation_risk",
                    threshold=Decimal("5"),
                    current_value=Decimal(str(distance)),
                    severity="critical",
                    message=f"Position is within {distance:.2f}% of liquidation price",
                    position_id=position.id,
                )
                events.append(event)

        return events

    async def get_user_risk_metrics(self, user_id: int) -> dict[str, Any]:
        """Get risk metrics for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary containing risk metrics
        """
        positions = await self.position_repo.get_by_user(self.db, user_id)

        # Calculate aggregate leverage (simplified)
        total_collateral = sum(pos.collateral for pos in positions)
        total_notional = sum(pos.size * pos.entry_price for pos in positions)
        aggregate_leverage = (
            Decimal(str(total_notional / total_collateral))
            if total_collateral > 0
            else Decimal("0")
        )

        # Get recent risk events
        recent_events = await self.risk_event_repo.get_by_user(self.db, user_id, limit=10)

        return {
            "user_id": user_id,
            "total_positions": len(positions),
            "aggregate_leverage": float(aggregate_leverage),
            "total_position_size": float(sum(pos.size for pos in positions)),
            "total_collateral": float(total_collateral),
            "recent_risk_events": [
                {
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "created_at": event.created_at.isoformat(),
                }
                for event in recent_events
            ],
        }

    async def get_platform_risk_metrics(self, skip: int = 0, limit: int = 100) -> dict[str, Any]:
        """Get platform-wide risk metrics.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            Dictionary containing platform risk metrics
        """
        # Get all active positions
        all_positions = await self.position_repo.get_all(self.db, skip, limit)

        total_positions = len(all_positions)
        total_position_size = sum(pos.size for pos in all_positions)
        total_collateral = sum(pos.collateral for pos in all_positions)
        total_notional = sum(pos.size * pos.entry_price for pos in all_positions)

        aggregate_leverage = (
            Decimal(str(total_notional / total_collateral))
            if total_collateral > 0
            else Decimal("0")
        )

        return {
            "total_positions": total_positions,
            "aggregate_leverage": float(aggregate_leverage),
            "total_position_size": float(total_position_size),
            "total_collateral": float(total_collateral),
            "total_notional": float(total_notional),
        }
