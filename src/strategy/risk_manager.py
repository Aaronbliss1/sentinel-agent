"""
Risk Manager — The 4 Institutional Pillars for Binance Agent OS
Blocks dangerous trades BEFORE they hit the MCP.
"""
import os
from typing import Dict, Tuple
from decimal import Decimal, ROUND_DOWN

class RiskManager:
    def __init__(self, max_notional: float = None, max_slippage_bps: int = None,
                 max_daily_loss_pct: float = None, position_pct: float = None):
        self.max_notional = float(max_notional or os.getenv("MAX_NOTIONAL_PER_TRADE", "100"))
        self.max_slippage_bps = int(max_slippage_bps or os.getenv("MAX_SLIPPAGE_BPS", "50"))
        self.max_daily_loss_pct = float(os.getenv("MAX_DAILY_LOSS_PCT", "3.0"))
        self.position_pct = float(os.getenv("POSITION_PCT_PER_TRADE", "2.0"))
        self.stop_loss_pct = float(os.getenv("STOP_LOSS_PCT", "1.5"))
        self.take_profit_pct = float(os.getenv("TAKE_PROFIT_PCT", "3.0"))
        self.daily_pnl = 0.0
        self.starting_balance = 1000.0
        self._exposure: Dict[str, float] = {}

    def check_notional(self, notional: float) -> Tuple[bool, str]:
        if notional < 5.0:
            return False, f"MIN_NOTIONAL: ${notional:.2f} < $5.00"
        if notional > self.max_notional:
            return False, f"NOTIONAL_CAP_EXCEEDED: ${notional:.2f} > cap ${self.max_notional}"
        return True, "OK"

    def check_slippage(self, mid_price: float, trade_price: float) -> Tuple[bool, str]:
        if mid_price == 0:
            return True, "OK"
        bps = abs(trade_price - mid_price) / mid_price * 10000
        if bps > self.max_slippage_bps:
            return False, f"PRICE_COLLAR_BREACH: {bps:.1f} bps > {self.max_slippage_bps} bps"
        return True, "OK"

    def check_daily_loss(self, balance: float) -> Tuple[bool, str]:
        # kill switch if daily loss exceeded
        loss_pct = (self.daily_pnl / self.starting_balance * 100) if self.starting_balance else 0
        if loss_pct <= -self.max_daily_loss_pct:
            return False, f"DAILY_LOSS_KILL: {loss_pct:.2f}% <= -{self.max_daily_loss_pct}% — trading halted"
        return True, "OK"

    def position_size(self, balance: float, price: float, confidence: float) -> float:
        """2% base * confidence scaling (0.5x to 1.5x)"""
        base = balance * (self.position_pct / 100)
        mult = 0.5 + (confidence)  # confidence 0.5-0.95 => 1.0-1.45x
        notional = base * mult
        notional = min(notional, self.max_notional)
        qty = notional / price if price else 0
        return qty

    def evaluate(self, symbol: str, side: str, qty: float, price: float, mid_price: float, balance: float) -> Dict:
        notional = qty * price
        checks = []
        ok1, msg1 = self.check_notional(notional)
        checks.append(("notional", ok1, msg1))
        ok2, msg2 = self.check_slippage(mid_price, price)
        checks.append(("slippage", ok2, msg2))
        ok3, msg3 = self.check_daily_loss(balance)
        checks.append(("daily_loss", ok3, msg3))
        all_ok = all(c[1] for c in checks)
        return {
            "approved": all_ok,
            "notional": round(notional, 2),
            "checks": checks,
            "reason": "APPROVED" if all_ok else "; ".join([c[2] for c in checks if not c[1]])
        }

    def update_pnl(self, pnl: float):
        self.daily_pnl += pnl
