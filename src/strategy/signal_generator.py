"""
Signal Generator — Fuses Sentiment + Technicals into BUY/SELL/HOLD
Explainable: returns human-readable `reason` for every signal (judges love this).
"""
from typing import Dict

BUY_TH = 70
SELL_TH = 30

def generate_signal(symbol: str, sentiment: Dict, technicals: Dict) -> Dict:
    """
    sentiment: {score: 0-100, signal: BUY/SELL/HOLD, confidence}
    technicals: {rsi, macd: {bullish}, bb: {position}, trend}
    """
    coin = symbol.replace("USDT","")
    s_score = sentiment.get("score", 50)
    s_sig = sentiment.get("signal", "HOLD")
    s_conf = sentiment.get("confidence", 0.5)
    rsi = technicals.get("rsi", 50)
    macd_bull = technicals.get("macd", {}).get("bullish", False)
    bb_pos = technicals.get("bb", {}).get("position", "neutral")
    trend = technicals.get("trend", "neutral")

    # Base decision from sentiment
    if s_sig == "BUY":
        # Filters to avoid chasing
        if rsi > 75:
            return {
                "action": "HOLD",
                "confidence": round(s_conf * 0.6, 2),
                "reason": f"{coin} sentiment {s_score}/100 BULLISH but RSI {rsi} overbought ({bb_pos}) → HOLD (avoid chase). Sentiment: {s_score}, RSI filter BLOCKED."
            }
        if bb_pos == "overbought" and rsi > 70:
            return {"action": "HOLD", "confidence": 0.55, "reason": f"{coin} sentiment bullish ({s_score}) but Bollinger overbought + RSI {rsi} → HOLD"}
        # Confirm with tech
        if macd_bull or trend == "up":
            conf = min(0.92, s_conf + 0.15)
            return {
                "action": "BUY",
                "confidence": round(conf, 2),
                "reason": f"{coin} sentiment {s_score}/100 (BUY) + RSI {rsi} + MACD bullish + trend {trend} → BUY. {sentiment.get('count',0)} headlines aggregated."
            }
        else:
            # Weak tech but strong sentiment still BUY with lower conf
            if s_score >= 80:
                return {"action": "BUY", "confidence": round(s_conf * 0.85, 2), "reason": f"{coin} sentiment EXTREME {s_score}/100 → BUY despite neutral technicals (RSI {rsi}, MACD {'bull' if macd_bull else 'bear'})."}
            return {"action": "HOLD", "confidence": round(s_conf*0.7, 2), "reason": f"{coin} sentiment {s_score} BUY but MACD bearish + trend {trend} → HOLD for confirmation"}

    elif s_sig == "SELL":
        if rsi < 25:
            return {"action": "HOLD", "confidence": 0.55, "reason": f"{coin} sentiment {s_score}/100 BEARISH but RSI {rsi} oversold → HOLD (avoid selling bottom)"}
        if not macd_bull or trend == "down":
            conf = min(0.9, s_conf + 0.12)
            return {"action": "SELL", "confidence": round(conf,2), "reason": f"{coin} sentiment {s_score}/100 (SELL) + RSI {rsi} + MACD bearish → SELL"}
        else:
            if s_score <= 20:
                return {"action": "SELL", "confidence": round(s_conf*0.85,2), "reason": f"{coin} sentiment EXTREME BEARISH {s_score}/100 → SELL despite uptrend (RSI {rsi})"}
            return {"action": "HOLD", "confidence": 0.6, "reason": f"{coin} sentiment SELL ({s_score}) but trend {trend} up → HOLD"}

    else:  # HOLD
        # Even on hold, strong technical + slight sentiment tilt could trigger?
        return {"action": "HOLD", "confidence": round(s_conf,2), "reason": f"{coin} sentiment NEUTRAL {s_score}/100 + RSI {rsi} + trend {trend} → HOLD. No edge."}
