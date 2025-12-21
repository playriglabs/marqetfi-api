"""Auth0 authentication provider implementation."""

import asyncio
from typing import Any, cast

from auth0 import Auth0Error
from auth0.authentication import GetToken
from auth0.management import Auth0

from app.core.security import verify_auth0_token
from app.services.providers.auth0.config import Auth0AuthConfig
from app.services.providers.base import BaseAuthProvider


class Auth0AuthProvider(BaseAuthProvider):
    """Auth0 authentication provider."""

    def __init__(self, config: Auth0AuthConfig):
        """Initialize Auth0 auth provider.

        Args:
            config: Auth0 configuration
        """
        super().__init__("auth0")
        self.config = config
        self.domain = config.domain
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.audience = config.audience
        self.management_client_id = config.management_client_id
        self.management_client_secret = config.management_client_secret
        self.algorithm = config.algorithm

        # Initialize Management API client
        self._management_api: Auth0 | None = None

    async def initialize(self) -> None:
        """Initialize Auth0 service connection."""
        if self._initialized:
            return

        if not self.domain or not self.management_client_id or not self.management_client_secret:
            raise ValueError(
                "Auth0 domain, management_client_id, and management_client_secret are required"
            )

        self._initialized = True

    async def health_check(self) -> bool:
        """Check if Auth0 service is healthy."""
        if not self._initialized:
            return False

        try:
            # Try to get management API token as a health check
            get_token = GetToken(
                self.domain,
                self.management_client_id,
                client_secret=self.management_client_secret,
            )
            await asyncio.to_thread(
                get_token.client_credentials, audience=f"https://{self.domain}/api/v2/"
            )
            return True
        except Exception:
            return False

    @property
    def management_api(self) -> Auth0:
        """Get or create Management API client."""
        if self._management_api is None:
            get_token = GetToken(
                self.domain,
                self.management_client_id,
                client_secret=self.management_client_secret,
            )
            token = get_token.client_credentials(audience=f"https://{self.domain}/api/v2/")
            mgmt_api_token = token["access_token"]

            self._management_api = Auth0(
                domain=self.domain,
                token=mgmt_api_token,
            )
        return self._management_api

    async def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """Verify Auth0 access token.

        Args:
            token: Auth0 access token

        Returns:
            Decoded token payload or None if invalid
        """
        if not self.domain or not self.audience:
            return None

        # Use existing verify_auth0_token function
        return verify_auth0_token(token)

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Get user by Auth0 user ID.

        Args:
            user_id: Auth0 user identifier

        Returns:
            User data or None if not found
        """
        try:
            await self.initialize()
            user = await asyncio.to_thread(self.management_api.users.get, user_id)
            if user is None:
                return None
            return cast(dict[str, Any], user if isinstance(user, dict) else dict(user))
        except Auth0Error:
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
        try:
            await self.initialize()
            users = await asyncio.to_thread(self.management_api.users.list, q=f'email:"{email}"')
            if users and len(users.get("users", [])) > 0:
                user = users["users"][0]
                return cast(dict[str, Any], user if isinstance(user, dict) else dict(user))
            return None
        except Auth0Error:
            return None
        except Exception:
            return None

    def extract_user_id_from_token(self, token_payload: dict[str, Any]) -> str | None:
        """Extract Auth0 user ID from token payload.

        Args:
            token_payload: Decoded token payload

        Returns:
            Auth0 user ID or None if not found
        """
        sub = token_payload.get("sub")
        if isinstance(sub, str) and "|" in sub:
            # Auth0 user ID format: "auth0|..." or "google-oauth2|..."
            return sub
        return None

    # Additional Auth0-specific methods for OAuth flows
    def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        state: str | None = None,
    ) -> str:
        """Get OAuth authorization URL.

        Args:
            provider: OAuth provider (google, apple)
            redirect_uri: Callback redirect URI
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        connection = f"{provider}-oauth2" if provider != "apple" else "apple"
        params = {
            "client_id": self.client_id,
            "connection": connection,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
        }
        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://{self.domain}/authorize?{query_string}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Callback redirect URI

        Returns:
            Token response with access_token, id_token, etc.

        Raises:
            Auth0Error: If token exchange fails
        """
        try:
            get_token = GetToken(self.domain, self.client_id, client_secret=self.client_secret)
            token_response = await asyncio.to_thread(
                get_token.authorization_code,
                code=code,
                redirect_uri=redirect_uri,
            )
            return cast(
                dict[str, Any],
                token_response if isinstance(token_response, dict) else dict(token_response),
            )
        except Auth0Error as e:
            raise e

    async def get_userinfo(self, access_token: str) -> dict[str, Any]:
        """Get user info from access token.

        Args:
            access_token: Auth0 access token

        Returns:
            User info

        Raises:
            Auth0Error: If request fails
        """
        try:
            from auth0.authentication import Users

            users = Users(self.domain)
            userinfo = await asyncio.to_thread(users.userinfo, access_token)
            return cast(dict[str, Any], userinfo if isinstance(userinfo, dict) else dict(userinfo))
        except Auth0Error as e:
            raise e
