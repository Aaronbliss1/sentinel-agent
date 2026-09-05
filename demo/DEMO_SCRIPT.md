# 🎬 Sentinel — Demo Video Script (2:00) — Track A

**Goal:** Show judges an **AI agent with Binance Agent OS** that **trades BTC/BNB/ETH based on news sentiment** — via MCP, with risk, explainable.

**Record with:** Screen + voiceover. Keep to 120 seconds.

---

### 0:00-0:15 — Hook (Problem)
> "Crypto moves on NEWS faster than charts. By the time you read 'BlackRock ETF +$500M', BTC is already +3%. I'm building Sentinel — an AI agent on **Binance Agent OS** that *reads the news, scores sentiment, and trades* — before the candle closes."

Show: README + Binance Agent OS page (agent.binance.com/mcp/agentic)

### 0:15-0:35 — Setup (Agent OS in 15s)
> "Sentinel connects via the **official MCP Endpoint** `https://agent.binance.com/mcp/agentic` using **Streamable HTTP**. It trades inside an **Agentic virtual sub-account** — isolated, no withdrawals ever, confirm-before-execute. One command: `claude mcp add binance-mcp-server --transport http https://agent.binance.com/mcp/agentic`"

Show: Terminal running `claude mcp add ...` + Binance Sub-account Asset Management → Transfer (fund with $100)

### 0:35-0:70 — Live Workflow (THE CORE 35s)
> "Watch one full agentic cycle. Every 2 minutes: **(1) fetch news** → **(2) LLM sentiment 0-100** → **(3) confirm with RSI/MACD/Bollinger** → **(4) risk gate** → **(5) MCP place_order**."

Run: `python -m src.agent --once --mock-news` (or live news)

Narrate as logs scroll:
- "3 headlines: BlackRock ETF inflow… Score 78/100 BULLISH via Gemini"
- "BNB burn → 71 bullish, ETH neutral 52"
- "BTC technicals: RSI 62, MACD bullish, trend up"
- "Signal: BUY BTC with 0.85 confidence — Reason: sentiment 78 + RSI 62 + MACD bullish"
- "Risk: APPROVED, notional $65 < cap $100, slippage 2bps"
- "MCP DRY-RUN: BUY 0.001 BTCUSDT @ $65,234 — payload shows SHA-256 clientOrderId"

Show: Terminal logs + `mcp_payload` JSON highlighted

### 0:70-1:30 — Dashboard (Polish)
> "Every trade is explainable. Dashboard shows sentiment tape, 0-100 gauges, kline with BUY markers, portfolio, and trade log with *reason* — not just price."

Show: `streamlit run dashboard/app.py` → walk through:
- Sentiment gauges BTC 78 BUY, BNB 71 BUY, ETH 52 HOLD
- Chart with BUY triangle
- Trade log: BUY 0.001 BTC | DRY_RUN_EXECUTED | reason

### 1:30-1:50 — Safety Pillars (Judges love this)
> "Four institutional pillars: **Idempotency** (SHA-256 no double-fill), **Precision** (Decimal LOT_SIZE), **Risk Engine** (cap + slippage + daily loss kill), **Clock Sync** (+ backoff for 429/418). It blocked a 0.05 BTC $3,250 trade — cap $100. And RSI 74 blocked chasing."

Show: Quick code flash of `risk_manager.py` + blocked log

### 1:50-2:00 — Close + Call to Action
> "Paper → Live in one env var: `BINANCE_DRY_RUN=false`. Official stack: **binance-connector-python + MCP + Streamlit + free Gemini/VADER**. For the $60K Binance Agent OS Mini Hackathon — Track A. GitHub + survey in description. **Sentinel: Don't just read the news — trade it.**"

Show: GitHub repo + QR to https://binance.com/agent-os + tweet reply screenshot.

---

## Checklist Before Recording

- [ ] `.env` has `BINANCE_DRY_RUN=true` (safe)
- [ ] `pip install -r requirements.txt`
- [ ] Test: `python -m src.agent --once --mock-news` succeeds
- [ ] Test: `streamlit run dashboard/app.py` opens
- [ ] Fund Agentic sub-account with $50-100 for LIVE snippet (optional)
- [ ] OBS 1080p, mic check, hide API keys
- [ ] Keep to 1:55-2:05

## YouTube Title / Description

**Title:** Sentinel — AI Sentiment Trader on Binance Agent OS | MCP Agentic Trading for BTC/BNB/ETH (Hackathon Track A)

**Description:**
Sentinel is an autonomous AI agent built on Binance Agent OS (MCP: https://agent.binance.com/mcp/agentic) that trades BTC, BNB, ETH based on market news sentiment.
News → Gemini/VADER sentiment 0-100 → RSI/MACD/Bollinger confluence → Risk Gate → MCP place_order inside Agentic virtual sub-account.
Paper → Live in 1 env var. Built for Binance Agent OS Mini Hackathon ($60K, Track A $20K, Sep 4-8 2026).
GitHub: https://github.com/yourhandle/sentinel-agent
Stack: binance-connector-python, MCP Streamable HTTP, Gemini Free, Streamlit.
Demo: dry-run trading, explainable reasons, 4-pillar safety.
#Binance #AgentOS #MCP #Hackathon #AI #Trading
