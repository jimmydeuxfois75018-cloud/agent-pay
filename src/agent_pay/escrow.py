"""Escrow for conditional agent-to-agent payments."""

import time
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class EscrowStatus(Enum):
    PENDING = "pending"
    FUNDED = "funded"
    RELEASED = "released"
    REFUNDED = "refunded"
    EXPIRED = "expired"


@dataclass
class EscrowRecord:
    id: str
    payer: str
    recipient: str
    amount: float
    currency: str
    condition: str
    status: EscrowStatus = EscrowStatus.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    tx_hash: Optional[str] = None


class Escrow:
    """Simple escrow system for agent-to-agent conditional payments.

    V1: Off-chain escrow tracked locally. Funds held in payer wallet until release.
    V2 (future): On-chain escrow smart contract on Base.
    """

    def __init__(self, wallet):
        self.wallet = wallet
        self._escrows: dict[str, EscrowRecord] = {}

    def create(
        self,
        recipient: str,
        amount: float,
        currency: str = "USDC",
        condition: str = "",
        timeout_seconds: int = 3600,
    ) -> EscrowRecord:
        """Create a new escrow. Funds stay in wallet until release()."""
        balance = self.wallet.balance(currency)
        if balance < amount:
            raise ValueError(f"Insufficient {currency} balance: {balance} < {amount}")

        escrow_id = f"escrow_{int(time.time())}_{recipient[:8]}"
        record = EscrowRecord(
            id=escrow_id,
            payer=self.wallet.address,
            recipient=recipient,
            amount=amount,
            currency=currency,
            condition=condition,
            status=EscrowStatus.FUNDED,
            expires_at=time.time() + timeout_seconds,
        )
        self._escrows[escrow_id] = record
        return record

    def release(self, escrow_id: str) -> dict:
        """Release escrow funds to the recipient."""
        record = self._escrows.get(escrow_id)
        if not record:
            raise ValueError(f"Escrow not found: {escrow_id}")
        if record.status != EscrowStatus.FUNDED:
            raise ValueError(f"Escrow not in funded state: {record.status.value}")
        if record.expires_at and time.time() > record.expires_at:
            record.status = EscrowStatus.EXPIRED
            raise ValueError("Escrow has expired")

        result = self.wallet.transfer(record.recipient, record.amount, record.currency)
        record.status = EscrowStatus.RELEASED
        record.tx_hash = result["hash"]
        return result

    def refund(self, escrow_id: str) -> None:
        """Cancel escrow and keep funds in payer wallet."""
        record = self._escrows.get(escrow_id)
        if not record:
            raise ValueError(f"Escrow not found: {escrow_id}")
        if record.status != EscrowStatus.FUNDED:
            raise ValueError(f"Cannot refund: {record.status.value}")
        record.status = EscrowStatus.REFUNDED

    def get(self, escrow_id: str) -> Optional[EscrowRecord]:
        return self._escrows.get(escrow_id)

    def list_active(self) -> list[EscrowRecord]:
        return [e for e in self._escrows.values() if e.status == EscrowStatus.FUNDED]
