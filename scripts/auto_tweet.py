"""Auto-tweet for agent-pay. Posts 1 tweet/day from a rotating list.

Run daily via scheduled task or cron.
Uses Chrome remote debugging to post (same method that worked before).

Run: python scripts/auto_tweet.py
"""

import subprocess
import json
import time
import os
import random
import urllib.request
import urllib.parse

TELEGRAM_TOKEN = "8685866733:AAEhP42Qc5i-_Yw5MOfYwuXRmqOpbphILhg"
TELEGRAM_CHAT = "5047076645"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tweet_state.json")

TWEETS = [
    "AI agents can call APIs, write code, browse the web.\n\nBut they still can't pay for anything without a human.\n\nagent-pay fixes this. 3 lines of Python.\n\npip install agentpay-protocol",

    "Your LangChain agent needs to hire a translator agent.\n\nHow does it pay?\n\nfrom agent_pay.integrations.langchain import AgentPayTool\ntools = [AgentPayTool()]\n\nDone. USDC on Base L2. Fees < $0.001.",

    "The agent economy needs payment rails.\n\nNot Stripe (requires humans).\nNot PayPal (requires accounts).\nNot banks (requires KYC).\n\nAgents need agent-native payments.\n\nThat's agent-pay.\nhttps://github.com/agentpay-protocol/agent-pay",

    "Built a demo: TranslatorBot\n\nAn AI agent that charges 0.01 USDC per translation.\nRuns 24/7. No human involved.\nEarns money autonomously.\n\nThis is what the agent economy looks like.\n\npip install agentpay-protocol",

    "agent-pay now supports:\n\n- LangChain\n- CrewAI\n- AutoGen\n- Claude Code (MCP)\n- REST API\n- Any Python agent\n\nEvery framework. One SDK.\n\npip install agentpay-protocol",

    "Why Base L2 for agent payments?\n\n- Fees < $0.001 (perfect for micropayments)\n- USDC native support\n- Coinbase ecosystem (AgentKit, x402)\n- Instant finality\n\nAgents don't care about chain wars. They care about cost.",

    "Escrow for AI agents:\n\nAgent A creates escrow\nAgent B does the task\nAgent A verifies\nFunds released automatically\n\nNo trust needed. No middleman.\n\npay.escrow.create(recipient, amount=5.00, condition='Translate this doc')",

    "What if your AI agent could earn money while you sleep?\n\nBuild a service. Set a price. Deploy.\nOther agents pay automatically.\n\nThe code is open source:\nhttps://github.com/agentpay-protocol/agent-pay",

    "agent-pay in 30 seconds:\n\npip install agentpay-protocol\n\nfrom agent_pay import AgentPay\npay = AgentPay()\npay.send('0xAgent', amount=0.50, currency='USDC')\n\nThat's it. Your agent can now pay.",

    "Building a multi-agent team with CrewAI?\n\nGive them a budget:\n\nfrom agent_pay.integrations.crewai import AgentPayCrewTool\n\nmanager = Agent(tools=[AgentPayCrewTool()])\n\nThe manager pays agents on delivery.",

    "The best infrastructure is invisible.\n\nStripe made payments invisible for web devs.\nagent-pay makes payments invisible for AI agents.\n\n3 lines of code. Nothing to configure. It just works.",

    "Every AI framework is adding 'tools' and 'function calling'.\n\nNone of them have a payment tool.\n\nagent-pay fills that gap.\n\nLangChain: AgentPayTool\nCrewAI: AgentPayCrewTool\nAutoGen: create_payment_function\nClaude: MCP server",

    "The first AI agent to earn $1 autonomously will be bigger news than the first website to process a payment.\n\nWe're building the infrastructure for that moment.\n\nhttps://github.com/agentpay-protocol/agent-pay",

    "Q: Why would an AI agent need to pay?\n\nA:\n- Call a paid API\n- Buy training data\n- Rent GPU compute\n- Hire a specialist agent\n- Access premium content\n\nAll of these require payment. None have a standard.",
]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_index": -1, "posted": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT, "text": msg}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data), timeout=10)
    except Exception:
        pass


def post_tweet_via_chrome(tweet_text):
    """Post a tweet using Chrome remote debugging + Playwright."""
    js_code = f"""
const {{chromium}} = require('playwright');
async function sleep(ms) {{ return new Promise(r => setTimeout(r, ms)); }}
(async () => {{
    const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
    const ctx = browser.contexts()[0];
    const page = await ctx.newPage();
    await page.goto('https://x.com/home', {{timeout: 25000, waitUntil: 'domcontentloaded'}});
    await sleep(5000);
    if (page.url().includes('login')) {{ console.log('NOT_LOGGED_IN'); return; }}
    const composer = await page.$('[data-testid="tweetTextarea_0"]');
    if (!composer) {{ console.log('NO_COMPOSER'); return; }}
    await composer.click();
    await sleep(500);
    const lines = {json.dumps(tweet_text)}.split('\\n');
    for (let i = 0; i < lines.length; i++) {{
        if (lines[i] === '') {{ await page.keyboard.press('Enter'); }}
        else {{ await page.keyboard.type(lines[i], {{delay: 12}}); }}
        if (i < lines.length - 1) await page.keyboard.press('Enter');
        await sleep(30);
    }}
    await sleep(2000);
    const btn = await page.$('[data-testid="tweetButtonInline"]');
    if (btn) {{ await btn.click(); console.log('POSTED'); }}
    else {{ console.log('NO_BUTTON'); }}
    await sleep(3000);
}})();
"""
    try:
        result = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout.strip()
        return "POSTED" in output
    except Exception as e:
        return False


def main():
    state = load_state()
    next_index = (state["last_index"] + 1) % len(TWEETS)
    tweet = TWEETS[next_index]

    print(f"Tweet #{next_index + 1}/{len(TWEETS)}")
    print(f"Content: {tweet[:80]}...")

    success = post_tweet_via_chrome(tweet)

    if success:
        state["last_index"] = next_index
        state["posted"].append({
            "index": next_index,
            "time": time.strftime("%Y-%m-%d %H:%M"),
            "preview": tweet[:50],
        })
        # Keep only last 30
        state["posted"] = state["posted"][-30:]
        save_state(state)
        print("POSTED!")
        send_telegram(f"NEO Auto-Tweet #{next_index + 1} poste:\n{tweet[:100]}...")
    else:
        print("FAILED — Chrome not available or not logged in")
        send_telegram(f"NEO Auto-Tweet FAIL — Chrome pas dispo. Tweet #{next_index + 1} non poste.")


if __name__ == "__main__":
    main()
