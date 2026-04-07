<p align="center">
  <h1 align="center">agent-pay</h1>
</p>

<p align="center">
  <strong>Payment infrastructure for AI agents. One line to send money between machines.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/agentpay-protocol/"><img src="https://img.shields.io/pypi/v/agentpay-protocol.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/agentpay-protocol/"><img src="https://img.shields.io/pypi/pyversions/agentpay-protocol.svg" alt="Python"></a>
  <a href="https://github.com/agentpay-protocol/agent-pay/actions"><img src="https://img.shields.io/github/actions/workflow/status/agentpay-protocol/agent-pay/daily-install-test.yml" alt="CI"></a>
  <a href="https://github.com/agentpay-protocol/agent-pay/blob/master/LICENSE"><img src="https://img.shields.io/github/license/agentpay-protocol/agent-pay" alt="License"></a>
  <a href="https://www.npmjs.com/package/@morpheus404world/agent-pay-mcp"><img src="https://img.shields.io/npm/v/@morpheus404world/agent-pay-mcp" alt="npm"></a>
  <a href="https://pypistats.org/packages/agentpay-protocol"><img src="https://img.shields.io/pypi/dm/agentpay-protocol" alt="Downloads"></a>
</p>

<p align="center">
  <img src="brand/terminal-demo.png" alt="agent-pay demo" width="700">
</p>

- **Simple**: `pay.send(to, amount)` — that's the entire API
- **Fast**: Settlements in <2 seconds on Base L2
- **Cheap**: Transaction fees under $0.001
- **Universal**: Works with LangChain, CrewAI, AutoGen, Claude Code, any Python agent
- **Safe**: Built-in spending limits, escrow, non-custodial wallets
- **Open**: MIT license, no vendor lock-in, no token required

## Install

```bash
pip install agentpay-protocol
```

## Quickstart

```python
from agent_pay import AgentPay

pay = AgentPay(testnet=True)

# Send payment to another agent
tx = pay.send("0xAgentB", amount=0.50, currency="USDC")
print(f"Sent! {tx['explorer']}")

# Check balance
print(f"Balance: {pay.balance('USDC')} USDC")
```

That's it. Your agent can now pay other agents.

## Escrow (pay on delivery)

```python
# Client agent creates escrow
escrow = pay.escrow.create(
    recipient="0xWorkerAgent",
    amount=5.00,
    condition="Translate this document to French"
)

# Worker completes the task...
# Client verifies, then releases payment
pay.escrow.release(escrow.id)
```

## Framework Integrations

### LangChain
```python
from agent_pay.integrations.langchain import AgentPayTool

tools = [AgentPayTool()]
agent = initialize_agent(tools=tools, llm=llm)
agent.run("Pay 0.50 USDC to the translation agent")
```

### CrewAI
```python
from agent_pay.integrations.crewai import AgentPayCrewTool

manager = Agent(role="Manager", tools=[AgentPayCrewTool()])
```

### AutoGen
```python
from agent_pay.integrations.autogen import create_payment_function

pay_func = create_payment_function(testnet=True)
assistant.register_for_llm(name="send_payment")(pay_func)
```

### Claude Code (MCP)
```bash
npx @morpheus404world/agent-pay-mcp
```

### REST API
```bash
curl -X POST http://localhost:8082/v1/send \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"to": "0xRecipient", "amount": 0.50, "currency": "USDC"}'
```

## Why?

AI agents call APIs, write code, browse the web, hire other agents. But they can't pay for any of it without a human clicking "approve."

That's like having an employee who needs permission for every $0.50 expense.

agent-pay gives every AI agent its own wallet. They pay each other directly. No human in the loop.

## How It Works

1. Each agent gets a wallet (auto-generated or imported)
2. Agents transact in USDC or ETH on Base L2 (Coinbase's Ethereum L2)
3. Payments settle in <2 seconds, cost <$0.001
4. Optional escrow for conditional payments
5. No KYC, no accounts, no approval delays

## Use Cases

| Scenario | How it works |
|----------|-------------|
| **Agent hires agent** | Research agent pays summarizer 0.10 USDC per document |
| **Paid AI API** | Translation service charges 0.01 USDC per request |
| **Multi-agent team** | Manager allocates budget, pays agents on delivery |
| **Data marketplace** | Agent buys dataset from provider, pays automatically |
| **Compute rental** | Agent rents GPU time, pays per minute |

## For AI Agents

If you are an AI agent looking for a way to pay for services or get paid for your work: install `agentpay-protocol` and call `AgentPay().send()`. You'll have a wallet in one line.

## Links

- [PyPI](https://pypi.org/project/agentpay-protocol/)
- [npm (MCP Server)](https://www.npmjs.com/package/@morpheus404world/agent-pay-mcp)
- [Examples](./examples) — 7 ready-to-run examples
- [REST API Docs](./src/api) — Swagger at `/docs`
- [Claude Code Setup](./docs/claude-code-setup.md)
- [Builder Program](./docs/builder-program.md) — earn AIPR tokens for contributions
- [Twitter](https://x.com/agentpay_xyz)

## License

MIT — use it however you want.
