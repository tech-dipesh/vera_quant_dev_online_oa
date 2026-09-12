import asyncio
from dataclasses import dataclass

from app.models import Position, Side


@dataclass
class PositionSnapshot:
    symbol: str
    side: Side | None
    quantity: int
    average_price: float
    realized_pnl: float


class BuggySnapshotter:
    async def snapshot(self, position: Position) -> PositionSnapshot:
        quantity = position.quantity
        await asyncio.sleep(0)
        return PositionSnapshot(
            symbol=position.symbol,
            side=position.side,
            quantity=quantity,
            average_price=position.average_price,
            realized_pnl=position.realized_pnl,
        )


class SafeSnapshotter:
    async def snapshot(self, position: Position) -> PositionSnapshot:
        snapshot = PositionSnapshot(
            symbol=position.symbol,
            side=position.side,
            quantity=position.quantity,
            average_price=position.average_price,
            realized_pnl=position.realized_pnl,
        )
        await asyncio.sleep(0)
        return snapshot
