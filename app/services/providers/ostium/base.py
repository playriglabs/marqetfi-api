"""Base Ostium service wrapper."""

import asyncio

from loguru import logger
from ostium_python_sdk import OstiumSDK

from app.config.providers.ostium import OstiumConfig
from app.services.providers.base import BaseExternalService
from app.services.providers.exceptions import ServiceUnavailableError


class OstiumService(BaseExternalService):
    """Base wrapper for Ostium SDK."""

    def __init__(self, config: OstiumConfig):
        """Initialize Ostium service."""
        super().__init__("ostium")
        self.config = config
        self._sdk: OstiumSDK | None = None

    async def initialize(self) -> None:
        """Initialize the Ostium SDK connection."""
        if self._initialized:
            return

        try:
            # Run SDK creation in thread pool since it may be blocking
            self._sdk = await asyncio.to_thread(self.config.create_sdk_instance)
            self._initialized = True
            logger.info(f"{self.service_name} service initialized")
        except Exception as e:
            error = self.handle_service_error(e, "initialization")
            raise ServiceUnavailableError(
                f"Failed to initialize {self.service_name}: {str(e)}",
                service_name=self.service_name,
            ) from error

    async def health_check(self) -> bool:
        """Check if Ostium service is healthy."""
        if not self._initialized or not self._sdk:
            return False

        try:
            # Try to get pairs as a health check
            await asyncio.to_thread(self._sdk.subgraph.get_pairs)
            return True
        except Exception as e:
            logger.warning(f"{self.service_name} health check failed: {e}")
            return False

    @property
    def sdk(self) -> OstiumSDK:
        """Get the SDK instance."""
        if not self._sdk:
            raise ServiceUnavailableError(
                f"{self.service_name} SDK not initialized",
                service_name=self.service_name,
            )
        return self._sdk
