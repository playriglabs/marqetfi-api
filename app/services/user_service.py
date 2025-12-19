"""User service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


class UserService:
    """User service for business logic."""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create new user."""
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()  # type: ignore

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()  # type: ignore

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> User | None:
        """Authenticate user."""
        user = await UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def get_user_by_auth0_id(
        db: AsyncSession,
        auth0_user_id: str,
    ) -> User | None:
        """Get user by Auth0 user ID."""
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.auth0_user_id == auth0_user_id))
        return result.scalar_one_or_none()  # type: ignore

    @staticmethod
    async def sync_user_from_auth0(
        db: AsyncSession,
        auth0_userinfo: dict,
    ) -> User:
        """Sync user from Auth0 user info."""

        from sqlalchemy import select

        from app.models.enums import AuthMethod

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
            existing_user = await UserService.get_user_by_email(db, email)
            if existing_user:
                # Link Auth0 account to existing user
                existing_user.auth0_user_id = auth0_user_id
                existing_user.auth_method = auth_method
                user = existing_user
            else:
                # Create new user
                from app.models.enums import FeatureAccessLevel, WalletType

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
