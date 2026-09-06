"""
One-shot proof for the demo: shows your REAL testnet balances and the
exchange's own record of your recent filled orders.

Usage:
    python demo/verify_fill.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

key = os.getenv("BINANCE_API_KEY", "")
secret = os.getenv("BINANCE_API_SECRET", "")
if not (key and secret):
    print("Set BINANCE_API_KEY / BINANCE_API_SECRET in .env first")
    sys.exit(1)

from binance.spot import Spot

client = Spot(key, secret, base_url="https://testnet.binance.vision")

print("=" * 52)
print("  SENTINEL — TESTNET PROOF (testnet.binance.vision)")
print("=" * 52)

print("\nYOUR ACCOUNT BALANCES:")
try:
    acc = client.account()
    shown = False
    for b in acc["balances"]:
        if float(b["free"]) > 0:
            print(f"  {b['asset']:>8}: {b['free']}")
            shown = True
    if not shown:
        print("  (empty)")
except Exception as e:
    print(f"  account query failed: {e}")

print("\nEXCHANGE RECORD OF RECENT FILLS:")
found = 0
for sym in ("BTCUSDT", "ETHUSDT", "BNBUSDT"):
    try:
        for o in client.get_orders(symbol=sym, limit=20):
            if o["status"] in ("FILLED", "PARTIALLY_FILLED"):
                found += 1
                print(
                    f"  #{o['orderId']}  {sym}  {o['side']:<4} "
                    f"{o['executedQty']} @ {o['price']}  "
                    f"[{o['status']}]  client: {o['clientOrderId']}"
                )
    except Exception:
        pass
if found == 0:
    print("  (no fills yet — keep the agent running)")
print()
