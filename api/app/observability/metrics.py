from prometheus_client import Counter, Gauge

FILLS_TOTAL = Counter("fills_total", "Total fills executed", ["engine"])
POSITION_QUANTITY = Gauge("position_quantity", "Current position quantity", ["engine"])
REALIZED_PNL = Gauge("realized_pnl", "Realized PnL", ["engine"])
RISK_GUARD_TRIPPED = Gauge(
    "risk_guard_tripped", "1 if the risk guard has tripped, else 0", ["engine"]
)


def record_engine_state(engine_name: str, engine) -> None:
    POSITION_QUANTITY.labels(engine=engine_name).set(engine.position.quantity)
    REALIZED_PNL.labels(engine=engine_name).set(engine.position.realized_pnl)
    RISK_GUARD_TRIPPED.labels(engine=engine_name).set(1 if engine.risk_guard.tripped else 0)


def record_fills(engine_name: str, fill_count: int) -> None:
    if fill_count:
        FILLS_TOTAL.labels(engine=engine_name).inc(fill_count)
