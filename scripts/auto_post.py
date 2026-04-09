"""Auto-poster for @agentpay_xyz via X API (Tweepy).

Posts 2 tweets per day from a rotating list.
No Chrome, no Playwright, no browser needed.

Run: python scripts/auto_post.py
Schedule: every 8 hours via Windows Task Scheduler
"""

import tweepy
import json
import time
import os
import urllib.request
import urllib.parse

CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.twitter_creds.json')
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.auto_post_state.json')
TELEGRAM_TOKEN = "8685866733:AAEhP42Qc5i-_Yw5MOfYwuXRmqOpbphILhg"
TELEGRAM_CHAT = "5047076645"

TWEETS = [
    "Hot take: in 2 years the most valuable AI companies wont build models. Theyll build the financial infrastructure between agents.",
    "Everyone is building the brain. Nobody is building the wallet.\n\nThats the gap.\n\nhttps://github.com/agentpay-protocol/agent-pay",
    "An agent economy without payments is like the internet without HTTP.\n\nTechnically possible. Practically useless at scale.",
    "Your competitors AI agent just hired 3 specialist agents, paid them in USDC, and delivered the report.\n\nYour agent is still waiting for you to approve a $0.10 transaction.",
    "The agent economy will be bigger than the creator economy.\n\nCreators needed Patreon and Stripe.\nAgents need payment rails.",
    "The cost of one agent-to-agent payment on Base L2:\n\n$0.0003\n\nThats 3,333 transactions for $1.\n\nMicropayments are finally real.",
    "Web2: Stripe lets humans pay on websites.\nWeb3: agent-pay lets machines pay each other.\n\nSame simplicity. Different era.",
    "If your agent can browse the web, call APIs, and write code...\n\nWhy does it still need your credit card?",
    "A research agent finds a paper behind a paywall.\nIt pays $0.02 to access it.\nNo human needed.\n\nThis is the future were building.\nhttps://github.com/agentpay-protocol/agent-pay",
    "The moment agents can pay for their own API calls without human approval, the entire SaaS model changes overnight.",
    "We just open-sourced everything:\n\nPython SDK + MCP server + REST API + LangChain + CrewAI + AutoGen integrations.\n\nFree. MIT license.\nhttps://github.com/agentpay-protocol/agent-pay",
    "Nobody talks about this but the coordination problem in multi-agent systems is always about money.\n\nWho pays who for what.",
    "The best multi-agent setups all hit the same wall:\n\nHow does Agent A pay Agent B for its work?\n\nWe built the answer. pip install agentpay-protocol",
    "Fun fact: HTTP 402 Payment Required was created in 1997 for machine payments.\n\n29 years later were still not there.\n\nBut were getting close.",
    "Agents dont need bank accounts.\nThey need programmable wallets with spending limits.\n\nThats the insight.",
    "Every great platform started as infrastructure nobody asked for.\n\nAWS. Stripe. Twilio.\n\nNobody asked for agent payment rails yet.\n\nBut they will.",
]


def load_creds():
    with open(CREDS_FILE) as f:
        return json.load(f)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_index": -1, "posted": 0}


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


def main():
    creds = load_creds()
    state = load_state()

    client = tweepy.Client(
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
    )

    next_index = (state["last_index"] + 1) % len(TWEETS)
    tweet_text = TWEETS[next_index]

    print(f"Posting tweet #{next_index + 1}/{len(TWEETS)}")
    print(f"Text: {tweet_text[:80]}...")

    try:
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data["id"]
        print(f"POSTED! ID: {tweet_id}")

        state["last_index"] = next_index
        state["posted"] += 1
        save_state(state)

        send_telegram(f"NEO Auto-Post #{state['posted']}: {tweet_text[:80]}...")
    except Exception as e:
        print(f"FAILED: {e}")
        send_telegram(f"NEO Auto-Post FAILED: {str(e)[:100]}")


if __name__ == "__main__":
    main()
