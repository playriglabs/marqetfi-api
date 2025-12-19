"""Deposit service for managing deposits and automatic token swaps."""

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deposit import Deposit, TokenSwap
from app.repositories.deposit_repository import DepositRepository, TokenSwapRepository
from app.services.providers.factory import ProviderFactory


class DepositService:
    """Service for managing deposits and automatic token swaps."""

    def __init__(self, db: AsyncSession):
        """Initialize deposit service.

        Args:
            db: Database session
        """
        self.db = db
        self.deposit_repo = DepositRepository()
        self.swap_repo = TokenSwapRepository()

    async def process_deposit(
        self,
        user_id: int,
        token_address: str,
        token_symbol: str,
        chain: str,
        amount: Decimal,
        provider: str,
        transaction_hash: str | None = None,
    ) -> Deposit:
        """Process a deposit and trigger automatic swap if needed.

        Args:
            user_id: User ID
            token_address: Token contract address
            token_symbol: Token symbol (USDC, USDT, etc.)
            chain: Chain identifier (arbitrum, ethereum, etc.)
            amount: Deposit amount
            provider: Provider name (ostium, lighter)
            transaction_hash: Optional transaction hash

        Returns:
            Created deposit record
        """
        # Create deposit record
        deposit = await self.deposit_repo.create(
            self.db,
            {
                "user_id": user_id,
                "token_address": token_address,
                "token_symbol": token_symbol,
                "chain": chain,
                "amount": amount,
                "status": "pending",
                "provider": provider,
                "transaction_hash": transaction_hash,
            },
        )

        # Check if swap is needed
        swap_needed = await self.check_swap_needed(token_symbol, chain, provider)

        if swap_needed:
            # Mark as processing and trigger swap
            await self.deposit_repo.update(
                self.db,
                deposit,
                {"status": "processing"},
            )
            # Execute automatic swap (async, don't wait)
            # In production, this might be a background task
            try:
                await self.execute_automatic_swap(deposit, provider)
            except Exception:
                # Log error and mark deposit as failed
                await self.deposit_repo.update(
                    self.db,
                    deposit,
                    {"status": "failed"},
                )
                raise
        else:
            # No swap needed, mark as completed
            await self.deposit_repo.update(
                self.db,
                deposit,
                {"status": "completed"},
            )

        return deposit

    async def check_swap_needed(
        self, deposit_token: str, deposit_chain: str, provider: str
    ) -> bool:
        """Check if a swap is needed based on provider requirements.

        Args:
            deposit_token: Token symbol of the deposit
            deposit_chain: Chain of the deposit
            provider: Provider name (ostium, lighter)

        Returns:
            True if swap is needed, False otherwise
        """
        # Get provider-specific config
        from app.config import get_settings
        from app.services.providers.factory import ProviderFactory

        try:
            if provider == "ostium":
                config = await ProviderFactory._get_provider_config("ostium")
                required_token = getattr(config, "required_token", "USDC")
                required_chain = getattr(config, "required_chain", "arbitrum")
            elif provider == "lighter":
                config = await ProviderFactory._get_provider_config("lighter")
                required_token = getattr(config, "required_token", "USDC")
                required_chain = getattr(config, "required_chain", "ethereum")
            else:
                # Unknown provider, assume no swap needed
                return False
        except Exception:
            # If config loading fails, use defaults from settings
            settings = get_settings()
            if provider == "ostium":
                required_token = getattr(settings, "ostium_required_token", "USDC")
                required_chain = getattr(settings, "ostium_required_chain", "arbitrum")
            elif provider == "lighter":
                required_token = getattr(settings, "lighter_required_token", "USDC")
                required_chain = getattr(settings, "lighter_required_chain", "ethereum")
            else:
                return False

        # Check if token or chain differs
        token_needs_swap = deposit_token.upper() != required_token.upper()
        chain_needs_swap = deposit_chain.lower() != required_chain.lower()

        return token_needs_swap or chain_needs_swap

    async def execute_automatic_swap(self, deposit: Deposit, provider: str) -> TokenSwap:
        """Execute automatic swap for a deposit.

        Args:
            deposit: Deposit record
            provider: Provider name (ostium, lighter)

        Returns:
            Created token swap record
        """
        # Get provider requirements
        from app.config import get_settings
        from app.services.providers.factory import ProviderFactory

        try:
            if provider == "ostium":
                config = await ProviderFactory._get_provider_config("ostium")
                required_token = getattr(config, "required_token", "USDC")
                required_chain = getattr(config, "required_chain", "arbitrum")
                required_token_address = getattr(config, "required_token_address", "")
            elif provider == "lighter":
                config = await ProviderFactory._get_provider_config("lighter")
                required_token = getattr(config, "required_token", "USDC")
                required_chain = getattr(config, "required_chain", "ethereum")
                required_token_address = getattr(config, "required_token_address", "")
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception:
            # If config loading fails, use defaults from settings
            settings = get_settings()
            if provider == "ostium":
                required_token = getattr(settings, "ostium_required_token", "USDC")
                required_chain = getattr(settings, "ostium_required_chain", "arbitrum")
                required_token_address = getattr(settings, "ostium_required_token_address", "")
            elif provider == "lighter":
                required_token = getattr(settings, "lighter_required_token", "USDC")
                required_chain = getattr(settings, "lighter_required_chain", "ethereum")
                required_token_address = getattr(settings, "lighter_required_token_address", "")
            else:
                raise ValueError(f"Unknown provider: {provider}") from None

        # Get swap provider (default to LI-FI)
        # Try to get from database config first, then env
        from app.services.configuration_service import ConfigurationService

        config_service = ConfigurationService(self.db)
        swap_provider_name = await config_service.get_config_with_fallback(
            "SWAP_PROVIDER", default="lifi"
        )
        swap_provider = await ProviderFactory.get_swap_provider(swap_provider_name)

        # Get swap quote
        quote = await swap_provider.get_swap_quote(
            from_token=deposit.token_address,
            to_token=required_token_address or required_token,
            from_chain=deposit.chain,
            to_chain=required_chain,
            amount=str(deposit.amount),
        )

        # Create swap record
        swap = await self.swap_repo.create(
            self.db,
            {
                "deposit_id": deposit.id,
                "from_token": deposit.token_address,
                "to_token": required_token_address or required_token,
                "from_chain": deposit.chain,
                "to_chain": required_chain,
                "amount": deposit.amount,
                "swap_provider": swap_provider_name,
                "swap_status": "pending",
                "estimated_output": Decimal(quote.get("estimated_amount", "0")),
            },
        )

        # Execute swap (this would typically require wallet signing)
        # For now, we'll store the quote and mark as pending
        # In production, this might require user approval or MPC wallet signing
        try:
            # Get user's wallet address (simplified - in production, get from user's wallet)
            # For now, we'll need the wallet address passed or retrieved
            # swap_result = await swap_provider.execute_swap(quote, wallet_address)

            # Update swap with transaction hash when available
            # await self.swap_repo.update(
            #     self.db,
            #     swap,
            #     {
            #         "swap_transaction_hash": swap_result.get("transaction_hash"),
            #         "swap_status": "processing",
            #     },
            # )

            # For now, mark as pending (requires manual execution or wallet integration)
            await self.swap_repo.update(
                self.db,
                swap,
                {"swap_status": "pending"},
            )

        except Exception as e:
            # Mark swap as failed
            await self.swap_repo.update(
                self.db,
                swap,
                {
                    "swap_status": "failed",
                    "error_message": str(e),
                },
            )
            raise

        return swap

    async def get_deposit(self, deposit_id: int) -> Deposit | None:
        """Get deposit by ID.

        Args:
            deposit_id: Deposit ID

        Returns:
            Deposit record or None
        """
        return await self.deposit_repo.get(self.db, deposit_id)

    async def list_deposits(
        self,
        user_id: int | None = None,
        status: str | None = None,
        provider: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Deposit]:
        """List deposits with optional filters.

        Args:
            user_id: Optional user ID filter
            status: Optional status filter
            provider: Optional provider filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of deposit records
        """
        if user_id:
            return await self.deposit_repo.get_by_user(self.db, user_id, skip, limit)
        elif status:
            return await self.deposit_repo.get_by_status(self.db, status, skip, limit)
        elif provider:
            return await self.deposit_repo.get_by_provider(self.db, provider, skip, limit)
        else:
            return await self.deposit_repo.get_all(self.db, skip, limit)

    async def get_swap_status(self, deposit_id: int) -> dict[str, Any]:
        """Get swap status for a deposit.

        Args:
            deposit_id: Deposit ID

        Returns:
            Dictionary containing swap status information
        """
        deposit = await self.get_deposit(deposit_id)
        if not deposit:
            raise ValueError(f"Deposit not found: {deposit_id}")

        swaps = await self.swap_repo.get_by_deposit(self.db, deposit_id)

        if not swaps:
            return {
                "deposit_id": deposit_id,
                "swap_needed": False,
                "swaps": [],
            }

        # Get latest swap status
        latest_swap = swaps[0]
        swap_status = latest_swap.swap_status

        # If swap is processing, check with swap provider
        if swap_status in ["pending", "processing"] and latest_swap.swap_transaction_hash:
            from app.services.configuration_service import ConfigurationService

            config_service = ConfigurationService(self.db)
            swap_provider_name = await config_service.get_config_with_fallback(
                "SWAP_PROVIDER", default="lifi"
            )
            swap_provider = await ProviderFactory.get_swap_provider(swap_provider_name)

            try:
                status_data = await swap_provider.get_swap_status(latest_swap.swap_transaction_hash)
                # Update swap status if changed
                if status_data.get("status") != swap_status:
                    await self.swap_repo.update(
                        self.db,
                        latest_swap,
                        {
                            "swap_status": status_data.get("status", swap_status),
                            "actual_output": (
                                Decimal(status_data.get("to_amount", "0"))
                                if status_data.get("to_amount")
                                else None
                            ),
                            "completed_at": (
                                latest_swap.updated_at
                                if status_data.get("status") == "completed"
                                else None
                            ),
                        },
                    )
                    # Update deposit status if swap completed
                    if status_data.get("status") == "completed":
                        await self.deposit_repo.update(
                            self.db,
                            deposit,
                            {"status": "completed"},
                        )
            except Exception:
                # If status check fails, return current status
                pass

        return {
            "deposit_id": deposit_id,
            "swap_needed": True,
            "swaps": [
                {
                    "id": swap.id,
                    "status": swap.swap_status,
                    "from_token": swap.from_token,
                    "to_token": swap.to_token,
                    "from_chain": swap.from_chain,
                    "to_chain": swap.to_chain,
                    "amount": str(swap.amount),
                    "estimated_output": (
                        str(swap.estimated_output) if swap.estimated_output else None
                    ),
                    "actual_output": str(swap.actual_output) if swap.actual_output else None,
                    "transaction_hash": swap.swap_transaction_hash,
                    "error": swap.error_message,
                }
                for swap in swaps
            ],
        }
