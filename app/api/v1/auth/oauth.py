"""OAuth authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth.oauth import OAuthAuthorizeResponse, OAuthConnectionResponse, OAuthLinkRequest
from app.services.oauth_service import OAuthService

router = APIRouter()
oauth_service = OAuthService()


@router.get("/authorize/{provider}", response_model=OAuthAuthorizeResponse)
async def authorize_oauth(
    provider: str,
    redirect_uri: str | None = Query(None),
) -> OAuthAuthorizeResponse:
    """Initiate OAuth flow for Google or Apple.

    Args:
        provider: OAuth provider (google, apple)
        redirect_uri: Optional redirect URI

    Returns:
        Authorization URL and state token
    """
    try:
        auth_url, state = oauth_service.get_oauth_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
        )
        return OAuthAuthorizeResponse(authorization_url=auth_url, state=state)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authorization failed: {str(e)}",
        ) from e


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    redirect_uri: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Handle OAuth callback.

    Args:
        code: Authorization code
        state: State parameter
        redirect_uri: Redirect URI
        db: Database session

    Returns:
        Token response
    """
    try:
        user, tokens = await oauth_service.handle_oauth_callback(
            db=db,
            code=code,
            state=state,
            redirect_uri=redirect_uri,
        )
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}",
        ) from e


@router.post("/link", response_model=OAuthConnectionResponse)
async def link_oauth_account(
    request: OAuthLinkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OAuthConnectionResponse:
    """Link OAuth account to existing user.

    Args:
        request: OAuth link request
        current_user: Current authenticated user
        db: Database session

    Returns:
        OAuth connection response
    """
    try:
        oauth_conn = await oauth_service.link_oauth_account(
            db=db,
            user=current_user,
            code=request.code,
            redirect_uri=request.redirect_uri,
        )
        return OAuthConnectionResponse(
            id=oauth_conn.id,
            provider=oauth_conn.provider,
            provider_user_id=oauth_conn.provider_user_id,
            created_at=oauth_conn.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth linking failed: {str(e)}",
        ) from e


@router.delete("/unlink/{provider}")
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Unlink OAuth account from user.

    Args:
        provider: OAuth provider (google, apple)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    try:
        await oauth_service.unlink_oauth_account(
            db=db,
            user=current_user,
            provider=provider,
        )
        return {"message": f"OAuth account {provider} unlinked successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth unlinking failed: {str(e)}",
        ) from e
