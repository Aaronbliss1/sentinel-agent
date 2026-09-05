"""
News Fetcher — pulls headlines for BTC/BNB/ETH from free sources.
Sources:
- CryptoPanic (free tier) if key present
- Binance public news RSS + Crypto news RSS
- Mock headlines for offline demo
"""
import os
import time
import random
import httpx
import feedparser
from typing import List, Dict
from datetime import datetime, timezone

# Free RSS feeds
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptonews.com/news/feed/",
]

MOCK_HEADLINES = {
    "BTC": [
        "BlackRock Bitcoin ETF sees $520M inflow, largest in 3 months",
        "Fed signals rate cut, Bitcoin jumps as dollar weakens",
        "Whale moves 2,000 BTC to cold storage, accumulation signal",
        "SEC delays decision on spot Ethereum ETF, market cautious",
        "Bitcoin hash rate hits new ATH, network security strengthens",
        "Mt. Gox repayments trigger sell pressure fears",
        "Michael Saylor buys additional 3,000 BTC for MicroStrategy",
        "Bitcoin funding rates spike, leverage overextended warning",
    ],
    "BNB": [
        "BNB Chain announces $10M builder grant, ecosystem expands",
        "Binance burns 1.2M BNB, supply reduction bullish",
        "BNB Chain TVL rises 12% after opBNB upgrade",
        "Regulatory FUD hits BNB as SEC comments on exchange tokens",
        "PancakeSwap volume on BNB Chain hits 6-month high",
    ],
    "ETH": [
        "Ethereum Dencun upgrade reduces fees 40%, L2s surge",
        "Vitalik proposes new EIP to improve staking, community bullish",
        "ETH staking hits 32M, supply squeeze narrative",
        "SEC investigates ETH staking services, bearish pressure",
        "BlackRock tokenized fund expands to Ethereum, $200M minted",
        "Ethereum gas fees lowest in 6 months, activity rising",
    ]
}

COIN_KEYWORDS = {
    "BTC": ["bitcoin", "btc", "saylor", "etf", "blackrock"],
    "BNB": ["bnb", "binance", "bsc", "pancakeswap", "opbnb"],
    "ETH": ["ethereum", "eth", "vitalik", "staking", "eip", "l2"],
}

class NewsFetcher:
    def __init__(self, cryptopanic_key: str = None):
        self.key = cryptopanic_key or os.getenv("CRYPTOPANIC_API_KEY")
        self.client = httpx.Client(timeout=10)

    def _classify(self, title: str) -> List[str]:
        title_l = title.lower()
        coins = []
        for coin, kws in COIN_KEYWORDS.items():
            if any(k in title_l for k in kws):
                coins.append(coin)
        return coins or ["BTC"]  # default tag

    def fetch_cryptopanic(self, limit: int = 10) -> List[Dict]:
        if not self.key:
            return []
        try:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={self.key}&public=true&kind=news&filter=hot"
            r = self.client.get(url)
            data = r.json()
            out = []
            for p in data.get("results", [])[:limit]:
                title = p.get("title", "")
                out.append({
                    "title": title,
                    "source": "CryptoPanic",
                    "published_at": p.get("published_at"),
                    "url": p.get("url"),
                    "coins": self._classify(title),
                    "raw": p
                })
            return out
        except Exception as e:
            print(f"[News] CryptoPanic failed: {e}")
            return []

    def fetch_rss(self, limit: int = 10) -> List[Dict]:
        out = []
        for feed_url in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:4]:
                    title = entry.get("title", "")
                    out.append({
                        "title": title,
                        "source": feed.feed.get("title", feed_url),
                        "published_at": entry.get("published", datetime.now(timezone.utc).isoformat()),
                        "url": entry.get("link"),
                        "coins": self._classify(title),
                    })
            except Exception as e:
                print(f"[News] RSS {feed_url} failed: {e}")
        # shuffle and trim
        random.shuffle(out)
        return out[:limit]

    def fetch_mock(self, coins: List[str] = None, count: int = 8) -> List[Dict]:
        """High-quality mock for hackathon demo (no API needed)"""
        coins = coins or ["BTC", "BNB", "ETH"]
        out = []
        for coin in coins:
            titles = MOCK_HEADLINES.get(coin, MOCK_HEADLINES["BTC"])
            for _ in range(2):
                title = random.choice(titles)
                # add freshness variance
                mins_ago = random.randint(1, 90)
                out.append({
                    "title": title,
                    "source": "MockFeed (Demo)",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "url": "https://example.com/news",
                    "coins": [coin],
                    "age_mins": mins_ago,
                    "mock": True
                })
        random.shuffle(out)
        return out[:count]

    def fetch_all(self, coins: List[str] = None, use_mock: bool = False) -> List[Dict]:
        if use_mock:
            return self.fetch_mock(coins)
        items = []
        # Try real sources first
        items += self.fetch_cryptopanic(limit=6)
        items += self.fetch_rss(limit=6)
        # If nothing, fall back to mock so demo never breaks
        if not items:
            print("[News] No live news, using mock headlines for demo resilience")
            items = self.fetch_mock(coins)
        # Filter to requested coins if provided
        if coins:
            items = [x for x in items if any(c in x["coins"] for c in coins)]
            if not items:
                items = self.fetch_mock(coins)
        # Add age_mins
        for it in items:
            if "age_mins" not in it:
                it["age_mins"] = random.randint(2, 45)
        return items[:10]

if __name__ == "__main__":
    f = NewsFetcher()
    print(f.fetch_all(use_mock=True))
