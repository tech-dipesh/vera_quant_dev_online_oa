from dataclasses import dataclass

from app.engines.common import RiskGuard, RiskLimits
from app.models import Fill, Position, Side, utc_now


@dataclass
class StopAndReverseConfig:
    symbol: str
    atr: float
    stop_multiplier: float
    size: int
    limits: RiskLimits


class StopAndReverseEngine:
    def __init__(self, config: StopAndReverseConfig) -> None:
        self.config = config
        self.position = Position(symbol=config.symbol)
        self.risk_guard = RiskGuard(config.limits)
        self.stop_price: float | None = None

    def enter(self, price: float, side: Side) -> Fill:
        fill = Fill(price=price, quantity=self.config.size, side=side, timestamp=utc_now())
        self.position.apply_fill(fill)
        self._set_stop(price, side)
        return fill

    def _set_stop(self, price: float, side: Side) -> None:
        distance = self.config.atr * self.config.stop_multiplier
        self.stop_price = price - distance if side == Side.LONG else price + distance

    def on_price(self, price: float) -> list[Fill]:
        if self.risk_guard.tripped or self.position.side is None or self.stop_price is None:
            return []

        stopped_long = self.position.side == Side.LONG and price <= self.stop_price
        stopped_short = self.position.side == Side.SHORT and price >= self.stop_price

        if not (stopped_long or stopped_short):
            return []

        reverse_side = Side.SHORT if self.position.side == Side.LONG else Side.LONG
        close_fill = Fill(
            price=price,
            quantity=self.position.quantity,
            side=reverse_side,
            timestamp=utc_now(),
        )
        self.position.apply_fill(close_fill)

        if not self.risk_guard.check(self.position, price):
            return [close_fill]

        reverse_fill = self.enter(price, reverse_side)
        return [close_fill, reverse_fill]
