"""Chain and contract configuration."""

from dataclasses import dataclass, field
from typing import Optional


# Base L2 USDC contract
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

# Base chain IDs
BASE_MAINNET = 8453
BASE_SEPOLIA = 84532

# ERC-20 ABI (minimal for transfers)
ERC20_ABI = [
    {
        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]


@dataclass
class ChainConfig:
    chain_id: int = BASE_MAINNET
    rpc_url: str = "https://mainnet.base.org"
    usdc_address: str = USDC_BASE
    explorer_url: str = "https://basescan.org"
    name: str = "Base"


@dataclass
class AgentPayConfig:
    chain: ChainConfig = field(default_factory=ChainConfig)
    private_key: Optional[str] = None
    spending_limit_usd: float = 100.0  # Max spend per day
    auto_approve_below: float = 1.0  # Auto-approve payments below this USD amount
    testnet: bool = False

    def __post_init__(self):
        if self.testnet:
            self.chain = ChainConfig(
                chain_id=BASE_SEPOLIA,
                rpc_url="https://sepolia.base.org",
                usdc_address=USDC_BASE_SEPOLIA,
                explorer_url="https://sepolia.basescan.org",
                name="Base Sepolia",
            )
