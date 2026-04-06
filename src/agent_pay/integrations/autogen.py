"""AutoGen integration for agent-pay."""

from typing import Optional
import json

try:
    from autogen import ConversableAgent
except ImportError:
    raise ImportError("Install autogen: pip install pyautogen")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from client import AgentPay


def create_payment_function(private_key: Optional[str] = None, testnet: bool = True):
    """Create an AutoGen-compatible function for sending payments.

    Usage:
        from agent_pay.integrations.autogen import create_payment_function

        pay_func = create_payment_function(testnet=True)

        assistant = ConversableAgent("assistant", llm_config=llm_config)
        assistant.register_for_llm(name="send_payment", description="Send USDC payment")(pay_func)
    """
    pay = AgentPay(private_key=private_key, testnet=testnet)

    def send_payment(to: str, amount: float, currency: str = "USDC", memo: str = "") -> str:
        """Send a crypto payment to another agent or address.

        Args:
            to: Recipient wallet address (0x...)
            amount: Amount to send (e.g. 0.50 for $0.50 USDC)
            currency: USDC or ETH
            memo: Optional description

        Returns:
            JSON string with transaction hash and explorer link
        """
        try:
            result = pay.send(to=to, amount=amount, currency=currency, memo=memo)
            return json.dumps({
                "status": "sent",
                "hash": result["hash"],
                "amount": amount,
                "currency": currency,
                "to": to,
                "explorer": result["explorer"],
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    send_payment._pay = pay
    return send_payment


def create_balance_function(private_key: Optional[str] = None, testnet: bool = True):
    """Create an AutoGen-compatible function for checking balance."""
    pay = AgentPay(private_key=private_key, testnet=testnet)

    def check_balance() -> str:
        """Check the wallet balance (USDC and ETH).

        Returns:
            JSON string with balances
        """
        try:
            return json.dumps({
                "address": pay.address,
                "USDC": pay.balance("USDC"),
                "ETH": pay.balance("ETH"),
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    return check_balance
