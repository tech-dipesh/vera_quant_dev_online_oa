import asyncio

from app.models import Fill, Position, Side, utc_now
from app.runtime.snapshotter import BuggySnapshotter, SafeSnapshotter


def _position() -> Position:
    return Position(symbol="NIFTY", side=Side.LONG, quantity=1, average_price=100.0)


async def _mutate(position: Position) -> None:
    position.apply_fill(Fill(price=102.0, quantity=1, side=Side.LONG, timestamp=utc_now()))


async def test_bug_this_is_the_race_i_caused_a_torn_read_under_concurrent_mutation():
    position = _position()
    snapshotter = BuggySnapshotter()

    snapshot_task = asyncio.create_task(snapshotter.snapshot(position))
    mutate_task = asyncio.create_task(_mutate(position))
    snapshot, _ = await asyncio.gather(snapshot_task, mutate_task)

    assert snapshot.quantity == 1
    assert snapshot.average_price == 101.0


async def test_fix_safe_snapshotter_never_produces_a_torn_read():
    position = _position()
    snapshotter = SafeSnapshotter()

    snapshot_task = asyncio.create_task(snapshotter.snapshot(position))
    mutate_task = asyncio.create_task(_mutate(position))
    snapshot, _ = await asyncio.gather(snapshot_task, mutate_task)

    consistent_before = snapshot.quantity == 1 and snapshot.average_price == 100.0
    consistent_after = snapshot.quantity == 2 and snapshot.average_price == 101.0
    assert consistent_before or consistent_after
