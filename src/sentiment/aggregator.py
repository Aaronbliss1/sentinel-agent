"""
Aggregator — weighted sentiment per coin (recency + confidence decay)
"""
from typing import List, Dict
import math

def aggregate_sentiment(scored_items: List[Dict], coin: str) -> Dict:
    """
    Weighted avg: weight = confidence * exp(-age_mins/60)
    Returns aggregate 0-100 + signal
    """
    relevant = [x for x in scored_items if x.get("coin") == coin]
    if not relevant:
        return {"coin": coin, "score": 50, "count": 0, "signal": "HOLD", "confidence": 0.0, "details": []}
    total_w = 0
    total_s = 0
    for it in relevant:
        age = it.get("age_mins", 30)
        decay = math.exp(-age / 60)  # half-life ~41m
        w = it.get("confidence", 0.5) * decay
        total_w += w
        total_s += it["score"] * w
    avg = total_s / total_w if total_w else 50
    avg = round(avg, 1)
    # confidence of aggregate = avg confidence weighted
    avg_conf = sum(x["confidence"]*math.exp(-x.get("age_mins",30)/60) for x in relevant)/len(relevant)
    # signal thresholds
    buy_th = int(__import__('os').getenv("SENTIMENT_THRESHOLD_BUY", "70"))
    sell_th = int(__import__('os').getenv("SENTIMENT_THRESHOLD_SELL", "30"))
    if avg >= buy_th:
        signal = "BUY"
    elif avg <= sell_th:
        signal = "SELL"
    else:
        signal = "HOLD"
    return {
        "coin": coin,
        "score": avg,
        "count": len(relevant),
        "signal": signal,
        "confidence": round(avg_conf, 2),
        "details": relevant[:5]
    }

def aggregate_all(scored_items: List[Dict], coins: List[str] = None) -> Dict[str, Dict]:
    coins = coins or ["BTC", "BNB", "ETH"]
    return {c: aggregate_sentiment(scored_items, c) for c in coins}
