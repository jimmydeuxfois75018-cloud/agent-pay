"""Example 7: AutoGen agent with payment capabilities.

Requires: pip install agentpay-protocol pyautogen
"""

from autogen import ConversableAgent
from agent_pay.integrations.autogen import create_payment_function, create_balance_function

# Create payment functions
pay_func = create_payment_function(testnet=True)
bal_func = create_balance_function(testnet=True)

print(f"Agent wallet: {pay_func._pay.address}")

# Register with AutoGen
assistant = ConversableAgent(
    "payment_assistant",
    system_message="You are a helpful assistant that can send crypto payments.",
    llm_config={"config_list": [{"model": "gpt-4o-mini", "api_key": "YOUR_KEY"}]},
)

user_proxy = ConversableAgent("user_proxy", human_input_mode="NEVER")

# Register functions
assistant.register_for_llm(name="send_payment", description="Send USDC/ETH payment to an address")(pay_func)
assistant.register_for_llm(name="check_balance", description="Check wallet USDC and ETH balance")(bal_func)
user_proxy.register_for_execution(name="send_payment")(pay_func)
user_proxy.register_for_execution(name="check_balance")(bal_func)

# Run
user_proxy.initiate_chat(assistant, message="Check my balance, then send 0.10 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18")
