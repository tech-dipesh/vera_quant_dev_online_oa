from dataclasses import dataclass, field

from app.models import Fill


@dataclass
class TradeBlotter:
    entries: list[Fill] = field(default_factory=list)

    def record(self, fill: Fill) -> None:
        self.entries.append(fill)

    def as_rows(self) -> list[dict]:
        return [
            {
                "timestamp": fill.timestamp.isoformat(),
                "side": fill.side.value,
                "price": fill.price,
                "quantity": fill.quantity,
            }
            for fill in self.entries
        ]
