"""Monitor agent-pay KPIs: GitHub stars, PyPI downloads, npm installs.

Run: python scripts/monitor.py
Schedule with cron/Task Scheduler for daily reports.
"""

import urllib.request
import json
import sys
import os

TELEGRAM_TOKEN = "8685866733:AAEhP42Qc5i-_Yw5MOfYwuXRmqOpbphILhg"
TELEGRAM_CHAT = "5047076645"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "agent-pay-monitor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)}


def github_stats():
    data = fetch_json("https://api.github.com/repos/agentpay-protocol/agent-pay")
    if "error" in data:
        return {"stars": "?", "forks": "?", "watchers": "?"}
    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("subscribers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
    }


def pypi_stats():
    data = fetch_json("https://api.pepy.tech/api/v2/projects/agentpay-protocol")
    if "error" in data:
        # Fallback
        data2 = fetch_json("https://pypi.org/pypi/agentpay-protocol/json")
        if "error" not in data2:
            return {"version": data2["info"]["version"], "downloads": "N/A"}
        return {"downloads": "?"}
    return {
        "total_downloads": data.get("total_downloads", 0),
        "versions": list(data.get("versions", {}).keys()),
    }


def npm_stats():
    data = fetch_json("https://registry.npmjs.org/@morpheus404world/agent-pay-mcp")
    if "error" in data:
        return {"version": "?"}
    latest = data.get("dist-tags", {}).get("latest", "?")
    return {"version": latest, "name": data.get("name", "?")}


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT, "text": message, "parse_mode": "HTML"}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data), timeout=10)
    except Exception:
        pass


def main():
    import urllib.parse

    gh = github_stats()
    pypi = pypi_stats()
    npm = npm_stats()

    report = f"""
<b>agent-pay — Daily KPI Report</b>

<b>GitHub</b>
  Stars: {gh.get('stars', '?')}
  Forks: {gh.get('forks', '?')}
  Watchers: {gh.get('watchers', '?')}
  Issues: {gh.get('open_issues', '?')}

<b>PyPI</b>
  Downloads: {pypi.get('total_downloads', pypi.get('downloads', '?'))}
  Version: {pypi.get('version', pypi.get('versions', ['?']))}

<b>npm</b>
  Version: {npm.get('version', '?')}

<b>Objectives</b>
  Stars: {gh.get('stars', 0)}/100
  Downloads: {pypi.get('total_downloads', '?')}/500
""".strip()

    print(report.replace("<b>", "").replace("</b>", ""))

    if "--telegram" in sys.argv:
        send_telegram(report)
        print("\nSent to Telegram.")


if __name__ == "__main__":
    main()
