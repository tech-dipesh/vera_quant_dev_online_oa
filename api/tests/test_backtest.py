from app.backtest.harness import CostModel, run_backtest
from app.engines.common import RiskLimits
from app.engines.grid import GridConfig, GridEngine


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


def test_backtest_reconciles_to_a_tick_by_tick_live_run():
    prices = [100, 98, 96, 97, 99, 101, 103, 105]

    backtest_engine = GridEngine(_config())
    result = run_backtest(backtest_engine, prices, CostModel())

    live_engine = GridEngine(_config())
    for price in prices:
        live_engine.on_price(price)

    assert backtest_engine.position.quantity == live_engine.position.quantity
    assert backtest_engine.position.realized_pnl == live_engine.position.realized_pnl
    assert result.ideal_realized_pnl == live_engine.position.realized_pnl


def test_cost_model_reduces_pnl():
    prices = [100, 97.5]

    result_no_cost = run_backtest(GridEngine(_config()), prices, CostModel())
    result_with_cost = run_backtest(
        GridEngine(_config()), prices, CostModel(slippage_bps=50, commission_per_fill=1.0)
    )

    assert result_with_cost.cost_adjusted_pnl < result_no_cost.cost_adjusted_pnl


def test_equity_curve_has_one_point_per_price():
    prices = [100, 98, 96]
    result = run_backtest(GridEngine(_config()), prices, CostModel())
    assert len(result.equity_curve) == len(prices)
