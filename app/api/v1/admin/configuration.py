"""Configuration admin API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin_user, get_db
from app.repositories.app_configuration_repository import (
    AppConfigurationRepository,
    ProviderConfigurationRepository,
)
from app.schemas.configuration import (
    AppConfigurationCreate,
    AppConfigurationListResponse,
    AppConfigurationResponse,
    AppConfigurationUpdate,
    ProviderConfigurationCreate,
    ProviderConfigurationListResponse,
    ProviderConfigurationResponse,
)
from app.services.configuration_admin_service import ConfigurationAdminService

router = APIRouter()


@router.get("/app-configs", response_model=AppConfigurationListResponse)
async def list_app_configs(
    category: str | None = Query(None, description="Filter by category"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> AppConfigurationListResponse:
    """List application configurations."""
    service = ConfigurationAdminService()
    repo = AppConfigurationRepository()

    if category:
        configs = await repo.get_by_category(db, category)
    else:
        configs = await repo.get_all_active(db)

    total = len(configs)
    items = [
        AppConfigurationResponse(**service.config_to_dict(config))
        for config in configs[skip : skip + limit]
    ]

    return AppConfigurationListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/app-configs/{config_id}", response_model=AppConfigurationResponse)
async def get_app_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> AppConfigurationResponse:
    """Get app configuration by ID."""
    service = ConfigurationAdminService()
    repo = AppConfigurationRepository()

    config = await repo.get(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration not found: {config_id}",
        )

    return AppConfigurationResponse(**service.config_to_dict(config))


@router.post(
    "/app-configs", response_model=AppConfigurationResponse, status_code=status.HTTP_201_CREATED
)
async def create_app_config(
    config_data: AppConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> AppConfigurationResponse:
    """Create new app configuration."""
    service = ConfigurationAdminService()

    try:
        config = await service.create_app_config(
            db=db,
            config_data=config_data.model_dump(),
            created_by=admin_user["id"],
        )
        return AppConfigurationResponse(**service.config_to_dict(config))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/app-configs/{config_id}", response_model=AppConfigurationResponse)
async def update_app_config(
    config_id: int,
    config_data: AppConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> AppConfigurationResponse:
    """Update app configuration."""
    service = ConfigurationAdminService()

    update_data = {k: v for k, v in config_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    try:
        config = await service.update_app_config(
            db=db, config_id=config_id, config_data=update_data
        )
        return AppConfigurationResponse(**service.config_to_dict(config))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/provider-configs", response_model=ProviderConfigurationListResponse)
async def list_provider_configs(
    provider_name: str | None = Query(None, description="Filter by provider name"),
    provider_type: str | None = Query(None, description="Filter by provider type"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> ProviderConfigurationListResponse:
    """List provider configurations."""
    repo = ProviderConfigurationRepository()

    if provider_name:
        configs = await repo.get_by_provider(db, provider_name)
    else:
        configs = await repo.get_all(db, skip=skip, limit=limit)

    if provider_type:
        configs = [c for c in configs if c.provider_type == provider_type]

    total = len(configs)
    items = [
        ProviderConfigurationResponse(
            id=c.id,
            provider_name=c.provider_name,
            provider_type=c.provider_type,
            config_data=c.config_data,
            is_active=c.is_active,
            version=c.version,
            created_by=c.created_by,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in configs[skip : skip + limit]
    ]

    return ProviderConfigurationListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/provider-configs/{config_id}", response_model=ProviderConfigurationResponse)
async def get_provider_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> ProviderConfigurationResponse:
    """Get provider configuration by ID."""
    repo = ProviderConfigurationRepository()

    config = await repo.get(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration not found: {config_id}",
        )

    return ProviderConfigurationResponse(
        id=config.id,
        provider_name=config.provider_name,
        provider_type=config.provider_type,
        config_data=config.config_data,
        is_active=config.is_active,
        version=config.version,
        created_by=config.created_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.post(
    "/provider-configs",
    response_model=ProviderConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_provider_config(
    config_data: ProviderConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> ProviderConfigurationResponse:
    """Create new provider configuration."""
    service = ConfigurationAdminService()

    try:
        config = await service.create_provider_config(
            db=db,
            config_data=config_data.model_dump(exclude={"activate"}),
            created_by=admin_user["id"],
            activate=config_data.activate,
        )
        return ProviderConfigurationResponse(
            id=config.id,
            provider_name=config.provider_name,
            provider_type=config.provider_type,
            config_data=config.config_data,
            is_active=config.is_active,
            version=config.version,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/provider-configs/{config_id}/activate", response_model=ProviderConfigurationResponse)
async def activate_provider_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_current_admin_user),
) -> ProviderConfigurationResponse:
    """Activate a provider configuration."""
    service = ConfigurationAdminService()

    try:
        config = await service.activate_provider_config(db=db, config_id=config_id)
        return ProviderConfigurationResponse(
            id=config.id,
            provider_name=config.provider_name,
            provider_type=config.provider_type,
            config_data=config.config_data,
            is_active=config.is_active,
            version=config.version,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
