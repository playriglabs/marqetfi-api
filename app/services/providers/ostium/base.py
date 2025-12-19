"""Base Ostium service wrapper."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar, cast

from loguru import logger
from ostium_python_sdk import OstiumSDK
from web3 import Web3

from app.config.providers.ostium import OstiumConfig
from app.core.wallet_signer import WalletSigner
from app.services.providers.base import BaseExternalService
from app.services.providers.exceptions import ServiceUnavailableError

T = TypeVar("T")


class OstiumService(BaseExternalService):
    """Base wrapper for Ostium SDK."""

    def __init__(self, config: OstiumConfig):
        """Initialize Ostium service."""
        super().__init__("ostium")
        self.config = config
        self._sdk: OstiumSDK | None = None
        self._web3: Web3 | None = None
        self._wallet_signer: WalletSigner | None = None

    async def initialize(self) -> None:
        """Initialize the Ostium SDK connection."""
        if self._initialized:
            return

        try:
            # Initialize wallet signer if wallet provider is configured
            if self.config.should_use_wallet_provider():
                self._wallet_signer = WalletSigner(
                    wallet_provider=self.config.wallet_provider,
                    wallet_id=self.config.wallet_provider_id,
                    private_key=(
                        self.config.private_key if self.config.fallback_to_private_key else None
                    ),
                )
                logger.info(
                    f"{self.service_name} wallet provider enabled: {self.config.wallet_provider}"
                )

            # Run SDK creation in thread pool since it may be blocking
            self._sdk = await asyncio.to_thread(self.config.create_sdk_instance)

            # Initialize web3 connection for transaction status checks
            # Try to get web3 from SDK first, fall back to creating our own
            try:
                # Check if SDK exposes web3
                if hasattr(self._sdk, "web3") and self._sdk.web3 is not None:  # type: ignore[union-attr]
                    self._web3 = self._sdk.web3  # type: ignore[union-attr]
                elif hasattr(self._sdk, "w3") and self._sdk.w3 is not None:  # type: ignore[union-attr]
                    self._web3 = self._sdk.w3  # type: ignore[union-attr]
                else:
                    # Create web3 connection using RPC URL
                    self._web3 = await asyncio.to_thread(
                        Web3, Web3.HTTPProvider(self.config.rpc_url)
                    )
            except Exception as web3_error:
                logger.warning(
                    f"Failed to initialize web3 connection: {web3_error}, will create on demand"
                )
                self._web3 = None

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
            # Try to get pairs as a health check with retry logic
            await self._execute_with_retry(
                self._sdk.subgraph.get_pairs,
                "health_check",
            )
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

    def get_web3(self) -> Web3:
        """Get web3 instance for blockchain interactions.

        Returns:
            Web3 instance connected to the configured RPC URL

        Raises:
            ServiceUnavailableError: If web3 cannot be initialized
        """
        if self._web3 is not None:
            return self._web3

        # Try to get from SDK if not already initialized
        if self._sdk:
            try:
                if hasattr(self._sdk, "web3") and self._sdk.web3 is not None:
                    self._web3 = self._sdk.web3
                    return self._web3
                elif hasattr(self._sdk, "w3") and self._sdk.w3 is not None:
                    self._web3 = self._sdk.w3
                    return self._web3
            except Exception:
                pass

        # Create new web3 connection
        if not self.config.rpc_url:
            raise ServiceUnavailableError(
                f"{self.service_name} RPC URL not configured",
                service_name=self.service_name,
            )

        self._web3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
        return self._web3

    @property
    def wallet_signer(self) -> WalletSigner | None:
        """Get wallet signer instance if wallet provider is configured.

        Returns:
            WalletSigner instance or None if not using wallet provider
        """
        return self._wallet_signer

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable.

        Args:
            error: The exception to check

        Returns:
            True if the error is retryable, False otherwise
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network-related errors (retryable)
        retryable_indicators = [
            "timeout",
            "connection",
            "network",
            "temporarily",
            "rate limit",
            "too many requests",
            "service unavailable",
            "bad gateway",
            "gateway timeout",
            "internal server error",
            "502",
            "503",
            "504",
        ]

        # Non-retryable errors
        non_retryable_indicators = [
            "validation",
            "invalid",
            "unauthorized",
            "forbidden",
            "not found",
            "insufficient funds",
            "insufficient balance",
            "401",
            "403",
            "404",
        ]

        # Check for non-retryable first
        for indicator in non_retryable_indicators:
            if indicator in error_str:
                return False

        # Check for retryable
        for indicator in retryable_indicators:
            if indicator in error_str or indicator in error_type:
                return True

        # Default: retry network errors, don't retry others
        return isinstance(error, ConnectionError | TimeoutError | asyncio.TimeoutError)

    async def _execute_with_retry(
        self,
        operation: Callable[..., T],
        operation_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute an operation with retry logic and timeout.

        Args:
            operation: The async function to execute
            operation_name: Name of the operation for logging
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            ServiceUnavailableError: If all retries are exhausted
            asyncio.TimeoutError: If operation times out
        """
        max_attempts = self.config.retry_attempts + 1  # +1 for initial attempt
        retry_delay = self.config.retry_delay
        timeout = self.config.timeout

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                # Apply timeout to the operation
                if asyncio.iscoroutinefunction(operation):
                    result = await asyncio.wait_for(
                        operation(*args, **kwargs),
                        timeout=timeout,
                    )
                else:
                    # For sync functions, run in thread pool with timeout
                    result = await asyncio.wait_for(
                        asyncio.to_thread(operation, *args, **kwargs),
                        timeout=timeout,
                    )

                # Success - log if it was a retry
                if attempt > 1:
                    logger.info(
                        f"{self.service_name} {operation_name} succeeded after {attempt} attempts"
                    )

                return cast(T, result)

            except TimeoutError as e:
                last_error = e
                error_msg = f"{self.service_name} {operation_name} timed out after {timeout}s"
                logger.warning(f"{error_msg} (attempt {attempt}/{max_attempts})")

                if attempt < max_attempts:
                    await asyncio.sleep(retry_delay * attempt)  # Exponential backoff
                    continue
                else:
                    raise ServiceUnavailableError(
                        f"{error_msg} after {max_attempts} attempts",
                        service_name=self.service_name,
                    ) from e

            except Exception as e:
                last_error = e

                # Check if error is retryable
                if not self._is_retryable_error(e):
                    # Non-retryable error - raise immediately
                    logger.error(
                        f"{self.service_name} {operation_name} failed with non-retryable error: {e}"
                    )
                    raise

                # Retryable error - log and retry
                logger.warning(
                    f"{self.service_name} {operation_name} failed (attempt {attempt}/{max_attempts}): {e}"
                )

                if attempt < max_attempts:
                    # Exponential backoff: delay * attempt number
                    delay = retry_delay * attempt
                    logger.debug(f"Retrying {operation_name} after {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    error_msg = (
                        f"{self.service_name} {operation_name} failed after {max_attempts} attempts"
                    )
                    logger.error(f"{error_msg}: {e}")
                    raise ServiceUnavailableError(
                        error_msg,
                        service_name=self.service_name,
                    ) from e

        # Should never reach here, but just in case
        if last_error:
            raise ServiceUnavailableError(
                f"{self.service_name} {operation_name} failed",
                service_name=self.service_name,
            ) from last_error

        raise ServiceUnavailableError(
            f"{self.service_name} {operation_name} failed",
            service_name=self.service_name,
        )
