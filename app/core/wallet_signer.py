"""Wallet signer wrapper for Ostium SDK integration."""

from typing import Any, cast

from eth_account import Account
from eth_account.messages import encode_defunct
from loguru import logger
from web3 import Web3

from app.services.wallet_providers.exceptions import WalletSigningError
from app.services.wallet_providers.factory import WalletProviderFactory


class WalletSigner:
    """Wallet signer that routes signing to wallet providers or falls back to private key."""

    def __init__(
        self,
        wallet_provider: str | None = None,
        wallet_id: str | None = None,
        private_key: str | None = None,
    ):
        """Initialize wallet signer.

        Args:
            wallet_provider: Wallet provider name (privy/dynamic) or None for direct signing
            wallet_id: Provider-specific wallet ID (required if wallet_provider is set)
            private_key: Private key for direct signing (fallback)
        """
        self.wallet_provider = wallet_provider
        self.wallet_id = wallet_id
        self.private_key = private_key
        self._provider: Any = None

    async def _get_provider(self) -> Any:
        """Get wallet provider instance."""
        if self._provider is None and self.wallet_provider:
            self._provider = await WalletProviderFactory.get_provider(self.wallet_provider)
        return self._provider

    async def sign_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
        """Sign a transaction.

        Args:
            transaction: Transaction dictionary with fields:
                - to: Recipient address
                - value: Amount in wei
                - data: Transaction data (optional)
                - gas: Gas limit
                - gasPrice: Gas price (optional)
                - maxFeePerGas: Max fee per gas (EIP-1559, optional)
                - maxPriorityFeePerGas: Max priority fee per gas (EIP-1559, optional)
                - nonce: Transaction nonce
                - chainId: Chain ID

        Returns:
            Signed transaction dictionary with 'rawTransaction' and 'hash' fields

        Raises:
            WalletSigningError: If signing fails
        """
        if self.wallet_provider and self.wallet_id:
            # Use wallet provider for signing
            try:
                provider = await self._get_provider()
                signature = await provider.sign_transaction(self.wallet_id, transaction)

                # If provider returns a signature, we need to construct the signed transaction
                # Otherwise, if it returns a raw transaction, use it directly
                if isinstance(signature, str) and signature.startswith("0x"):
                    # Check if it's a raw transaction or just a signature
                    if len(signature) > 100:  # Raw transaction is much longer
                        # It's a raw transaction
                        tx_hash = Web3.keccak(hexstr=signature)
                        return {
                            "rawTransaction": signature,
                            "hash": tx_hash.hex(),
                        }
                    else:
                        # It's a signature, need to construct signed transaction
                        # This is a simplified version - actual implementation may vary
                        signed_tx = Account.sign_transaction(transaction, signature)
                        return {
                            "rawTransaction": signed_tx.rawTransaction.hex(),
                            "hash": signed_tx.hash.hex(),
                        }
                else:
                    # Provider returned transaction hash directly
                    return {
                        "rawTransaction": signature,
                        "hash": signature,
                    }
            except Exception as e:
                logger.error(f"Wallet provider signing failed: {e}")
                if not self.private_key:
                    raise WalletSigningError(
                        f"Wallet provider signing failed and no private key fallback: {str(e)}",
                        service_name="wallet_signer",
                    ) from e
                # Fall through to private key signing

        # Fall back to direct private key signing
        if not self.private_key:
            raise WalletSigningError(
                "No wallet provider or private key configured",
                service_name="wallet_signer",
            )

        try:
            account = Account.from_key(self.private_key)
            signed_tx = account.sign_transaction(transaction)
            return {
                "rawTransaction": signed_tx.rawTransaction.hex(),
                "hash": signed_tx.hash.hex(),
            }
        except Exception as e:
            raise WalletSigningError(
                f"Private key signing failed: {str(e)}",
                service_name="wallet_signer",
            ) from e

    async def sign_message(self, message: str) -> str:
        """Sign a message.

        Args:
            message: Message to sign (will be hashed according to EIP-191)

        Returns:
            Message signature (hex string)

        Raises:
            WalletSigningError: If signing fails
        """
        if self.wallet_provider and self.wallet_id:
            # Use wallet provider for signing
            try:
                provider = await self._get_provider()
                result = await provider.sign_message(self.wallet_id, message)
                return cast(str, result)
            except Exception as e:
                logger.error(f"Wallet provider message signing failed: {e}")
                if not self.private_key:
                    raise WalletSigningError(
                        f"Wallet provider signing failed and no private key fallback: {str(e)}",
                        service_name="wallet_signer",
                    ) from e
                # Fall through to private key signing

        # Fall back to direct private key signing
        if not self.private_key:
            raise WalletSigningError(
                "No wallet provider or private key configured",
                service_name="wallet_signer",
            )

        try:
            account = Account.from_key(self.private_key)
            message_hash = encode_defunct(text=message)
            signed_message = account.sign_message(message_hash)
            return cast(str, signed_message.signature.hex())
        except Exception as e:
            raise WalletSigningError(
                f"Private key message signing failed: {str(e)}",
                service_name="wallet_signer",
            ) from e

    def get_address(self) -> str | None:
        """Get wallet address.

        Returns:
            Wallet address or None if not available
        """
        if self.private_key:
            try:
                account = Account.from_key(self.private_key)
                return cast(str, account.address)
            except Exception:
                pass
        return None

    async def get_wallet_address(self) -> str | None:
        """Get wallet address from provider.

        Returns:
            Wallet address or None if not available
        """
        if self.wallet_provider and self.wallet_id:
            try:
                provider = await self._get_provider()
                result = await provider.get_wallet_address(self.wallet_id)
                return cast(str | None, result)
            except Exception as e:
                logger.warning(f"Failed to get wallet address from provider: {e}")
                return self.get_address()
        return self.get_address()
