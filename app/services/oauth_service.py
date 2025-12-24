"""OAuth service for handling OAuth operations."""

import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.cache import cache_manager
from app.models.auth import OAuthConnection
from app.models.user import User
from app.services.auth0_service import Auth0Service
from app.services.auth_service import AuthenticationService

settings = get_settings()

# OAuth state expiration time (10 minutes)
OAUTH_STATE_EXPIRATION = 600


class OAuthService:
    """Service for OAuth operations."""

    def __init__(self) -> None:
        """Initialize OAuth service."""
        self.auth0_service = Auth0Service()
        self.auth_service = AuthenticationService()

    async def _store_oauth_state(self, state: str, provider: str, redirect_uri: str) -> None:
        """Store OAuth state in cache.

        Args:
            state: State token
            provider: OAuth provider
            redirect_uri: Redirect URI
        """
        state_key = f"oauth:state:{state}"
        state_data = {
            "provider": provider,
            "redirect_uri": redirect_uri,
        }
        await cache_manager.set(state_key, state_data, expire=OAUTH_STATE_EXPIRATION)

    async def _validate_oauth_state(self, state: str) -> dict[str, str]:
        """Validate OAuth state and retrieve state data.

        Args:
            state: State token to validate

        Returns:
            State data dictionary with provider and redirect_uri

        Raises:
            ValueError: If state is invalid or expired
        """
        state_key = f"oauth:state:{state}"
        state_data = await cache_manager.get(state_key)

        if not state_data:
            raise ValueError("Invalid or expired OAuth state")

        # Delete state after use (one-time use)
        await cache_manager.delete(state_key)

        return state_data

    async def get_oauth_authorization_url(
        self,
        provider: str,
        redirect_uri: str | None = None,
    ) -> tuple[str, str]:
        """Get OAuth authorization URL.

        Args:
            provider: OAuth provider (google, apple)
            redirect_uri: Optional redirect URI (defaults to configured URI)

        Returns:
            Tuple of (authorization URL, state token)

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in ["google", "apple"]:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        # Check if provider is enabled
        if provider == "google" and not settings.AUTH0_GOOGLE_ENABLED:
            raise ValueError("Google OAuth is not enabled")
        if provider == "apple" and not settings.AUTH0_APPLE_ENABLED:
            raise ValueError("Apple OAuth is not enabled")

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Use configured redirect URI if not provided
        redirect_uri = redirect_uri or settings.AUTH0_OAUTH_REDIRECT_URI

        # Store state in cache
        await self._store_oauth_state(state, provider, redirect_uri)

        # Get authorization URL
        auth_url = self.auth0_service.get_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
            state=state,
        )

        return auth_url, state

    async def handle_oauth_callback(
        self,
        db: AsyncSession,
        code: str,
        state: str,
        redirect_uri: str | None = None,
        provider: str | None = None,
    ) -> tuple[User, dict[str, Any]]:
        """Handle OAuth callback.

        Args:
            db: Database session
            code: Authorization code
            state: State parameter (should match the one sent)
            redirect_uri: Redirect URI (optional, will use from state if available)
            provider: OAuth provider (optional, will use from state if available)

        Returns:
            Tuple of (User, tokens dict)

        Raises:
            ValueError: If state is invalid or callback fails
        """
        # Validate state and get state data
        try:
            state_data = await self._validate_oauth_state(state)
            # Use provider and redirect_uri from state if not provided
            provider = provider or state_data.get("provider")
            redirect_uri = redirect_uri or state_data.get("redirect_uri") or settings.AUTH0_OAUTH_REDIRECT_URI
        except ValueError as e:
            raise ValueError(f"OAuth state validation failed: {str(e)}") from e

        # Validate provider matches state
        if provider and state_data.get("provider") != provider:
            raise ValueError("OAuth provider mismatch")

        try:
            # Exchange code for tokens
            token_response = await self.auth0_service.exchange_code_for_tokens(
                code=code,
                redirect_uri=redirect_uri,
            )
        except Exception as e:
            raise ValueError(f"OAuth token exchange failed: {str(e)}") from e

        try:
            # Get user info
            userinfo = await self.auth0_service.get_userinfo(token_response["access_token"])
        except Exception as e:
            raise ValueError(f"OAuth user info retrieval failed: {str(e)}") from e

        # Determine provider from userinfo if not provided
        if not provider:
            auth0_user_id = userinfo.get("sub", "")
            if "google-oauth2" in auth0_user_id:
                provider = "google"
            elif "apple" in auth0_user_id:
                provider = "apple"
            else:
                raise ValueError("Unable to determine OAuth provider from user info")

        # Create or update user
        user = await self.auth_service.create_or_update_user_from_auth0(db, userinfo)

        # Store OAuth connection
        auth0_user_id = userinfo.get("sub", "")
        await self.auth_service._store_oauth_connection(
            db=db,
            user=user,
            provider=provider,
            provider_user_id=auth0_user_id,
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            expires_in=token_response.get("expires_in", 3600),
        )

        # Generate tokens
        tokens = await self.auth_service._generate_tokens(db, user)

        return user, tokens

    async def link_oauth_account(
        self,
        db: AsyncSession,
        user: User,
        code: str,
        redirect_uri: str | None = None,
    ) -> OAuthConnection:
        """Link OAuth account to existing user.

        Args:
            db: Database session
            user: User instance
            code: Authorization code
            redirect_uri: Redirect URI

        Returns:
            OAuthConnection instance
        """
        # Exchange code for tokens
        redirect_uri = redirect_uri or settings.AUTH0_OAUTH_REDIRECT_URI
        token_response = await self.auth0_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=redirect_uri,
        )

        # Get user info
        userinfo = await self.auth0_service.get_userinfo(token_response["access_token"])

        # Determine provider
        auth0_user_id = userinfo.get("sub", "")
        provider = "google" if "google-oauth2" in auth0_user_id else "apple"

        # Store OAuth connection
        oauth_conn = await self.auth_service._store_oauth_connection(
            db=db,
            user=user,
            provider=provider,
            provider_user_id=auth0_user_id,
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            expires_in=token_response.get("expires_in", 3600),
        )

        return oauth_conn

    async def unlink_oauth_account(
        self,
        db: AsyncSession,
        user: User,
        provider: str,
    ) -> None:
        """Unlink OAuth account from user.

        Args:
            db: Database session
            user: User instance
            provider: OAuth provider (google, apple)

        Raises:
            ValueError: If connection not found
        """
        # Find OAuth connection
        result = await db.execute(
            select(OAuthConnection).where(
                OAuthConnection.user_id == user.id,
                OAuthConnection.provider == provider,
            )
        )
        oauth_conn = result.scalar_one_or_none()

        if not oauth_conn:
            raise ValueError(f"OAuth connection for {provider} not found")

        # Delete connection
        await db.delete(oauth_conn)
        await db.commit()

    async def get_user_oauth_connections(
        self,
        db: AsyncSession,
        user: User,
    ) -> list[OAuthConnection]:
        """Get all OAuth connections for user.

        Args:
            db: Database session
            user: User instance

        Returns:
            List of OAuth connections
        """
        result = await db.execute(select(OAuthConnection).where(OAuthConnection.user_id == user.id))
        return list(result.scalars().all())
