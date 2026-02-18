from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    max_market_notional: float
    max_open_orders: int
    max_daily_drawdown_pct: float


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str


class RiskEngine:
    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def evaluate_order(
        self,
        order_notional: float,
        current_open_orders: int,
        daily_drawdown_pct: float,
    ) -> RiskDecision:
        if daily_drawdown_pct >= self.limits.max_daily_drawdown_pct:
            return RiskDecision(False, "daily drawdown breach")
        if current_open_orders >= self.limits.max_open_orders:
            return RiskDecision(False, "open order limit reached")
        if order_notional > self.limits.max_market_notional:
            return RiskDecision(False, "market notional limit exceeded")
        return RiskDecision(True, "allowed")
