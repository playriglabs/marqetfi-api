"""Ostium admin API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin_user, get_db
from app.repositories.ostium_settings_repository import OstiumSettingsRepository
from app.schemas.ostium_admin import (
    OstiumSettingsCreate,
    OstiumSettingsHistoryResponse,
    OstiumSettingsResponse,
    OstiumSettingsUpdate,
)
from app.services.ostium_admin_service import OstiumAdminService

router = APIRouter()


@router.get("/settings", response_model=OstiumSettingsResponse)
async def get_active_settings(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> OstiumSettingsResponse:
    """Get currently active Ostium settings.

    Args:
        db: Database session
        admin_user: Current admin user

    Returns:
        OstiumSettingsResponse: Active settings

    Raises:
        HTTPException: If no active settings found
    """
    service = OstiumAdminService()
    repository = OstiumSettingsRepository()

    settings = await repository.get_active(db)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active settings found",
        )

    settings_dict = service.settings_to_dict(settings, include_private_key=False)
    return OstiumSettingsResponse(**settings_dict)


@router.get("/settings/history", response_model=OstiumSettingsHistoryResponse)
async def get_settings_history(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=100, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> OstiumSettingsHistoryResponse:
    """Get settings history with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        admin_user: Current admin user

    Returns:
        OstiumSettingsHistoryResponse: Paginated settings history
    """
    service = OstiumAdminService()
    repository = OstiumSettingsRepository()

    settings_list = await repository.get_history(db, skip=skip, limit=limit)
    total = len(settings_list)  # Simplified - in production, use count query

    items = [
        OstiumSettingsResponse(**service.settings_to_dict(settings, include_private_key=False))
        for settings in settings_list
    ]

    return OstiumSettingsHistoryResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/settings/{settings_id}", response_model=OstiumSettingsResponse)
async def get_settings(
    settings_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> OstiumSettingsResponse:
    """Get specific settings version by ID.

    Args:
        settings_id: Settings ID
        db: Database session
        admin_user: Current admin user

    Returns:
        OstiumSettingsResponse: Settings

    Raises:
        HTTPException: If settings not found
    """
    service = OstiumAdminService()
    repository = OstiumSettingsRepository()

    settings = await repository.get(db, settings_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings with id {settings_id} not found",
        )

    settings_dict = service.settings_to_dict(settings, include_private_key=False)
    return OstiumSettingsResponse(**settings_dict)


@router.post(
    "/settings", response_model=OstiumSettingsResponse, status_code=status.HTTP_201_CREATED
)
async def create_settings(
    settings_data: OstiumSettingsCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> OstiumSettingsResponse:
    """Create new Ostium settings.

    Args:
        settings_data: Settings data to create
        db: Database session
        admin_user: Current admin user

    Returns:
        OstiumSettingsResponse: Created settings

    Raises:
        HTTPException: If validation fails
    """
    service = OstiumAdminService()

    try:
        settings = await service.create_settings(
            db=db,
            settings_data=settings_data.model_dump(),
            created_by=admin_user["id"],
            activate=settings_data.activate,
        )
        settings_dict = service.settings_to_dict(settings, include_private_key=False)
        return OstiumSettingsResponse(**settings_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/settings/{settings_id}", response_model=OstiumSettingsResponse)
async def update_settings(
    settings_id: int,
    settings_data: OstiumSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> OstiumSettingsResponse:
    """Update existing Ostium settings.

    Args:
        settings_id: Settings ID to update
        settings_data: Updated settings data
        db: Database session
        admin_user: Current admin user

    Returns:
        OstiumSettingsResponse: Updated settings

    Raises:
        HTTPException: If settings not found or validation fails
    """
    service = OstiumAdminService()

    # Filter out None values
    update_data = {k: v for k, v in settings_data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    try:
        settings = await service.update_settings(
            db=db,
            settings_id=settings_id,
            settings_data=update_data,
        )
        settings_dict = service.settings_to_dict(settings, include_private_key=False)
        return OstiumSettingsResponse(**settings_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/settings/{settings_id}", response_model=OstiumSettingsResponse)
async def deactivate_settings(
    settings_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> OstiumSettingsResponse:
    """Deactivate Ostium settings.

    Args:
        settings_id: Settings ID to deactivate
        db: Database session
        admin_user: Current admin user

    Returns:
        OstiumSettingsResponse: Deactivated settings

    Raises:
        HTTPException: If settings not found
    """
    service = OstiumAdminService()
    repository = OstiumSettingsRepository()

    try:
        settings = await repository.deactivate(db, settings_id)
        settings_dict = service.settings_to_dict(settings, include_private_key=False)
        return OstiumSettingsResponse(**settings_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/settings/{settings_id}/activate", response_model=OstiumSettingsResponse)
async def activate_settings(
    settings_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> OstiumSettingsResponse:
    """Activate a specific settings version.

    Args:
        settings_id: Settings ID to activate
        db: Database session
        admin_user: Current admin user

    Returns:
        OstiumSettingsResponse: Activated settings

    Raises:
        HTTPException: If settings not found
    """
    service = OstiumAdminService()
    repository = OstiumSettingsRepository()

    try:
        settings = await repository.activate(db, settings_id)
        settings_dict = service.settings_to_dict(settings, include_private_key=False)
        return OstiumSettingsResponse(**settings_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
