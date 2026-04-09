"""Twitter Reply Agent v2 — Growth via smart replies using X API.

No Chrome, no Playwright. 100% API-based.
Searches for relevant tweets, replies with smart comments, follows accounts.

Run: python scripts/twitter_agent_v2.py
Schedule: every 3 hours
"""

import tweepy
import json
import time
import random
import os
import urllib.request
import urllib.parse

CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.twitter_creds.json')
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.twitter_agent_v2_state.json')
TELEGRAM_TOKEN = "8685866733:AAEhP42Qc5i-_Yw5MOfYwuXRmqOpbphILhg"
TELEGRAM_CHAT = "5047076645"

# === SEARCH QUERIES (rotated each run) ===
SEARCH_QUERIES = [
    "AI agents",
    "multi agent system",
    "agentic AI",
    "LangChain agent",
    "CrewAI",
    "autonomous AI",
    "AI agent framework",
    "building AI agents",
    "agent economy",
    "AI agent Python",
    "AI infrastructure",
    "AI agent tool",
]

# === TARGET ACCOUNTS — reply to their tweets specifically ===
TARGET_ACCOUNTS = [
    "hwchase17",      # LangChain
    "yaborosc",       # AI agents
    "jerryjliu0",     # LlamaIndex
    "simonw",         # dev tools
    "levelsio",       # indie hacker
    "oaborosc",       # AI agents
    "swaborosc",      # AI engineering
    "karpaborosc",    # ML
]

# === REPLY TEMPLATES — 90% value, 10% soft promo ===
# Each reply is short, direct, sounds like a real dev

VALUE_REPLIES = [
    # Value-add
    "the real bottleneck in multi-agent systems isnt intelligence — its economic coordination. who pays who for what",
    "agents are smart but broke. they can reason, plan, and execute but cant spend $0.10 without asking permission",
    "everyone builds the brain, nobody builds the wallet. thats the actual gap right now",
    "hot take: the most valuable AI companies in 2 years wont build models. theyll build infra between agents",
    "this is so underrated. agents that can autonomously spend on better data sources will crush agents that cant",
    "the moment agents pay for their own API calls the entire SaaS model breaks overnight",
    "the coordination problem in multi-agent systems always comes back to money. always",
    "without financial autonomy agents are just fancy cron jobs with a human bottleneck at every step",
    "the agent economy is gonna be bigger than the creator economy and most people arent ready",
    "HTTP 402 Payment Required was created in 1997 for machine payments. 29 years later were still not there lol",
    # Contrarian
    "respectfully disagree — the hard part isnt building the agent. its making agents trust and pay each other without a middleman",
    "i see this differently. the models are a commodity now. coordination, payments, identity — thats where the moats actually are",
    "nah the real unlock isnt better reasoning. its letting agents hire other agents and compensate them autonomously",
    # Story
    "we ran into exactly this. built agents for 4 months in silence, zero traction. the moment we solved the payment layer everything clicked",
    "tested this approach for 3 months. 40% of agent transactions failed because of gas fees. moving to L2 stablecoins fixed everything",
    # Question
    "genuine question: how do you handle idempotency on the payment retries? thats usually the first wall at scale",
    "curious — what happens when agent A disagrees with the price agent B charges? whos the arbitrator?",
    "have you thought about escrow for this? pay-on-delivery eliminates the trust problem between agents entirely",
]

PROMO_REPLIES = [
    "been building exactly this — open source SDK for agent payments. 3 lines of python and agents can pay each other autonomously",
    "we ship this. agents dont need bank accounts, they need programmable wallets with spending limits",
    "working on this right now. payment infra for AI agents. turns out the hard part wasnt the crypto, it was making it dead simple",
]

# === CONFIG ===
MAX_REPLIES_PER_RUN = 8
MAX_FOLLOWS_PER_RUN = 5
MIN_LIKES_TO_REPLY = 3  # Skip dead tweets
PROMO_RATIO = 0.1  # 10% promo, 90% value


def load_creds():
    with open(CREDS_FILE) as f:
        return json.load(f)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"replied_tweets": [], "total_replies": 0, "total_follows": 0, "last_run": None}


def save_state(state):
    state["last_run"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    # Keep last 500 replied tweet IDs
    state["replied_tweets"] = state["replied_tweets"][-500:]
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT, "text": msg}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data), timeout=10)
    except Exception:
        pass


def pick_reply(is_promo=False):
    templates = PROMO_REPLIES if is_promo else VALUE_REPLIES
    return random.choice(templates)


def main():
    creds = load_creds()
    state = load_state()

    # Two clients: Bearer for search, OAuth for posting/replying
    BEARER = "AAAAAAAAAAAAAAAAAAAAAAFy8wEAAAAAVDrOTKdUvZly1MCaDW0POWftC%2Fc%3DThLjyNT0b2TaqoBKctj3YiggyTqBPsEMKWVsfqF4c6vuTn3Yv1"

    search_client = tweepy.Client(bearer_token=BEARER)

    write_client = tweepy.Client(
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
    )

    # Pick 2 random search queries
    queries = random.sample(SEARCH_QUERIES, min(2, len(SEARCH_QUERIES)))
    replies_made = 0
    follows_made = 0

    for query in queries:
        print(f"\nSearching: {query}")

        try:
            # Search recent tweets with engagement
            tweets = search_client.search_recent_tweets(
                query=f"{query} -is:retweet -is:reply lang:en",
                max_results=20,
                tweet_fields=["public_metrics", "created_at", "author_id", "reply_settings"],
                expansions=["author_id"],
                user_fields=["username", "public_metrics"],
            )
        except Exception as e:
            print(f"  Search error: {e}")
            continue

        if not tweets.data:
            print("  No tweets found")
            continue

        # Build user map
        users = {}
        if tweets.includes and "users" in tweets.includes:
            for u in tweets.includes["users"]:
                users[u.id] = u

        # Sort by engagement (likes + replies + retweets)
        sorted_tweets = sorted(
            tweets.data,
            key=lambda t: (
                t.public_metrics["like_count"]
                + t.public_metrics["reply_count"]
                + t.public_metrics["retweet_count"]
            ),
            reverse=True,
        )

        print(f"  Found {len(sorted_tweets)} tweets (sorted by engagement)")

        for tweet in sorted_tweets:
            if replies_made >= MAX_REPLIES_PER_RUN:
                break

            tweet_id = str(tweet.id)
            metrics = tweet.public_metrics
            likes = metrics["like_count"]
            reply_count = metrics["reply_count"]
            rts = metrics["retweet_count"]
            engagement = likes + reply_count + rts

            # Skip already replied
            if tweet_id in state["replied_tweets"]:
                continue

            # Skip low engagement
            if likes < MIN_LIKES_TO_REPLY:
                continue

            # Skip tweets with restricted replies
            reply_settings = getattr(tweet, 'reply_settings', 'everyone')
            if reply_settings and reply_settings != 'everyone':
                print(f"  SKIP (replies restricted: {reply_settings})")
                continue

            # Skip our own tweets
            author = users.get(tweet.author_id)
            if author and author.username == "agentpay_xyz":
                continue

            author_name = author.username if author else "?"
            author_followers = author.public_metrics["followers_count"] if author else 0

            print(f"\n  @{author_name} ({author_followers} followers) | {likes}L {reply_count}R {rts}RT")
            print(f"  {tweet.text[:100].encode('ascii', 'replace').decode()}")

            # Pick reply type
            is_promo = random.random() < PROMO_RATIO
            reply_text = pick_reply(is_promo)

            try:
                write_client.create_tweet(
                    text=reply_text,
                    in_reply_to_tweet_id=tweet.id,
                )
                replies_made += 1
                state["replied_tweets"].append(tweet_id)
                state["total_replies"] += 1
                print(f"  REPLIED ({'promo' if is_promo else 'value'}): {reply_text[:60]}...")

                # Follow the author if interesting (10k+ followers, not already following too many)
                if follows_made < MAX_FOLLOWS_PER_RUN and author_followers > 1000:
                    try:
                        write_client.follow_user(author.id)
                        follows_made += 1
                        state["total_follows"] += 1
                        print(f"  FOLLOWED @{author_name}")
                    except Exception:
                        pass

                # Human-like delay between replies
                delay = random.randint(30, 90)
                print(f"  Waiting {delay}s...")
                time.sleep(delay)

            except tweepy.errors.Forbidden as e:
                print(f"  SKIP (forbidden): {str(e)[:80]}")
                continue  # Try next tweet
            except tweepy.errors.TooManyRequests:
                print("  RATE LIMITED — stopping")
                break
            except Exception as e:
                print(f"  Error: {e}")

    save_state(state)
    print(f"\n=== DONE: {replies_made} replies, {follows_made} follows ===")
    print(f"Total: {state['total_replies']} replies, {state['total_follows']} follows")

    if replies_made > 0:
        send_telegram(
            f"NEO Twitter Agent: {replies_made} replies + {follows_made} follows\n"
            f"Total: {state['total_replies']} replies, {state['total_follows']} follows"
        )


if __name__ == "__main__":
    main()
