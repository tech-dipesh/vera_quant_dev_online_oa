from dataclasses import dataclass


@dataclass(frozen=True)
class MarginRates:
    exposure_margin_rate: float
    span_margin_rate_estimate: float


@dataclass(frozen=True)
class MarginRequirement:
    exposure_margin: float
    span_margin_estimate: float

    @property
    def total(self) -> float:
        return round(self.exposure_margin + self.span_margin_estimate, 2)


def required_margin(notional_value: float, rates: MarginRates) -> MarginRequirement:
    return MarginRequirement(
        exposure_margin=round(notional_value * rates.exposure_margin_rate, 2),
        span_margin_estimate=round(notional_value * rates.span_margin_rate_estimate, 2),
    )
