from collections.abc import Callable
from dataclasses import dataclass

from app.engines.common import RiskGuard


@dataclass
class Alert:
    level: str
    message: str


class AlertManager:
    def __init__(self, notify: Callable[[Alert], None]) -> None:
        self._notify = notify
        self.history: list[Alert] = []

    def check_risk_guard(self, guard: RiskGuard) -> None:
        if guard.tripped:
            self._raise("critical", "risk guard tripped, trading halted for this engine")

    def check_deviation(self, expected_pnl: float, actual_pnl: float, tolerance: float) -> None:
        if abs(expected_pnl - actual_pnl) > tolerance:
            self._raise(
                "critical",
                f"pnl deviation detected: expected {expected_pnl}, actual {actual_pnl}",
            )

    def _raise(self, level: str, message: str) -> None:
        alert = Alert(level=level, message=message)
        self.history.append(alert)
        self._notify(alert)
