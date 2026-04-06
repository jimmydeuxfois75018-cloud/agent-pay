"""LangChain integration for agent-pay."""

from typing import Optional, Type
from pydantic import BaseModel, Field

try:
    from langchain_core.tools import BaseTool
except ImportError:
    raise ImportError("Install langchain-core: pip install langchain-core")

from ..client import AgentPay


class PaymentInput(BaseModel):
    to: str = Field(description="Recipient wallet address (0x...)")
    amount: float = Field(description="Amount to send (e.g. 0.50 for $0.50 USDC)")
    currency: str = Field(default="USDC", description="Currency: USDC or ETH")
    memo: str = Field(default="", description="Optional payment description")


class AgentPayTool(BaseTool):
    """LangChain tool to send crypto payments from an AI agent.

    Usage:
        from agent_pay.integrations.langchain import AgentPayTool

        tools = [AgentPayTool()]
        agent = initialize_agent(tools=tools, llm=llm)
        agent.run("Pay 0.50 USDC to 0x...")
    """

    name: str = "agent_pay_send"
    description: str = (
        "Send a crypto payment (USDC or ETH on Base L2) to another AI agent or address. "
        "Use this when you need to pay for a service, buy data, hire another agent, "
        "or transfer funds. Fees are less than $0.001."
    )
    args_schema: Type[BaseModel] = PaymentInput
    pay_client: Optional[AgentPay] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, private_key: Optional[str] = None, testnet: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pay_client = AgentPay(private_key=private_key, testnet=testnet)

    def _run(self, to: str, amount: float, currency: str = "USDC", memo: str = "") -> str:
        result = self.pay_client.send(to=to, amount=amount, currency=currency, memo=memo)
        return (
            f"Payment sent! {amount} {currency} to {to}. "
            f"TX: {result['explorer']}"
        )

    async def _arun(self, to: str, amount: float, currency: str = "USDC", memo: str = "") -> str:
        return self._run(to, amount, currency, memo)


class BalanceTool(BaseTool):
    """LangChain tool to check AI agent wallet balance."""

    name: str = "agent_pay_balance"
    description: str = "Check the crypto wallet balance (USDC and ETH) of this AI agent."
    pay_client: Optional[AgentPay] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, private_key: Optional[str] = None, testnet: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pay_client = AgentPay(private_key=private_key, testnet=testnet)

    def _run(self) -> str:
        usdc = self.pay_client.balance("USDC")
        eth = self.pay_client.balance("ETH")
        return f"Wallet {self.pay_client.address}: {usdc:.2f} USDC, {eth:.6f} ETH"

    async def _arun(self) -> str:
        return self._run()
