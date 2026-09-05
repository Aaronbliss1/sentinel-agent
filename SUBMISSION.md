# ✅ Submission — Binance Agent OS Mini Hackathon



### 1. Push to GitHub 
```bash
cd sentinel-agent
git init
git add .
git commit -m "Sentinel: Binance Agent OS Sentiment Trader — Track A"
# Create repo on GitHub (public) then:
git remote add origin https://github.com/YOURHANDLE/sentinel-agent.git
git branch -M main
git push -u origin main
```


### 2. Record Demo 
Upload to X/Twitter.


### 3. Verify Before Submitting
```bash
python -m src.mcp_client.demo  # shows 4 pillars
python -m src.agent --once --mock-news  # full cycle
streamlit run dashboard/app.py  # dashboard live
pytest -q  # tests pass
```

