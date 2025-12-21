"""Privy authentication service for token verification and user management."""

from typing import Any, cast

from app.config import get_settings

settings = get_settings()

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


class PrivyAuthService:
    """Service for Privy authentication and user management."""

    def __init__(self) -> None:
        """Initialize Privy auth service."""
        self.app_id = settings.PRIVY_APP_ID
        self.app_secret = settings.PRIVY_APP_SECRET
        self.timeout = settings.PRIVY_TIMEOUT
        self.retry_attempts = settings.PRIVY_RETRY_ATTEMPTS

        # Initialize Management API client
        self._client: AsyncPrivyAPI | None = None

    @property
    async def client(self) -> AsyncPrivyAPI:
        """Get or create Privy API client."""
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
            client = await self.client
            # Privy SDK has verify_access_token method
            # According to Privy docs: https://docs.privy.io/basics/python/verify-access-token
            verified_token = await client.auth.verify_access_token(token)

            # Convert to dict if needed
            if hasattr(verified_token, "to_dict"):
                return cast(dict[str, Any], verified_token.to_dict())
            if isinstance(verified_token, dict):
                return cast(dict[str, Any], verified_token)
            # If it's an object with attributes, extract them
            if hasattr(verified_token, "user_id"):
                return {
                    "user_id": getattr(verified_token, "user_id", None),
                    "sub": getattr(verified_token, "user_id", None),  # Use sub for consistency
                    "email": getattr(verified_token, "email", None),
                    "exp": getattr(verified_token, "exp", None),
                    "iat": getattr(verified_token, "iat", None),
                }
            return None
        except (AuthenticationError, APIStatusError):
            # Token is invalid
            return None
        except Exception:
            return None

    async def get_user_by_id(self, privy_user_id: str) -> dict[str, Any] | None:
        """Get user by Privy user ID.

        Args:
            privy_user_id: Privy user identifier (UUID)

        Returns:
            User data or None if not found
        """
        if not self.app_id or not self.app_secret:
            return None

        try:
            client = await self.client
            # Privy SDK has users.get method
            # According to Privy docs: https://docs.privy.io/basics/python/users
            user = await client.users.get(privy_user_id)

            # Convert to dict
            if hasattr(user, "to_dict"):
                return cast(dict[str, Any], user.to_dict())
            if isinstance(user, dict):
                return cast(dict[str, Any], user)
            # Extract attributes if it's an object
            return {
                "id": getattr(user, "id", privy_user_id),
                "user_id": getattr(user, "id", privy_user_id),
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
            client = await self.client
            # Privy SDK may have search/list users by email
            # Note: This depends on Privy API capabilities
            # For now, we'll try to use the users.list with email filter if available
            # If not available, we may need to iterate through users
            # This is a simplified implementation - may need adjustment based on actual Privy API
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
                            if isinstance(account, dict) and account.get("email") == email:
                                return cast(dict[str, Any], user_dict)
                    elif user_email == email:
                        return cast(dict[str, Any], user_dict)

            return None
        except (APIStatusError, APIError):
            return None
        except Exception:
            return None
