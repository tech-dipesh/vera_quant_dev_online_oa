from app.market.costs import (
    CostRates,
    brokerage,
    stt_or_ctt,
    total_cost,
    transaction_charges,
)


def _rates() -> CostRates:
    return CostRates(
        stt_or_ctt_rate=0.0002,
        brokerage_flat=20.0,
        brokerage_percent=0.0003,
        exchange_transaction_rate=0.00005,
        gst_rate=0.18,
        stamp_duty_rate=0.00002,
    )


def test_brokerage_takes_the_lower_of_flat_and_percent():
    rates = _rates()
    assert brokerage(turnover=10_000, rates=rates) == min(20.0, 10_000 * 0.0003)


def test_stt_or_ctt_only_applies_on_sell_side():
    rates = _rates()
    assert stt_or_ctt(10_000, rates, is_sell=True) == 2.0
    assert stt_or_ctt(10_000, rates, is_sell=False) == 0.0


def test_transaction_charges_scale_with_turnover():
    rates = _rates()
    assert transaction_charges(10_000, rates) == 0.5


def test_total_cost_composes_all_components_and_rounds_to_the_paisa():
    rates = _rates()
    turnover = 10_000

    result = total_cost(turnover, rates, is_sell=True)

    broker_fee = min(20.0, turnover * rates.brokerage_percent)
    exchange_fee = turnover * rates.exchange_transaction_rate
    tax = turnover * rates.stt_or_ctt_rate
    gst = (broker_fee + exchange_fee) * rates.gst_rate
    expected = round(broker_fee + exchange_fee + tax + gst, 2)

    assert result == expected


def test_stamp_duty_only_applies_on_buy_side():
    rates = _rates()
    buy_cost = total_cost(10_000, rates, is_sell=False)
    sell_cost = total_cost(10_000, rates, is_sell=True)
    assert buy_cost != sell_cost
