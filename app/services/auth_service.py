"""Authentication service for handling all authentication methods."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import create_access_token, create_refresh_token
from app.models.auth import OAuthConnection, Session
from app.models.enums import AuthMethod, FeatureAccessLevel, WalletType
from app.models.user import User
from app.services.auth0_service import Auth0Service
from app.services.user_service import UserService

settings = get_settings()


class AuthenticationService:
    """Service for handling authentication operations."""

    def __init__(self) -> None:
        """Initialize authentication service."""
        self.auth0_service = Auth0Service()
        self.user_service = UserService()

    async def register_with_email(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        username: str | None = None,
    ) -> tuple[User, dict[str, Any]]:
        """Register a new user with email/password via Auth0.

        Args:
            db: Database session
            email: User email
            password: User password
            username: Optional username

        Returns:
            Tuple of (User, tokens dict)

        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        existing_user = await self.user_service.get_user_by_email(db, email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Register user in Auth0
        auth0_user = await self.auth0_service.register_user(
            email=email,
            password=password,
            username=username,
        )

        # Create user in local database
        username = username or email.split("@")[0]
        user = User(
            email=email,
            username=username,
            auth0_user_id=auth0_user["user_id"],
            auth_method=AuthMethod.EMAIL,
            wallet_type=WalletType.NONE,
            feature_access_level=FeatureAccessLevel.FULL,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Generate tokens
        tokens = await self._generate_tokens(db, user)

        return user, tokens

    async def login_with_email(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[User, dict[str, Any]]:
        """Login user with email/password.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            Tuple of (User, tokens dict)

        Raises:
            ValueError: If credentials are invalid
        """
        # Get user from database
        user = await self.user_service.get_user_by_email(db, email)
        if not user:
            raise ValueError("Invalid email or password")

        # If user has Auth0 ID, verify with Auth0
        if user.auth0_user_id:
            # For now, we'll use local password verification for email users
            # In production, you might want to verify with Auth0
            if not user.hashed_password:
                raise ValueError("Invalid email or password")

            from app.core.security import verify_password

            if not verify_password(password, user.hashed_password):
                raise ValueError("Invalid email or password")
        else:
            # Legacy user without Auth0
            if not user.hashed_password:
                raise ValueError("Invalid email or password")

            from app.core.security import verify_password

            if not verify_password(password, user.hashed_password):
                raise ValueError("Invalid email or password")

        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()

        # Generate tokens
        tokens = await self._generate_tokens(db, user)

        return user, tokens

    async def handle_oauth_callback(
        self,
        db: AsyncSession,
        code: str,
        redirect_uri: str,
    ) -> tuple[User, dict[str, Any]]:
        """Handle OAuth callback from Auth0.

        Args:
            db: Database session
            code: Authorization code
            redirect_uri: Redirect URI

        Returns:
            Tuple of (User, tokens dict)
        """
        # Exchange code for tokens
        token_response = await self.auth0_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=redirect_uri,
        )

        # Get user info from Auth0
        userinfo = await self.auth0_service.get_userinfo(token_response["access_token"])

        # Create or update user
        user = await self.create_or_update_user_from_auth0(db, userinfo)

        # Store OAuth connection if needed
        provider = (
            userinfo.get("sub", "").split("|")[0] if "|" in userinfo.get("sub", "") else "unknown"
        )
        if provider in ["google-oauth2", "apple"]:
            await self._store_oauth_connection(
                db=db,
                user=user,
                provider=provider.replace("-oauth2", ""),
                provider_user_id=userinfo.get("sub", ""),
                access_token=token_response["access_token"],
                refresh_token=token_response.get("refresh_token"),
                expires_in=token_response.get("expires_in", 3600),
            )

        # Generate tokens
        tokens = await self._generate_tokens(db, user)

        return user, tokens

    async def create_or_update_user_from_auth0(
        self,
        db: AsyncSession,
        auth0_userinfo: dict[str, Any],
    ) -> User:
        """Create or update user from Auth0 user info.

        Args:
            db: Database session
            auth0_userinfo: Auth0 user info

        Returns:
            User instance
        """
        auth0_user_id = auth0_userinfo.get("sub", "")
        email = auth0_userinfo.get("email", "")
        name = auth0_userinfo.get("name", "")
        username = auth0_userinfo.get("nickname") or email.split("@")[0] if email else "user"

        # Determine auth method from Auth0 user ID format
        auth_method = AuthMethod.EMAIL
        if "google-oauth2" in auth0_user_id:
            auth_method = AuthMethod.GOOGLE
        elif "apple" in auth0_user_id:
            auth_method = AuthMethod.APPLE

        # Check if user exists by Auth0 ID
        result = await db.execute(select(User).where(User.auth0_user_id == auth0_user_id))
        user = result.scalar_one_or_none()

        if user:
            # Update existing user
            user.email = email
            user.auth_method = auth_method
            if name and not user.username:
                user.username = username
        else:
            # Check if user exists by email
            existing_user = await self.user_service.get_user_by_email(db, email)
            if existing_user:
                # Link Auth0 account to existing user
                existing_user.auth0_user_id = auth0_user_id
                existing_user.auth_method = auth_method
                user = existing_user
            else:
                # Create new user
                user = User(
                    email=email,
                    username=username,
                    auth0_user_id=auth0_user_id,
                    auth_method=auth_method,
                    wallet_type=WalletType.NONE,
                    feature_access_level=FeatureAccessLevel.FULL,
                    email_verified=auth0_userinfo.get("email_verified", False),
                )
                db.add(user)

        await db.commit()
        await db.refresh(user)

        return user

    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> dict[str, Any]:
        """Refresh access token.

        Args:
            db: Database session
            refresh_token: Refresh token

        Returns:
            New tokens dict

        Raises:
            ValueError: If refresh token is invalid
        """
        from app.core.security import decode_token

        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid refresh token")

        # Get user
        user = await self.user_service.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise ValueError("Invalid refresh token")

        # Generate new tokens
        tokens = await self._generate_tokens(db, user)

        return tokens

    async def logout(
        self,
        db: AsyncSession,
        user_id: int,
        token_hash: str,
    ) -> None:
        """Logout user by revoking session.

        Args:
            db: Database session
            user_id: User ID
            token_hash: Token hash to revoke
        """
        # Find and revoke session
        result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.token_hash == token_hash,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.revoked = True
            session.revoked_at = datetime.utcnow()
            await db.commit()

    async def _generate_tokens(
        self,
        db: AsyncSession,
        user: User,
    ) -> dict[str, Any]:
        """Generate access and refresh tokens for user.

        Args:
            db: Database session
            user: User instance

        Returns:
            Tokens dict
        """
        # Create token payload
        token_data = {"sub": str(user.id), "email": user.email}

        # Generate tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Hash tokens for storage
        from app.core.security import get_password_hash

        token_hash = get_password_hash(access_token)
        refresh_token_hash = get_password_hash(refresh_token)

        # Create session
        expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        session = Session(
            user_id=user.id,
            token_hash=token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def _store_oauth_connection(
        self,
        db: AsyncSession,
        user: User,
        provider: str,
        provider_user_id: str,
        access_token: str,
        refresh_token: str | None,
        expires_in: int,
    ) -> OAuthConnection:
        """Store OAuth connection.

        Args:
            db: Database session
            user: User instance
            provider: OAuth provider
            provider_user_id: Provider user ID
            access_token: Access token
            refresh_token: Refresh token
            expires_in: Token expiration in seconds

        Returns:
            OAuthConnection instance
        """
        # Check if connection already exists
        result = await db.execute(
            select(OAuthConnection).where(
                OAuthConnection.user_id == user.id,
                OAuthConnection.provider == provider,
            )
        )
        oauth_conn = result.scalar_one_or_none()

        expires_at = datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None

        if oauth_conn:
            # Update existing connection
            oauth_conn.access_token = access_token
            oauth_conn.refresh_token = refresh_token
            oauth_conn.expires_at = expires_at
        else:
            # Create new connection
            oauth_conn = OAuthConnection(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            db.add(oauth_conn)

        await db.commit()
        await db.refresh(oauth_conn)

        return oauth_conn
