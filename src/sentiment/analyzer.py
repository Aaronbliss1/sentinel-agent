"""
Sentiment Analyzer — Free-first: Gemini Flash > Groq > VADER fallback.
Scores headline 0-100 (0=extreme bearish, 50=neutral, 100=extreme bullish) with confidence.
Supports both old google-generativeai and new google.genai SDKs.
"""
import os
import re
from typing import Tuple, Dict, Optional
from dotenv import load_dotenv
load_dotenv()
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Keyword boosters (calibrated against VADER compounds of typical headlines)
BULLISH_TRIGGERS = ["inflow", "etf", "accumulation", "ath", "upgrade", "burn", "grant", "adoption", "buy", "buys", "surge", "hits new high", "expands", "reduces fees", "record", "largest"]
BEARISH_TRIGGERS = ["hack", "sell pressure", "outflow", "delay", "sec", "lawsuit", "investigate", "fud", "dump", "leverage overextended", "repayments", "fears"]

_vader = SentimentIntensityAnalyzer()

def _vader_score(title: str) -> Tuple[int, float, str]:
    vs = _vader.polarity_scores(title)
    compound = vs["compound"]  # -1 to 1
    score = int((compound + 1) * 50)  # 0-100
    title_l = title.lower()
    boost = 0
    for k in BULLISH_TRIGGERS:
        if k in title_l:
            boost += 7
    for k in BEARISH_TRIGGERS:
        if k in title_l:
            boost -= 7
    score = max(0, min(100, score + boost))
    conf = min(0.95, abs(compound) + 0.3 + (abs(boost)/50))
    label = "BULLISH" if score >= 60 else "BEARISH" if score <= 40 else "NEUTRAL"
    return score, round(conf, 2), label

def _gemini_score(title: str, coin: str) -> Optional[Tuple[int, float, str]]:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    # Use batch-optimized path if available — caller will prefer batch, this is per-headline fallback
    try:
        from google import genai
        client = genai.Client(api_key=key)
        prompt = f"""Score headline for {coin} 0-100: 0=extreme bearish, 50=neutral, 100=extreme bullish. Headline: "{title}" Reply ONLY JSON: {{"score": 78, "confidence": 0.85, "label": "BULLISH"}}"""
        # flash-lite-latest has 5+ calls quota vs flash-latest/pro limited
        for model_name in ["gemini-flash-lite-latest", "gemini-flash-latest"]:
            try:
                resp = client.models.generate_content(model=model_name, contents=prompt)
                text = resp.text.strip()
                import json
                m = re.search(r'\{.*\}', text, re.DOTALL)
                if m:
                    j = json.loads(m.group(0))
                    print(f"[Sentiment] Gemini OK via {model_name}: {title[:60]}... -> {j}")
                    return int(j["score"]), float(j["confidence"]), j["label"]
            except Exception as e:
                last_err = e
                continue
        print(f"[Sentiment] Gemini per-headline failed: {last_err}")
    except Exception as e:
        print(f"[Sentiment] google.genai SDK failed: {e}")
    return None

def gemini_batch_available() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY"))

def _gemini_batch(headlines: list) -> dict:
    """1 API call for N headlines — proven to work with gemini-flash-lite-latest even for 6 headlines"""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return {}
    try:
        from google import genai
        client = genai.Client(api_key=key)
        lines = []
        for i, h in enumerate(headlines):
            coins = ",".join(h.get("coins", ["BTC"]))
            lines.append(f'{i+1}. [{coins}] "{h["title"]}"')
        prompt = "Score EACH crypto headline 0-100 bullish (0=bearish,50=neutral,100=bullish). Headlines:\n" + "\n".join(lines) + "\nReply ONLY as JSON array in order: [{\"score\":85,\"confidence\":0.9,\"label\":\"BULLISH\"}, ...]"
        # flash-lite-latest has highest free quota (tested 5+ calls OK, flash fails with 503)
        resp = client.models.generate_content(model="gemini-flash-lite-latest", contents=prompt)
        text = resp.text.strip()
        import json
        m = re.search(r'\[.*\]', text, re.DOTALL)
        if m:
            arr = json.loads(m.group(0))
            result = {}
            for idx, obj in enumerate(arr):
                if idx < len(headlines):
                    result[headlines[idx]["title"]] = obj
            print(f"[Sentiment] Gemini BATCH OK via gemini-flash-lite-latest: {len(arr)} headlines in 1 call")
            return result
        else:
            print(f"[Sentiment] Batch no JSON found: {text[:200]}")
    except Exception as e:
        print(f"[Sentiment] Batch failed: {e}")
    return {}

def _groq_score(title: str, coin: str) -> Optional[Tuple[int, float, str]]:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=key)
        prompt = f"Score headline for {coin} 0-100 bullish: '{title}'. Reply JSON only: {{\"score\": 78, \"confidence\": 0.85, \"label\": \"BULLISH\"}}"
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            max_tokens=100
        )
        import json, re
        text = chat.choices[0].message.content
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            j = json.loads(m.group(0))
            return int(j["score"]), float(j["confidence"]), j["label"]
    except Exception as e:
        print(f"[Sentiment] Groq failed: {e}")
    return None

def analyze_headline(title: str, coin: str = "BTC") -> Dict:
    """
    Returns: {score: 0-100, confidence: 0-1, label: BULLISH/BEARISH/NEUTRAL, reason, model}
    Free-first cascade: Gemini -> Groq -> VADER
    """
    res = _gemini_score(title, coin)
    model = "gemini-flash-lite-latest"
    if res is None:
        res = _groq_score(title, coin)
        model = "groq-llama-3.1"
    if res is None:
        res = _vader_score(title)
        model = "vader+keywords (offline)"
    score, conf, label = res
    return {
        "title": title,
        "coin": coin,
        "score": max(0, min(100, score)),
        "confidence": conf,
        "label": label,
        "model": model,
        "reason": f"{label} {score}/100 via {model}"
    }

def batch_analyze(news_items: list) -> list:
    # Try batch Gemini first: 1 API call for all headlines (saves quota!)
    if gemini_batch_available() and len(news_items) > 2:
        batch_map = _gemini_batch(news_items)
        if batch_map:
            out = []
            for item in news_items:
                title = item["title"]
                # batch returns one score per headline (reuse for all its coins, adjust later)
                b = batch_map.get(title)
                if b:
                    for coin in item.get("coins", ["BTC"]):
                        out.append({
                            "title": title,
                            "coin": coin,
                            "score": max(0, min(100, int(b.get("score",50)))),
                            "confidence": float(b.get("confidence",0.85)),
                            "label": b.get("label","NEUTRAL"),
                            "model": "gemini-flash-lite-latest (batch)",
                            "reason": f"{b.get('label')} {b.get('score')}/100 via gemini-flash-lite (batch)",
                            "source": item.get("source"),
                            "url": item.get("url"),
                            "age_mins": item.get("age_mins", 10),
                            "published_at": item.get("published_at")
                        })
                    continue
                # fallback if not in batch
                for coin in item.get("coins", ["BTC"]):
                    result = analyze_headline(title, coin)
                    result.update({"source": item.get("source"), "url": item.get("url"), "age_mins": item.get("age_mins",10), "published_at": item.get("published_at")})
                    out.append(result)
            return out

    # Fallback: per-headline
    out = []
    for item in news_items:
        for coin in item.get("coins", ["BTC"]):
            result = analyze_headline(item["title"], coin)
            result.update({
                "source": item.get("source"),
                "url": item.get("url"),
                "age_mins": item.get("age_mins", 10),
                "published_at": item.get("published_at")
            })
            out.append(result)
    return out

if __name__ == "__main__":
    tests = [
        "BlackRock Bitcoin ETF sees $520M inflow, largest in 3 months",
        "SEC delays decision on spot Ethereum ETF, market cautious",
        "BNB Chain burns 1.2M BNB, supply reduction bullish"
    ]
    for t in tests:
        print(analyze_headline(t))
