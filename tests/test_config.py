import pytest

from polymarket_bot.config import BotConfig


def test_config_validation_passes() -> None:
    cfg = BotConfig(
        signer_address="0xabc",
        funder_address="0xdef",
        signature_type="PROXY",
    )
    cfg.validate()


def test_config_validation_fails_for_signature_type() -> None:
    cfg = BotConfig(
        signer_address="0xabc",
        funder_address="0xdef",
        signature_type="BAD",
    )
    with pytest.raises(ValueError):
        cfg.validate()
