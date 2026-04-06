"""Agent wallet management."""

from eth_account import Account
from web3 import Web3
from typing import Optional
from .config import AgentPayConfig, ERC20_ABI


class AgentWallet:
    """A crypto wallet for an AI agent."""

    def __init__(self, private_key: Optional[str] = None, config: Optional[AgentPayConfig] = None):
        self.config = config or AgentPayConfig()
        self.w3 = Web3(Web3.HTTPProvider(self.config.chain.rpc_url))

        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()

        self.address = self.account.address
        self._usdc = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.config.chain.usdc_address),
            abi=ERC20_ABI,
        )

    @property
    def private_key(self) -> str:
        return self.account.key.hex()

    def balance(self, currency: str = "USDC") -> float:
        """Get wallet balance."""
        if currency.upper() == "ETH":
            wei = self.w3.eth.get_balance(self.address)
            return float(Web3.from_wei(wei, "ether"))
        elif currency.upper() == "USDC":
            raw = self._usdc.functions.balanceOf(self.address).call()
            return raw / 1e6  # USDC has 6 decimals
        else:
            raise ValueError(f"Unsupported currency: {currency}")

    def transfer(self, to: str, amount: float, currency: str = "USDC") -> dict:
        """Send tokens to another address."""
        to = Web3.to_checksum_address(to)

        if currency.upper() == "ETH":
            return self._transfer_eth(to, amount)
        elif currency.upper() == "USDC":
            return self._transfer_usdc(to, amount)
        else:
            raise ValueError(f"Unsupported currency: {currency}")

    def _transfer_eth(self, to: str, amount: float) -> dict:
        nonce = self.w3.eth.get_transaction_count(self.address)
        tx = {
            "nonce": nonce,
            "to": to,
            "value": Web3.to_wei(amount, "ether"),
            "gas": 21000,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.config.chain.chain_id,
        }
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        return {
            "hash": tx_hash.hex(),
            "status": "success" if receipt["status"] == 1 else "failed",
            "explorer": f"{self.config.chain.explorer_url}/tx/{tx_hash.hex()}",
        }

    def _transfer_usdc(self, to: str, amount: float) -> dict:
        raw_amount = int(amount * 1e6)  # USDC = 6 decimals
        nonce = self.w3.eth.get_transaction_count(self.address)

        tx = self._usdc.functions.transfer(to, raw_amount).build_transaction({
            "from": self.address,
            "nonce": nonce,
            "gas": 100000,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.config.chain.chain_id,
        })
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        return {
            "hash": tx_hash.hex(),
            "status": "success" if receipt["status"] == 1 else "failed",
            "explorer": f"{self.config.chain.explorer_url}/tx/{tx_hash.hex()}",
        }
