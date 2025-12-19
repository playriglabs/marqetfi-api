"""Auth0 service for authentication and user management."""

import asyncio
from typing import Any, cast

from auth0 import Auth0Error
from auth0.authentication import GetToken
from auth0.management import Auth0

from app.config import get_settings

settings = get_settings()


class Auth0Service:
    """Service for Auth0 authentication and management."""

    def __init__(self) -> None:
        """Initialize Auth0 service."""
        self.domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.audience = settings.AUTH0_AUDIENCE
        self.management_client_id = settings.AUTH0_MANAGEMENT_CLIENT_ID
        self.management_client_secret = settings.AUTH0_MANAGEMENT_CLIENT_SECRET

        # Initialize Management API client
        self._management_api: Auth0 | None = None

    @property
    def management_api(self) -> Auth0:
        """Get or create Management API client."""
        if self._management_api is None:
            get_token = GetToken(
                self.domain,
                self.management_client_id,
                client_secret=self.management_client_secret,
            )
            # Note: This is called during property access, so we can't use async here
            # Token refresh should be handled separately if needed
            token = get_token.client_credentials(audience=f"https://{self.domain}/api/v2/")
            mgmt_api_token = token["access_token"]

            self._management_api = Auth0(
                domain=self.domain,
                token=mgmt_api_token,
            )
        return self._management_api

    async def register_user(
        self,
        email: str,
        password: str,
        username: str | None = None,
    ) -> dict[str, Any]:
        """Register a new user with email/password via Auth0.

        Args:
            email: User email
            password: User password
            username: Optional username

        Returns:
            Auth0 user data

        Raises:
            Auth0Error: If registration fails
        """
        try:
            user_data: dict[str, Any] = {
                "email": email,
                "password": password,
                "connection": "Username-Password-Authentication",
                "email_verified": False,
            }
            if username:
                user_data["username"] = username

            user = await asyncio.to_thread(self.management_api.users.create, user_data)
            return cast(dict[str, Any], user if isinstance(user, dict) else dict(user))
        except Auth0Error as e:
            raise e

    async def get_user_by_id(self, auth0_user_id: str) -> dict[str, Any] | None:
        """Get user by Auth0 user ID.

        Args:
            auth0_user_id: Auth0 user identifier

        Returns:
            User data or None if not found
        """
        try:
            user = await asyncio.to_thread(self.management_api.users.get, auth0_user_id)
            if user is None:
                return None
            return cast(dict[str, Any], user if isinstance(user, dict) else dict(user))
        except Auth0Error:
            return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User data or None if not found
        """
        try:
            users = await asyncio.to_thread(self.management_api.users.list, q=f'email:"{email}"')
            if users and len(users.get("users", [])) > 0:
                user = users["users"][0]
                return cast(dict[str, Any], user if isinstance(user, dict) else dict(user))
            return None
        except Auth0Error:
            return None

    async def update_user(
        self,
        auth0_user_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update user in Auth0.

        Args:
            auth0_user_id: Auth0 user identifier
            **kwargs: Fields to update

        Returns:
            Updated user data

        Raises:
            Auth0Error: If update fails
        """
        try:
            user = await asyncio.to_thread(self.management_api.users.update, auth0_user_id, kwargs)
            return cast(dict[str, Any], user if isinstance(user, dict) else dict(user))
        except Auth0Error as e:
            raise e

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
