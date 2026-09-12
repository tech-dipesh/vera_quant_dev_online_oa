from datetime import date

import pytest

from app.market.contracts import ContractSpec, next_rollover_contract


def _spec(symbol: str, expiry: date, tick_size: float = 0.05) -> ContractSpec:
    return ContractSpec(
        symbol=symbol,
        exchange="NFO",
        lot_size=50,
        tick_size=tick_size,
        price_quotation="per unit",
        expiry=expiry,
    )


def test_is_expired_on_or_after_expiry_date():
    contract = _spec("NIFTY24SEPFUT", date(2026, 9, 25))
    assert contract.is_expired(date(2026, 9, 25)) is True
    assert contract.is_expired(date(2026, 9, 24)) is False


def test_round_to_tick_snaps_to_nearest_valid_price():
    contract = _spec("NIFTY24SEPFUT", date(2026, 9, 25), tick_size=0.05)
    assert contract.round_to_tick(101.02) == 101.0
    assert contract.round_to_tick(101.03) == 101.05


def test_next_rollover_picks_the_nearest_later_expiry():
    current = _spec("NIFTY24SEPFUT", date(2026, 9, 25))
    next_month = _spec("NIFTY24OCTFUT", date(2026, 10, 30))
    far_month = _spec("NIFTY24NOVFUT", date(2026, 11, 27))

    chosen = next_rollover_contract(current, [next_month, far_month, current])

    assert chosen.symbol == "NIFTY24OCTFUT"


def test_next_rollover_raises_when_nothing_later_available():
    current = _spec("NIFTY24SEPFUT", date(2026, 9, 25))
    with pytest.raises(ValueError):
        next_rollover_contract(current, [current])
