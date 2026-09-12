from datetime import date

from app.market.contracts import ContractSpec, staggered_delivery_window


def _contract(expiry: date) -> ContractSpec:
    return ContractSpec(
        symbol="GOLDDEC26",
        exchange="MCX",
        lot_size=1,
        tick_size=1.0,
        price_quotation="per 10 grams",
        expiry=expiry,
    )


def test_delivery_window_starts_before_expiry():
    contract = _contract(date(2026, 12, 30))
    window = staggered_delivery_window(contract, delivery_period_days=5)
    assert window.delivery_start == date(2026, 12, 25)
    assert window.expiry == date(2026, 12, 30)


def test_is_in_delivery_period_true_inside_window():
    contract = _contract(date(2026, 12, 30))
    window = staggered_delivery_window(contract, delivery_period_days=5)
    assert window.is_in_delivery_period(date(2026, 12, 27)) is True


def test_is_in_delivery_period_false_before_window():
    contract = _contract(date(2026, 12, 30))
    window = staggered_delivery_window(contract, delivery_period_days=5)
    assert window.is_in_delivery_period(date(2026, 12, 1)) is False
