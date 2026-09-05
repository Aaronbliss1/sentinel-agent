"""
Technical Indicators — RSI, MACD, Bollinger Bands
Uses Binance klines + `ta` library. No API cost.
"""
import pandas as pd
import numpy as np

def klines_to_df(klines):
    """Binance klines -> DataFrame with OHLCV"""
    cols = ["openTime","open","high","low","close","volume","closeTime","quoteVol","trades","tbBase","tbQuote","ignore"]
    df = pd.DataFrame(klines, columns=cols)
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c])
    return df

def compute_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 50.0

def compute_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df["close"].ewm(span=fast).mean()
    ema_slow = df["close"].ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal).mean()
    hist = macd - sig
    return {
        "macd": float(macd.iloc[-1]),
        "signal": float(sig.iloc[-1]),
        "hist": float(hist.iloc[-1]),
        "bullish": bool(macd.iloc[-1] > sig.iloc[-1])
    }

def compute_bollinger(df, period=20, std=2):
    sma = df["close"].rolling(period).mean()
    stdv = df["close"].rolling(period).std()
    upper = sma + std * stdv
    lower = sma - std * stdv
    price = df["close"].iloc[-1]
    sma_v = sma.iloc[-1]
    return {
        "upper": float(upper.iloc[-1]),
        "lower": float(lower.iloc[-1]),
        "sma": float(sma_v),
        "position": "overbought" if price > upper.iloc[-1] else "oversold" if price < lower.iloc[-1] else "neutral",
        "price": float(price)
    }

def analyze_technicals(klines) -> dict:
    if not klines or len(klines) < 30:
        return {"rsi": 50, "macd": {"bullish": False}, "bb": {"position": "neutral"}, "trend": "neutral"}
    df = klines_to_df(klines)
    rsi = compute_rsi(df)
    macd = compute_macd(df)
    bb = compute_bollinger(df)
    # simple trend
    ema20 = df["close"].ewm(span=20).mean().iloc[-1]
    ema50 = df["close"].ewm(span=50).mean().iloc[-1] if len(df) >= 50 else ema20
    trend = "up" if ema20 > ema50 else "down" if ema20 < ema50 else "sideways"
    return {
        "rsi": round(float(rsi), 2),
        "macd": macd,
        "bb": bb,
        "trend": trend,
        "close": float(df["close"].iloc[-1])
    }
