"""Price schemas."""

from pydantic import BaseModel, Field


class PriceRequest(BaseModel):
    """Schema for price request."""

    asset: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    quote: str = Field(default="USD", description="Quote currency (e.g., USD)")


class PriceResponse(BaseModel):
    """Schema for price response."""

    price: float = Field(..., description="Current price")
    timestamp: int = Field(..., description="Price timestamp")
    source: str = Field(..., description="Price source")
    asset: str = Field(..., description="Asset symbol")
    quote: str = Field(..., description="Quote currency")


class PricesResponse(BaseModel):
    """Schema for multiple prices response."""

    prices: dict[str, PriceResponse] = Field(..., description="Prices by asset/quote")

