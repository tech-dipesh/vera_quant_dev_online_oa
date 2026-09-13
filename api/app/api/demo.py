import asyncio
import logging

from app.broker.models import Tick
from app.data.loader import load_daily_ohlc
from app.engines.common import RiskLimits
from app.engines.grid import GridConfig, GridEngine
from app.engines.stop_and_reverse import StopAndReverseConfig, StopAndReverseEngine
from app.macro_regime.engine import MacroProxy, MacroRegimeEngine
from app.models import Fill, Side, utc_now
from app.observability.alerts import AlertManager
from app.observability.blotter import TradeBlotter
from app.pubsub.ticks import TickPublisher
from app.runtime.pipeline import EnginePipeline
from app.state.store import StateStore
from app.ta.indicators import atr as compute_atr

logger = logging.getLogger("api.demo")


class DemoManager:
    def __init__(self, database_url: str, redis_url: str, symbol: str = "^NSEI") -> None:
        self.symbol = symbol
        self.store = StateStore(database_url)
        self.publisher = TickPublisher(redis_url)
        self.macro_engine = MacroRegimeEngine(
            [
                MacroProxy(
                    name="india_vix", value=14.0, elevated_threshold=20.0, crisis_threshold=35.0
                )
            ]
        )
        self.blotters: dict[str, TradeBlotter] = {
            "grid": TradeBlotter(),
            "stop_and_reverse": TradeBlotter(),
        }
        self.alerts = AlertManager(notify=lambda alert: logger.warning("alert: %s", alert.message))

        self.grid_engine: GridEngine | None = None
        self.sar_engine: StopAndReverseEngine | None = None
        self.pipelines: dict[str, EnginePipeline] = {}
        self._tasks: list[asyncio.Task] = []
        self._prices: list[float] = []
        self._interval_seconds = 0.2
        self.running = False

    def _build_engines(self, reference_price: float, atr: float) -> None:
        limits = RiskLimits(max_position=20, max_loss=5000.0)

        grid_config = GridConfig(
            symbol=self.symbol,
            reference_price=reference_price,
            atr=atr,
            spacing_multiplier=1.0,
            levels_each_side=4,
            size_per_level=1,
            pyramiding_factor=1.0,
            limits=limits,
        )
        self.macro_engine.apply_to_grid_config(grid_config)
        self.grid_engine = GridEngine(grid_config)

        sar_config = StopAndReverseConfig(
            symbol=self.symbol, atr=atr, stop_multiplier=1.5, size=1, limits=limits
        )
        self.sar_engine = StopAndReverseEngine(sar_config)
        initial_fill = self.sar_engine.enter(reference_price, Side.LONG)
        self.blotters["stop_and_reverse"].record(initial_fill)
        self.store.record_fill(self.symbol, initial_fill)

    def engines(self) -> dict[str, object]:
        return {"grid": self.grid_engine, "stop_and_reverse": self.sar_engine}

    async def start(self) -> None:
        if self.running:
            return

        if self.macro_engine.overrides().trading_halted:
            logger.warning("macro regime is in crisis, refusing to start")
            return

        ohlc = load_daily_ohlc(self.symbol)
        self._prices = ohlc["close"].tolist()
        reference_price = self._prices[0]
        atr_series = compute_atr(ohlc, length=14).dropna()
        atr = round(float(atr_series.iloc[0]), 2) if len(atr_series) else 1.0
        atr = max(atr, 0.5)
        self._build_engines(reference_price, atr)

        self.pipelines = {
            "grid": EnginePipeline(
                self.grid_engine,
                name="grid",
                store=self.store,
                blotter=self.blotters["grid"],
                alerts=self.alerts,
            ),
            "stop_and_reverse": EnginePipeline(
                self.sar_engine,
                name="stop_and_reverse",
                store=self.store,
                blotter=self.blotters["stop_and_reverse"],
                alerts=self.alerts,
            ),
        }

        self._tasks = [asyncio.create_task(pipeline.run()) for pipeline in self.pipelines.values()]
        self._tasks.append(asyncio.create_task(self._run_feed()))
        self.running = True

    async def _run_feed(self) -> None:
        for price in self._prices:
            if not self.running:
                break
            tick = Tick(symbol=self.symbol, price=price)
            for pipeline in self.pipelines.values():
                pipeline.submit_tick(tick)
            self.publisher.publish(tick)
            await asyncio.sleep(self._interval_seconds)
        self.running = False

    async def stop(self) -> None:
        self.running = False
        for pipeline in self.pipelines.values():
            await pipeline.shutdown()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks = []

    def flatten(self) -> list[Fill]:
        closed = []
        last_price = self._prices[-1] if self._prices else None
        if last_price is None:
            return closed

        for name, engine in self.engines().items():
            if engine is None or engine.position.quantity == 0:
                continue
            closing_side = Side.SHORT if engine.position.side == Side.LONG else Side.LONG
            fill = Fill(
                price=last_price,
                quantity=engine.position.quantity,
                side=closing_side,
                timestamp=utc_now(),
            )
            engine.position.apply_fill(fill)
            self.store.save_position_snapshot(engine.position)
            self.publisher.publish_fill(
                name, self.symbol, closing_side.value, last_price, fill.quantity
            )
            closed.append(fill)

        return closed

    def status(self) -> dict:
        return {
            "running": self.running,
            "symbol": self.symbol,
            "engines": list(self.pipelines.keys()),
        }

    def positions(self) -> dict:
        result = {}
        for name, engine in self.engines().items():
            if engine is None:
                continue
            position = engine.position
            result[name] = {
                "symbol": position.symbol,
                "side": position.side.value if position.side else None,
                "quantity": position.quantity,
                "average_price": position.average_price,
                "realized_pnl": position.realized_pnl,
            }
        return result
