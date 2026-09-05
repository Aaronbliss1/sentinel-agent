"""
Demo: Talks to Binance Agent OS MCP directly (and via REST fallback)
Shows judges the MCP payload.

Usage:
  python -m src.mcp_client.demo
  python -m src.mcp_client.demo --show-payload
"""
import argparse
import asyncio
import json
import os

from src.mcp_client.binance_mcp import BinanceMCPClient


async def run(show_payload: bool = False):
    print("=== Binance Agent OS MCP Demo ===")
    print(f"Endpoint: {os.getenv('BINANCE_MCP_ENDPOINT', 'https://agent.binance.com/mcp/agentic')}")
    async with BinanceMCPClient(dry_run=True) as c:
        h = await c.health()
        print("Health:", h)
        for sym in ["BTCUSDT", "BNBUSDT", "ETHUSDT"]:
            price = await c.get_price(sym)
            ticker = await c.get_24hr_ticker(sym)
            print(f"{sym}: ${price:.2f} (24h {float(ticker['priceChangePercent']):+.2f}%)")
        bal = await c.get_account_balance()
        print("Balances:", json.dumps(bal, indent=2))

        # Demo pillars
        print("\n--- Pillar 2: Precision Normalizer ---")
        print("Normalize 0.001234 BTC qty ->", c.normalize_quantity("BTCUSDT", 0.001234))
        print("Normalize $65234.567 price ->", c.normalize_price("BTCUSDT", 65234.567))

        print("\n--- Pillar 3: Idempotency ---")
        r1 = await c.place_order("BTCUSDT", "BUY", 0.001, reason="Demo sentiment 78")
        print("Order1:", json.dumps(r1, indent=2))
        r2 = await c.place_order("BTCUSDT", "BUY", 0.001, reason="Demo sentiment 78")
        print("Order2 (duplicate within same minute):", json.dumps(r2, indent=2))

        print("\n--- Pillar 4: Risk Block ---")
        r3 = await c.place_order("BTCUSDT", "BUY", 0.05, reason="Too large")
        print("Large order:", json.dumps(r3, indent=2))

        if show_payload:
            print("\n--- MCP JSON-RPC payload (exactly what Agent OS receives) ---")
            print(json.dumps(r1.get("mcp_payload"), indent=2))


def main():
    parser = argparse.ArgumentParser(description="Binance Agent OS MCP demo")
    parser.add_argument("--show-payload", action="store_true",
                        help="Print the full MCP JSON-RPC payload at the end")
    args = parser.parse_args()
    asyncio.run(run(show_payload=args.show_payload))


if __name__ == "__main__":
    main()
