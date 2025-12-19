"""OAuth authentication schemas."""

from pydantic import BaseModel


class OAuthAuthorizeRequest(BaseModel):
    """OAuth authorization request schema."""

    provider: str  # google, apple
    redirect_uri: str | None = None


class OAuthAuthorizeResponse(BaseModel):
    """OAuth authorization response schema."""

    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request schema."""

    code: str
    state: str
    redirect_uri: str | None = None


class OAuthLinkRequest(BaseModel):
    """OAuth link request schema."""

    provider: str  # google, apple
    code: str
    redirect_uri: str | None = None


class OAuthConnectionResponse(BaseModel):
    """OAuth connection response schema."""

    id: int
    provider: str
    provider_user_id: str
    created_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True
