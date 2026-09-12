from app.market.margins import MarginRates, required_margin


def _rates() -> MarginRates:
    return MarginRates(exposure_margin_rate=0.03, span_margin_rate_estimate=0.10)


def test_required_margin_scales_with_notional_value():
    result = required_margin(notional_value=100_000, rates=_rates())
    assert result.exposure_margin == 3_000.0
    assert result.span_margin_estimate == 10_000.0
    assert result.total == 13_000.0


def test_total_is_the_sum_of_both_components():
    result = required_margin(notional_value=50_000, rates=_rates())
    assert result.total == round(result.exposure_margin + result.span_margin_estimate, 2)
