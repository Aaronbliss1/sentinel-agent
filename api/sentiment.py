from http.server import BaseHTTPRequestHandler
import json, random, os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Mock live sentiment - on Vercel, this would call Gemini + Binance MCP
        # For demo, returns same structure as real agent, but live on Vercel edge
        data = {
            "coins": {
                "BTC": {"score": random.randint(65,88), "signal": "BUY", "confidence": 0.85, "price": 65234.5, "headline": "BlackRock Bitcoin ETF sees $520M inflow"},
                "BNB": {"score": random.randint(55,82), "signal": "BUY", "confidence": 0.72, "price": 612.3, "headline": "BNB Chain burns 1.2M BNB"},
                "ETH": {"score": random.randint(28,55), "signal": "HOLD", "confidence": 0.61, "price": 2650.8, "headline": "Ethereum Dencun upgrade"}
            },
            "mcp_endpoint": "https://agent.binance.com/mcp/agentic",
            "mode": "PAPER (Dry-Run via Vercel)",
            "note": "Full Python agent runs via Binance Agent OS MCP. This API is a Vercel edge preview."
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
