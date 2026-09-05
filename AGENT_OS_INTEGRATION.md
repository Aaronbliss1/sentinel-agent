# Binance Agent OS — Integration Map (Sentinel)

This doc proves Sentinel uses the **official Binance Agent OS** exactly as documented at  
`https://developers.binance.com/en/docs/agent-native/mcp-server/agentic`

---

## 1. MCP Endpoint (Streamable HTTP)

**Official:** `https://agent.binance.com/mcp/agentic`  
**Sentinel:** `src/mcp_client/binance_mcp.py` → `MCP_ENDPOINT = "https://agent.binance.com/mcp/agentic"`

Every trade builds a JSON-RPC payload:

```json
{
  "jsonrpc": "2.0",
  "id": "mcp_a1b2c3",
  "method": "tools/call",
  "params": {
    "name": "place_order",
    "arguments": {
      "symbol": "BTCUSDT",
      "side": "BUY",
      "type": "MARKET",
      "quantity": "0.001",
      "clientOrderId": "mcp_a1b2c3",
      "reason": "BTC sentiment 78 + RSI 62"
    }
  },
  "mcp_endpoint": "https://agent.binance.com/mcp/agentic"
}
```

**Connection (as per docs):**
```bash
claude mcp add binance-mcp-server --transport http https://agent.binance.com/mcp/agentic
# Also works: Claude Desktop, Codex CLI, ChatGPT, VS Code, Grok Bot
```

---

## 2. Scopes (User-Controlled Permissions)

| Scope | Doc Says | Sentinel Uses | File |
|-------|----------|---------------|------|
| **Market Data** (no auth) | tickers, order books, candles, funding | `get_price`, `get_order_book`, `get_klines`, `get_24hr_ticker` | `binance_mcp.py` |
| **Account** | Agentic sub-account balances + read-only main | `get_account_balance()` → parses `balances` array | `binance_mcp.py` |
| **Trade** | Spot, Margin, Convert, USD-M, COIN-M (only if granted) | `place_order()` with `MARKET`/`LIMIT`, respects `LOT_SIZE`/`TICK_SIZE` | `binance_mcp.py` + `risk_manager.py` |
| **Transfer** | Between wallets inside sub-account only | Documented, not auto-used (user must manually fund via UI) | `README.md` |
| **Withdrawal** | **NEVER available** | Never requested, never implemented | — |

**Confirm-before-execute:** All MCP `place_order` calls are logged and require Risk approval first. In LIVE mode, Binance still prompts user confirmation in the agent UI before spending funds.

---

## 3. Agentic Virtual Sub-Account

**Doc flow:**
1. Authorize at `agent.binance.com/mcp/agentic` → creates **Agentic virtual sub** 
2. Fund manually: **Binance.com → Profile → Dashboard → Sub-account → Asset Management → Transfer**
3. Agent trades only inside sub-account; cannot pull from main.

**Sentinel:**
- `get_account_balance()` detects `PAPER (Dry-Run via MCP)` vs `LIVE Agentic Sub-Account`
- `BINANCE_DRY_RUN=true` (default) simulates trades; no real funds touched.
- Emergency stop: `python -m src.agent --panic-close` (cancels all orders) + Binance UI **Disconnect agents** or **Emergency stop** (disconnect + cancel all).

Funding link: `https://www.binance.com/en/my/sub-account/asset-management/transfer?asset=BTC`

---

## 4. Official SDKs (from https://developers.binance.com/en/docs/sdks-tools/overview)

Sentinel declares both:

- **MCP path (primary, for Agent OS):** `mcp==1.9.4` + `httpx` → Streamable HTTP to Agent OS.
- **Official Connector (fallback/production):** `binance-connector` (Python) → `src/mcp_client/binance_connector_example.py`

```python
from binance.spot import Spot as SpotClient
client = SpotClient(api_key, api_secret)
client.ticker_price("BTCUSDT")  # market data
client.account()                # agentic sub-account
# client.new_order(...)         # via RiskManager only
```

Other official connectors available (JS, Rust, Go, Java, .NET, PHP, Ruby) — swap in 1 line.

---

## 5. Environments

- **Production:** `https://api.binance.com` (live market data & trading)
- **Testnet:** `https://testnet.binance.vision` (toggle `BINANCE_TESTNET=true`)
- **Demo/Paper:** `BINANCE_DRY_RUN=true` → mock prices/klines when geo-blocked (e.g., 451 from E2B sandbox). Judges can still evaluate without API keys.

Rate limits respected: Sentinel does clock sync (corrects 1021 errors), idempotent clientOrderId (prevents 429 retries double-fill), and backoff on 418/429.


See `README.md`, `demo/DEMO_SCRIPT.md`, and live `dashboard/app.py` for the full story.
