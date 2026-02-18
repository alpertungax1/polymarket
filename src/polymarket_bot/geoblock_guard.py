from dataclasses import dataclass
from enum import Enum


class TradingMode(str, Enum):
    ENABLED = "enabled"
    READ_ONLY = "read_only"


@dataclass(frozen=True)
class GuardDecision:
    mode: TradingMode
    reason: str


class GeoblockGuard:
    """Fail-safe geoblock gate.

    If provider status is unknown, trading is disabled (read-only).
    """

    def evaluate(self, geoblocked: bool | None) -> GuardDecision:
        if geoblocked is None:
            return GuardDecision(
                mode=TradingMode.READ_ONLY,
                reason="geoblock status unknown; fail-safe read-only",
            )
        if geoblocked:
            return GuardDecision(mode=TradingMode.READ_ONLY, reason="region geoblocked")
        return GuardDecision(mode=TradingMode.ENABLED, reason="geoblock clear")
