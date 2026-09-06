"""
Sentinel Agent — Main Orchestrator
Implements the agentic workflows: News → Sentiment → Technicals → Risk → MCP Trade
Officially integrates with Binance Agent OS via MCP (agent.binance.com/mcp/agentic)
Also supports official binance-connector-python for direct REST fallback.

Usage:
  python -m src.agent --once --dry-run
  python -m src.agent --continuous --interval 120
"""
import asyncio
import os
import time
import argparse
from typing import List
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()
console = Console()

from src.mcp_client.binance_mcp import BinanceMCPClient
from src.sentiment.news_fetcher import NewsFetcher
from src.sentiment.analyzer import batch_analyze
from src.sentiment.aggregator import aggregate_all
from src.strategy.indicators import analyze_technicals
from src.strategy.signal_generator import generate_signal
from src.strategy.risk_manager import RiskManager

SYMBOLS = {"BTC": "BTCUSDT", "BNB": "BNBUSDT", "ETH": "ETHUSDT"}

class SentinelAgent:
    def __init__(self, coins: List[str] = None, dry_run: bool = True, testnet: bool = False):
        self.coins = coins or ["BTC","BNB","ETH"]
        self.dry_run = dry_run
        self.testnet = testnet
        self.fetcher = NewsFetcher()
        self.risk = RiskManager()
        self.mcp = None
        self.trade_log = []

    async def __aenter__(self):
        self.mcp = BinanceMCPClient(dry_run=self.dry_run, testnet=self.testnet)
        await self.mcp.__aenter__()
        return self
    async def __aexit__(self, *a):
        if self.mcp:
            await self.mcp.__aexit__(*a)

    async def run_cycle(self, use_mock_news: bool = False) -> List[dict]:
        """
        One full agentic cycle:
        1. Fetch news for BTC/BNB/ETH
        2. Score with free LLM (Gemini/Groq/VADER)
        3. For each coin: fetch klines + compute technicals
        4. Fuse into signal
        5. Risk check + MCP place_order
        """
        console.print(Panel(f"🔁 Sentinel Cycle — {time.strftime('%Y-%m-%d %H:%M:%S')} | DRY_RUN={self.dry_run} | TESTNET={self.testnet} | Coins: {','.join(self.coins)}", style="bold cyan"))

        # 1. News
        console.print("[1/5] 📰 Fetching news...")
        news = self.fetcher.fetch_all(coins=self.coins, use_mock=use_mock_news)
        console.print(f"  → {len(news)} headlines")
        for n in news[:3]:
            console.print(f"    • [{','.join(n['coins'])}] {n['title'][:80]}... ({n['source']})")

        # 2. Sentiment
        console.print("[2/5] 🧠 Scoring sentiment (Gemini → Groq → VADER)...")
        scored = batch_analyze(news)
        aggregated = aggregate_all(scored, self.coins)
        table = Table(title="Aggregated Sentiment")
        table.add_column("Coin", style="bold")
        table.add_column("Score")
        table.add_column("Signal")
        table.add_column("Confidence")
        table.add_column("Count")
        for coin in self.coins:
            agg = aggregated[coin]
            color = "green" if agg["signal"]=="BUY" else "red" if agg["signal"]=="SELL" else "yellow"
            table.add_row(coin, f"{agg['score']}", f"[{color}]{agg['signal']}[/{color}]", str(agg["confidence"]), str(agg["count"]))
        console.print(table)
        for coin in self.coins:
            agg = aggregated[coin]
            if agg["details"]:
                console.print(f"  {coin} top headline: \"{agg['details'][0]['title'][:70]}...\" → {agg['details'][0]['score']}/100 {agg['details'][0]['label']} ({agg['details'][0]['model']})")

        # 3 & 4: For each coin, get technicals + generate signal + trade
        account = await self.mcp.get_account_balance()
        usdt_balance = 1000.0
        try:
            for b in account.get("balances", []):
                if b["asset"] == "USDT":
                    usdt_balance = float(b["free"])
        except:
            pass
        console.print(f"[3/5] 📊 Account USDT: ${usdt_balance:.2f} ({account.get('mode','')})")

        results = []
        for coin in self.coins:
            symbol = SYMBOLS[coin]
            console.print(f"\n[4/5] 🔍 Analyzing {coin} ({symbol})...")
            try:
                klines = await self.mcp.get_klines(symbol, interval="15m", limit=100)
                tech = analyze_technicals(klines)
                console.print(f"  RSI {tech['rsi']} | MACD {'bull' if tech['macd']['bullish'] else 'bear'} | BB {tech['bb']['position']} | Trend {tech['trend']} | Price ${tech['close']:.2f}")
            except Exception as e:
                console.print(f"  ⚠️ Technicals failed: {e}")
                tech = {"rsi": 50, "macd": {"bullish": False}, "bb": {"position": "neutral"}, "trend": "neutral", "close": await self.mcp.get_price(symbol)}

            sentiment = aggregated[coin]
            signal = generate_signal(symbol, sentiment, tech)
            console.print(f"  → Signal: [bold]{signal['action']}[/bold] (conf {signal['confidence']})")
            console.print(f"    Reason: {signal['reason']}")

            if signal["action"] in ("BUY", "SELL"):
                price = tech.get("close") or await self.mcp.get_price(symbol)
                qty = self.risk.position_size(usdt_balance, price, signal["confidence"])
                # Ensure min qty respecting LOT_SIZE
                if qty * price < 5:
                    qty = 5 / price * 1.05
                mid = price  # simplified; real would use order book mid
                risk_eval = self.risk.evaluate(symbol, signal["action"], qty, price, mid, usdt_balance)
                console.print(f"  🛡️ Risk: {risk_eval['reason']} | Notional ${risk_eval['notional']:.2f}")
                if not risk_eval["approved"]:
                    console.print(f"  ⛔ BLOCKED by Risk Manager: {risk_eval['reason']}")
                    results.append({"coin": coin, "symbol": symbol, "signal": signal, "risk": risk_eval, "executed": False})
                    continue

                # 5. Execute via MCP
                reason = signal["reason"][:120]
                console.print(f"[5/5] 🚀 Placing {signal['action']} via MCP {self.mcp.mcp_endpoint} ...")
                order = await self.mcp.place_order(symbol, signal["action"], quantity=qty, reason=reason)
                console.print(f"  → Result: {order.get('status')} | ID {order.get('clientOrderId')} | {order.get('msg','')}")
                self.trade_log.append({"time": time.strftime("%H:%M:%S"), "coin": coin, "symbol": symbol, "action": signal["action"],
                                       "qty": order.get("quantity"), "price": price, "notional": risk_eval["notional"],
                                       "reason": reason, "status": order.get("status"), "sentiment": sentiment["score"]})
                results.append({"coin": coin, "symbol": symbol, "signal": signal, "risk": risk_eval, "order": order, "executed": True})
            else:
                console.print(f"  💤 HOLD — no trade")
                results.append({"coin": coin, "symbol": symbol, "signal": signal, "executed": False})

        console.print(Panel(f"✅ Cycle complete — {len([r for r in results if r.get('executed')])} orders placed", style="green"))
        return results

async def main():
    parser = argparse.ArgumentParser(description="Sentinel — Binance Agent OS Sentiment Trader")
    parser.add_argument("--coins", nargs="+", default=["BTC","BNB","ETH"], help="Coins to trade")
    parser.add_argument("--interval", type=int, default=120, help="Seconds between cycles in continuous mode")
    parser.add_argument("--continuous", action="store_true", help="Run forever every --interval seconds")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Paper trade (default true)")
    parser.add_argument("--live", action="store_true", help="Live trade on Agentic sub-account (sets dry-run=false)")
    parser.add_argument("--mock-news", action="store_true", help="Use mock headlines (for offline demo)")
    parser.add_argument("--testnet", action="store_true", help="Route data + orders to Binance TESTNET (testnet.binance.vision)")
    parser.add_argument("--panic-close", action="store_true", help="EMERGENCY: cancel all open orders and exit")
    args = parser.parse_args()

    testnet = args.testnet or os.getenv("BINANCE_TESTNET", "false").lower() == "true"
    dry_run = not args.live and not testnet
    if os.getenv("BINANCE_DRY_RUN", "true").lower() == "false":
        dry_run = False
    if args.live:
        dry_run = False

    console.print(Panel.fit("🤖 SENTINEL — Agentic Sentiment Trader\nMCP: https://agent.binance.com/mcp/agentic", style="bold magenta"))
    mode_str = "🔵 TESTNET (testnet.binance.vision)" if testnet else ("🔴 LIVE" if not dry_run else "🟢 PAPER (Dry-Run)")
    console.print(f"Mode: {mode_str} | Interval: {args.interval}s | Coins: {args.coins}")
    console.print("Using Official SDKs: binance-connector-python + MCP Streamable HTTP\n")

    if args.panic_close:
        async with SentinelAgent(coins=args.coins, dry_run=dry_run, testnet=testnet) as agent:
            res = await agent.mcp.cancel_all_orders()
            console.print(Panel(f"🚨 PANIC CLOSE — {res.get('status')}: {res.get('msg', res)}", style="bold red"))
        return

    async with SentinelAgent(coins=args.coins, dry_run=dry_run, testnet=testnet) as agent:
        if args.continuous:
            while True:
                await agent.run_cycle(use_mock_news=args.mock_news)
                console.print(f"⏳ Sleeping {args.interval}s...\n")
                await asyncio.sleep(args.interval)
        else:
            await agent.run_cycle(use_mock_news=args.mock_news)
            # Print trade log
            if agent.trade_log:
                t = Table(title="Trade Log")
                t.add_column("Time"); t.add_column("Coin"); t.add_column("Side"); t.add_column("Qty"); t.add_column("Notional"); t.add_column("Status")
                for tr in agent.trade_log:
                    color = "green" if tr["action"]=="BUY" else "red"
                    t.add_row(tr["time"], tr["coin"], f"[{color}]{tr['action']}[/{color}]", str(tr["qty"]), f"${tr['notional']}", tr["status"])
                console.print(t)

def cli():
    """Console entry point (see [project.scripts] in pyproject.toml)."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
