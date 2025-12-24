"""Risk monitoring background tasks."""

import asyncio
from typing import Any

from app.tasks.celery_app import celery_app


@celery_app.task(name="monitor_position_risk")
def monitor_position_risk_task() -> dict[str, Any]:
    """Monitor all open positions for risk threshold breaches.

    This task runs periodically to check positions for:
    - Margin ratio below threshold
    - Liquidation risk
    - Other risk events

    Returns:
        Task result dictionary
    """

    from app.core.database import get_session_maker
    from app.repositories.position_repository import PositionRepository
    from app.services.risk_management_service import RiskManagementService

    async def _monitor() -> dict[str, Any]:
        """Async monitoring logic."""
        AsyncSessionLocal = get_session_maker()
        async with AsyncSessionLocal() as db:
            position_repo = PositionRepository()
            risk_service = RiskManagementService(db)

            # Get all open positions
            positions = await position_repo.get_all(db, skip=0, limit=1000)

            events_generated = 0
            for position in positions:
                try:
                    events = await risk_service.monitor_position_risk(position)
                    events_generated += len(events)
                except Exception:
                    # Log error but continue with other positions
                    continue

            return {
                "status": "completed",
                "positions_checked": len(positions),
                "events_generated": events_generated,
            }

    # Run async function in sync context
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_monitor())
