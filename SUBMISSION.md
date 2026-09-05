# ✅ Submission — Binance Agent OS Mini Hackathon (Track A)

**Project:** Sentinel — Binance Agent OS Sentiment Trader
**Deadline:** Sept 8, 2026 23:59 UTC

## 1. GitHub (done)
- Repo (public): https://github.com/Aaronbliss1/sentinel-agent

## 2. Deployed dashboard (Vercel)
- Dashboard URL: https://<your-app>.vercel.app  ← **update with real URL**
- Live endpoint: https://<your-app>.vercel.app/api/sentiment

## 3. Demo video
- Record following `demo/DEMO_SCRIPT.md` (checklist: `demo/video_checklist.md`)
- Upload to X and reply with your submission per the hackathon rules.


## 4. Verify
```bash
pip install -r requirements.txt
cp .env.example .env      # optional — works without any keys (paper + VADER)

pytest -q                                  # unit tests pass
python -m src.mcp_client.demo              # 4 pillars + MCP payload demo
python -m src.mcp_client.demo --show-payload
python -m src.agent --once --mock-news     # full agentic cycle
streamlit run dashboard/app.py             # live dashboard on :8501
```


