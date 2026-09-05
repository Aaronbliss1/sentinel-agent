"""
Batch analyzer — scores ALL headlines in ONE Gemini call (saves quota!)
"""
import os, re, json
from typing import List, Dict

def gemini_batch_score(headlines: List[Dict]) -> Dict[str, Dict]:
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
        # Minimal prompt — tested to work with gemini-flash-lite-latest even under high demand
        prompt = "Score EACH crypto headline 0-100 bullish (0=bearish,50=neutral,100=bullish). Headlines:\n" + "\n".join(lines) + "\nReply ONLY as JSON array in order: [{\"score\":85,\"confidence\":0.9,\"label\":\"BULLISH\"}, ...]"
        for model in ["gemini-flash-lite-latest", "gemini-flash-latest"]:
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                text = resp.text.strip()
                m = re.search(r'\[.*\]', text, re.DOTALL)
                if m:
                    arr = json.loads(m.group(0))
                    result = {}
                    for idx, obj in enumerate(arr):
                        if idx < len(headlines):
                            result[headlines[idx]["title"]] = obj
                    print(f"[Sentiment] Gemini BATCH OK via {model}: {len(arr)} headlines in 1 call")
                    return result
            except Exception as e:
                last = e
                print(f"[Sentiment] Batch {model} fail: {e}")
                continue
        print(f"[Sentiment] Batch all failed: {last}")
    except Exception as e:
        print(f"[Sentiment] Batch genai error: {e}")
    return {}
