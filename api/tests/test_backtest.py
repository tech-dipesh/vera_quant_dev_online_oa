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


def test_walk_forward_splits_into_non_overlapping_sequential_folds():
    from app.backtest.harness import run_walk_forward

    prices = list(range(100, 130))
    folds = run_walk_forward(
        lambda: GridEngine(_config()), prices, fold_count=3, cost_model=CostModel()
    )

    assert len(folds) == 3
    all_fold_prices = [price for fold in folds for price in fold.prices]
    assert all_fold_prices == prices


def test_walk_forward_gives_each_fold_a_fresh_engine():
    from app.backtest.harness import run_walk_forward

    prices = [100.0] * 10 + [90.0] * 10
    folds = run_walk_forward(
        lambda: GridEngine(_config()), prices, fold_count=2, cost_model=CostModel()
    )

    assert folds[0].result.fills == []
    assert len(folds[1].result.fills) >= 1
