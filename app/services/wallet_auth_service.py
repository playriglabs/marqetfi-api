"""Wallet authentication service for Web3 wallet connections."""

import secrets
from datetime import datetime
from typing import Any, cast

from eth_account.messages import encode_defunct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from app.config import get_settings
from app.core.cache import cache_manager
from app.models.auth import WalletConnection
from app.models.enums import WalletType
from app.models.user import User
from app.services.user_service import UserService

settings = get_settings()
w3 = Web3()


class WalletAuthService:
    """Service for Web3 wallet authentication."""

    def __init__(self) -> None:
        """Initialize wallet auth service."""
        self.user_service = UserService()

    async def generate_nonce(
        self,
        wallet_address: str,
    ) -> str:
        """Generate nonce for wallet signature.

        Args:
            wallet_address: Wallet address

        Returns:
            Nonce string
        """
        # Generate random nonce
        nonce = secrets.token_urlsafe(32)

        # Store nonce in cache with expiration (5 minutes)
        cache_key = f"wallet_nonce:{wallet_address.lower()}"
        await cache_manager.set(cache_key, nonce, expire=300)

        return nonce

    async def verify_wallet_signature(
        self,
        wallet_address: str,
        signature: str,
        message: str,
    ) -> bool:
        """Verify wallet signature.

        Args:
            wallet_address: Wallet address
            signature: Signature hex string
            message: Original message

        Returns:
            True if signature is valid
        """
        try:
            # Encode message
            message_encoded = encode_defunct(text=message)

            # Recover address from signature
            recovered_address = w3.eth.account.recover_message(message_encoded, signature=signature)

            # Compare addresses (case-insensitive)
            return cast(bool, recovered_address.lower() == wallet_address.lower())
        except Exception:
            return False

    async def connect_wallet(
        self,
        db: AsyncSession,
        user: User,
        wallet_address: str,
        signature: str,
        nonce: str,
        provider: str | None = None,
    ) -> WalletConnection:
        """Connect external wallet to user account.

        Args:
            db: Database session
            user: User instance
            wallet_address: Wallet address
            signature: Signature of the nonce
            nonce: Nonce that was signed
            provider: Wallet provider (metamask, walletconnect, etc.)

        Returns:
            WalletConnection instance

        Raises:
            ValueError: If signature verification fails
        """
        # Normalize wallet address
        wallet_address = w3.to_checksum_address(wallet_address)

        # Verify nonce from cache
        cache_key = f"wallet_nonce:{wallet_address.lower()}"
        stored_nonce = await cache_manager.get(cache_key)
        if not stored_nonce or stored_nonce != nonce:
            raise ValueError("Invalid or expired nonce")

        # Create message
        message = f"Sign this message to connect your wallet:\n\nNonce: {nonce}"

        # Verify signature
        is_valid = await self.verify_wallet_signature(
            wallet_address=wallet_address,
            signature=signature,
            message=message,
        )

        if not is_valid:
            raise ValueError("Invalid signature")

        # Check if wallet connection already exists
        result = await db.execute(
            select(WalletConnection).where(
                WalletConnection.wallet_address == wallet_address,
            )
        )
        existing_conn = result.scalar_one_or_none()

        if existing_conn:
            # Update existing connection
            if existing_conn.user_id != user.id:
                raise ValueError("Wallet is already connected to another account")
            existing_conn.verified = True
            existing_conn.verified_at = datetime.utcnow()
            existing_conn.last_used_at = datetime.utcnow()
            if provider:
                existing_conn.provider = provider
            wallet_conn = existing_conn
        else:
            # Check if user has any primary wallet
            result = await db.execute(
                select(WalletConnection).where(
                    WalletConnection.user_id == user.id,
                    WalletConnection.is_primary == True,  # noqa: E712
                )
            )
            has_primary = result.scalar_one_or_none() is not None

            # Create new connection
            wallet_conn = WalletConnection(
                user_id=user.id,
                wallet_address=wallet_address,
                wallet_type=WalletType.EXTERNAL,
                provider=provider,
                is_primary=not has_primary,  # First wallet is primary
                verified=True,
                verified_at=datetime.utcnow(),
                last_used_at=datetime.utcnow(),
            )
            db.add(wallet_conn)

        # Update user's primary wallet address if this is primary
        if wallet_conn.is_primary:
            user.wallet_address = wallet_address
            user.wallet_type = WalletType.EXTERNAL

        # Delete nonce from cache
        await cache_manager.delete(cache_key)

        await db.commit()
        await db.refresh(wallet_conn)

        return wallet_conn

    async def create_mpc_wallet(
        self,
        db: AsyncSession,
        user: User,
        provider: str = "privy",
        network: str = "mainnet",
    ) -> dict[str, Any]:
        """Create MPC wallet for user via Privy.

        According to Privy docs: https://docs.privy.io/basics/python/quickstart
        Wallets are created server-side using the Privy SDK with app credentials.

        Args:
            db: Database session
            user: User instance
            provider: Wallet provider (privy, dynamic) - defaults to privy
            network: Network name (testnet/mainnet) - defaults to mainnet

        Returns:
            Wallet creation response with wallet_id, address, and database ID

        Raises:
            ValueError: If provider is not supported or wallet creation fails
        """
        from app.models.wallet import Wallet
        from app.repositories.wallet_repository import WalletRepository
        from app.services.wallet_providers.factory import WalletProviderFactory

        # Validate provider
        if provider not in ["privy", "dynamic"]:
            raise ValueError(f"Unsupported provider: {provider}. Supported: privy, dynamic")

        try:
            # Get wallet provider
            wallet_provider = await WalletProviderFactory.get_provider(provider)
            await wallet_provider.initialize()

            # Create wallet via Privy SDK
            # According to Privy docs: https://docs.privy.io/basics/python/quickstart
            # Wallets are created server-side using client.wallets.create(chain_type="ethereum")
            # No owner parameter needed - uses app credentials for server-side wallets
            wallet_data = await wallet_provider.create_wallet(network)

            # Extract wallet information
            provider_wallet_id = wallet_data.get("wallet_id") or wallet_data.get("id")
            wallet_address = wallet_data.get("address") or wallet_data.get("wallet_address")

            if not provider_wallet_id or not wallet_address:
                raise ValueError("Invalid wallet data from provider: missing wallet_id or address")

            # Normalize wallet address
            wallet_address = w3.to_checksum_address(wallet_address)

            # Check if wallet already exists in database
            wallet_repo = WalletRepository()
            result = await db.execute(
                select(Wallet).where(
                    Wallet.provider_type == provider,
                    Wallet.provider_wallet_id == str(provider_wallet_id),
                )
            )
            existing_wallet = result.scalar_one_or_none()

            if existing_wallet:
                # Wallet already exists, check if it belongs to this user
                if existing_wallet.user_id != user.id:
                    raise ValueError("Wallet already exists and belongs to another user")
                wallet = existing_wallet
            else:
                # Check if user has any primary wallet
                result = await db.execute(
                    select(Wallet).where(
                        Wallet.user_id == user.id,
                        Wallet.is_primary == True,  # noqa: E712
                    )
                )
                has_primary = result.scalar_one_or_none() is not None

                # Create new wallet record in database
                wallet = await wallet_repo.create(
                    db,
                    {
                        "user_id": user.id,
                        "provider_type": provider,
                        "provider_wallet_id": str(provider_wallet_id),
                        "wallet_address": wallet_address,
                        "network": network,
                        "is_active": True,
                        "is_primary": not has_primary,  # First wallet is primary
                        "wallet_metadata": wallet_data.get("metadata", {}),
                    },
                )

            # Link wallet to user account via WalletConnection
            wallet_connection = await self.link_wallet_to_user(
                db=db,
                user=user,
                wallet_address=wallet_address,
                wallet_type=WalletType.MPC,
                provider=provider,
                provider_wallet_id=str(provider_wallet_id),
            )

            # Update user's MPC wallet reference
            if not user.mpc_wallet_id:
                user.mpc_wallet_id = wallet.id

            # Update user's wallet type and address if this is primary
            if wallet.is_primary:
                user.wallet_type = WalletType.MPC
                user.wallet_address = wallet_address

            await db.commit()
            await db.refresh(wallet)
            await db.refresh(wallet_connection)

            return {
                "wallet_id": wallet.id,
                "provider_wallet_id": provider_wallet_id,
                "address": wallet_address,
                "network": network,
                "provider": provider,
                "wallet_connection_id": wallet_connection.id,
                "is_primary": wallet.is_primary,
            }
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Failed to create MPC wallet: {str(e)}") from e

    async def link_wallet_to_user(
        self,
        db: AsyncSession,
        user: User,
        wallet_address: str,
        wallet_type: WalletType,
        provider: str | None = None,
        provider_wallet_id: str | None = None,
    ) -> WalletConnection:
        """Link wallet to user account (for MPC wallets).

        Args:
            db: Database session
            user: User instance
            wallet_address: Wallet address
            wallet_type: Wallet type (MPC or EXTERNAL)
            provider: Wallet provider
            provider_wallet_id: Provider-specific wallet ID

        Returns:
            WalletConnection instance
        """
        # Normalize wallet address
        wallet_address = w3.to_checksum_address(wallet_address)

        # Check if connection already exists
        result = await db.execute(
            select(WalletConnection).where(
                WalletConnection.user_id == user.id,
                WalletConnection.wallet_address == wallet_address,
            )
        )
        existing_conn = result.scalar_one_or_none()

        if existing_conn:
            # Update existing connection
            existing_conn.wallet_type = wallet_type
            existing_conn.provider = provider
            existing_conn.provider_wallet_id = provider_wallet_id
            existing_conn.verified = True
            existing_conn.verified_at = datetime.utcnow()
            wallet_conn = existing_conn
        else:
            # Check if user has any primary wallet
            result = await db.execute(
                select(WalletConnection).where(
                    WalletConnection.user_id == user.id,
                    WalletConnection.is_primary == True,  # noqa: E712
                )
            )
            has_primary = result.scalar_one_or_none() is not None

            # Create new connection
            wallet_conn = WalletConnection(
                user_id=user.id,
                wallet_address=wallet_address,
                wallet_type=wallet_type,
                provider=provider,
                provider_wallet_id=provider_wallet_id,
                is_primary=not has_primary,
                verified=True,
                verified_at=datetime.utcnow(),
            )
            db.add(wallet_conn)

        # Update user's primary wallet address if this is primary
        if wallet_conn.is_primary:
            user.wallet_address = wallet_address
            user.wallet_type = wallet_type

        await db.commit()
        await db.refresh(wallet_conn)

        return wallet_conn

    async def get_user_wallet_connections(
        self,
        db: AsyncSession,
        user: User,
    ) -> list[WalletConnection]:
        """Get all wallet connections for user.

        Args:
            db: Database session
            user: User instance

        Returns:
            List of wallet connections
        """
        result = await db.execute(
            select(WalletConnection).where(WalletConnection.user_id == user.id)
        )
        return list(result.scalars().all())
