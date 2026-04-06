"""CrewAI integration for agent-pay."""

from typing import Optional

try:
    from crewai.tools import BaseTool
except ImportError:
    raise ImportError("Install crewai: pip install crewai")

from ..client import AgentPay


class AgentPayCrewTool(BaseTool):
    """CrewAI tool to send crypto payments from an AI agent.

    Usage:
        from agent_pay.integrations.crewai import AgentPayCrewTool

        agent = Agent(
            role="Buyer",
            tools=[AgentPayCrewTool()],
            goal="Purchase data and pay for services"
        )
    """

    name: str = "Send Crypto Payment"
    description: str = (
        "Send a crypto payment (USDC or ETH on Base L2) to another agent or address. "
        "Input format: 'to_address amount currency memo'. "
        "Example: '0x1234...5678 0.50 USDC Payment for translation'. "
        "Fees are less than $0.001."
    )

    def __init__(self, private_key: Optional[str] = None, testnet: bool = False):
        super().__init__()
        self._pay = AgentPay(private_key=private_key, testnet=testnet)

    def _run(self, argument: str) -> str:
        parts = argument.strip().split(maxsplit=3)
        if len(parts) < 2:
            return "Error: provide at least 'address amount'. Example: '0x... 0.50 USDC'"

        to = parts[0]
        amount = float(parts[1])
        currency = parts[2] if len(parts) > 2 else "USDC"
        memo = parts[3] if len(parts) > 3 else ""

        result = self._pay.send(to=to, amount=amount, currency=currency, memo=memo)
        return f"Sent {amount} {currency} to {to}. TX: {result['explorer']}"
