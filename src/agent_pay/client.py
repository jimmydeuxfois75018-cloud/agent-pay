"""Main client — the 3-line interface."""

from typing import Optional
from .config import AgentPayConfig
from .wallet import AgentWallet
from .escrow import Escrow


class AgentPay:
    """The payment protocol for AI agents.

    Usage:
        pay = AgentPay()
        tx = pay.send("0xRecipient", amount=0.50, currency="USDC")
    """

    def __init__(
        self,
        private_key: Optional[str] = None,
        testnet: bool = False,
        spending_limit_usd: float = 100.0,
    ):
        self.config = AgentPayConfig(
            private_key=private_key,
            testnet=testnet,
            spending_limit_usd=spending_limit_usd,
        )
        self.wallet = AgentWallet(private_key=private_key, config=self.config)
        self.escrow = Escrow(self.wallet)
        self.address = self.wallet.address
        self._daily_spent = 0.0

    def send(self, to: str, amount: float, currency: str = "USDC", memo: str = "") -> dict:
        """Send a payment to another agent or address.

        Args:
            to: Recipient wallet address (0x...)
            amount: Amount to send (in human-readable units, e.g. 0.50 for $0.50 USDC)
            currency: "USDC" or "ETH"
            memo: Optional description of the payment

        Returns:
            dict with tx hash, status, and explorer link
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.config.spending_limit_usd:
            raise ValueError(
                f"Amount ${amount} exceeds daily spending limit ${self.config.spending_limit_usd}. "
                f"Set spending_limit_usd higher if needed."
            )

        result = self.wallet.transfer(to, amount, currency)
        result["memo"] = memo
        result["from"] = self.address
        result["to"] = to
        result["amount"] = amount
        result["currency"] = currency
        self._daily_spent += amount
        return result

    def balance(self, currency: str = "USDC") -> float:
        """Check wallet balance."""
        return self.wallet.balance(currency)

    def receive_address(self) -> str:
        """Get the address to receive payments."""
        return self.address

    def export_key(self) -> str:
        """Export the private key (store securely!)."""
        return self.wallet.private_key
