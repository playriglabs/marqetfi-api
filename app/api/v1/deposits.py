"""Deposit endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.deposit import (
    DepositCreate,
    DepositListResponse,
    DepositResponse,
    SwapStatusResponse,
)
from app.services.deposit_service import DepositService

router = APIRouter()


def get_deposit_service(db: AsyncSession = Depends(get_db)) -> DepositService:
    """Get deposit service instance."""
    return DepositService(db)


@router.post("/deposits", response_model=DepositResponse, status_code=http_status.HTTP_201_CREATED)
async def create_deposit(
    deposit: DepositCreate,
    current_user: User = Depends(get_current_active_user),
    deposit_service: DepositService = Depends(get_deposit_service),
) -> DepositResponse:
    """Create a new deposit.

    Args:
        deposit: Deposit creation data
        current_user: Current authenticated user
        deposit_service: Deposit service instance

    Returns:
        Created deposit record
    """
    try:
        created_deposit = await deposit_service.process_deposit(
            user_id=current_user.id,
            token_address=deposit.token_address,
            token_symbol=deposit.token_symbol,
            chain=deposit.chain,
            amount=deposit.amount,
            provider=deposit.provider,
            transaction_hash=deposit.transaction_hash,
        )

        return DepositResponse(
            id=created_deposit.id,
            user_id=created_deposit.user_id,
            token_address=created_deposit.token_address,
            token_symbol=created_deposit.token_symbol,
            chain=created_deposit.chain,
            amount=str(created_deposit.amount),
            status=created_deposit.status,
            provider=created_deposit.provider,
            transaction_hash=created_deposit.transaction_hash,
            created_at=created_deposit.created_at,
            updated_at=created_deposit.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deposit: {str(e)}",
        ) from e


@router.get("/deposits", response_model=DepositListResponse)
async def list_deposits(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=100, description="Maximum number of records"),
    status: str | None = Query(default=None, description="Filter by status"),
    provider: str | None = Query(default=None, description="Filter by provider"),
    current_user: User = Depends(get_current_active_user),
    deposit_service: DepositService = Depends(get_deposit_service),
) -> DepositListResponse:
    """List deposits for the current user.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        status: Optional status filter
        provider: Optional provider filter
        current_user: Current authenticated user
        deposit_service: Deposit service instance

    Returns:
        List of deposit records
    """
    try:
        deposits = await deposit_service.list_deposits(
            user_id=current_user.id,
            status=status,
            provider=provider,
            skip=skip,
            limit=limit,
        )

        return DepositListResponse(
            deposits=[
                DepositResponse(
                    id=d.id,
                    user_id=d.user_id,
                    token_address=d.token_address,
                    token_symbol=d.token_symbol,
                    chain=d.chain,
                    amount=str(d.amount),
                    status=d.status,
                    provider=d.provider,
                    transaction_hash=d.transaction_hash,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
                for d in deposits
            ],
            total=len(deposits),
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list deposits: {str(e)}",
        ) from e


@router.get("/deposits/{deposit_id}", response_model=DepositResponse)
async def get_deposit(
    deposit_id: int,
    current_user: User = Depends(get_current_active_user),
    deposit_service: DepositService = Depends(get_deposit_service),
) -> DepositResponse:
    """Get deposit details by ID.

    Args:
        deposit_id: Deposit ID
        current_user: Current authenticated user
        deposit_service: Deposit service instance

    Returns:
        Deposit record
    """
    try:
        deposit = await deposit_service.get_deposit(deposit_id)

        if not deposit:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Deposit not found: {deposit_id}",
            )

        # Verify deposit belongs to current user
        if deposit.user_id != current_user.id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Access denied to this deposit",
            )

        return DepositResponse(
            id=deposit.id,
            user_id=deposit.user_id,
            token_address=deposit.token_address,
            token_symbol=deposit.token_symbol,
            chain=deposit.chain,
            amount=str(deposit.amount),
            status=deposit.status,
            provider=deposit.provider,
            transaction_hash=deposit.transaction_hash,
            created_at=deposit.created_at,
            updated_at=deposit.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deposit: {str(e)}",
        ) from e


@router.get("/deposits/{deposit_id}/swap-status", response_model=SwapStatusResponse)
async def get_swap_status(
    deposit_id: int,
    current_user: User = Depends(get_current_active_user),
    deposit_service: DepositService = Depends(get_deposit_service),
) -> SwapStatusResponse:
    """Get swap status for a deposit.

    Args:
        deposit_id: Deposit ID
        current_user: Current authenticated user
        deposit_service: Deposit service instance

    Returns:
        Swap status information
    """
    try:
        deposit = await deposit_service.get_deposit(deposit_id)

        if not deposit:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Deposit not found: {deposit_id}",
            )

        # Verify deposit belongs to current user
        if deposit.user_id != current_user.id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Access denied to this deposit",
            )

        swap_status = await deposit_service.get_swap_status(deposit_id)

        return SwapStatusResponse(**swap_status)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get swap status: {str(e)}",
        ) from e
