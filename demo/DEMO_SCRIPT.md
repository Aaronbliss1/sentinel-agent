# 🎬 Sentinel — Demo Video Script (2:00) — Track A

**Goal:** Show judges an **AI agent on Binance Agent OS** that **trades BTC/BNB/ETH from live news sentiment** — real data, real testnet execution, explainable signals.

**Record with:** Screen + voiceover. Keep to 120 seconds.

**The two panels you'll have open:**
1. **Terminal** — `python -m src.agent --continuous --testnet` (live cycles every 2 min)
2. **Vercel dashboard** — your deployed URL (live prices every 15s, sentiment + headlines every 60s, candlestick chart, signal, event log)

---

### 0:00-0:15 — Hook (Problem)
> "Crypto moves on NEWS faster than charts. By the time you read 'BlackRock ETF +$500M', BTC is already +3%. This is Sentinel — an AI agent on **Binance Agent OS** that *reads the news, scores it, and trades* — before the candle closes."

Show: GitHub repo front page + Binance Agent OS (agent.binance.com)

### 0:15-0:35 — Setup (Agent OS in 15s)
> "Sentinel speaks to Binance the official way — **binance-connector-python** over **MCP Streamable HTTP** (`https://agent.binance.com/mcp/agentic`), executing on the **Binance Spot Testnet** with my real test account. One command to run it:"

Show: terminal typing `python -m src.agent --continuous --testnet` → banner:
`Mode: 🔵 TESTNET (testnet.binance.vision) | Coins: BTC, BNB, ETH`

### 0:35-1:10 — Live Workflow (THE CORE 35s)
Narrate as the real cycle scrolls:
- "**(1) Live news** — 3 fresh headlines from CoinDesk and Cointelegraph, filtered per coin"
- "**(2) Gemini scores each 0–100** in one batch call — 'Bitcoin below 80K' → 25 BEARISH, 'Double Three rally' → 78 BULLISH"
- "**(3) My real testnet account** — $10,000 USDT on testnet"
- "**(4) Technicals confirm** — RSI, MACD, Bollinger, trend per coin"
- "**(5) The signal, with its reasoning** — 'BUY ETH: sentiment 78 + RSI 60 + MACD bullish' … or the safety pillar catching it: 'RSI 78 overbought — HOLD, don't chase'"
- "**(6) Order executed on testnet** — see it filled"

Show: terminal logs. If a fill happens, cut to **testnet.binance.vision → My Orders** showing the filled order.

### 1:10-1:35 — Dashboard (Polish)
> "Every decision is explainable — and live. The dashboard pulls real prices every 15 seconds, real headlines scored by Gemini, a live candlestick chart, and the current signal with its reason. No mock data anywhere."

Show: Vercel dashboard — prices ticking, sentiment gauges, chart, event log appending.

### 1:35-1:50 — Safety Pillars (Judges love this)
> "Four institutional pillars: **idempotency** — SHA-256 client order IDs, no double-fills. **Precision** — Decimal LOT_SIZE. **Risk engine** — position cap + slippage guard. And the **confluence filter** — a BULLISH headline alone never trades; watch it block an overbought RSI 78 in real time. It degrades gracefully too: geo-blocked networks get clean error states, not crashes."

Show: quick flash of the RSI-block log line + `risk_manager.py`

### 1:50-2:00 — Close + CTA
> "Testnet today, mainnet is one env var away. Official stack: **binance-connector-python + MCP + Gemini free tier**. Built for the Binance Agent OS Mini Hackathon — Track A. GitHub and survey in the description. **Sentinel: don't just read the news — trade it.**"

Show: GitHub repo + agent.binance.com

---

## Checklist Before Recording
- [ ] `.env` in place (testnet keys + Gemini key) — **never show the .env file on screen**
- [ ] `python -m src.agent --continuous --testnet` running, at least 1 clean cycle visible
- [ ] Vercel dashboard open on your phone/browser — prices visibly ticking ("updated Xs ago" counter)
- [ ] testnet.binance.vision open in a 3rd tab (for the "My Orders" proof shot)
- [ ] OBS 1080p, mic check, ~5 min of buffer (you can cut to 2:00 in edit)
- [ ] If a fill happens: zoom on the order line + My Orders page

## If no order fills before recording
Record the **terminal cycle + dashboard** anyway (it's the strongest 60% of the video), then keep the agent running in the background; if a fill lands, record a 10-second insert of the terminal + My Orders page.

## YouTube Title / Description

**Title:** Sentinel — AI Sentiment Trader on Binance Agent OS | MCP Agentic Trading for BTC/BNB/ETH (Hackathon Track A)

**Description:**
Sentinel is an autonomous AI agent built on Binance Agent OS (MCP: https://agent.binance.com/mcp/agentic) that trades BTC, BNB, ETH from live market news sentiment.
Live RSS news → Gemini sentiment 0–100 → RSI/MACD/Bollinger confluence → Risk Gate → order execution on Binance Spot Testnet with my real test account.
Testnet → mainnet in 1 env var. Built for the Binance Agent OS Mini Hackathon ($60K, Track A $20K, Sep 4–8 2026).
GitHub: https://github.com/Aaronbliss1/sentinel-agent
Stack: binance-connector-python, MCP Streamable HTTP, Gemini free tier, live Vercel dashboard.
#Binance #AgentOS #MCP #Hackathon #AI #Trading
