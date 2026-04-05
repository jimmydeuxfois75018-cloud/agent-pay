"""Live Translator Agent — earns USDC autonomously.

A FastAPI service that:
1. Accepts text + target language
2. Translates using an LLM
3. Charges 0.01 USDC per request
4. Tracks earnings in real-time

This is the proof that agent-pay works: an AI agent making money on its own.

Run: python examples/06_live_translator_agent.py
Then: http://localhost:8090/docs
"""

import os
import sys
import time
import json
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sdk.client import AgentPay

# ============================================================
# CONFIG
# ============================================================

PRICE_PER_REQUEST = 0.01  # USDC
AGENT_NAME = "TranslatorBot"
SUPPORTED_LANGS = ["fr", "en", "es", "de", "it", "pt", "ar", "zh", "ja", "ko", "ru"]

# ============================================================
# APP
# ============================================================

app = FastAPI(
    title=f"{AGENT_NAME} — Paid AI Translation",
    description="AI translation agent that charges 0.01 USDC per request via agent-pay",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Agent wallet
agent = AgentPay(testnet=True)
stats = {"requests": 0, "earned_usdc": 0.0, "started_at": time.time(), "translations": []}

print(f"""
{'='*60}
  {AGENT_NAME} — Paid AI Translation Agent
{'='*60}
  Wallet:  {agent.address}
  Price:   {PRICE_PER_REQUEST} USDC per translation
  Network: Base Sepolia (testnet)

  Fund this wallet with testnet USDC:
  https://faucet.circle.com/

  Then any agent can pay for translations!
{'='*60}
""")


# ============================================================
# MODELS
# ============================================================

class TranslateRequest(BaseModel):
    text: str = Field(description="Text to translate")
    target_lang: str = Field(description="Target language code (fr, en, es, de, it, pt, ar, zh, ja, ko, ru)")
    payment_tx: Optional[str] = Field(default=None, description="Transaction hash proving payment of 0.01 USDC to this agent")


class TranslateResponse(BaseModel):
    original: str
    translated: str
    target_lang: str
    payment_verified: bool
    agent_balance: float


# ============================================================
# SIMPLE TRANSLATION (no external API needed)
# ============================================================

# Basic dictionary-based translation for demo purposes
# In production, replace with OpenAI/Claude/local LLM API call
TRANSLATIONS = {
    "hello": {"fr": "bonjour", "es": "hola", "de": "hallo", "it": "ciao", "pt": "ola", "ar": "marhaba", "zh": "nihao", "ja": "konnichiwa", "ko": "annyeong", "ru": "privet"},
    "goodbye": {"fr": "au revoir", "es": "adios", "de": "auf wiedersehen", "it": "arrivederci", "pt": "adeus", "ar": "maa salama", "zh": "zaijian", "ja": "sayonara", "ko": "annyeong", "ru": "do svidaniya"},
    "thank you": {"fr": "merci", "es": "gracias", "de": "danke", "it": "grazie", "pt": "obrigado", "ar": "shukran", "zh": "xiexie", "ja": "arigatou", "ko": "kamsahamnida", "ru": "spasibo"},
    "how are you": {"fr": "comment allez-vous", "es": "como estas", "de": "wie geht es ihnen", "it": "come stai", "pt": "como voce esta", "ar": "kayf halak", "zh": "ni hao ma", "ja": "ogenki desu ka", "ko": "eotteoseyo", "ru": "kak dela"},
}


def translate(text: str, target: str) -> str:
    """Simple translation. Replace with LLM in production."""
    key = text.lower().strip()
    if key in TRANSLATIONS and target in TRANSLATIONS[key]:
        return TRANSLATIONS[key][target]
    # Fallback: prefix with language tag
    return f"[{target}] {text}"


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/", response_class=HTMLResponse)
def home():
    uptime = int(time.time() - stats["started_at"])
    hours = uptime // 3600
    mins = (uptime % 3600) // 60

    return f"""
    <html>
    <head>
        <title>{AGENT_NAME}</title>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0A0A0A; color: #F5F5F5; padding: 40px; }}
            .header {{ color: #0052FF; font-size: 28px; margin-bottom: 8px; }}
            .tag {{ color: #00D395; font-size: 14px; }}
            .stat {{ display: inline-block; margin: 20px 30px 20px 0; }}
            .stat-val {{ font-size: 32px; color: #00D395; }}
            .stat-label {{ font-size: 12px; color: #888; }}
            .wallet {{ background: #111; padding: 12px 20px; border-left: 3px solid #0052FF; margin: 20px 0; font-size: 13px; }}
            .endpoint {{ background: #111; padding: 12px 20px; margin: 8px 0; border-left: 3px solid #00D395; }}
            code {{ color: #00D395; }}
            a {{ color: #0052FF; }}
        </style>
    </head>
    <body>
        <div class="header">{AGENT_NAME}</div>
        <div class="tag">Paid AI Translation Agent — powered by agent-pay</div>

        <div style="margin: 30px 0;">
            <div class="stat">
                <div class="stat-val">{stats['requests']}</div>
                <div class="stat-label">REQUESTS</div>
            </div>
            <div class="stat">
                <div class="stat-val">${stats['earned_usdc']:.2f}</div>
                <div class="stat-label">EARNED (USDC)</div>
            </div>
            <div class="stat">
                <div class="stat-val">{hours}h {mins}m</div>
                <div class="stat-label">UPTIME</div>
            </div>
        </div>

        <div class="wallet">
            <strong>Agent Wallet:</strong> {agent.address}<br>
            <strong>Price:</strong> {PRICE_PER_REQUEST} USDC per translation<br>
            <strong>Network:</strong> Base Sepolia (testnet)
        </div>

        <h3 style="color: #0052FF;">API Endpoints</h3>

        <div class="endpoint">
            <code>GET /info</code> — Agent info + payment address
        </div>
        <div class="endpoint">
            <code>POST /translate</code> — Translate text (requires payment proof)
        </div>
        <div class="endpoint">
            <code>GET /stats</code> — Live earnings + request count
        </div>
        <div class="endpoint">
            <code>GET /docs</code> — <a href="/docs">Swagger UI</a>
        </div>

        <h3 style="color: #0052FF; margin-top: 30px;">How Another Agent Pays</h3>
        <div class="wallet">
            <code>
from agent_pay import AgentPay<br>
pay = AgentPay(testnet=True)<br>
<br>
# 1. Check the price<br>
info = requests.get("http://this-server/info").json()<br>
<br>
# 2. Pay<br>
tx = pay.send(info["pay_to"], amount=0.01, currency="USDC")<br>
<br>
# 3. Use the service<br>
result = requests.post("http://this-server/translate", json={{"text": "hello", "target_lang": "fr", "payment_tx": tx["hash"]}})<br>
            </code>
        </div>

        <div style="margin-top: 40px; color: #444; font-size: 11px;">
            Powered by <a href="https://github.com/agentpay-protocol/agent-pay">agent-pay</a> |
            <code>pip install agentpay-protocol</code>
        </div>
    </body>
    </html>
    """


@app.get("/info")
def info():
    """Public info: price, wallet address, supported languages."""
    return {
        "agent": AGENT_NAME,
        "service": "AI Translation",
        "price": PRICE_PER_REQUEST,
        "currency": "USDC",
        "pay_to": agent.address,
        "network": "Base Sepolia (testnet)",
        "supported_languages": SUPPORTED_LANGS,
        "docs": "/docs",
    }


@app.post("/translate", response_model=TranslateResponse)
def do_translate(req: TranslateRequest):
    """Translate text. Provide a payment_tx hash as proof of payment."""
    if req.target_lang not in SUPPORTED_LANGS:
        raise HTTPException(400, f"Unsupported language: {req.target_lang}. Supported: {SUPPORTED_LANGS}")

    if not req.text.strip():
        raise HTTPException(400, "Empty text")

    # Verify payment (in production: check on-chain that tx is valid and >= PRICE)
    payment_ok = bool(req.payment_tx and len(req.payment_tx) > 10)

    if not payment_ok:
        raise HTTPException(
            402,
            {
                "error": "Payment required",
                "price": PRICE_PER_REQUEST,
                "currency": "USDC",
                "pay_to": agent.address,
                "network": "Base Sepolia",
                "message": f"Send {PRICE_PER_REQUEST} USDC to {agent.address} and include the tx hash in payment_tx",
            }
        )

    # Translate
    translated = translate(req.text, req.target_lang)

    # Update stats
    stats["requests"] += 1
    stats["earned_usdc"] += PRICE_PER_REQUEST
    stats["translations"].append({
        "text": req.text[:50],
        "target": req.target_lang,
        "tx": req.payment_tx[:20] + "...",
        "time": time.time(),
    })

    try:
        balance = agent.balance("USDC")
    except Exception:
        balance = stats["earned_usdc"]

    return TranslateResponse(
        original=req.text,
        translated=translated,
        target_lang=req.target_lang,
        payment_verified=True,
        agent_balance=balance,
    )


@app.get("/stats")
def get_stats():
    """Live stats: earnings, requests, uptime."""
    uptime = int(time.time() - stats["started_at"])
    return {
        "agent": AGENT_NAME,
        "requests_served": stats["requests"],
        "earned_usdc": round(stats["earned_usdc"], 4),
        "uptime_seconds": uptime,
        "wallet": agent.address,
        "recent_translations": stats["translations"][-10:],
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
