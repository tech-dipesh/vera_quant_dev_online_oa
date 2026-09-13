from app.engines.common import RiskLimits
from app.engines.grid import GridConfig
from app.macro_regime.engine import MacroProxy, MacroRegimeEngine, Regime


def _proxy(value: float, elevated: float = 20.0, crisis: float = 35.0) -> MacroProxy:
    return MacroProxy(
        name="india_vix", value=value, elevated_threshold=elevated, crisis_threshold=crisis
    )


def test_calm_when_all_proxies_below_thresholds():
    engine = MacroRegimeEngine([_proxy(12.0)])
    assert engine.current_regime() == Regime.CALM
    assert engine.overrides().trading_halted is False


def test_elevated_when_a_proxy_crosses_elevated_threshold():
    engine = MacroRegimeEngine([_proxy(12.0), _proxy(24.0)])
    assert engine.current_regime() == Regime.ELEVATED


def test_crisis_dominates_when_any_proxy_hits_crisis_threshold():
    engine = MacroRegimeEngine([_proxy(12.0), _proxy(24.0), _proxy(40.0)])
    assert engine.current_regime() == Regime.CRISIS
    assert engine.overrides().trading_halted is True


def test_apply_to_grid_config_widens_spacing_and_shrinks_size_in_elevated():
    engine = MacroRegimeEngine([_proxy(24.0)])
    config = GridConfig(
        symbol="NIFTY",
        reference_price=100.0,
        atr=2.0,
        spacing_multiplier=1.0,
        levels_each_side=3,
        size_per_level=4,
        pyramiding_factor=1.0,
        limits=RiskLimits(max_position=100, max_loss=1000.0),
    )

    engine.apply_to_grid_config(config)

    assert config.spacing_multiplier == 1.5
    assert config.size_per_level == 2
