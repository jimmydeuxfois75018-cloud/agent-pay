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
    "2030: AI agents will handle $30 trillion in transactions.\n\n2026: There's still no standard way for them to pay each other.\n\nWe're fixing that.",

    "A research agent finds a paper behind a paywall.\nIt pays $0.02 to access it.\nNo human needed.\n\nThis is the future we're building.\nhttps://github.com/agentpay-protocol/agent-pay",

    "Hot take: The biggest bottleneck in multi-agent systems isn't intelligence.\n\nIt's money.\n\nAgents can't hire, tip, or pay each other. That's a coordination failure, not a tech one.",

    "OpenAI charges per token.\nAnthropic charges per token.\nGoogle charges per token.\n\nBut your agent can't pay any of them without YOU clicking approve.\n\nThat's broken.",

    "Imagine a world where your AI assistant negotiates its own cloud costs, pays for premium data, and hires specialists.\n\nAll while you sleep.\n\nThat world needs payment rails.",

    "Fun fact: the first HTTP payment status code (402 Payment Required) was reserved in 1997.\n\n29 years later, we're finally building what it was meant for.\n\nMachine-to-machine payments.",

    "Web2: Stripe lets humans pay on websites.\nWeb3: agent-pay lets machines pay each other.\n\nSame simplicity. Different era.",

    "If your agent can browse the web, call APIs, and write code...\n\nWhy does it still need your credit card?",

    "The cost of one agent-to-agent payment on Base L2:\n\n$0.0003\n\nThat's 3,333 transactions for $1.\n\nMicropayments are finally real.",

    "Every great platform started as infrastructure nobody asked for.\n\nAWS. Stripe. Twilio.\n\nNobody asked for agent payment rails yet.\n\nBut they will.",

    "An agent economy without payments is like the internet without HTTP.\n\nTechnically possible. Practically useless at scale.",

    "We just open-sourced everything:\n\n- Python SDK\n- MCP server for Claude\n- REST API\n- LangChain + CrewAI + AutoGen integrations\n- Live demo agent\n\nFree. MIT license. Build whatever you want.",

    "Your competitor's AI agent just hired 3 specialist agents, paid them in USDC, and delivered the report.\n\nYour agent is still waiting for you to approve a $0.10 transaction.",

    "The agent economy will be bigger than the creator economy.\n\nCreators needed Patreon and Stripe.\nAgents need agent-pay.",
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
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tweet_one.js")
    tweet_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tweet_temp.txt")
    try:
        with open(tweet_file, "w", encoding="utf-8") as f:
            f.write(tweet_text)
        result = subprocess.run(
            ["node", script_path, tweet_file],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout.strip()
        print("  Node output: " + output)
        return "POSTED" in output
    except Exception as e:
        print("  Error: " + str(e))
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
