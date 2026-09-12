from app.engines.common import RiskLimits
from app.engines.stop_and_reverse import StopAndReverseConfig, StopAndReverseEngine
from app.models import Side


def _engine() -> StopAndReverseEngine:
    config = StopAndReverseConfig(
        symbol="NIFTY",
        atr=2.0,
        stop_multiplier=1.0,
        size=1,
        limits=RiskLimits(max_position=100, max_loss=1000.0),
    )
    return StopAndReverseEngine(config)


def test_enter_sets_stop_below_price_for_long():
    engine = _engine()
    engine.enter(100.0, Side.LONG)
    assert engine.stop_price == 98.0


def test_stop_hit_closes_and_reverses_to_short():
    engine = _engine()
    engine.enter(100.0, Side.LONG)
    fills = engine.on_price(97.0)
    assert len(fills) == 2
    assert fills[0].side == Side.SHORT
    assert fills[1].side == Side.SHORT
    assert engine.position.side == Side.SHORT
    assert engine.position.quantity == 1


def test_no_action_before_stop_is_hit():
    engine = _engine()
    engine.enter(100.0, Side.LONG)
    fills = engine.on_price(99.0)
    assert fills == []


def test_kill_switch_stops_reversal_after_max_loss():
    engine = _engine()
    engine.config.limits.max_loss = 1.0
    engine.enter(100.0, Side.LONG)
    fills = engine.on_price(97.0)
    assert len(fills) == 1
    assert engine.risk_guard.tripped is True
    second = engine.on_price(200.0)
    assert second == []
