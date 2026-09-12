from app.engines.common import RiskGuard, RiskLimits
from app.models import Position, Side


def test_trips_when_position_exceeds_max_size():
    guard = RiskGuard(RiskLimits(max_position=5, max_loss=1000.0))
    position = Position(symbol="NIFTY", side=Side.LONG, quantity=6, average_price=100.0)
    assert guard.check(position, 100.0) is False
    assert guard.tripped is True


def test_trips_when_loss_exceeds_limit():
    guard = RiskGuard(RiskLimits(max_position=100, max_loss=50.0))
    position = Position(symbol="NIFTY", side=Side.LONG, quantity=1, average_price=100.0)
    assert guard.check(position, 40.0) is False


def test_passes_within_limits():
    guard = RiskGuard(RiskLimits(max_position=100, max_loss=50.0))
    position = Position(symbol="NIFTY", side=Side.LONG, quantity=1, average_price=100.0)
    assert guard.check(position, 99.0) is True
