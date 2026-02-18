from polymarket_bot.risk import RiskEngine, RiskLimits


def _engine() -> RiskEngine:
    return RiskEngine(
        RiskLimits(
            max_market_notional=500,
            max_open_orders=5,
            max_daily_drawdown_pct=2.0,
        )
    )


def test_allows_valid_order() -> None:
    decision = _engine().evaluate_order(100, 2, 1.0)
    assert decision.allowed


def test_blocks_drawdown_breach() -> None:
    decision = _engine().evaluate_order(100, 2, 2.1)
    assert not decision.allowed


def test_blocks_notional_breach() -> None:
    decision = _engine().evaluate_order(600, 2, 1.0)
    assert not decision.allowed
