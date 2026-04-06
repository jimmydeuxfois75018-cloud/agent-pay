"""agent-pay REST API — payment protocol for AI agents.

Run: uvicorn src.api.main:app --host 0.0.0.0 --port 8080
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import hashlib
import hmac
import time
import os
import json

app = FastAPI(
    title="agent-pay API",
    description="REST API for AI agent payments. Send and receive USDC/ETH on Base L2.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

from fastapi.responses import FileResponse

@app.get("/dashboard", response_class=FileResponse)
def dashboard():
    """Dashboard UI."""
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store (replace with DB in production)
API_KEYS = {}  # api_key -> {wallet_address, private_key, created_at}
TRANSACTIONS = []
ESCROWS = {}


# ============================================================
# Models
# ============================================================

class CreateWalletRequest(BaseModel):
    """Create a new agent wallet."""
    testnet: bool = Field(default=True, description="Use Base Sepolia testnet (true) or mainnet (false)")

class CreateWalletResponse(BaseModel):
    api_key: str
    address: str
    network: str
    note: str = "Save your API key securely. Use it in the Authorization header."

class SendRequest(BaseModel):
    to: str = Field(description="Recipient wallet address (0x...)")
    amount: float = Field(description="Amount to send (e.g. 0.50 for $0.50 USDC)")
    currency: str = Field(default="USDC", description="USDC or ETH")
    memo: str = Field(default="", description="Optional description")

class SendResponse(BaseModel):
    status: str
    hash: str
    from_address: str = Field(alias="from")
    to: str
    amount: float
    currency: str
    explorer: str

class BalanceResponse(BaseModel):
    address: str
    USDC: str
    ETH: str
    network: str

class EscrowCreateRequest(BaseModel):
    recipient: str = Field(description="Worker agent address (0x...)")
    amount: float
    currency: str = Field(default="USDC")
    condition: str = Field(description="Task description for payment release")
    timeout_seconds: int = Field(default=3600)

class EscrowResponse(BaseModel):
    escrow_id: str
    status: str
    amount: float
    currency: str
    recipient: str
    condition: str

class EscrowReleaseRequest(BaseModel):
    escrow_id: str


# ============================================================
# Auth
# ============================================================

def get_api_key(authorization: str = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(401, "Missing Authorization header. Use: Authorization: Bearer YOUR_API_KEY")

    key = authorization.replace("Bearer ", "").strip()
    if key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")

    return API_KEYS[key]


# ============================================================
# Endpoints
# ============================================================

@app.get("/")
def root():
    return {
        "service": "agent-pay API",
        "version": "0.1.0",
        "description": "Payment protocol for AI agents",
        "docs": "/docs",
        "endpoints": {
            "POST /v1/wallet/create": "Create a new agent wallet + API key",
            "GET /v1/balance": "Check wallet balance",
            "POST /v1/send": "Send a payment",
            "POST /v1/escrow/create": "Create an escrow payment",
            "POST /v1/escrow/release": "Release escrow funds",
            "GET /v1/transactions": "List transactions",
        }
    }


@app.post("/v1/wallet/create", response_model=CreateWalletResponse)
def create_wallet(req: CreateWalletRequest):
    """Create a new agent wallet. Returns an API key for all future requests."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from agent_pay.client import AgentPay

    pay = AgentPay(testnet=req.testnet)

    # Generate API key
    raw = f"{pay.address}:{time.time()}:{os.urandom(16).hex()}"
    api_key = "ap_" + hashlib.sha256(raw.encode()).hexdigest()[:32]

    API_KEYS[api_key] = {
        "address": pay.address,
        "private_key": pay.wallet.private_key,
        "testnet": req.testnet,
        "created_at": time.time(),
    }

    network = "Base Sepolia (testnet)" if req.testnet else "Base (mainnet)"

    return CreateWalletResponse(
        api_key=api_key,
        address=pay.address,
        network=network,
    )


@app.get("/v1/balance", response_model=BalanceResponse)
def get_balance(auth: dict = Depends(get_api_key)):
    """Check wallet balance (USDC and ETH)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from agent_pay.client import AgentPay

    pay = AgentPay(private_key=auth["private_key"], testnet=auth.get("testnet", True))

    try:
        usdc = pay.balance("USDC")
        eth = pay.balance("ETH")
    except Exception as e:
        raise HTTPException(502, f"Blockchain RPC error: {str(e)}")

    network = "Base Sepolia" if auth.get("testnet", True) else "Base"

    return BalanceResponse(
        address=auth["address"],
        USDC=f"{usdc:.2f}",
        ETH=f"{eth:.6f}",
        network=network,
    )


@app.post("/v1/send")
def send_payment(req: SendRequest, auth: dict = Depends(get_api_key)):
    """Send a payment to another agent or address."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from agent_pay.client import AgentPay

    pay = AgentPay(private_key=auth["private_key"], testnet=auth.get("testnet", True))

    try:
        result = pay.send(to=req.to, amount=req.amount, currency=req.currency, memo=req.memo)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Transaction failed: {str(e)}")

    tx = {
        "status": result["status"],
        "hash": result["hash"],
        "from": auth["address"],
        "to": req.to,
        "amount": req.amount,
        "currency": req.currency,
        "memo": req.memo,
        "explorer": result["explorer"],
        "timestamp": time.time(),
    }
    TRANSACTIONS.append(tx)

    return tx


@app.post("/v1/escrow/create")
def create_escrow(req: EscrowCreateRequest, auth: dict = Depends(get_api_key)):
    """Create an escrow. Funds are held until released or timeout."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from agent_pay.client import AgentPay

    pay = AgentPay(private_key=auth["private_key"], testnet=auth.get("testnet", True))

    try:
        escrow = pay.escrow.create(
            recipient=req.recipient,
            amount=req.amount,
            currency=req.currency,
            condition=req.condition,
            timeout_seconds=req.timeout_seconds,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    ESCROWS[escrow.id] = {
        "pay_key": auth["private_key"],
        "testnet": auth.get("testnet", True),
    }

    return EscrowResponse(
        escrow_id=escrow.id,
        status=escrow.status.value,
        amount=escrow.amount,
        currency=escrow.currency,
        recipient=escrow.recipient,
        condition=escrow.condition,
    )


@app.post("/v1/escrow/release")
def release_escrow(req: EscrowReleaseRequest, auth: dict = Depends(get_api_key)):
    """Release escrowed funds to the recipient."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from agent_pay.client import AgentPay

    escrow_meta = ESCROWS.get(req.escrow_id)
    if not escrow_meta:
        raise HTTPException(404, f"Escrow not found: {req.escrow_id}")

    pay = AgentPay(private_key=escrow_meta["pay_key"], testnet=escrow_meta.get("testnet", True))

    try:
        result = pay.escrow.release(req.escrow_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Release failed: {str(e)}")

    return {
        "status": "released",
        "escrow_id": req.escrow_id,
        "hash": result["hash"],
        "explorer": result["explorer"],
    }


@app.get("/v1/transactions")
def list_transactions(auth: dict = Depends(get_api_key)):
    """List recent transactions for this wallet."""
    wallet_txs = [
        tx for tx in TRANSACTIONS
        if tx.get("from") == auth["address"] or tx.get("to") == auth["address"]
    ]
    return {"transactions": wallet_txs[-50:]}  # Last 50


@app.get("/v1/info")
def info():
    """Public info about this agent-pay node."""
    return {
        "protocol": "agent-pay",
        "version": "0.1.0",
        "supported_currencies": ["USDC", "ETH"],
        "supported_chains": ["Base L2", "Base Sepolia"],
        "fees": "< $0.001 per transaction",
        "docs": "https://github.com/agentpay-protocol/agent-pay",
        "pypi": "pip install agentpay-protocol",
        "npm_mcp": "npx @morpheus404world/agent-pay-mcp",
    }


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok", "wallets": len(API_KEYS), "transactions": len(TRANSACTIONS)}
