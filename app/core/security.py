"""Security utilities."""

from datetime import datetime, timedelta
from typing import Any, cast

import httpx
from jose import JWTError, jwk, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


def get_password_hash(password: str) -> str:
    """Hash a password."""
    result: str = pwd_context.hash(password)
    return result


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def get_auth0_jwks() -> dict[str, Any]:
    """Get Auth0 JWKS (JSON Web Key Set).

    Returns:
        JWKS dictionary
    """
    if not settings.AUTH0_DOMAIN:
        return {}

    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    try:
        response = httpx.get(jwks_url, timeout=5.0)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]
    except Exception:
        return {}


def verify_auth0_token(token: str) -> dict[str, Any] | None:
    """Verify Auth0 JWT token.

    Args:
        token: Auth0 JWT token

    Returns:
        Decoded token payload or None if invalid
    """
    if not settings.AUTH0_DOMAIN or not settings.AUTH0_AUDIENCE:
        return None

    try:
        # Get JWKS
        jwks = get_auth0_jwks()
        if not jwks:
            return None

        # Get unverified header to find key ID
        unverified_header = jwt.get_unverified_header(token)

        # Find the key
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            return None

        # Decode and verify token
        public_key = jwk.construct(rsa_key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.AUTH0_ALGORITHM],
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
        return cast(dict[str, Any] | None, payload if isinstance(payload, dict) else None)
    except Exception:
        return None


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify JWT token (supports both Auth0 and custom tokens).

    Args:
        token: JWT token

    Returns:
        Decoded token payload or None if invalid
    """
    # Try Auth0 token first (RS256)
    if settings.AUTH0_DOMAIN:
        auth0_payload = verify_auth0_token(token)
        if auth0_payload:
            return auth0_payload

    # Try custom token (HS256)
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
