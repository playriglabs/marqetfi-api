"""Price endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_price_feed_service
from app.schemas.price import PriceResponse, PricesResponse
from app.services.price_feed_service import PriceFeedService

router = APIRouter()


@router.get("/{pair}", response_model=PriceResponse)
async def get_price(
    pair: str,
    use_cache: bool = Query(default=True, description="Use cached price if available"),
    price_service: PriceFeedService = Depends(get_price_feed_service),
) -> PriceResponse:
    """Get current price for a trading pair.

    Args:
        pair: Trading pair in combined format (e.g., BTCUSDT, EURUSD, ETHUSDT)
    """
    try:
        price, timestamp, source, asset, quote = await price_service.get_price_by_pair(
            pair.upper(), use_cache=use_cache
        )
        return PriceResponse(
            price=price,
            timestamp=timestamp,
            source=source,
            asset=asset,
            quote=quote,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get price: {str(e)}",
        ) from e


@router.get("", response_model=PricesResponse)
async def get_prices(
    pairs: str = Query(
        ..., description="Comma-separated trading pairs (e.g., BTCUSDT,EURUSD,ETHUSDT)"
    ),
    use_cache: bool = Query(default=True, description="Use cached prices if available"),
    price_service: PriceFeedService = Depends(get_price_feed_service),
) -> PricesResponse:
    """Get prices for multiple trading pairs.

    Args:
        pairs: Comma-separated trading pairs in combined format
    """
    try:
        pair_list = [p.strip().upper() for p in pairs.split(",")]
        prices_dict = await price_service.get_prices_by_pairs(pair_list, use_cache=use_cache)

        prices = {
            pair: PriceResponse(
                price=price_data[0],
                timestamp=price_data[1],
                source=price_data[2],
                asset=price_data[3],
                quote=price_data[4],
            )
            for pair, price_data in prices_dict.items()
        }

        return PricesResponse(prices=prices)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prices: {str(e)}",
        ) from e


@router.get("/pairs", response_model=list[dict])
async def get_pairs(
    category: str | None = None,
    price_service: PriceFeedService = Depends(get_price_feed_service),
) -> list[dict]:
    """Get all available trading pairs.

    Args:
        category: Optional category filter (crypto, forex, indices, commodities)
    """
    try:
        pairs = await price_service.get_pairs(category=category)
        return pairs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pairs: {str(e)}",
        ) from e
