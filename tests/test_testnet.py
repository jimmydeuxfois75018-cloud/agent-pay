"""Test SDK on Base Sepolia testnet — real blockchain interaction.

This test creates wallets, checks balances, and verifies RPC connectivity.
No funds needed — just checks that the chain is reachable.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from sdk.client import AgentPay
from sdk.config import AgentPayConfig, BASE_SEPOLIA


def test_wallet_creation():
    """Create a wallet on Base Sepolia."""
    pay = AgentPay(testnet=True)
    assert pay.address.startswith("0x")
    assert len(pay.address) == 42
    assert pay.config.chain.chain_id == BASE_SEPOLIA
    print(f"  Wallet: {pay.address}")
    print(f"  Chain: {pay.config.chain.name} (ID {pay.config.chain.chain_id})")
    print(f"  RPC: {pay.config.chain.rpc_url}")


def test_balance_check():
    """Check balance on Base Sepolia (should be 0 for new wallet)."""
    pay = AgentPay(testnet=True)
    eth_bal = pay.balance("ETH")
    usdc_bal = pay.balance("USDC")
    assert eth_bal >= 0
    assert usdc_bal >= 0
    print(f"  ETH: {eth_bal}")
    print(f"  USDC: {usdc_bal}")


def test_import_key():
    """Import a known private key and verify address."""
    key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    pay = AgentPay(private_key=key, testnet=True)
    assert pay.address == "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    print(f"  Imported: {pay.address}")


def test_export_key():
    """Export private key and reimport — should get same address."""
    pay1 = AgentPay(testnet=True)
    key = pay1.export_key()
    pay2 = AgentPay(private_key=key, testnet=True)
    assert pay1.address == pay2.address
    print(f"  Export/import match: {pay1.address}")


def test_spending_limit():
    """Spending limit should block large transactions."""
    pay = AgentPay(testnet=True, spending_limit_usd=5.0)
    try:
        pay.send("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18", amount=10.0)
        assert False, "Should have raised"
    except ValueError as e:
        assert "exceeds" in str(e)
        print(f"  Spending limit works: {e}")


def test_escrow_lifecycle():
    """Create and refund an escrow."""
    pay = AgentPay(testnet=True)
    pay.wallet.balance = lambda currency: 100.0  # Mock balance

    escrow = pay.escrow.create(
        recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18",
        amount=1.0,
        condition="Test task",
    )
    assert escrow.status.value == "funded"
    print(f"  Escrow created: {escrow.id}")

    pay.escrow.refund(escrow.id)
    assert pay.escrow.get(escrow.id).status.value == "refunded"
    print(f"  Escrow refunded")


def test_receive_address():
    """Receive address should match wallet address."""
    pay = AgentPay(testnet=True)
    assert pay.receive_address() == pay.address
    print(f"  Receive address: {pay.receive_address()}")


if __name__ == "__main__":
    tests = [
        ("Wallet Creation", test_wallet_creation),
        ("Balance Check (Base Sepolia RPC)", test_balance_check),
        ("Import Key", test_import_key),
        ("Export/Import Key", test_export_key),
        ("Spending Limit", test_spending_limit),
        ("Escrow Lifecycle", test_escrow_lifecycle),
        ("Receive Address", test_receive_address),
    ]

    passed = 0
    failed = 0

    print("\n" + "=" * 60)
    print("  agent-pay SDK — Base Sepolia Testnet Tests")
    print("=" * 60 + "\n")

    for name, func in tests:
        try:
            print(f"[TEST] {name}")
            func()
            print(f"  PASS\n")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
