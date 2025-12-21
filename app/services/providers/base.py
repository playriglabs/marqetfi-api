"""Base classes for external service providers."""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from app.services.providers.exceptions import ExternalServiceError


class BaseExternalService(ABC):
    """Base class for all external service wrappers."""

    def __init__(self, service_name: str):
        """Initialize base external service."""
        self.service_name = service_name
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service connection."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy."""
        pass

    def get_service_name(self) -> str:
        """Get the service name."""
        return self.service_name

    def handle_service_error(
        self, error: Exception, operation: str, context: dict[str, Any] | None = None
    ) -> ExternalServiceError:
        """Handle and transform service errors."""
        context_str = f" Context: {context}" if context else ""
        message = f"{self.service_name} {operation} failed: {str(error)}{context_str}"
        logger.error(message, exc_info=error)
        return ExternalServiceError(message, service_name=self.service_name)


class BaseTradingProvider(BaseExternalService, ABC):
    """Abstract interface for trading operations."""

    @abstractmethod
    async def open_trade(
        self,
        collateral: float,
        leverage: int,
        asset_type: int,
        direction: bool,
        order_type: str,
        at_price: float | None = None,
        tp: float | None = None,
        sl: float | None = None,
    ) -> dict[str, Any]:
        """Open a new trade."""
        pass

    @abstractmethod
    async def close_trade(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Close an existing trade."""
        pass

    @abstractmethod
    async def update_tp(self, pair_id: int, trade_index: int, tp_price: float) -> dict[str, Any]:
        """Update take profit for a trade."""
        pass

    @abstractmethod
    async def update_sl(self, pair_id: int, trade_index: int, sl_price: float) -> dict[str, Any]:
        """Update stop loss for a trade."""
        pass

    @abstractmethod
    async def get_open_trades(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open trades for a trader."""
        pass

    @abstractmethod
    async def get_open_trade_metrics(self, pair_id: int, trade_index: int) -> dict[str, Any]:
        """Get metrics for an open trade."""
        pass

    @abstractmethod
    async def get_orders(self, trader_address: str) -> list[dict[str, Any]]:
        """Get all open orders for a trader."""
        pass

    @abstractmethod
    async def cancel_limit_order(self, pair_id: int, order_index: int) -> dict[str, Any]:
        """Cancel a limit order."""
        pass

    @abstractmethod
    async def update_limit_order(
        self,
        pair_id: int,
        order_index: int,
        at_price: float,
    ) -> dict[str, Any]:
        """Update a limit order."""
        pass

    @abstractmethod
    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        pass


class BasePriceProvider(BaseExternalService, ABC):
    """Abstract interface for price feeds."""

    @abstractmethod
    async def get_price(self, asset: str, quote: str) -> tuple[float, int, str]:
        """Get current price for an asset.

        Returns:
            Tuple of (price, timestamp, source)
        """
        pass

    @abstractmethod
    async def get_prices(self, assets: list[tuple[str, str]]) -> dict[str, tuple[float, int, str]]:
        """Get prices for multiple assets.

        Args:
            assets: List of (asset, quote) tuples

        Returns:
            Dictionary mapping "{asset}/{quote}" to (price, timestamp, source)
        """
        pass

    @abstractmethod
    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        pass


class BaseSettlementProvider(BaseExternalService, ABC):
    """Abstract interface for trade execution."""

    @abstractmethod
    async def execute_trade(
        self,
        collateral: float,
        leverage: int,
        asset_type: int,
        direction: bool,
        order_type: str,
        at_price: float | None = None,
    ) -> dict[str, Any]:
        """Execute a trade."""
        pass

    @abstractmethod
    async def get_transaction_status(self, transaction_hash: str) -> dict[str, Any]:
        """Get status of a transaction."""
        pass


class BaseSwapProvider(BaseExternalService, ABC):
    """Abstract interface for cross-chain token swaps."""

    @abstractmethod
    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        from_chain: str,
        to_chain: str,
        amount: str,
    ) -> dict[str, Any]:
        """Get a quote for a token swap.

        Args:
            from_token: Source token address
            to_token: Destination token address
            from_chain: Source chain identifier
            to_chain: Destination chain identifier
            amount: Amount to swap (as string to preserve precision)

        Returns:
            Dictionary containing quote information including:
            - estimated_amount: Estimated output amount
            - fee: Swap fee
            - transaction: Transaction data (if needed)
            - validity: Quote validity information
        """
        pass

    @abstractmethod
    async def execute_swap(
        self,
        quote: dict[str, Any],
        wallet_address: str,
    ) -> dict[str, Any]:
        """Execute a token swap.

        Args:
            quote: Quote data from get_swap_quote
            wallet_address: Wallet address to execute swap from

        Returns:
            Dictionary containing:
            - transaction_hash: Transaction hash
            - status: Swap status
            - estimated_completion: Estimated completion time
        """
        pass

    @abstractmethod
    async def get_swap_status(self, transaction_hash: str) -> dict[str, Any]:
        """Get status of a swap transaction.

        Args:
            transaction_hash: Transaction hash from execute_swap

        Returns:
            Dictionary containing:
            - status: Swap status (pending, completed, failed)
            - transaction_hash: Transaction hash
            - from_amount: Source amount
            - to_amount: Destination amount (if completed)
            - error: Error message (if failed)
        """
        pass


class BaseAuthProvider(BaseExternalService, ABC):
    """Abstract interface for authentication providers."""

    @abstractmethod
    async def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """Verify an access token.

        Args:
            token: Access token to verify

        Returns:
            Decoded token payload or None if invalid
        """
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Get user information by provider user ID.

        Args:
            user_id: Provider-specific user identifier

        Returns:
            User data dictionary or None if not found
        """
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user information by email.

        Args:
            email: User email address

        Returns:
            User data dictionary or None if not found
        """
        pass

    @abstractmethod
    def extract_user_id_from_token(self, token_payload: dict[str, Any]) -> str | None:
        """Extract provider user ID from token payload.

        Args:
            token_payload: Decoded token payload

        Returns:
            Provider user ID or None if not found
        """
        pass
