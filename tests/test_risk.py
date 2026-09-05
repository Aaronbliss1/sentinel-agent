from src.strategy.risk_manager import RiskManager
def test_notional_cap():
    rm = RiskManager(max_notional=100)
    assert not rm.check_notional(150)[0]
    assert rm.check_notional(50)[0]
def test_slippage():
    rm = RiskManager(max_slippage_bps=50)
    assert not rm.check_slippage(65000, 65350)[0]  # ~53bps
    assert rm.check_slippage(65000, 65020)[0]
