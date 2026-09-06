# Sentinel — Binance Agent OS Sentiment Trader
### 🏆 Submission for Binance Agent OS Mini Hackathon — Track A ($20K)

> **An autonomous AI agent that determines WHEN to buy/sell BTC, BNB, and ETH based on real-time market news & sentiment, executed via Binance Agent OS.**

**Tagline:** *Don't just read the news — trade it. Before the candle closes.*

**MCP Endpoint:** `https://agent.binance.com/mcp/agentic` (Streamable HTTP)  
**Deadline:** Sept 8, 2026 23:59 UTC  
**Track:** A — Build an AI Agent with Agent OS  

---

## 🎯 The Problem
Retail traders miss moves because **sentiment shifts faster than charts**. By the time you read "BlackRock Bitcoin ETF inflow +$500M", BTC is already +3%. Existing bots are either:
- Purely technical (ignore news)
- Purely sentiment (ignore risk)
- Require coding, API keys, and devops hell

## 💡 The Solution — Sentinel
Sentinel is an **agentic workflow** that fuses **3 signals** into 1 disciplined trader:

```
[News Ingestion] → [LLM Sentiment Scoring] → [Technical Confluence] → [Risk Gate] → [Binance Agent OS Execution]
        │                       │                         │                   │                    │
   CryptoPanic          Gemini Flash / VADER         RSI + MACD + BB     Notional Cap      MCP Place Order
   Binance News         (0-100 bullish score)        Trend Filter        Slippage Check     (Dry-Run / Live)
   RSS Feeds            Per-coin: BTC/BNB/ETH        Volatility Filter   Daily Loss Limit
```

### 3 Trading Workflows (Agentic)
1.  **News-Sentinel Workflow:** Every 2 mins, fetch headlines for BTC/BNB/ETH → score each headline 0-100 → aggregate weighted sentiment → emit BUY/SELL/HOLD.
2.  **Tech-Confluence Workflow:** Confirms sentiment with RSI, MACD, Bollinger on 15m/1h klines. No momentum chasing.
3.  **Risk-Captain Workflow:** Position sizing (1-3% per trade), 0.5% slippage collar, $100 notional cap (configurable), daily -3% kill switch.

---

##  Key Features
- ✅ **Binance Agent OS Native:** Connects via official MCP over Streamable HTTP. Uses `get_price`, `get_order_book`, `get_klines`, `get_account_balance`, `place_order` — all through Agent OS permissions. No raw API key handling in agent logic.
- ✅ **Institutional Safety Pillars (like reference winner):**
    - Deterministic Idempotency (SHA-256 clientOrderId → no double fills on retry)
    - Zero-Float Precision (Decimal math, respects LOT_SIZE / TICK_SIZE)
    - Pre-Trade Risk Engine (cap, slippage, exposure)
    - Clock Sync + Backoff (protects against 1021/429)
- ✅ **Explainable Trades:** Every order includes `reason: "BTC sentiment 78/100 (3 bullish headlines) + RSI 62 + MACD bullish → BUY"` — judges can audit.
- 

## Architecture
```
                  ┌─────────────────────────────────┐
                  │      User (Cursor/Claude)       │
                  │   "Trade BTC sentiment >70"     │
                  └──────────────┬──────────────────┘
                                 │ MCP Streamable HTTP
                  ┌──────────────▼──────────────────┐
                  │   Binance Agent OS MCP Server   │  https://agent.binance.com/mcp/agentic
                  │  - Market Data (no auth)        │
                  │  - Account (read-only)          │
                  │  - Trading (with confirm)       │
                  └──────────────┬──────────────────┘
                                 │
                  ┌──────────────▼──────────────────┐
                  │      SENTINEL AGENT (Python)    │
                  │  ┌──────────┐  ┌──────────────┐ │
                  │  │ News     │→ │ Sentiment    │ │
                  │  │ Fetcher  │  │ Analyzer     │ │
                  │  └──────────┘  └──────┬───────┘ │
                  │                      ▼          │
                  │               ┌──────────────┐  │
                  │               │ Strategy     │  │
                  │               │ Engine       │  │
                  │               └──────┬───────┘  │
                  │                      ▼          │
                  │               ┌──────────────┐  │
                  │               │ Risk Manager │  │
                  │               └──────┬───────┘  │
                  └──────────────────────┼──────────┘
                                         │ place_order (via MCP)
                              ┌──────────▼──────────┐
                              │ Binance SPOT (BTC/  │
                              │  BNB/ETH) Agentic   │
                              │ Sub-Account         │
                              └─────────────────────┘
```

##  Quickstart (2 Minutes)

### 1. Install
```bash
git clone https://github.com/Aaronbliss1/sentinel-agent.git
cd sentinel-agent
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env:
BINANCE_API_KEY=your_agentic_subaccount_key
BINANCE_API_SECRET=your_secret
BINANCE_DRY_RUN=true  # keep true for hackathon demo
GOOGLE_API_KEY=your_gemini_free_key  # optional, falls back to VADER
```

### 3. Run Agent (Headless Workflow)
```bash
# Paper mode (no orders placed at all):
python -m src.agent --once --mock-news

# TESTNET trading (free testnet keys from https://testnet.binance.vision):
python -m src.agent --continuous --testnet

# Continuous live loop:
python -m src.agent --continuous
```

### 4. Run Live Dashboard
```bash
# Open http://localhost:8501
```

### 5. Run MCP Demo (Talks to Agent OS)
```bash
python -m src.mcp_client.demo --show-payload
```

### 6. Run Backtest
```bash
python -m src.strategy.backtest --coin BTC --days 30
```

## 🔌 Binance Agent OS MCP Integration

We implement the **official MCP spec**:
- **Transport:** Streamable HTTP to `https://agent.binance.com/mcp/agentic`
- **Client:** `mcp` Python SDK + `httpx`
- **Tools Wrapped:**
    - `get_price(symbol)` → `BTCUSDT`, `BNBUSDT`, `ETHUSDT`
    - `get_order_book(symbol, limit=20)`
    - `get_klines(symbol, interval="1m"|"15m"|"1h", limit=100)`
    - `get_24hr_ticker(symbol)`
    - `get_account_balance()` (agentic sub-account)
    - `place_order(symbol, side, type="MARKET", quantity, clientOrderId)` with idempotency

> **Security:** Agent never holds main account keys. Only Agentic sub-account with isolated balance. Withdrawals disabled by design. All orders go through Risk Engine first.

Example MCP call (via our client):
```python
from src.mcp_client.binance_mcp import BinanceMCPClient

async with BinanceMCPClient(dry_run=True) as client:
    price = await client.get_price("BTCUSDT")
    sentiment = await analyzer.score("BlackRock ETF inflow $500M")
    if sentiment > 70:
        await client.place_order("BTCUSDT", "BUY", quantity=0.001, reason=sentiment)
```



- **Primary:** Google Gemini 2.0 Flash (`gemini-1.5-flash` free tier) — 5-line prompt scoring 0-100
- **Fallback:** `vaderSentiment` + keyword boosters (`ETF`, `hack`, `SEC lawsuit`, etc.) — zero API cost, offline
- **Sources:**
    - CryptoPanic API (free tier)
    - Binance News RSS
    - CoinDesk / CoinTelegraph RSS (optional)
- **Aggregation:** Weighted by recency + source credibility. `BTC: 78/100 bullish (3 headlines, avg 2m ago)`


## 📈 Strategy Logic

```
IF sentiment >= 70 AND RSI < 70 AND MACD bullish → BUY (1-3% position)
IF sentiment <= 30 AND RSI > 30 AND MACD bearish → SELL (or close long)
IF 30 < sentiment < 70 → HOLD
IF sentiment 70+ BUT RSI > 75 → HOLD (overbought filter)
```

Position sizing via Kelly_fraction / volatility. Stop-loss 1.5% trailing, take-profit 3%.

## 📊 Dashboard Preview
- Live sentiment tape with headline + score + coin tags
- Signal strength gauges (0-100)
- Kline charts with buy/sell markers
- Portfolio & P&L (paper)
- Trade log with `reason` + MCP payload


## 🚀 Deploy (Vercel — dashboard + live endpoint)

The deployed artifact is the **dashboard** (`index.html`) plus the
**`/api/sentiment`** Python function:

1. Push this repo to GitHub (already public).
2. In Vercel: **Add New → Project** → import `sentinel-agent`. No build
   command needed — Vercel auto-detects the Python function in `api/`.
3. Deploy. You get:
   - `https://<app>.vercel.app/` → Sentinel dashboard (live data)
   - `https://<app>.vercel.app/api/sentiment` → live prices + scored headlines JSON

Notes:
- Prices come from CoinGecko (Binance 451s US servers, incl. testnet);
  testnet **execution** runs in the Python agent from a non-US location.
- Optional Vercel env var `GOOGLE_API_KEY` → headlines scored by Gemini
  (batched) instead of VADER.

## 🧪 Tests & Reliability
```bash
pytest -q                                  # unit tests (risk engine + sentiment)
python -m src.mcp_client.demo --show-payload  # 4 pillars + MCP payload
python -m src.agent --panic-close           # emergency stop (cancels open orders)
```

##  Project Structure
```
sentinel-agent/
├── api/
│   └── sentiment.py            # Vercel /api/sentiment (stdlib-only)
├── src/
│   ├── agent.py                # Orchestrator (the AI agent)
│   ├── mcp_client/
│   │   ├── binance_mcp.py      # Agent OS MCP client (+ paper fallback, panic-close)
│   │   ├── binance_connector_example.py  # Official SDK example
│   │   └── demo.py             # 4-pillar demo
│   ├── sentiment/
│   │   ├── news_fetcher.py     # CryptoPanic / RSS / mock
│   │   ├── analyzer.py         # Gemini → Groq → VADER cascade
│   │   └── aggregator.py
│   └── strategy/
│       ├── indicators.py       # RSI/MACD/BB
│       ├── signal_generator.py
│       ├── risk_manager.py     # 4 pillars
│       └── backtest.py
├── dashboard/
│   └── app.py                  # Streamlit (local/dev)
├── index.html                  # Deployed static dashboard (Vercel)
├── demo/
│   ├── DEMO_SCRIPT.md
│   └── video_checklist.md
├── requirements.txt            # local/dev deps (Vercel keeps bundle tiny)
├── .env.example
├── vercel.json
└── README.md
```



**why sentinel?:**
- [x] Uses **Agent OS** (not just Binance API)
- [x] MCP Streamable HTTP to `agent.binance.com/mcp/agentic`
- [x] Agentic sub-account isolation
- [x] Clear agentic workflow (news→sentiment→trade)
- [x] Real market data + trading capability
  

**Differentiator vs other bots:** Most hackathon bots trade on RSI alone. Sentinel trades *narratives* — the meta-game of crypto. And it explains *why* in plain English.



## License
MIT — Built for Binance Agent OS Mini Hackathon 2026

---
**Built with ❤️ for the agentic crypto future.** *September 2026**
