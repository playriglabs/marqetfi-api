"""Base classes for wallet providers."""

from abc import ABC, abstractmethod
from typing import Any

from app.services.providers.base import BaseExternalService


class BaseWalletProvider(BaseExternalService, ABC):
    """Abstract interface for wallet providers."""

    @abstractmethod
    async def create_wallet(self, network: str) -> dict[str, Any]:
        """Create a new wallet.

        Args:
            network: Network name (testnet/mainnet)

        Returns:
            Dictionary containing wallet information including:
            - wallet_id: Provider-specific wallet identifier
            - address: Ethereum wallet address
            - network: Network name
            - metadata: Additional provider-specific data
        """
        pass

    @abstractmethod
    async def get_wallet_address(self, wallet_id: str) -> str:
        """Get wallet address for a given wallet ID.

        Args:
            wallet_id: Provider-specific wallet identifier

        Returns:
            Ethereum wallet address
        """
        pass

    @abstractmethod
    async def sign_transaction(self, wallet_id: str, transaction: dict[str, Any]) -> str:
        """Sign a transaction using the wallet.

        Args:
            wallet_id: Provider-specific wallet identifier
            transaction: Transaction dictionary with fields like:
                - to: Recipient address
                - value: Amount in wei
                - data: Transaction data
                - gas: Gas limit
                - gasPrice: Gas price
                - nonce: Transaction nonce

        Returns:
            Signed transaction hash or signature
        """
        pass

    @abstractmethod
    async def sign_message(self, wallet_id: str, message: str) -> str:
        """Sign a message using the wallet.

        Args:
            wallet_id: Provider-specific wallet identifier
            message: Message to sign (will be hashed according to EIP-191)

        Returns:
            Message signature
        """
        pass

    @abstractmethod
    async def get_wallet_info(self, wallet_id: str) -> dict[str, Any]:
        """Get wallet information.

        Args:
            wallet_id: Provider-specific wallet identifier

        Returns:
            Dictionary containing wallet information:
            - wallet_id: Provider-specific wallet identifier
            - address: Ethereum wallet address
            - network: Network name
            - metadata: Additional provider-specific data
        """
        pass
