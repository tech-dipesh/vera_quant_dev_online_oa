import asyncio

from app.broker.models import Tick
from app.engines.common import RiskLimits
from app.engines.grid import GridConfig, GridEngine
from app.runtime.pipeline import (
    EnginePipeline,
    ReplayFeed,
    put_dropping_oldest,
    run_replay_demo,
)


def _config() -> GridConfig:
    return GridConfig(
        symbol="NIFTY",
        reference_price=100.0,
        atr=2.0,
        spacing_multiplier=1.0,
        levels_each_side=3,
        size_per_level=1,
        pyramiding_factor=1.0,
        limits=RiskLimits(max_position=100, max_loss=1000.0),
    )


def test_put_dropping_oldest_discards_oldest_when_queue_is_full():
    queue: asyncio.Queue = asyncio.Queue(maxsize=2)
    put_dropping_oldest(queue, Tick(symbol="NIFTY", price=1))
    put_dropping_oldest(queue, Tick(symbol="NIFTY", price=2))
    put_dropping_oldest(queue, Tick(symbol="NIFTY", price=3))

    remaining = [queue.get_nowait().price, queue.get_nowait().price]

    assert remaining == [2, 3]


async def test_replay_feed_submits_every_price_in_order():
    received = []

    class FakePipeline:
        def submit_tick(self, tick):
            received.append(tick.price)

    feed = ReplayFeed("NIFTY", [100, 98, 96], interval_seconds=0)
    await feed.run(FakePipeline())

    assert received == [100, 98, 96]


async def test_replay_feed_stops_early_when_asked():
    received = []

    class FakePipeline:
        def submit_tick(self, tick):
            received.append(tick.price)

    feed = ReplayFeed("NIFTY", [100, 98, 96], interval_seconds=0.05)

    async def stop_after_first_tick():
        await asyncio.sleep(0.02)
        feed.stop()

    await asyncio.gather(feed.run(FakePipeline()), stop_after_first_tick())

    assert received == [100]


async def test_pipeline_processes_ticks_and_reconciles_to_a_direct_call():
    prices = [100, 98, 96, 97, 99]

    pipeline_engine = GridEngine(_config())
    pipeline = await run_replay_demo(pipeline_engine, prices, interval_seconds=0.01)

    direct_engine = GridEngine(_config())
    for price in prices:
        direct_engine.on_price(price)

    assert pipeline_engine.position.quantity == direct_engine.position.quantity
    assert pipeline_engine.position.realized_pnl == direct_engine.position.realized_pnl
    assert len(pipeline.fills) == len(direct_engine.filled_levels)


async def test_pipeline_records_fills_in_the_blotter_and_raises_alerts_on_risk_guard_trip():
    from app.observability.alerts import AlertManager
    from app.observability.blotter import TradeBlotter

    engine = GridEngine(
        GridConfig(
            symbol="NIFTY",
            reference_price=100.0,
            atr=2.0,
            spacing_multiplier=1.0,
            levels_each_side=3,
            size_per_level=1,
            pyramiding_factor=1.0,
            limits=RiskLimits(max_position=0, max_loss=1000.0),
        )
    )
    blotter = TradeBlotter()
    notified = []
    alerts = AlertManager(notify=notified.append)
    pipeline = EnginePipeline(engine, blotter=blotter, alerts=alerts)

    run_task = asyncio.create_task(pipeline.run())
    pipeline.submit_tick(Tick(symbol="NIFTY", price=97.5))
    await asyncio.sleep(0.1)
    await pipeline.shutdown()
    await asyncio.wait_for(run_task, timeout=1.0)

    assert len(blotter.entries) == 1
    assert any(alert.level == "critical" for alert in notified)
    pipeline = EnginePipeline(GridEngine(_config()))
    run_task = asyncio.create_task(pipeline.run())
    await asyncio.sleep(0.05)

    await pipeline.shutdown()
    await asyncio.wait_for(run_task, timeout=1.0)

    assert run_task.done()
