"""Ostium admin service for managing configuration settings."""

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.providers.ostium import OstiumConfig
from app.models.ostium_settings import OstiumSettings
from app.repositories.ostium_settings_repository import OstiumSettingsRepository
from app.utils.encryption import decrypt_value, encrypt_value


class OstiumAdminService:
    """Service for managing Ostium admin settings."""

    def __init__(self) -> None:
        """Initialize service."""
        self.repository = OstiumSettingsRepository()

    def validate_settings(self, settings_data: dict[str, Any]) -> None:
        """Validate settings data.

        Args:
            settings_data: Dictionary containing settings to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate slippage percentage
        slippage = settings_data.get("slippage_percentage")
        if slippage is not None:
            slippage_decimal = Decimal(str(slippage))
            if slippage_decimal < 0 or slippage_decimal > 100:
                raise ValueError("slippage_percentage must be between 0.0 and 100.0")

        # Validate fee percentage
        fee_percentage = settings_data.get("default_fee_percentage")
        if fee_percentage is not None:
            fee_decimal = Decimal(str(fee_percentage))
            if fee_decimal < 0 or fee_decimal > 100:
                raise ValueError("default_fee_percentage must be between 0.0 and 100.0")

        # Validate min/max fee relationship
        min_fee = settings_data.get("min_fee")
        max_fee = settings_data.get("max_fee")
        if min_fee is not None and max_fee is not None:
            min_fee_decimal = Decimal(str(min_fee))
            max_fee_decimal = Decimal(str(max_fee))
            if min_fee_decimal < 0:
                raise ValueError("min_fee must be >= 0")
            if max_fee_decimal < 0:
                raise ValueError("max_fee must be >= 0")
            if min_fee_decimal >= max_fee_decimal:
                raise ValueError("min_fee must be less than max_fee")

        # Validate network
        network = settings_data.get("network")
        if network is not None:
            network_lower = network.lower()
            if network_lower not in ["testnet", "mainnet"]:
                raise ValueError("network must be 'testnet' or 'mainnet'")

        # Validate timeout
        timeout = settings_data.get("timeout")
        if timeout is not None:
            if not isinstance(timeout, int) or timeout <= 0:
                raise ValueError("timeout must be a positive integer")
            if timeout > 300:
                raise ValueError("timeout must be <= 300 seconds")

        # Validate retry attempts
        retry_attempts = settings_data.get("retry_attempts")
        if retry_attempts is not None:
            if not isinstance(retry_attempts, int) or retry_attempts < 0:
                raise ValueError("retry_attempts must be a non-negative integer")
            if retry_attempts > 10:
                raise ValueError("retry_attempts must be <= 10")

        # Validate retry delay
        retry_delay = settings_data.get("retry_delay")
        if retry_delay is not None:
            retry_delay_decimal = Decimal(str(retry_delay))
            if retry_delay_decimal < 0:
                raise ValueError("retry_delay must be >= 0")

        # Validate RPC URL format (basic check)
        rpc_url = settings_data.get("rpc_url")
        if rpc_url is not None:
            if not rpc_url.startswith(("http://", "https://")):
                raise ValueError("rpc_url must be a valid HTTP/HTTPS URL")

        # Validate private key format (basic hex check)
        private_key = settings_data.get("private_key")
        if private_key is not None and private_key:
            private_key_clean = private_key.strip()
            if private_key_clean.startswith("0x"):
                private_key_clean = private_key_clean[2:]
            if not all(c in "0123456789abcdefABCDEF" for c in private_key_clean):
                raise ValueError("private_key must be a valid hex string")

    async def create_settings(
        self,
        db: AsyncSession,
        settings_data: dict[str, Any],
        created_by: int,
        activate: bool = False,
    ) -> OstiumSettings:
        """Create new settings.

        Args:
            db: Database session
            settings_data: Dictionary containing settings data
            created_by: User ID creating the settings
            activate: Whether to activate these settings immediately

        Returns:
            OstiumSettings: Created settings

        Raises:
            ValueError: If validation fails
        """
        # Validate settings
        self.validate_settings(settings_data)

        # Get next version number
        version = await self.repository.get_next_version(db)

        # Encrypt private key if provided
        private_key = settings_data.get("private_key", "")
        private_key_encrypted = encrypt_value(private_key) if private_key else ""

        # Prepare data for creation
        create_data = {
            "enabled": settings_data.get("enabled", True),
            "private_key_encrypted": private_key_encrypted,
            "rpc_url": settings_data.get("rpc_url", ""),
            "network": settings_data.get("network", "testnet").lower(),
            "verbose": settings_data.get("verbose", False),
            "slippage_percentage": Decimal(str(settings_data.get("slippage_percentage", 1.0))),
            "default_fee_percentage": Decimal(
                str(settings_data.get("default_fee_percentage", 0.1))
            ),
            "min_fee": Decimal(str(settings_data.get("min_fee", 0.01))),
            "max_fee": Decimal(str(settings_data.get("max_fee", 10.0))),
            "timeout": settings_data.get("timeout", 30),
            "retry_attempts": settings_data.get("retry_attempts", 3),
            "retry_delay": Decimal(str(settings_data.get("retry_delay", 1.0))),
            "is_active": False,  # Will be set by activate if needed
            "version": version,
            "created_by": created_by,
        }

        # Create settings
        settings = await self.repository.create(db, create_data)

        # Activate if requested
        if activate:
            settings = await self.repository.activate(db, settings.id)

        return settings

    async def update_settings(
        self,
        db: AsyncSession,
        settings_id: int,
        settings_data: dict[str, Any],
    ) -> OstiumSettings:
        """Update existing settings.

        Args:
            db: Database session
            settings_id: ID of settings to update
            settings_data: Dictionary containing updated settings data

        Returns:
            OstiumSettings: Updated settings

        Raises:
            ValueError: If settings not found or validation fails
        """
        # Get existing settings
        settings = await self.repository.get(db, settings_id)
        if not settings:
            raise ValueError(f"Settings with id {settings_id} not found")

        # Validate settings
        self.validate_settings(settings_data)

        # Prepare update data
        update_data: dict[str, Any] = {}

        # Update fields if provided
        if "enabled" in settings_data:
            update_data["enabled"] = settings_data["enabled"]
        if "rpc_url" in settings_data:
            update_data["rpc_url"] = settings_data["rpc_url"]
        if "network" in settings_data:
            update_data["network"] = settings_data["network"].lower()
        if "verbose" in settings_data:
            update_data["verbose"] = settings_data["verbose"]
        if "slippage_percentage" in settings_data:
            update_data["slippage_percentage"] = Decimal(str(settings_data["slippage_percentage"]))
        if "default_fee_percentage" in settings_data:
            update_data["default_fee_percentage"] = Decimal(
                str(settings_data["default_fee_percentage"])
            )
        if "min_fee" in settings_data:
            update_data["min_fee"] = Decimal(str(settings_data["min_fee"]))
        if "max_fee" in settings_data:
            update_data["max_fee"] = Decimal(str(settings_data["max_fee"]))
        if "timeout" in settings_data:
            update_data["timeout"] = settings_data["timeout"]
        if "retry_attempts" in settings_data:
            update_data["retry_attempts"] = settings_data["retry_attempts"]
        if "retry_delay" in settings_data:
            update_data["retry_delay"] = Decimal(str(settings_data["retry_delay"]))

        # Handle private key encryption if provided
        if "private_key" in settings_data:
            private_key = settings_data["private_key"]
            if private_key:
                update_data["private_key_encrypted"] = encrypt_value(private_key)
            elif private_key == "":  # Explicitly empty string means clear it
                update_data["private_key_encrypted"] = ""

        # Update settings
        return await self.repository.update(db, settings, update_data)

    async def get_active_config(self, db: AsyncSession) -> OstiumConfig | None:
        """Get active settings as OstiumConfig.

        Args:
            db: Database session

        Returns:
            OstiumConfig if active settings exist, None otherwise
        """
        settings = await self.repository.get_active(db)
        if not settings:
            return None

        # Decrypt private key
        private_key = (
            decrypt_value(settings.private_key_encrypted) if settings.private_key_encrypted else ""
        )

        # Create OstiumConfig from settings
        return OstiumConfig(
            enabled=settings.enabled,
            private_key=private_key,
            rpc_url=settings.rpc_url,
            network=settings.network,
            verbose=settings.verbose,
            slippage_percentage=float(settings.slippage_percentage),
            timeout=settings.timeout,
            retry_attempts=settings.retry_attempts,
            retry_delay=float(settings.retry_delay),
        )

    def settings_to_dict(
        self, settings: OstiumSettings, include_private_key: bool = False
    ) -> dict[str, Any]:
        """Convert settings model to dictionary.

        Args:
            settings: OstiumSettings model instance
            include_private_key: Whether to include decrypted private key

        Returns:
            Dictionary representation of settings
        """
        data = {
            "id": settings.id,
            "enabled": settings.enabled,
            "rpc_url": settings.rpc_url,
            "network": settings.network,
            "verbose": settings.verbose,
            "slippage_percentage": float(settings.slippage_percentage),
            "default_fee_percentage": float(settings.default_fee_percentage),
            "min_fee": float(settings.min_fee),
            "max_fee": float(settings.max_fee),
            "timeout": settings.timeout,
            "retry_attempts": settings.retry_attempts,
            "retry_delay": float(settings.retry_delay),
            "is_active": settings.is_active,
            "version": settings.version,
            "created_by": settings.created_by,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat(),
        }

        if include_private_key and settings.private_key_encrypted:
            data["private_key"] = decrypt_value(settings.private_key_encrypted)
        else:
            data["private_key"] = None  # Never expose encrypted value

        return data
