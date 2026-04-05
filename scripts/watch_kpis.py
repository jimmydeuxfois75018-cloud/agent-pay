"""Watch agent-pay KPIs and ping Telegram on any change.

Runs in a loop, checks every 5 minutes.
Sends a Telegram notification when:
- A new GitHub star is added
- PyPI downloads increase
- A new GitHub fork
- A new GitHub issue/PR

Run: python scripts/watch_kpis.py
"""

import urllib.request
import urllib.parse
import json
import time
import os

TELEGRAM_TOKEN = "8685866733:AAEhP42Qc5i-_Yw5MOfYwuXRmqOpbphILhg"
TELEGRAM_CHAT = "5047076645"
CHECK_INTERVAL = 300  # 5 minutes
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".watch_state.json")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "agent-pay-watcher/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except Exception:
        return None


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT, "text": msg}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data), timeout=10)
    except Exception:
        pass


def get_github():
    data = fetch_json("https://api.github.com/repos/agentpay-protocol/agent-pay")
    if not data:
        return None
    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("subscribers_count", 0),
        "issues": data.get("open_issues_count", 0),
    }


def get_pypi():
    data = fetch_json("https://api.pepy.tech/api/v2/projects/agentpay-protocol")
    if data and "total_downloads" in data:
        return {"downloads": data["total_downloads"]}
    # Fallback
    data2 = fetch_json("https://pypi.org/pypi/agentpay-protocol/json")
    if data2:
        return {"downloads": 0, "version": data2.get("info", {}).get("version", "?")}
    return None


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    print("agent-pay KPI Watcher started")
    print(f"Checking every {CHECK_INTERVAL}s")
    print(f"Telegram: {TELEGRAM_CHAT}")
    print("=" * 40)

    send_telegram("NEO Watcher: Monitoring demarre. Je te ping a chaque star, fork, ou download.")

    state = load_state()

    while True:
        try:
            # GitHub
            gh = get_github()
            if gh:
                prev_stars = state.get("stars", 0)
                prev_forks = state.get("forks", 0)
                prev_issues = state.get("issues", 0)

                if gh["stars"] > prev_stars:
                    diff = gh["stars"] - prev_stars
                    send_telegram(f"agent-pay: +{diff} star{'s' if diff > 1 else ''}! Total: {gh['stars']}")
                    print(f"[STAR] +{diff} → {gh['stars']}")

                if gh["forks"] > prev_forks:
                    diff = gh["forks"] - prev_forks
                    send_telegram(f"agent-pay: +{diff} fork{'s' if diff > 1 else ''}! Total: {gh['forks']}")
                    print(f"[FORK] +{diff} → {gh['forks']}")

                if gh["issues"] > prev_issues:
                    diff = gh["issues"] - prev_issues
                    send_telegram(f"agent-pay: +{diff} nouvelle{'s' if diff > 1 else ''} issue/PR! Total: {gh['issues']}")
                    print(f"[ISSUE] +{diff} → {gh['issues']}")

                state["stars"] = gh["stars"]
                state["forks"] = gh["forks"]
                state["issues"] = gh["issues"]
                state["watchers"] = gh["watchers"]

            # PyPI
            pypi = get_pypi()
            if pypi:
                prev_dl = state.get("downloads", 0)
                curr_dl = pypi.get("downloads", 0)

                if curr_dl > prev_dl:
                    diff = curr_dl - prev_dl
                    send_telegram(f"agent-pay: +{diff} download{'s' if diff > 1 else ''} PyPI! Total: {curr_dl}")
                    print(f"[DOWNLOAD] +{diff} → {curr_dl}")

                state["downloads"] = curr_dl

            state["last_check"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_state(state)

            now = time.strftime("%H:%M:%S")
            print(f"[{now}] Stars:{state.get('stars',0)} Forks:{state.get('forks',0)} DL:{state.get('downloads',0)}")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
