"""Risk management admin endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin_user, get_db
from app.schemas.risk import (
    PlatformRiskMetricsResponse,
    RiskEventListResponse,
    RiskEventResponse,
    RiskLimitCreate,
    RiskLimitListResponse,
    RiskLimitResponse,
    RiskLimitUpdate,
    UserRiskMetricsResponse,
)
from app.services.risk_management_service import RiskManagementService

router = APIRouter()


def get_risk_service(db: AsyncSession = Depends(get_db)) -> RiskManagementService:
    """Get risk management service instance."""
    return RiskManagementService(db)


@router.post("/risk/limits", response_model=RiskLimitResponse, status_code=status.HTTP_201_CREATED)
async def create_risk_limit(
    risk_limit: RiskLimitCreate,
    _admin: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service),
) -> RiskLimitResponse:
    """Create a new risk limit.

    Args:
        risk_limit: Risk limit creation data
        _admin: Current admin user
        db: Database session
        risk_service: Risk management service

    Returns:
        Created risk limit
    """
    from app.repositories.risk_repository import RiskLimitRepository

    risk_limit_repo = RiskLimitRepository()
    created = await risk_limit_repo.create(
        db,
        {
            "user_id": risk_limit.user_id,
            "asset": risk_limit.asset,
            "max_leverage": risk_limit.max_leverage,
            "max_position_size": risk_limit.max_position_size,
            "min_margin": risk_limit.min_margin,
            "is_active": risk_limit.is_active,
        },
    )
    return RiskLimitResponse.model_validate(created)


@router.get("/risk/limits", response_model=RiskLimitListResponse)
async def list_risk_limits(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    _admin: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service),
) -> RiskLimitListResponse:
    """List all risk limits.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        _admin: Current admin user
        db: Database session
        risk_service: Risk management service

    Returns:
        List of risk limits
    """
    from app.repositories.risk_repository import RiskLimitRepository

    risk_limit_repo = RiskLimitRepository()
    limits = await risk_limit_repo.get_all_active(db, skip, limit)
    return RiskLimitListResponse(
        items=[RiskLimitResponse.model_validate(limit) for limit in limits],
        total=len(limits),
        skip=skip,
        limit=limit,
    )


@router.put("/risk/limits/{limit_id}", response_model=RiskLimitResponse)
async def update_risk_limit(
    limit_id: int,
    risk_limit: RiskLimitUpdate,
    _admin: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service),
) -> RiskLimitResponse:
    """Update a risk limit.

    Args:
        limit_id: Risk limit ID
        risk_limit: Risk limit update data
        _admin: Current admin user
        db: Database session
        risk_service: Risk management service

    Returns:
        Updated risk limit
    """
    from app.repositories.risk_repository import RiskLimitRepository

    risk_limit_repo = RiskLimitRepository()
    limit = await risk_limit_repo.get(db, limit_id)
    if not limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk limit not found: {limit_id}",
        )

    from typing import Any

    update_data: dict[str, Any] = {}
    if risk_limit.max_leverage is not None:
        update_data["max_leverage"] = risk_limit.max_leverage
    if risk_limit.max_position_size is not None:
        update_data["max_position_size"] = risk_limit.max_position_size
    if risk_limit.min_margin is not None:
        update_data["min_margin"] = risk_limit.min_margin
    if risk_limit.is_active is not None:
        update_data["is_active"] = risk_limit.is_active

    updated = await risk_limit_repo.update(db, limit, update_data)
    return RiskLimitResponse.model_validate(updated)


@router.get("/risk/metrics/users/{user_id}", response_model=UserRiskMetricsResponse)
async def get_user_risk_metrics(
    user_id: int,
    _admin: dict = Depends(get_current_admin_user),
    risk_service: RiskManagementService = Depends(get_risk_service),
) -> UserRiskMetricsResponse:
    """Get risk metrics for a user.

    Args:
        user_id: User ID
        _admin: Current admin user
        risk_service: Risk management service

    Returns:
        User risk metrics
    """
    metrics = await risk_service.get_user_risk_metrics(user_id)
    return UserRiskMetricsResponse(**metrics)


@router.get("/risk/metrics/platform", response_model=PlatformRiskMetricsResponse)
async def get_platform_risk_metrics(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    _admin: dict = Depends(get_current_admin_user),
    risk_service: RiskManagementService = Depends(get_risk_service),
) -> PlatformRiskMetricsResponse:
    """Get platform-wide risk metrics.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        _admin: Current admin user
        risk_service: Risk management service

    Returns:
        Platform risk metrics
    """
    metrics = await risk_service.get_platform_risk_metrics(skip, limit)
    return PlatformRiskMetricsResponse(**metrics)


@router.get("/risk/events", response_model=RiskEventListResponse)
async def list_risk_events(
    user_id: int | None = Query(None, description="Filter by user ID"),
    event_type: str | None = Query(None, description="Filter by event type"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    _admin: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RiskEventListResponse:
    """List risk events.

    Args:
        user_id: Optional user ID filter
        event_type: Optional event type filter
        skip: Number of records to skip
        limit: Maximum number of records
        _admin: Current admin user
        db: Database session

    Returns:
        List of risk events
    """
    from app.repositories.risk_repository import RiskEventRepository

    risk_event_repo = RiskEventRepository()
    if user_id:
        events = await risk_event_repo.get_by_user(
            db, user_id, event_type=event_type, skip=skip, limit=limit
        )
    else:
        events = await risk_event_repo.get_all(db, skip, limit)

    return RiskEventListResponse(
        items=[RiskEventResponse.model_validate(event) for event in events],
        total=len(events),
        skip=skip,
        limit=limit,
    )
