from src.sentiment.analyzer import analyze_headline
def test_bullish():
    r = analyze_headline("BlackRock Bitcoin ETF sees $520M inflow, largest in 3 months", "BTC")
    assert r["score"] > 60
    assert r["label"] == "BULLISH"
def test_bearish():
    r = analyze_headline("SEC delays decision on spot Ethereum ETF, market cautious", "ETH")
    # VADER may be neutral, but keyword should push bearish-ish
    assert r["score"] < 60
