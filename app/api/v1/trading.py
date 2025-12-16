"""Trading endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_trading_service
from app.schemas.trading import PairResponse, TradeCreate, TradeResponse
from app.services.trading_service import TradingService

router = APIRouter()


@router.post("/trades", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def open_trade(
    trade: TradeCreate,
    trading_service: TradingService = Depends(get_trading_service),
) -> TradeResponse:
    """Open a new trade."""
    try:
        result = await trading_service.open_trade(
            collateral=trade.collateral,
            leverage=trade.leverage,
            asset_type=trade.asset_type,
            direction=trade.direction,
            order_type=trade.order_type,
            at_price=trade.at_price,
            tp=trade.tp,
            sl=trade.sl,
        )
        return TradeResponse(
            transaction_hash=result["transaction_hash"],
            status=result.get("status", "success"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to open trade: {str(e)}",
        ) from e


@router.delete("/trades/{pair_id}/{index}", response_model=TradeResponse)
async def close_trade(
    pair_id: int,
    index: int,
    trading_service: TradingService = Depends(get_trading_service),
) -> TradeResponse:
    """Close an existing trade."""
    try:
        result = await trading_service.close_trade(pair_id, index)
        return TradeResponse(
            transaction_hash=result["transaction_hash"],
            pair_id=pair_id,
            trade_index=index,
            status=result.get("status", "closed"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close trade: {str(e)}",
        ) from e


@router.patch("/trades/{pair_id}/{index}/tp", response_model=TradeResponse)
async def update_take_profit(
    pair_id: int,
    index: int,
    tp_price: float,
    trading_service: TradingService = Depends(get_trading_service),
) -> TradeResponse:
    """Update take profit for a trade."""
    try:
        result = await trading_service.update_tp(pair_id, index, tp_price)
        return TradeResponse(
            transaction_hash=result.get("transaction_hash", ""),
            pair_id=pair_id,
            trade_index=index,
            status=result.get("status", "updated"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update take profit: {str(e)}",
        ) from e


@router.patch("/trades/{pair_id}/{index}/sl", response_model=TradeResponse)
async def update_stop_loss(
    pair_id: int,
    index: int,
    sl_price: float,
    trading_service: TradingService = Depends(get_trading_service),
) -> TradeResponse:
    """Update stop loss for a trade."""
    try:
        result = await trading_service.update_sl(pair_id, index, sl_price)
        return TradeResponse(
            transaction_hash=result.get("transaction_hash", ""),
            pair_id=pair_id,
            trade_index=index,
            status=result.get("status", "updated"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stop loss: {str(e)}",
        ) from e


@router.get("/trades", response_model=list[dict])
async def get_open_trades(
    trader_address: str | None = None,
    trading_service: TradingService = Depends(get_trading_service),
) -> list[dict]:
    """Get all open trades."""
    try:
        # TODO: Get trader address from authenticated user
        if not trader_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="trader_address is required",
            )
        trades = await trading_service.get_open_trades(trader_address)
        return trades
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get open trades: {str(e)}",
        ) from e


@router.get("/trades/{pair_id}/{index}/metrics", response_model=dict)
async def get_trade_metrics(
    pair_id: int,
    index: int,
    trading_service: TradingService = Depends(get_trading_service),
) -> dict:
    """Get metrics for an open trade."""
    try:
        metrics = await trading_service.get_open_trade_metrics(pair_id, index)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trade metrics: {str(e)}",
        ) from e


@router.get("/orders", response_model=list[dict])
async def get_orders(
    trader_address: str | None = None,
    trading_service: TradingService = Depends(get_trading_service),
) -> list[dict]:
    """Get all open orders."""
    try:
        if not trader_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="trader_address is required",
            )
        orders = await trading_service.get_orders(trader_address)
        return orders
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}",
        ) from e


@router.delete("/orders/{pair_id}/{index}", response_model=TradeResponse)
async def cancel_limit_order(
    pair_id: int,
    index: int,
    trading_service: TradingService = Depends(get_trading_service),
) -> TradeResponse:
    """Cancel a limit order."""
    try:
        result = await trading_service.cancel_limit_order(pair_id, index)
        return TradeResponse(
            transaction_hash=result["transaction_hash"],
            pair_id=pair_id,
            trade_index=index,
            status=result.get("status", "cancelled"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}",
        ) from e


@router.patch("/orders/{pair_id}/{index}", response_model=TradeResponse)
async def update_limit_order(
    pair_id: int,
    index: int,
    at_price: float,
    trading_service: TradingService = Depends(get_trading_service),
) -> TradeResponse:
    """Update a limit order."""
    try:
        result = await trading_service.update_limit_order(pair_id, index, at_price)
        return TradeResponse(
            transaction_hash=result["transaction_hash"],
            pair_id=pair_id,
            trade_index=index,
            status=result.get("status", "updated"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order: {str(e)}",
        ) from e


@router.get("/pairs", response_model=PairResponse)
async def get_pairs(
    trading_service: TradingService = Depends(get_trading_service),
) -> PairResponse:
    """Get all available trading pairs."""
    try:
        pairs = await trading_service.get_pairs()
        return PairResponse(pairs=pairs)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pairs: {str(e)}",
        ) from e

