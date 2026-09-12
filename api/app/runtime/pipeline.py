import asyncio
import logging
from collections.abc import Iterable

from app.broker.models import Tick
from app.models import Fill
from app.observability.alerts import AlertManager
from app.observability.blotter import TradeBlotter
from app.observability.metrics import record_engine_state, record_fills
from app.state.store import StateStore

logger = logging.getLogger("runtime.pipeline")


def put_dropping_oldest(queue: asyncio.Queue, item: Tick) -> None:
    try:
        queue.put_nowait(item)
    except asyncio.QueueFull:
        queue.get_nowait()
        queue.put_nowait(item)


class EnginePipeline:
    def __init__(
        self,
        engine,
        name: str = "engine",
        store: StateStore | None = None,
        blotter: TradeBlotter | None = None,
        alerts: AlertManager | None = None,
        queue_size: int = 100,
    ) -> None:
        self.engine = engine
        self.name = name
        self.store = store
        self.blotter = blotter
        self.alerts = alerts
        self.queue: asyncio.Queue[Tick] = asyncio.Queue(maxsize=queue_size)
        self.fills: list[Fill] = []
        self._stopping = asyncio.Event()

    def submit_tick(self, tick: Tick) -> None:
        put_dropping_oldest(self.queue, tick)

    async def run(self) -> None:
        while not self._stopping.is_set():
            try:
                tick = await asyncio.wait_for(self.queue.get(), timeout=0.2)
            except TimeoutError:
                continue

            fills = self.engine.on_price(tick.price)
            for fill in fills:
                self.fills.append(fill)
                logger.info("fill executed price=%s quantity=%s", fill.price, fill.quantity)
                if self.store is not None:
                    self.store.record_fill(self.engine.position.symbol, fill)
                if self.blotter is not None:
                    self.blotter.record(fill)

            record_fills(self.name, len(fills))
            record_engine_state(self.name, self.engine)

            if self.store is not None and fills:
                self.store.save_position_snapshot(self.engine.position)

            if self.alerts is not None:
                self.alerts.check_risk_guard(self.engine.risk_guard)

    async def shutdown(self) -> None:
        self._stopping.set()


class ReplayFeed:
    def __init__(self, symbol: str, prices: Iterable[float], interval_seconds: float = 0.1) -> None:
        self.symbol = symbol
        self.prices = list(prices)
        self.interval_seconds = interval_seconds
        self._stopping = asyncio.Event()

    async def run(self, pipeline: EnginePipeline) -> None:
        for price in self.prices:
            if self._stopping.is_set():
                break
            pipeline.submit_tick(Tick(symbol=self.symbol, price=price))
            await asyncio.sleep(self.interval_seconds)

    def stop(self) -> None:
        self._stopping.set()


async def run_replay_demo(
    engine,
    prices: Iterable[float],
    store: StateStore | None = None,
    interval_seconds: float = 0.01,
) -> EnginePipeline:
    pipeline = EnginePipeline(engine, store=store)
    feed = ReplayFeed(engine.position.symbol, prices, interval_seconds=interval_seconds)

    consumer_task = asyncio.create_task(pipeline.run())
    await feed.run(pipeline)
    await asyncio.sleep(interval_seconds * 3)

    await pipeline.shutdown()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    return pipeline
