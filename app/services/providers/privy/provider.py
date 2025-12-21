"""Privy authentication provider implementation."""

from typing import Any, cast

from app.services.providers.base import BaseAuthProvider
from app.services.providers.privy.config import PrivyAuthConfig

# Import Privy SDK
try:
    from privy import AsyncPrivyAPI

    # Try to import exceptions
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


class PrivyAuthProvider(BaseAuthProvider):
    """Privy authentication provider."""

    def __init__(self, config: PrivyAuthConfig):
        """Initialize Privy auth provider.

        Args:
            config: Privy configuration
        """
        super().__init__("privy")
        self.config = config
        self.app_id = config.app_id
        self.app_secret = config.app_secret
        self.environment = config.environment
        self.timeout = config.timeout
        self.retry_attempts = config.retry_attempts

        # Initialize Privy SDK client
        self._client: AsyncPrivyAPI | None = None

    async def initialize(self) -> None:
        """Initialize Privy service connection."""
        if self._initialized:
            return

        if AsyncPrivyAPI is None:
            raise ImportError(
                "privy-client is not installed. Install with: pip install privy-client"
            )

        if not self.app_id or not self.app_secret:
            raise ValueError("Privy app_id and app_secret are required")

        self._initialized = True

    async def health_check(self) -> bool:
        """Check if Privy service is healthy."""
        if not self._initialized or not self._client:
            return False

        try:
            # Verify the client is initialized
            client = await self._get_client()
            return client is not None
        except Exception:
            return False

    async def _get_client(self) -> AsyncPrivyAPI:
        """Get or create Privy SDK client."""
        if self._client is None:
            if AsyncPrivyAPI is None:
                raise ImportError(
                    "privy-client is not installed. Install with: pip install privy-client"
                )
            self._client = AsyncPrivyAPI(
                app_id=self.app_id,
                app_secret=self.app_secret,
                timeout=self.timeout,
                max_retries=self.retry_attempts,
            )
        return self._client

    async def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """Verify Privy access token.

        Args:
            token: Privy access token

        Returns:
            Decoded token payload or None if invalid
        """
        if not self.app_id or not self.app_secret:
            return None

        try:
            await self.initialize()
            client = await self._get_client()
            # Privy SDK has verify_access_token method
            verified_token = await client.auth.verify_access_token(token)

            # Convert to dict if needed
            if hasattr(verified_token, "to_dict"):
                token_dict = verified_token.to_dict()
            elif isinstance(verified_token, dict):
                token_dict = verified_token
            else:
                # Extract attributes if it's an object
                token_dict = {
                    "user_id": getattr(verified_token, "user_id", None),
                    "sub": getattr(verified_token, "user_id", None),  # Use sub for consistency
                    "email": getattr(verified_token, "email", None),
                    "exp": getattr(verified_token, "exp", None),
                    "iat": getattr(verified_token, "iat", None),
                }

            return cast(dict[str, Any], token_dict) if token_dict else None
        except (AuthenticationError, APIStatusError):
            # Token is invalid
            return None
        except Exception:
            return None

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Get user by Privy user ID.

        Args:
            user_id: Privy user identifier (UUID)

        Returns:
            User data or None if not found
        """
        if not self.app_id or not self.app_secret:
            return None

        try:
            await self.initialize()
            client = await self._get_client()
            # Privy SDK has users.get method
            user = await client.users.get(user_id)

            # Convert to dict
            if hasattr(user, "to_dict"):
                return cast(dict[str, Any], user.to_dict())
            if isinstance(user, dict):
                return cast(dict[str, Any], user)
            # Extract attributes if it's an object
            return {
                "id": getattr(user, "id", user_id),
                "user_id": getattr(user, "id", user_id),
                "email": getattr(user, "email", None),
                "created_at": getattr(user, "created_at", None),
                "linked_accounts": getattr(user, "linked_accounts", []),
            }
        except (APIStatusError, APIError):
            # User not found or API error
            return None
        except Exception:
            return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User data or None if not found
        """
        if not self.app_id or not self.app_secret:
            return None

        try:
            await self.initialize()
            client = await self._get_client()
            # Privy SDK may have search/list users by email
            # Note: This depends on Privy API capabilities
            users = await client.users.list()

            # Convert to list of dicts
            users_list = []
            if hasattr(users, "to_dict"):
                users_data = users.to_dict()
                users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
            elif isinstance(users, dict):
                users_list = users.get("users", [])
            elif hasattr(users, "users"):
                users_list = list(users.users) if hasattr(users.users, "__iter__") else []

            # Search for user with matching email
            for user in users_list:
                user_dict = user.to_dict() if hasattr(user, "to_dict") else user
                if isinstance(user_dict, dict):
                    user_email = user_dict.get("email")
                    # Check linked accounts for email
                    if not user_email:
                        linked_accounts = user_dict.get("linked_accounts", [])
                        for account in linked_accounts:
                            if isinstance(account, dict) and account.get("type") == "email":
                                user_email = account.get("address") or account.get("email")
                                break
                    if user_email == email:
                        return cast(dict[str, Any], user_dict)

            return None
        except (APIStatusError, APIError):
            return None
        except Exception:
            return None

    def extract_user_id_from_token(self, token_payload: dict[str, Any]) -> str | None:
        """Extract Privy user ID from token payload.

        Args:
            token_payload: Decoded token payload

        Returns:
            Privy user ID (UUID) or None if not found
        """
        # Privy user IDs are UUIDs
        user_id = token_payload.get("user_id") or token_payload.get("sub")
        if isinstance(user_id, str):
            # Check if it's a UUID format
            import re

            uuid_pattern = re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
            )
            if uuid_pattern.match(user_id):
                return user_id
        return None
