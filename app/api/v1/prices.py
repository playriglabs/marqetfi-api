"""Price endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_price_feed_service
from app.schemas.price import PriceRequest, PriceResponse, PricesResponse
from app.services.price_feed_service import PriceFeedService

router = APIRouter()


@router.get("/{asset}/{quote}", response_model=PriceResponse)
async def get_price(
    asset: str,
    quote: str = "USD",
    use_cache: bool = Query(default=True, description="Use cached price if available"),
    price_service: PriceFeedService = Depends(get_price_feed_service),
) -> PriceResponse:
    """Get current price for an asset."""
    try:
        price, timestamp, source = await price_service.get_price(
            asset.upper(), quote.upper(), use_cache=use_cache
        )
        return PriceResponse(
            price=price,
            timestamp=timestamp,
            source=source,
            asset=asset.upper(),
            quote=quote.upper(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get price: {str(e)}",
        ) from e


@router.get("", response_model=PricesResponse)
async def get_prices(
    assets: str = Query(
        ..., description="Comma-separated asset symbols (e.g., BTC,ETH)"
    ),
    quote: str = Query(default="USD", description="Quote currency"),
    use_cache: bool = Query(default=True, description="Use cached prices if available"),
    price_service: PriceFeedService = Depends(get_price_feed_service),
) -> PricesResponse:
    """Get prices for multiple assets."""
    try:
        asset_list = [a.strip().upper() for a in assets.split(",")]
        asset_quotes = [(asset, quote.upper()) for asset in asset_list]

        prices_dict = await price_service.get_prices(asset_quotes, use_cache=use_cache)

        prices = {
            key: PriceResponse(
                price=price_data[0],
                timestamp=price_data[1],
                source=price_data[2],
                asset=key.split("/")[0],
                quote=key.split("/")[1] if "/" in key else quote.upper(),
            )
            for key, price_data in prices_dict.items()
        }

        return PricesResponse(prices=prices)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prices: {str(e)}",
        ) from e


@router.get("/pairs", response_model=list[dict])
async def get_pairs(
    price_service: PriceFeedService = Depends(get_price_feed_service),
) -> list[dict]:
    """Get all available trading pairs."""
    try:
        pairs = await price_service.get_pairs()
        return pairs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pairs: {str(e)}",
        ) from e

