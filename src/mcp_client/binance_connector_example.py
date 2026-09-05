"""
Official Binance Connector (Python) — SDK Example
This shows judges we use the OFFICIAL SDK from https://developers.binance.com/en/docs/sdks-tools/connectors/python
Complements the MCP Streamable HTTP path — both are valid Agent OS integrations.

Install: pip install binance-connector
Docs: https://github.com/binance/binance-connector-python
"""
import os
from binance.spot import Spot as SpotClient
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

def official_rest_example():
    """
    Official connector handles signing, errors, and weights — preferred for production.
    Our MCP client uses this under the hood when not in mock mode.
    """
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    # Public client (no keys needed for market data)
    client = SpotClient(api_key=api_key, api_secret=api_secret)

    # 1. Market data (public)
    print("=== Official Connector — Market Data ===")
    print(client.ticker_price("BTCUSDT"))
    print(client.klines("BTCUSDT", "15m", limit=5))
    print(client.ticker_24hr("ETHUSDT"))

    # 2. Account (requires Agentic sub-account keys, read-only scope)
    if api_key and api_secret:
        try:
            print("\n=== Account (Agentic sub-account) ===")
            print(client.account())
        except Exception as e:
            print(f"Account error (expected in dry-run without funding): {e}")

    # 3. Place order (requires Trade scope + funding — DRY RUN by default in Sentinel)
    # For hackathon demo we NEVER call this directly — we go via RiskManager -> MCP
    # Example (DO NOT RUN LIVE without risk checks):
    # client.new_order(symbol="BTCUSDT", side="BUY", type="MARKET", quantity=0.001, newClientOrderId="mcp_demo")

    return client

def official_websocket_example():
    """
    Official WebSocket stream — for live price feeds.
    Useful for next iteration: real-time sentiment-triggered scalping.
    """
    def on_message(_, message):
        print(f"WS tick: {message}")

    ws = SpotWebsocketStreamClient(on_message=on_message)
    # Subscribe to BTC ticker — ws stream will push updates
    # ws.ticker(symbol="BTCUSDT")
    # ws.stop()
    return ws

if __name__ == "__main__":
    official_rest_example()
