# ✅ Submission — Binance Agent OS Mini Hackathon (Track A)

**Project:** Sentinel — Binance Agent OS Sentiment Trader
**Deadline:** Sept 8, 2026 23:59 UTC

## 1. GitHub (done)
- Repo (public): https://github.com/Aaronbliss1/sentinel-agent

## 2. Deployed dashboard (Vercel)
- Dashboard URL: https://sentinelagent1.vercel.app/

## 3. Demo video
- Recorded a demo and posted on x ()

## 4. Verify (reproduce)
```bash
pip install -r requirements.txt

pytest -q                                  # 5 unit tests pass

# Live agent (real news → Gemini → technicals → risk → order)
cp .env.example .env      # add testnet keys + GOOGLE_API_KEY for full path
python -m src.agent --once --testnet       # one live cycle
python -m src.agent --continuous --testnet # 24/7 loop

# Proof: exchange's own record of testnet balances + fills
python demo/verify_fill.py
```
The Vercel dashboard works with **zero keys** (public data + VADER); with `GOOGLE_API_KEY` it scores via Gemini.


