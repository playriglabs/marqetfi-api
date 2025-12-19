"""Wallet authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth.wallet import (
    CreateMPCWalletRequest,
    CreateMPCWalletResponse,
    WalletConnectionResponse,
    WalletConnectRequest,
    WalletConnectResponse,
    WalletNonceRequest,
    WalletNonceResponse,
)
from app.services.wallet_auth_service import WalletAuthService

router = APIRouter()
wallet_auth_service = WalletAuthService()


@router.post("/nonce", response_model=WalletNonceResponse)
async def get_wallet_nonce(
    request: WalletNonceRequest,
) -> WalletNonceResponse:
    """Get nonce for wallet signature.

    Args:
        request: Wallet nonce request

    Returns:
        Nonce and message to sign
    """
    try:
        nonce = await wallet_auth_service.generate_nonce(request.wallet_address)
        message = f"Sign this message to connect your wallet:\n\nNonce: {nonce}"
        return WalletNonceResponse(nonce=nonce, message=message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate nonce: {str(e)}",
        ) from e


@router.post("/connect", response_model=WalletConnectResponse)
async def connect_wallet(
    request: WalletConnectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WalletConnectResponse:
    """Connect external wallet to user account.

    Args:
        request: Wallet connection request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Wallet connection response
    """
    try:
        wallet_conn = await wallet_auth_service.connect_wallet(
            db=db,
            user=current_user,
            wallet_address=request.wallet_address,
            signature=request.signature,
            nonce=request.nonce,
            provider=request.provider,
        )
        return WalletConnectResponse(
            id=wallet_conn.id,
            wallet_address=wallet_conn.wallet_address,
            wallet_type=wallet_conn.wallet_type,
            provider=wallet_conn.provider,
            is_primary=wallet_conn.is_primary,
            verified=wallet_conn.verified,
            verified_at=wallet_conn.verified_at.isoformat() if wallet_conn.verified_at else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wallet connection failed: {str(e)}",
        ) from e


@router.post("/create-mpc", response_model=CreateMPCWalletResponse)
async def create_mpc_wallet(
    request: CreateMPCWalletRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CreateMPCWalletResponse:
    """Create MPC wallet for user.

    Args:
        request: Create MPC wallet request
        current_user: Current authenticated user
        db: Database session

    Returns:
        MPC wallet creation response
    """
    try:
        result = await wallet_auth_service.create_mpc_wallet(
            db=db,
            user=current_user,
            provider=request.provider,
        )
        return CreateMPCWalletResponse(**result)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MPC wallet creation failed: {str(e)}",
        ) from e


@router.post("/use-own")
async def use_own_wallet(
    request: WalletConnectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Use own wallet with limited features.

    Args:
        request: Wallet connection request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    try:
        wallet_conn = await wallet_auth_service.connect_wallet(
            db=db,
            user=current_user,
            wallet_address=request.wallet_address,
            signature=request.signature,
            nonce=request.nonce,
            provider=request.provider,
        )
        return {
            "message": "Wallet connected successfully",
            "wallet_address": wallet_conn.wallet_address,
            "note": "Limited features available. Create an MPC wallet for full access.",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wallet connection failed: {str(e)}",
        ) from e


@router.get("/connections", response_model=list[WalletConnectionResponse])
async def get_wallet_connections(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[WalletConnectionResponse]:
    """Get all wallet connections for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of wallet connections
    """
    try:
        connections = await wallet_auth_service.get_user_wallet_connections(
            db=db,
            user=current_user,
        )
        return [
            WalletConnectionResponse(
                id=conn.id,
                wallet_address=conn.wallet_address,
                wallet_type=conn.wallet_type,
                provider=conn.provider,
                provider_wallet_id=conn.provider_wallet_id,
                is_primary=conn.is_primary,
                verified=conn.verified,
                verified_at=conn.verified_at.isoformat() if conn.verified_at else None,
                last_used_at=conn.last_used_at.isoformat() if conn.last_used_at else None,
                created_at=conn.created_at.isoformat(),
            )
            for conn in connections
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wallet connections: {str(e)}",
        ) from e
