from dataclasses import dataclass

from app.models import Side


@dataclass(frozen=True)
class OrderRequest:
    client_order_id: str
    symbol: str
    exchange: str
    side: Side
    quantity: int
    order_type: str = "MARKET"
    price: float | None = None


@dataclass(frozen=True)
class OrderAck:
    client_order_id: str
    broker_order_id: str
    status: str


@dataclass(frozen=True)
class Tick:
    symbol: str
    price: float
