"""Trading endpoints."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db, get_trading_service
from app.models.enums import OrderStatus
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.schemas.trading import OrderCreate, OrderResponse, PairResponse, TradeCreate, TradeResponse
from app.services.trading_service import TradingService

router = APIRouter()


@router.post("/trades", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def open_trade(
    trade: TradeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    trading_service: TradingService = Depends(get_trading_service),
) -> TradeResponse:
    """Open a new trade."""
    try:
        # Update trading service with db for risk checks
        trading_service.db = db

        # Calculate available balance (simplified: use collateral as minimum available)
        # In production, this would query user's actual balance from deposits/wallet
        available_balance = Decimal(str(trade.collateral))

        result = await trading_service.open_trade(
            collateral=trade.collateral,
            leverage=trade.leverage,
            asset_type=trade.asset_type,
            direction=trade.direction,
            order_type=trade.order_type,
            at_price=trade.at_price,
            tp=trade.tp,
            sl=trade.sl,
            asset=trade.asset,
            user_id=current_user.id,
            available_balance=available_balance,
        )
        return TradeResponse(
            transaction_hash=result["transaction_hash"],
            pair_id=result.get("pair_id"),
            trade_index=result.get("trade_index"),
            status=result.get("status", "success"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order: {str(e)}",
        ) from e


@router.get("/pairs", response_model=PairResponse)
async def get_pairs(
    category: str | None = None,
    trading_service: TradingService = Depends(get_trading_service),
) -> PairResponse:
    """Get all available trading pairs.

    Args:
        category: Optional category filter (crypto, forex, indices, commodities)
    """
    try:
        pairs = await trading_service.get_pairs(category=category)
        return PairResponse(pairs=pairs)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pairs: {str(e)}",
        ) from e


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """Create a new order with advanced order type support."""
    advanced_order_types = ["stop_loss", "take_profit", "trailing_stop", "oco"]

    if order_data.order_type.value in advanced_order_types:
        if not order_data.stop_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="stop_price required for advanced orders",
            )

    if order_data.order_type.value == "trailing_stop":
        if not order_data.trailing_offset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="trailing_offset required for trailing stop orders",
            )

    if order_data.order_type.value == "oco":
        if not order_data.linked_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="linked_order_id required for OCO orders",
            )

    order_repo = OrderRepository()
    order = await order_repo.create(
        db,
        {
            "user_id": current_user.id,
            "asset": order_data.asset,
            "quote": order_data.quote,
            "side": order_data.side,
            "order_type": order_data.order_type,
            "quantity": order_data.quantity,
            "price": order_data.price,
            "leverage": order_data.leverage,
            "stop_price": order_data.stop_price,
            "trailing_offset": order_data.trailing_offset,
            "linked_order_id": order_data.linked_order_id,
            "status": OrderStatus.PENDING,
            "provider": "ostium",
        },
    )

    if order.order_type.value in advanced_order_types:
        from app.services.order_monitoring_service import OrderMonitoringService
        from app.services.price_stream_service import price_stream_service

        monitoring = OrderMonitoringService(db, price_stream_service)
        await monitoring.monitor_order(order.id)

    return OrderResponse.model_validate(order)


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a pending order."""
    order_repo = OrderRepository()
    order = await order_repo.get(db, order_id)

    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending orders",
        )

    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.utcnow()
    await db.commit()

    advanced_order_types = ["stop_loss", "take_profit", "trailing_stop", "oco"]

    if order.order_type.value in advanced_order_types:
        from app.services.order_monitoring_service import OrderMonitoringService
        from app.services.price_stream_service import price_stream_service

        monitoring = OrderMonitoringService(db, price_stream_service)
        await monitoring.stop_monitoring_order(order_id)


@router.get("/orders/list", response_model=list[OrderResponse])
async def list_user_orders(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    status_filter: OrderStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[OrderResponse]:
    """List orders for the current user."""
    order_repo = OrderRepository()

    if status_filter:
        orders = await order_repo.get_by_status(db, current_user.id, status_filter, skip, limit)
    else:
        orders = await order_repo.get_by_user(db, current_user.id, skip, limit)

    return [OrderResponse.model_validate(order) for order in orders]
