from app.engines.common import RiskLimits
from app.engines.grid import GridConfig, GridEngine
from app.models import Side


def _engine(**overrides) -> GridEngine:
    config = GridConfig(
        symbol="NIFTY",
        reference_price=100.0,
        atr=2.0,
        spacing_multiplier=1.0,
        levels_each_side=3,
        size_per_level=1,
        pyramiding_factor=1.0,
        limits=RiskLimits(max_position=100, max_loss=1000.0),
    )
    for key, value in overrides.items():
        setattr(config, key, value)
    return GridEngine(config)


def test_builds_symmetric_levels_around_reference_price():
    engine = _engine()
    assert engine.levels == [94.0, 96.0, 98.0, 102.0, 104.0, 106.0]


def test_price_drop_fills_one_buy_level():
    engine = _engine()
    fills = engine.on_price(97.5)
    assert len(fills) == 1
    assert fills[0].side == Side.LONG
    assert engine.position.quantity == 1


def test_does_not_refill_same_level_twice():
    engine = _engine()
    engine.on_price(97.5)
    fills = engine.on_price(97.4)
    assert fills == []


def test_kill_switch_stops_new_fills_after_max_loss():
    engine = _engine(limits=RiskLimits(max_position=100, max_loss=1.0))
    engine.on_price(97.5)
    engine.risk_guard.check(engine.position, 50.0)
    fills = engine.on_price(93.9)
    assert fills == []
