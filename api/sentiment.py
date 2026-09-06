"""
Sentinel — /api/sentiment (Vercel Python function, /api directory)

HANDLER FORM: `handler` class subclassing BaseHTTPRequestHandler
(entrypoint declared in pyproject.toml: [tool.vercel] entrypoint =
"api.sentiment:handler").

LIVE DATA (no API keys required):
  - Prices: CoinGecko public API (api.binance.com returns 451 from
    Vercel's US region, so prices come from CoinGecko — same market,
    same underlying assets).
  - Klines: CoinGecko 1-day 5m points resampled to 15m candles (BTC chart).
  - News:   live RSS (Cointelegraph / CoinDesk / Cryptonews), classified
    per coin, scored with VADER + crypto lexicon (mirrors the local
    agent's offline path).
  - Optional LLM: if GOOGLE_API_KEY is set as a Vercel env var, one batch
    Gemini call (gemini-flash-lite-latest) scores all headlines and takes
    precedence over VADER.

TRADING: executes on Binance TESTNET via the local Python agent
(`python -m src.agent --testnet`), which runs from a non-US location.
Vercel (US) is geo-blocked from testnet, so this endpoint never trades —
it only serves market + sentiment data.

Routing:
  - .../sentiment        -> live JSON payload
  - / , /dashboard.html  -> static dashboard (safety net if the function
                            intercepts all routes; CDN normally serves it)
  - anything else        -> 404
"""
from http.server import BaseHTTPRequestHandler
import json
import math
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

MCP_ENDPOINT = "https://agent.binance.com/mcp/agentic"

COINGECKO_IDS = {"BTC": "bitcoin", "BNB": "binancecoin", "ETH": "ethereum"}
COINS = ["BTC", "BNB", "ETH"]

# Word-boundary patterns for short tokens (so "Tether" doesn't match "eth")
COIN_KEYWORDS = {
    "BTC": [r"bitcoin", r"\bbtc\b", r"saylor", r"blackrock", r"microstrategy", r"\betf\b"],
    "BNB": [r"\bbnb\b", r"binance", r"\bbcs\b", r"pancakeswap", r"opbnb"],
    "ETH": [r"ethereum", r"\beth\b", r"\bether\b", r"vitalik", r"staking", r"\beip\d*", r"dencun"],
}

FEEDS = [
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("CoinDesk", "https://coindesk.com/arc/outboundfeeds/rss/"),
    ("Cryptonews", "https://cryptonews.com/news/feed/"),
]

# Same boosters as src/sentiment/analyzer.py (kept in sync)
BULLISH = ["inflow", "etf", "accumulation", "ath", "upgrade", "burn", "grant", "adoption", "buy", "buys", "surge", "hits new high", "expands", "reduces fees", "record", "largest"]
BEARISH = ["hack", "sell pressure", "outflow", "delay", "sec", "lawsuit", "investigate", "fud", "dump", "leverage overextended", "repayments", "fears"]

# Static fallback (offline preview / total network failure)
FALLBACK = {
    "BTC": {"score": 78, "signal": "BUY", "confidence": 0.85, "count": 3,
            "top_headline": "BlackRock Bitcoin ETF sees $520M inflow, largest in 3 months",
            "headlines": [], "price": 65234.5, "change_24h": 1.84},
    "BNB": {"score": 71, "signal": "BUY", "confidence": 0.67, "count": 2,
            "top_headline": "BNB Chain burns 1.2M BNB, supply reduction bullish",
            "headlines": [], "price": 612.3, "change_24h": 0.92},
    "ETH": {"score": 52, "signal": "HOLD", "confidence": 0.41, "count": 2,
            "top_headline": "Ethereum Dencun upgrade reduces fees 40%, L2s surge",
            "headlines": [], "price": 2650.8, "change_24h": -0.31},
}

# ---------------- tiny in-memory cache (Fluid compute warm instances) ----
_CACHE = {"ts": 0, "payload": None}
CACHE_TTL = 45  # seconds


# ---------------- low-level helpers -------------------------------------
def _http_get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Sentinel/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _age_mins(pub_date: str) -> int:
    try:
        dt = parsedate_to_datetime(pub_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        mins = (datetime.now(timezone.utc) - dt).total_seconds() / 60
        return max(1, int(mins))
    except Exception:
        return 45


def _classify(title: str):
    # No default tag: unrelated coins (XRP, Tether, ...) must not pollute
    # BTC/BNB/ETH sentiment.
    t = title.lower()
    return [c for c, pats in COIN_KEYWORDS.items() if any(re.search(p, t) for p in pats)]


# ---------------- data sources ------------------------------------------
def fetch_prices():
    url = ("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,binancecoin,ethereum"
           "&vs_currencies=usd&include_24hr_change=true")
    j = json.loads(_http_get(url, timeout=10))
    out = {}
    for coin, gid in COINGECKO_IDS.items():
        out[coin] = {
            "price": round(float(j[gid]["usd"]), 2),
            "change_24h": round(float(j[gid].get("usd_24h_change") or 0.0), 2),
        }
    return out


def fetch_btc_candles(limit=48):
    """CoinGecko 1-day 5m points -> 15m OHLC candles for the BTC chart."""
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1"
    j = json.loads(_http_get(url, timeout=12))
    points = j.get("prices") or []
    if len(points) < 20:
        return []
    buckets = {}
    for ts, p in points:
        b = int(ts // (15 * 60 * 1000))
        c = buckets.get(b)
        if c is None:
            buckets[b] = {"o": p, "h": p, "l": p, "c": p}
        else:
            c["h"] = max(c["h"], p)
            c["l"] = min(c["l"], p)
            c["c"] = p
    out = []
    for b, c in list(buckets.items())[-limit:]:
        out.append([b * 15 * 60 * 1000, round(c["o"], 2), round(c["h"], 2),
                    round(c["l"], 2), round(c["c"], 2)])
    return out


def fetch_headlines():
    items = []
    for source, url in FEEDS:
        try:
            root = ET.fromstring(_http_get(url, timeout=10))
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                if not title:
                    continue
                items.append({
                    "title": title,
                    "source": source,
                    "age_mins": _age_mins((item.findtext("pubDate") or "").strip()),
                    "coins": _classify(title),
                })
        except Exception:
            continue
    seen, out = set(), []
    for it in items:
        key = it["title"].lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out[:30]


# ---------------- sentiment ----------------------------------------------
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER = SentimentIntensityAnalyzer()
except Exception:
    _VADER = None


def score_headline(title: str):
    t = title.lower()
    boost = 7 * sum(1 for k in BULLISH if k in t) - 7 * sum(1 for k in BEARISH if k in t)
    if _VADER is not None:
        compound = _VADER.polarity_scores(title)["compound"]
        base = (compound + 1) * 50
        conf = min(0.95, abs(compound) + 0.35)
        model = "vader+lexicon"
    else:
        base, conf, model = 50.0, 0.4, "lexicon"
    score = max(0, min(100, int(base + boost)))
    label = "BULLISH" if score >= 60 else "BEARISH" if score <= 40 else "NEUTRAL"
    return score, round(conf, 2), label, model


def gemini_batch(items):
    """Optional: one Gemini call scores all headlines (needs GOOGLE_API_KEY)."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key or not items:
        return {}
    lines = "\n".join(
        f'{i+1}. [{",".join(it["coins"])}] "{it["title"]}"' for i, it in enumerate(items))
    prompt = (
        "Score EACH crypto headline 0-100 bullish (0=bearish, 50=neutral, 100=bullish). "
        "Headlines:\n" + lines +
        '\nReply ONLY as a JSON array in order: [{"score":85,"confidence":0.9,"label":"BULLISH"}, ...]')
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent"
        f"?key={key}",
        data=body, headers={"Content-Type": "application/json", "User-Agent": "Sentinel/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.loads(r.read())
        text = j["candidates"][0]["content"]["parts"][0]["text"].strip()
        m = re.search(r"\[.*\]", text, re.DOTALL)
        arr = json.loads(m.group(0))
        return {items[i]["title"]: arr[i] for i in range(min(len(items), len(arr)))}
    except Exception:
        return {}


def build_payload():
    prices = {}
    try:
        prices = fetch_prices()
    except Exception:
        pass

    chart = []
    try:
        chart = fetch_btc_candles()
    except Exception:
        pass

    headlines = []
    try:
        headlines = fetch_headlines()
    except Exception:
        pass

    model_used = "vader+lexicon"
    if headlines:
        gmap = gemini_batch(headlines)
        if gmap:
            model_used = "gemini-flash-lite (batch)"

    coins = {}
    for coin in COINS:
        rel = [h for h in headlines if coin in h["coins"]]
        if rel:
            total_w = total_s = 0.0
            confs = []
            details = []
            for h in rel[:6]:
                g = gmap.get(h["title"])
                if g:
                    s = max(0, min(100, int(g.get("score", 50))))
                    c = float(g.get("confidence", 0.7))
                else:
                    s, c, _, _ = score_headline(h["title"])
                w = c * math.exp(-h["age_mins"] / 60.0)
                total_w += w
                total_s += s * w
                confs.append(c)
                details.append({"title": h["title"], "score": s, "source": h["source"],
                                "age_mins": h["age_mins"]})
            avg = round(total_s / total_w, 1) if total_w else 50
            conf = round(sum(confs) / len(confs), 2)
            details.sort(key=lambda d: abs(d["score"] - 50), reverse=True)
            top_headline = details[0]["title"] if details else ""
        else:
            avg, conf, details = 50, 0.0, []
            top_headline = (f"No live {coin} headlines in the last feed cycle — "
                            "re-checking in a minute")

        signal = "BUY" if avg >= 70 else "SELL" if avg <= 30 else "HOLD"
        fb = FALLBACK[coin]
        coins[coin] = {
            "score": int(round(avg)),
            "signal": signal,
            "confidence": conf,
            "count": len(details),
            "model": model_used if rel else "live (no matches yet)",
            "top_headline": top_headline,
            "headlines": details[:3],
            "price": prices.get(coin, {}).get("price", fb["price"]),
            "change_24h": prices.get(coin, {}).get("change_24h", fb["change_24h"]),
        }

    return {
        "agent": "Sentinel — agentic sentiment trader",
        "mcp_endpoint": MCP_ENDPOINT,
        "mode": "testnet",
        "sources": {
            "prices": "coingecko (live)" if prices else "offline fallback",
            "news": f"{len(headlines)} live headlines" if headlines else "offline fallback",
            "chart": "coingecko 15m candles (live)" if chart else "offline fallback",
            "sentiment": model_used,
        },
        "coins": coins,
        "chart": {"symbol": "BTC/USD", "interval": "15m", "candles": chart},
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def get_payload():
    now = time.time()
    if _CACHE["payload"] is not None and now - _CACHE["ts"] < CACHE_TTL:
        return _CACHE["payload"]
    payload = build_payload()
    _CACHE.update(ts=now, payload=payload)
    return payload


# ---------------- HTTP ----------------------------------------------------
_DASHBOARD_PATHS = {"/", "/dashboard", "/dashboard.html", "/index", "/index.html"}


class handler(BaseHTTPRequestHandler):
    """Vercel loads the top-level `handler` name (see [tool.vercel])."""

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if not path:
            path = "/"
        if path.endswith("/sentiment"):
            self._send_json()
        elif path in _DASHBOARD_PATHS:
            self._send_dashboard()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

    def _send_json(self):
        body = json.dumps(get_payload()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_dashboard(self):
        candidates = [
            "dashboard.html",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dashboard.html"),
        ]
        body = b""
        for cand in candidates:
            try:
                with open(cand, "rb") as f:
                    body = f.read()
                break
            except OSError:
                continue
        if body:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"dashboard.html not found")

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    from http.server import HTTPServer
    HTTPServer(("127.0.0.1", 8123), handler).serve_forever()
