from polymarket_bot.geoblock_guard import GeoblockGuard, TradingMode


def test_geoblocked_is_read_only() -> None:
    guard = GeoblockGuard()
    decision = guard.evaluate(True)
    assert decision.mode == TradingMode.READ_ONLY


def test_unknown_status_is_fail_safe_read_only() -> None:
    guard = GeoblockGuard()
    decision = guard.evaluate(None)
    assert decision.mode == TradingMode.READ_ONLY


def test_clear_status_enables_trading() -> None:
    guard = GeoblockGuard()
    decision = guard.evaluate(False)
    assert decision.mode == TradingMode.ENABLED
