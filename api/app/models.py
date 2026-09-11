from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class Side(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Fill:
    price: float
    quantity: int
    side: Side
    timestamp: datetime


@dataclass
class Position:
    symbol: str
    side: Side | None = None
    quantity: int = 0
    average_price: float = 0.0
    realized_pnl: float = 0.0

    def apply_fill(self, fill: Fill) -> None:
        if self.side is None or self.quantity == 0:
            self.side = fill.side
            self.quantity = fill.quantity
            self.average_price = fill.price
            return

        if fill.side == self.side:
            total_cost = self.average_price * self.quantity + fill.price * fill.quantity
            self.quantity += fill.quantity
            self.average_price = total_cost / self.quantity
            return

        closing_quantity = min(self.quantity, fill.quantity)
        direction = 1 if self.side == Side.LONG else -1
        self.realized_pnl += direction * (fill.price - self.average_price) * closing_quantity
        self.quantity -= closing_quantity

        remaining = fill.quantity - closing_quantity
        if self.quantity == 0 and remaining > 0:
            self.side = fill.side
            self.quantity = remaining
            self.average_price = fill.price
        elif self.quantity == 0:
            self.side = None
            self.average_price = 0.0

    def unrealized_pnl(self, mark_price: float) -> float:
        if self.side is None or self.quantity == 0:
            return 0.0
        direction = 1 if self.side == Side.LONG else -1
        return direction * (mark_price - self.average_price) * self.quantity


def utc_now() -> datetime:
    return datetime.now(UTC)
