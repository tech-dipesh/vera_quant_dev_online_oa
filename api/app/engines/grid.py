from dataclasses import dataclass

from app.engines.common import RiskGuard, RiskLimits
from app.models import Fill, Position, Side, utc_now


@dataclass
class GridConfig:
    symbol: str
    reference_price: float
    atr: float
    spacing_multiplier: float
    levels_each_side: int
    size_per_level: int
    pyramiding_factor: float
    limits: RiskLimits


class GridEngine:
    def __init__(self, config: GridConfig) -> None:
        self.config = config
        self.position = Position(symbol=config.symbol)
        self.risk_guard = RiskGuard(config.limits)
        self.levels = self._build_levels()
        self.filled_levels: set[float] = set()

    def _build_levels(self) -> list[float]:
        spacing = self.config.atr * self.config.spacing_multiplier
        levels = []
        for i in range(1, self.config.levels_each_side + 1):
            levels.append(round(self.config.reference_price - spacing * i, 2))
            levels.append(round(self.config.reference_price + spacing * i, 2))
        return sorted(levels)

    def _size_for_level(self, level_index: int) -> int:
        size = self.config.size_per_level * (self.config.pyramiding_factor**level_index)
        return max(1, round(size))

    def on_price(self, price: float) -> list[Fill]:
        if self.risk_guard.tripped:
            return []

        fills = []
        for index, level in enumerate(self.levels):
            if level in self.filled_levels:
                continue

            crossed_down = price <= level < self.config.reference_price
            crossed_up = price >= level > self.config.reference_price

            if not (crossed_down or crossed_up):
                continue

            side = Side.LONG if crossed_down else Side.SHORT
            quantity = self._size_for_level(index)
            fill = Fill(price=level, quantity=quantity, side=side, timestamp=utc_now())
            self.position.apply_fill(fill)
            self.filled_levels.add(level)
            fills.append(fill)

            if not self.risk_guard.check(self.position, price):
                break

        return fills
