from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol

from app.models import Fill, Position, Side


class ExecutionEngine(Protocol):
    position: Position

    def on_price(self, price: float) -> list[Fill]: ...


@dataclass
class CostModel:
    slippage_bps: float = 0.0
    commission_per_fill: float = 0.0

    def adjusted_price(self, price: float, side: Side) -> float:
        slip = price * (self.slippage_bps / 10_000)
        return price + slip if side == Side.LONG else price - slip

    def slippage_cost(self, fill: Fill) -> float:
        return abs(self.adjusted_price(fill.price, fill.side) - fill.price) * fill.quantity


@dataclass
class BacktestResult:
    fills: list[Fill] = field(default_factory=list)
    ideal_realized_pnl: float = 0.0
    slippage_cost: float = 0.0
    commissions_paid: float = 0.0
    equity_curve: list[float] = field(default_factory=list)

    @property
    def cost_adjusted_pnl(self) -> float:
        return self.ideal_realized_pnl - self.slippage_cost - self.commissions_paid


def run_backtest(
    engine: ExecutionEngine, prices: Iterable[float], cost_model: CostModel
) -> BacktestResult:
    result = BacktestResult()

    for price in prices:
        for fill in engine.on_price(price):
            result.fills.append(fill)
            result.slippage_cost += cost_model.slippage_cost(fill)
            result.commissions_paid += cost_model.commission_per_fill

        result.equity_curve.append(
            engine.position.realized_pnl + engine.position.unrealized_pnl(price)
        )

    result.ideal_realized_pnl = engine.position.realized_pnl
    return result
