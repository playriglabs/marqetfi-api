"""Configuration schemas for admin API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AppConfigurationCreate(BaseModel):
    """Schema for creating app configuration."""

    config_key: str = Field(..., description="Configuration key")
    config_value: str = Field(..., description="Configuration value")
    config_type: str = Field(default="string", description="Type: string, int, float, bool, json")
    category: str = Field(..., description="Configuration category")
    description: str | None = Field(None, description="Description")
    is_encrypted: bool = Field(default=False, description="Whether value is encrypted")
    is_active: bool = Field(default=True, description="Whether configuration is active")


class AppConfigurationUpdate(BaseModel):
    """Schema for updating app configuration."""

    config_value: str | None = Field(None, description="Configuration value")
    config_type: str | None = Field(None, description="Type")
    category: str | None = Field(None, description="Category")
    description: str | None = Field(None, description="Description")
    is_encrypted: bool | None = Field(None, description="Whether value is encrypted")
    is_active: bool | None = Field(None, description="Whether configuration is active")


class AppConfigurationResponse(BaseModel):
    """Schema for app configuration response."""

    id: int
    config_key: str
    config_value: str | None
    config_type: str
    category: str
    description: str | None
    is_encrypted: bool
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ProviderConfigurationCreate(BaseModel):
    """Schema for creating provider configuration."""

    provider_name: str = Field(..., description="Provider name (ostium, lighter, lifi, etc.)")
    provider_type: str = Field(
        ..., description="Provider type (trading, price, settlement, swap, wallet)"
    )
    config_data: dict[str, Any] = Field(..., description="Configuration data as JSON")
    activate: bool = Field(default=True, description="Activate this configuration immediately")


class ProviderConfigurationUpdate(BaseModel):
    """Schema for updating provider configuration."""

    config_data: dict[str, Any] | None = Field(None, description="Configuration data")
    is_active: bool | None = Field(None, description="Whether configuration is active")


class ProviderConfigurationResponse(BaseModel):
    """Schema for provider configuration response."""

    id: int
    provider_name: str
    provider_type: str
    config_data: dict[str, Any]
    is_active: bool
    version: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class AppConfigurationListResponse(BaseModel):
    """Schema for app configuration list response."""

    items: list[AppConfigurationResponse]
    total: int
    skip: int
    limit: int


class ProviderConfigurationListResponse(BaseModel):
    """Schema for provider configuration list response."""

    items: list[ProviderConfigurationResponse]
    total: int
    skip: int
    limit: int
