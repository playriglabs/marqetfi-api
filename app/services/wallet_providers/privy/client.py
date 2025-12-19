"""Privy API client wrapper using the official privy-client SDK.

Official SDK: https://pypi.org/project/privy-client/
Documentation: https://docs.privy.io
"""

from typing import Any, cast

# Import Privy SDK and exceptions with multiple fallback paths
try:
    from privy import AsyncPrivyAPI

    # Try to import exceptions - Stainless-generated SDKs typically use _exceptions
    # Try multiple import paths to handle different SDK versions
    _privy_exceptions_imported = False
    try:
        from privy._exceptions import (
            APIConnectionError,
            APIError,
            APIStatusError,
            AuthenticationError,
            RateLimitError,
        )

        _privy_exceptions_imported = True
    except ImportError:
        try:
            # Alternative: try privy.exceptions
            from privy.exceptions import (
                APIConnectionError,
                APIError,
                APIStatusError,
                AuthenticationError,
                RateLimitError,
            )

            _privy_exceptions_imported = True
        except ImportError:
            try:
                # Alternative: try importing from privy directly
                from privy import (
                    APIConnectionError,
                    APIError,
                    APIStatusError,
                    AuthenticationError,
                    RateLimitError,
                )

                _privy_exceptions_imported = True
            except ImportError:
                pass

    # If exceptions weren't imported, create placeholder classes
    # We'll use string matching in error handling as fallback
    if not _privy_exceptions_imported:

        class APIError(Exception):  # type: ignore[no-redef]
            """Placeholder for Privy APIError."""

            pass

        class APIConnectionError(Exception):  # type: ignore[no-redef]
            """Placeholder for Privy APIConnectionError."""

            pass

        class APIStatusError(Exception):  # type: ignore[no-redef]
            """Placeholder for Privy APIStatusError."""

            status_code: int = 0

        class AuthenticationError(Exception):  # type: ignore[no-redef]
            """Placeholder for Privy AuthenticationError."""

            pass

        class RateLimitError(Exception):  # type: ignore[no-redef]
            """Placeholder for Privy RateLimitError."""

            pass

except ImportError:
    AsyncPrivyAPI = None

    # Create placeholder exception classes when SDK is not installed
    class APIError(Exception):  # type: ignore[no-redef]
        """Placeholder for Privy APIError."""

        pass

    class APIConnectionError(Exception):  # type: ignore[no-redef]
        """Placeholder for Privy APIConnectionError."""

        pass

    class APIStatusError(Exception):  # type: ignore[no-redef]
        """Placeholder for Privy APIStatusError."""

        status_code: int = 0

    class AuthenticationError(Exception):  # type: ignore[no-redef]
        """Placeholder for Privy AuthenticationError."""

        pass

    class RateLimitError(Exception):  # type: ignore[no-redef]
        """Placeholder for Privy RateLimitError."""

        pass


from app.services.wallet_providers.privy.config import PrivyWalletConfig
from app.services.wallet_providers.privy.exceptions import (
    PrivyAPIError,
    PrivyAuthenticationError,
    PrivyRateLimitError,
)


class PrivyClient:
    """Client for interacting with Privy API using the official SDK."""

    def __init__(self, config: PrivyWalletConfig):
        """Initialize Privy client.

        Args:
            config: Privy configuration
        """
        if AsyncPrivyAPI is None:
            raise ImportError(
                "privy-client is not installed. Install with: pip install privy-client"
            )

        self.config = config
        self.app_id = config.app_id
        self.app_secret = config.app_secret
        self.environment = config.environment  # Privy SDK uses "production" or "staging"

        # Initialize the Privy SDK client
        self._client: AsyncPrivyAPI | None = None

    async def _get_client(self) -> AsyncPrivyAPI:
        """Get or create Privy SDK client.

        According to Privy docs: https://docs.privy.io/basics/python/setup
        Uses PrivyAPI (sync) or AsyncPrivyAPI (async) with app_id and app_secret.
        """
        if self._client is None:
            self._client = AsyncPrivyAPI(
                app_id=self.app_id,
                app_secret=self.app_secret,
                # Note: environment parameter may not exist in all SDK versions
                # It defaults to "production" if not specified
                timeout=self.config.timeout,
                max_retries=self.config.retry_attempts,
            )
        return self._client

    async def close(self) -> None:
        """Close Privy SDK client."""
        if self._client:
            await self._client.close()
            self._client = None

    def _handle_error(self, error: Exception) -> None:
        """Handle and transform Privy SDK errors.

        Args:
            error: Exception from Privy SDK

        Raises:
            PrivyAPIError: For API errors
            PrivyAuthenticationError: For authentication errors
            PrivyRateLimitError: For rate limit errors
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Check for authentication errors
        if (
            isinstance(error, AuthenticationError)
            or "authentication" in error_str
            or "401" in error_str
        ):
            raise PrivyAuthenticationError(
                f"Privy authentication failed: {str(error)}",
                service_name="privy",
            ) from error

        # Check for rate limit errors
        if isinstance(error, RateLimitError) or "rate limit" in error_str or "429" in error_str:
            raise PrivyRateLimitError(
                f"Privy rate limit exceeded: {str(error)}",
                service_name="privy",
            ) from error

        # Check for connection errors
        if (
            isinstance(error, APIConnectionError)
            or "connection" in error_str
            or "timeout" in error_str
        ):
            raise PrivyAPIError(
                f"Privy connection error: {str(error)}",
                service_name="privy",
            ) from error

        # Check for API status errors
        if isinstance(error, APIStatusError):
            status_code = getattr(error, "status_code", 0)
            raise PrivyAPIError(
                f"Privy API error: {status_code} - {str(error)}",
                service_name="privy",
            ) from error

        # Check for generic API errors
        if isinstance(error, APIError):
            raise PrivyAPIError(
                f"Privy API error: {str(error)}",
                service_name="privy",
            ) from error

        # For unknown errors, wrap in PrivyAPIError
        raise PrivyAPIError(
            f"Privy error ({error_type}): {str(error)}",
            service_name="privy",
        ) from error

    async def create_wallet(self, network: str) -> dict[str, Any]:
        """Create a new wallet via Privy API.

        Args:
            network: Network name (testnet/mainnet)

        Returns:
            Wallet information
        """
        try:
            client = await self._get_client()

            # Map network to chain_type
            # Privy uses chain_type like "ethereum", "base", etc.
            # For testnet/mainnet, we need to determine the chain
            # Defaulting to ethereum for now
            chain_type = "ethereum"  # Could be extended to support other chains

            # Create wallet using Privy SDK
            # According to Privy docs, wallets are created with chain_type and owner
            # For server-side wallets, owner may be optional or use app credentials
            wallet = await client.wallets.create(
                chain_type=chain_type,
            )

            # Convert Privy SDK response to dict
            if hasattr(wallet, "to_dict"):
                wallet_dict = wallet.to_dict()
            else:
                wallet_dict = {
                    "id": getattr(wallet, "id", None),
                    "address": getattr(wallet, "address", None),
                    "chain_type": getattr(wallet, "chain_type", chain_type),
                }

            # Ensure we have the required fields
            wallet_id = wallet_dict.get("id") or getattr(wallet, "id", None)
            address = wallet_dict.get("address") or getattr(wallet, "address", None)

            return {
                "id": wallet_id,
                "wallet_id": wallet_id,  # Alias for compatibility
                "address": address,
                "wallet_address": address,  # Alias for compatibility
                "chain_type": wallet_dict.get("chain_type", chain_type),
                "network": network,
                "metadata": wallet_dict,
            }
        except Exception as e:
            self._handle_error(e)
            raise  # Never reached, but satisfies type checker

    async def get_wallet(self, wallet_id: str) -> dict[str, Any]:
        """Get wallet information.

        Args:
            wallet_id: Privy wallet ID

        Returns:
            Wallet information
        """
        try:
            client = await self._get_client()
            wallet = await client.wallets.get(wallet_id)

            # Convert Privy SDK response to dict
            if hasattr(wallet, "to_dict"):
                wallet_dict = wallet.to_dict()
            else:
                wallet_dict = {
                    "id": getattr(wallet, "id", None),
                    "address": getattr(wallet, "address", None),
                    "wallet_address": getattr(wallet, "address", None),  # Alias
                    "chain_type": getattr(wallet, "chain_type", None),
                    "owner": getattr(wallet, "owner", None),
                }

            # Ensure address field exists
            if "address" not in wallet_dict and "wallet_address" in wallet_dict:
                wallet_dict["address"] = wallet_dict["wallet_address"]
            elif "address" in wallet_dict and "wallet_address" not in wallet_dict:
                wallet_dict["wallet_address"] = wallet_dict["address"]

            return cast(dict[str, Any], wallet_dict)
        except Exception as e:
            self._handle_error(e)
            raise  # Never reached, but satisfies type checker

    async def sign_transaction(self, wallet_id: str, transaction: dict[str, Any]) -> str:
        """Sign a transaction via Privy API.

        According to Privy docs: https://docs.privy.io/basics/python/quickstart
        Uses client.wallets.rpc() with method "eth_signTransaction"

        Args:
            wallet_id: Privy wallet ID
            transaction: Transaction data with fields like:
                - to: Recipient address
                - value: Amount in wei
                - data: Transaction data (optional)
                - gas: Gas limit (optional, will be populated)
                - gasPrice: Gas price (optional, will be populated)
                - nonce: Transaction nonce (optional, will be populated)

        Returns:
            Signed transaction hash or signature
        """
        try:
            client = await self._get_client()

            # Privy SDK uses RPC pattern for signing transactions
            # Method: "eth_signTransaction" for EVM chains
            # Extract chain_id from transaction or use default (1 for mainnet)
            chain_id = transaction.get("chainId", 1)
            caip2 = f"eip155:{chain_id}"

            # Use Privy's RPC method for signing transactions
            result = await client.wallets.rpc(
                wallet_id=wallet_id,
                method="eth_signTransaction",
                caip2=caip2,
                params={
                    "transaction": transaction,
                },
            )

            # Extract signature/transaction hash from response
            if hasattr(result, "to_dict"):
                data = result.to_dict()
                return cast(
                    str,
                    data.get("signature")
                    or data.get("transaction_hash")
                    or data.get("hash")
                    or data.get("signed_transaction", ""),
                )
            if isinstance(result, str):
                return result
            if isinstance(result, dict):
                return cast(
                    str,
                    result.get("signature")
                    or result.get("transaction_hash")
                    or result.get("hash")
                    or result.get("signed_transaction", ""),
                )
            # Try to get signature attribute
            if hasattr(result, "signature"):
                return cast(str, result.signature)
            if hasattr(result, "transaction_hash"):
                return cast(str, result.transaction_hash)
            if hasattr(result, "hash"):
                return cast(str, result.hash)
            return str(result)
        except Exception as e:
            self._handle_error(e)
            raise  # Never reached, but satisfies type checker

    async def sign_message(self, wallet_id: str, message: str) -> str:
        """Sign a message via Privy API.

        According to Privy docs: https://docs.privy.io/basics/python/quickstart
        Uses client.wallets.rpc() with method "personal_sign"

        Args:
            wallet_id: Privy wallet ID
            message: Message to sign (plaintext)

        Returns:
            Message signature (hex string)
        """
        try:
            client = await self._get_client()

            # Privy SDK uses RPC pattern for signing messages
            # Method: "personal_sign" for Ethereum/EVM chains
            # Default to Ethereum mainnet (chain_id=1, caip2="eip155:1")
            # Note: For other chains, you may need to pass chain_id or get it from wallet
            caip2 = "eip155:1"  # Default to Ethereum mainnet, can be made configurable

            # Use Privy's RPC method for signing messages
            result = await client.wallets.rpc(
                wallet_id=wallet_id,
                method="personal_sign",
                caip2=caip2,
                params={
                    "message": message,
                    "encoding": "utf-8",
                },
            )

            # Extract signature from response
            if hasattr(result, "to_dict"):
                data = result.to_dict()
                return cast(str, data.get("signature", ""))
            if isinstance(result, str):
                return result
            if isinstance(result, dict):
                return cast(str, result.get("signature", ""))
            # Try to get signature attribute
            if hasattr(result, "signature"):
                return cast(str, result.signature)
            return str(result)
        except Exception as e:
            self._handle_error(e)
            raise  # Never reached, but satisfies type checker
