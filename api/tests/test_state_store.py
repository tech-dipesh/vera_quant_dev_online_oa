import pytest

from app.engines.common import RiskLimits
from app.engines.grid import GridConfig, GridEngine
from app.models import Side
from app.state.store import StateStore

TEST_DATABASE_URL = "postgresql+psycopg://quant:quant@localhost:5432/quant_system"


@pytest.fixture
def store():
    instance = StateStore(TEST_DATABASE_URL)
    yield instance
    instance.drop_all()
    instance.close()


def _grid_config() -> GridConfig:
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


def test_load_position_returns_none_when_nothing_saved(store):
    assert store.load_position("NIFTY") is None


def test_save_and_load_position_roundtrip(store):
    engine = GridEngine(_grid_config())
    engine.on_price(97.5)

    store.save_position_snapshot(engine.position)
    restored = store.load_position("NIFTY")

    assert restored.side == Side.LONG
    assert restored.quantity == engine.position.quantity
    assert restored.average_price == engine.position.average_price


def test_record_fill_increments_fill_count(store):
    engine = GridEngine(_grid_config())
    fills = engine.on_price(97.5)
    for fill in fills:
        store.record_fill("NIFTY", fill)

    assert store.fill_count("NIFTY") == len(fills)


def test_crash_recovery_restores_position_into_a_fresh_engine(store):
    original_engine = GridEngine(_grid_config())
    original_engine.on_price(97.5)
    original_engine.on_price(95.5)
    store.save_position_snapshot(original_engine.position)

    recovered_engine = GridEngine(_grid_config())
    recovered_position = store.load_position("NIFTY")
    recovered_engine.position = recovered_position

    assert recovered_engine.position.quantity == original_engine.position.quantity
    assert recovered_engine.position.average_price == original_engine.position.average_price
