"""Base Lighter service wrapper."""

import asyncio
from typing import Any

from loguru import logger

from app.config.providers.lighter import LighterConfig
from app.services.providers.base import BaseExternalService
from app.services.providers.exceptions import ServiceUnavailableError

# Optional import for lighter SDK
try:
    import lighter
except ImportError:
    lighter = None  # type: ignore


class LighterService(BaseExternalService):
    """Base wrapper for Lighter SDK."""

    def __init__(self, config: LighterConfig):
        """Initialize Lighter service."""
        super().__init__("lighter")
        self.config = config
        self._client: Any | None = None

    async def initialize(self) -> None:
        """Initialize the Lighter API client connection."""
        if self._initialized:
            return

        try:
            # Run client creation in thread pool since it may be blocking
            self._client = await asyncio.to_thread(self.config.create_api_client)
            self._initialized = True
            logger.info(f"{self.service_name} service initialized")
        except Exception as e:
            error = self.handle_service_error(e, "initialization")
            raise ServiceUnavailableError(
                f"Failed to initialize {self.service_name}: {str(e)}",
                service_name=self.service_name,
            ) from error

    async def health_check(self) -> bool:
        """Check if Lighter service is healthy."""
        if lighter is None:
            logger.warning("lighter SDK is not installed")
            return False

        if not self._initialized or not self._client:
            return False

        try:
            # Try to get account info as a health check
            account_api = lighter.AccountApi(self._client)
            # Try to get account with index 0 as health check
            result = await asyncio.to_thread(account_api.account, by="index", value="0")
            _ = result  # Use result to avoid unused coroutine warning
            return True
        except Exception as e:
            logger.warning(f"{self.service_name} health check failed: {e}")
            return False

    @property
    def client(self) -> Any:
        """Get the API client instance."""
        if not self._client:
            raise ServiceUnavailableError(
                f"{self.service_name} client not initialized",
                service_name=self.service_name,
            )
        return self._client

    async def close(self) -> None:
        """Close the API client connection."""
        if self._client:
            try:
                await asyncio.to_thread(self._client.close)
            except Exception as e:
                logger.warning(f"Error closing {self.service_name} client: {e}")
