import json
import logging

from app.engines.common import RiskGuard, RiskLimits
from app.models import Fill, Position, Side, utc_now
from app.observability.alerts import AlertManager
from app.observability.blotter import TradeBlotter
from app.observability.logging import JsonFormatter


def test_json_formatter_produces_parseable_structured_line():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="engine.grid",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="fill executed",
        args=(),
        exc_info=None,
    )

    parsed = json.loads(formatter.format(record))

    assert parsed["message"] == "fill executed"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "engine.grid"


def test_blotter_records_fills_as_rows():
    blotter = TradeBlotter()
    blotter.record(Fill(price=100.0, quantity=1, side=Side.LONG, timestamp=utc_now()))

    rows = blotter.as_rows()

    assert len(rows) == 1
    assert rows[0]["side"] == "long"
    assert rows[0]["price"] == 100.0


def test_alert_manager_notifies_when_risk_guard_trips():
    notified = []
    manager = AlertManager(notify=notified.append)
    guard = RiskGuard(RiskLimits(max_position=1, max_loss=1000.0))
    guard.check(Position(symbol="NIFTY", side=Side.LONG, quantity=5, average_price=100.0), 100.0)

    manager.check_risk_guard(guard)

    assert len(notified) == 1
    assert notified[0].level == "critical"


def test_alert_manager_flags_pnl_deviation_beyond_tolerance():
    notified = []
    manager = AlertManager(notify=notified.append)

    manager.check_deviation(expected_pnl=100.0, actual_pnl=50.0, tolerance=10.0)

    assert len(notified) == 1
    assert "deviation" in notified[0].message


def test_alert_manager_stays_quiet_within_tolerance():
    notified = []
    manager = AlertManager(notify=notified.append)

    manager.check_deviation(expected_pnl=100.0, actual_pnl=95.0, tolerance=10.0)

    assert notified == []
