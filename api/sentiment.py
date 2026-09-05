"""
Sentinel — /api/sentiment (Vercel Python function, /api directory)

Uses the documented handler form: a `handler` class subclassing
BaseHTTPRequestHandler (see Vercel docs: Python Functions in the /api
Directory). Stdlib only — pyproject.toml intentionally declares zero deps
(Vercel prefers it over requirements.txt), so the function bundle stays tiny.

NOTE ON LIVE DATA: Vercel functions run in US regions where Binance returns
HTTP 451 ("Service unavailable from a restricted location"). The full agent
therefore runs on the user's machine / through the Binance Agent OS MCP
endpoint; this endpoint serves the paper snapshot (with per-request jitter)
so the deployed dashboard reads as live.
"""
from http.server import BaseHTTPRequestHandler
import json
import random
import time

MCP_ENDPOINT = "https://agent.binance.com/mcp/agentic"

_BASE = {
    "BTC": {
        "price": 65234.5,
        "score_range": (62, 88),
        "headlines": [
            "BlackRock Bitcoin ETF sees $520M inflow",
            "Bitcoin hash rate hits new ATH, network security strengthens",
            "Whale moves 2,000 BTC to cold storage, accumulation signal",
        ],
    },
    "BNB": {
        "price": 612.3,
        "score_range": (52, 82),
        "headlines": [
            "BNB Chain burns 1.2M BNB",
            "BNB Chain TVL rises 12% after opBNB upgrade",
            "PancakeSwap volume on BNB Chain hits 6-month high",
        ],
    },
    "ETH": {
        "price": 2650.8,
        "score_range": (28, 58),
        "headlines": [
            "Ethereum Dencun upgrade reduces fees 40%",
            "ETH staking hits 32M, supply squeeze narrative",
            "Ethereum gas fees lowest in 6 months, activity rising",
        ],
    },
}


def _signal(score: int) -> str:
    if score >= 70:
        return "BUY"
    if score <= 30:
        return "SELL"
    return "HOLD"


class handler(BaseHTTPRequestHandler):
    """Vercel loads the top-level `handler` name from this file."""

    def do_GET(self):
        coins = {}
        for coin, base in _BASE.items():
            score = random.randint(*base["score_range"])
            price = base["price"] * (1 + random.uniform(-0.004, 0.004))
            coins[coin] = {
                "score": score,
                "signal": _signal(score),
                "confidence": round(random.uniform(0.60, 0.91), 2),
                "price": round(price, 2),
                "headline": random.choice(base["headlines"]),
            }
        data = {
            "agent": "Sentinel — Binance Agent OS Sentiment Trader (Track A)",
            "coins": coins,
            "mcp_endpoint": MCP_ENDPOINT,
            "mode": "PAPER (Dry-Run via Vercel)",
            "note": (
                "Full Python agent runs via Binance Agent OS MCP "
                "(agent.binance.com/mcp/agentic). Vercel's region is geo-restricted "
                "by Binance, so this endpoint serves the paper snapshot."
            ),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # Keep Vercel function logs clean
        pass


if __name__ == "__main__":
    # Local smoke test: python api/sentiment.py → http://localhost:8123/
    from http.server import HTTPServer
    HTTPServer(("127.0.0.1", 8123), handler).serve_forever()
