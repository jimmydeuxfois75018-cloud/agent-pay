# agent-pay MCP — Claude Code Setup

## Quick Setup

Add to your Claude Code MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "agent-pay": {
      "command": "npx",
      "args": ["@morpheus404world/agent-pay-mcp"]
    }
  }
}
```

## Available Tools

Once installed, Claude Code can use these tools:

| Tool | Description |
|------|-------------|
| `agent_pay_create_wallet` | Create a new wallet for an AI agent |
| `agent_pay_send` | Send USDC/ETH to another agent |
| `agent_pay_balance` | Check wallet balance |
| `agent_pay_escrow_create` | Create conditional payment |
| `agent_pay_escrow_release` | Release escrow funds |
| `agent_pay_receive_address` | Get address to receive payments |

## Example Usage in Claude Code

Just ask Claude:

> "Create a wallet for my agent and check the balance"

> "Send 0.50 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18"

> "Create an escrow of 5 USDC for a translation task"

Claude will use the MCP tools automatically.

## Testnet vs Mainnet

By default, the MCP server uses **Base Sepolia testnet** (safe for testing).

To use mainnet, call `agent_pay_create_wallet` with `testnet: false`.

## Get Testnet USDC

1. Go to https://faucet.circle.com/
2. Select "Base Sepolia"
3. Paste your agent's wallet address
4. Get free testnet USDC
