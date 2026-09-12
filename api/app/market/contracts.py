from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ContractSpec:
    symbol: str
    exchange: str
    lot_size: int
    tick_size: float
    price_quotation: str
    expiry: date

    def is_expired(self, as_of: date) -> bool:
        return as_of >= self.expiry

    def round_to_tick(self, price: float) -> float:
        ticks = round(price / self.tick_size)
        return round(ticks * self.tick_size, 2)


def next_rollover_contract(current: ContractSpec, candidates: list[ContractSpec]) -> ContractSpec:
    upcoming = [
        contract
        for contract in candidates
        if contract.symbol != current.symbol and contract.expiry > current.expiry
    ]
    if not upcoming:
        raise ValueError("no later-expiry contract available for rollover")
    return min(upcoming, key=lambda contract: contract.expiry)


@dataclass(frozen=True)
class StaggeredDeliveryWindow:
    delivery_start: date
    expiry: date

    def is_in_delivery_period(self, as_of: date) -> bool:
        return self.delivery_start <= as_of <= self.expiry


def staggered_delivery_window(
    contract: ContractSpec, delivery_period_days: int
) -> StaggeredDeliveryWindow:
    delivery_start = contract.expiry - timedelta(days=delivery_period_days)
    return StaggeredDeliveryWindow(delivery_start=delivery_start, expiry=contract.expiry)
