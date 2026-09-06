# 🎙️ Sentinel — Full Voiceover Script (~2:30, trim to 2:00)

**How to use:** read the **NARRATION** lines aloud verbatim. **SHOW** lines tell you what's on screen at that moment. ⏱️ = rough cumulative timestamp. [TRIM] marks optional cuts to hit exactly 2:00.

**Pace:** relaxed, ~150 words/min. Total ≈ 380 words → ~2:30. Cut the two [TRIM] blocks (~25s) for a 2:00 version.

**Mic tips:** smile on the hook line, slow down for numbers ("twenty-five", "eighty-four percent"), pause a beat before "and the order executes."

---

### ⏱️ 0:00 — HOOK
**SHOW:** GitHub repo front page, scrolling slowly
> "Crypto moves on NEWS faster than charts. By the time you read — 'BlackRock ETF, plus five hundred million dollars' — Bitcoin is already up three percent. This is **Sentinel** — an AI agent built on **Binance Agent OS** that reads the news, scores it, and trades — before the candle closes."

### ⏱️ 0:20 — WHAT IT IS
**SHOW:** terminal banner (Mode: TESTNET) + the architecture diagram from the README
> "Sentinel is an autonomous trading agent. Every two minutes it pulls **live crypto news**, uses a **large language model** to score each headline from zero to one hundred, and fuses that with **RSI, MACD, and Bollinger Bands** into one disciplined decision: buy, sell, or hold. Then it **executes the order on Binance Spot Testnet** — with a real test account. And every decision comes with a reason you can audit."

### ⏱️ 0:55 — LIVE CYCLE (the core — don't trim this)
**SHOW:** the real terminal cycle scrolling (news → Gemini scores → account → technicals → signal → order), then cut to Vercel dashboard
> "Watch one **live** cycle. Step one: fresh headlines from CoinDesk and Cointelegraph. Step two: Gemini scores each — 'Bitcoin below eighty thousand' comes in at **twenty-five: bearish**. Step three: my real testnet account — ten thousand dollars of test USDT. Step four: the technicals confirm — RSI fifty-seven, MACD bullish, trend up. Step five: the signal — **buy Bitcoin, eighty-four percent confidence** — and the order executes. [beat] Now watch the safety layer: the same model says ETH is bullish at seventy-eight — but the RSI is seventy-eight: **overbought**. So Sentinel **refuses the trade**. It never chases."

### ⏱️ 1:35 — SAFETY
**SHOW:** zoom on the RSI-block log line, quick flash of risk_manager.py
> "Four pillars, the way institutions do it: SHA-256 order IDs so nothing ever double-fills; Decimal precision that respects lot sizes; a **risk engine** with position caps and slippage guards; and the confluence filter you just watched. [TRIM: cut from 'It degrades' —] It degrades gracefully too: blocked networks and rate limits produce clean error states, never crashes."

### ⏱️ 1:55 — HOW ANYONE USES IT
**SHOW:** README quickstart section, then the three commands typed in terminal (clone / keys / run)
> "And anyone can run this in five minutes. Step one: clone the repo. Step two: two **free** keys — a Binance **Spot Testnet** key, and a **Gemini** key from Google AI Studio. Step three: one command — **python -m src.agent --continuous --testnet**. That's it. No devops, no real money at risk."

### ⏱️ 2:15 — ANY AI
**SHOW:** the MCP endpoint URL on screen + `claude mcp add binance-mcp-server --transport http https://agent.binance.com/mcp/agentic`
> "The brain is **pluggable** — it ships with a Gemini, Groq, and VADER fallback chain, so it runs on any LLM, or fully offline. [TRIM: cut from 'And the connection' —] And the connection to Binance is **MCP** — the open standard that **Claude, ChatGPT, Codex**, and Cursor all speak. The same endpoint, any client."

### ⏱️ 2:35 — CLOSE
**SHOW:** GitHub repo + agent.binance.com, hold 3s
> "Testnet today. Mainnet is one environment variable away. Built for the **Binance Agent OS Mini Hackathon** — GitHub and survey link in the description. **Sentinel: don't just read the news — trade it.**"

---

## B-roll checklist while recording
- [ ] Terminal: one full live cycle (news → scores → technicals → signal)
- [ ] If a fill lands mid-recording: zoom on the order line, then `python demo/verify_fill.py` output (exchange's fill record + balances)
- [ ] Vercel dashboard: 30s of it running (prices tick, "updated Xs ago" counts)
- [ ] README architecture diagram (screenshot is fine)
- [ ] risk_manager.py flash (2–3s max)
- [ ] README quickstart / the 3 onboarding commands
- [ ] `claude mcp add ...` one-liner on screen (3s)
- [ ] NEVER show the `.env` file or its contents

## Editing notes
- Total 2:30 → cut the two [TRIM] sentences for 2:00
- If no fill happened during recording: use the `verify_fill.py` output (the earlier real fill) as the "exchange record" shot — it's genuine
- Background music: subtle, stop during the "order executes" beat for impact
