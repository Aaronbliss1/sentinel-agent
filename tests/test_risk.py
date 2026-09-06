from src.strategy.risk_manager import RiskManager
def test_notional_cap():
    rm = RiskManager(max_notional=100)
    assert not rm.check_notional(150)[0]
    assert rm.check_notional(50)[0]
def test_notional_cap_lot_rounding_tolerance():
    # Lot-size rounding of qty can push qty*price a couple cents past the
    # cap — structural noise that must not block; real violations still do.
    rm = RiskManager(max_notional=100)
    assert rm.check_notional(100.0)[0]
    assert rm.check_notional(100.004)[0]   # float noise (observed in field)
    assert rm.check_notional(100.02)[0]    # one lot-step overshoot
    assert not rm.check_notional(100.06)[0]
    assert not rm.check_notional(100.8)[0]
def test_slippage():
    rm = RiskManager(max_slippage_bps=50)
    assert not rm.check_slippage(65000, 65350)[0]  # ~53bps
    assert rm.check_slippage(65000, 65020)[0]
