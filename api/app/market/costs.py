from dataclasses import dataclass


@dataclass(frozen=True)
class CostRates:
    stt_or_ctt_rate: float
    brokerage_flat: float
    brokerage_percent: float
    exchange_transaction_rate: float
    gst_rate: float
    stamp_duty_rate: float


def brokerage(turnover: float, rates: CostRates) -> float:
    percent_based = turnover * rates.brokerage_percent
    if percent_based <= 0:
        return rates.brokerage_flat
    return min(rates.brokerage_flat, percent_based)


def transaction_charges(turnover: float, rates: CostRates) -> float:
    return turnover * rates.exchange_transaction_rate


def stt_or_ctt(turnover: float, rates: CostRates, is_sell: bool) -> float:
    return turnover * rates.stt_or_ctt_rate if is_sell else 0.0


def total_cost(turnover: float, rates: CostRates, is_sell: bool) -> float:
    broker_fee = brokerage(turnover, rates)
    exchange_fee = transaction_charges(turnover, rates)
    tax = stt_or_ctt(turnover, rates, is_sell)
    gst = (broker_fee + exchange_fee) * rates.gst_rate
    stamp_duty = turnover * rates.stamp_duty_rate if not is_sell else 0.0
    return round(broker_fee + exchange_fee + tax + gst + stamp_duty, 2)
