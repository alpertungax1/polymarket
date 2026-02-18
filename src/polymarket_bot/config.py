from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    """Runtime configuration for the first coding phase."""

    signer_address: str
    funder_address: str
    signature_type: str
    geoblock_poll_seconds: int = 60
    wss_timeout_seconds: int = 30
    max_daily_drawdown_pct: float = 2.0

    def validate(self) -> None:
        if not self.signer_address.startswith("0x"):
            raise ValueError("signer_address must be a hex address")
        if not self.funder_address.startswith("0x"):
            raise ValueError("funder_address must be a hex address")
        if self.signature_type not in {"EOA", "PROXY"}:
            raise ValueError("signature_type must be EOA or PROXY")
        if self.geoblock_poll_seconds <= 0:
            raise ValueError("geoblock_poll_seconds must be positive")
        if not (0 < self.max_daily_drawdown_pct <= 100):
            raise ValueError("max_daily_drawdown_pct must be in (0, 100]")
