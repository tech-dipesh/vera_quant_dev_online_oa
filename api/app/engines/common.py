from dataclasses import dataclass

from app.models import Position


@dataclass
class RiskLimits:
    max_position: int
    max_loss: float


class RiskGuard:
    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits
        self.tripped = False

    def check(self, position: Position, mark_price: float) -> bool:
        if self.tripped:
            return False

        if abs(position.quantity) > self.limits.max_position:
            self.tripped = True
            return False

        total_pnl = position.realized_pnl + position.unrealized_pnl(mark_price)
        if total_pnl <= -abs(self.limits.max_loss):
            self.tripped = True
            return False

        return True

    def reset(self) -> None:
        self.tripped = False
