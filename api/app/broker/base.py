from collections.abc import Callable
from typing import Protocol

from app.broker.models import OrderRequest, Tick


class OrderGateway(Protocol):
    def place_order(self, request: OrderRequest) -> object: ...

    def get_positions(self) -> object: ...


class MarketDataFeed(Protocol):
    def on_tick(self, callback: Callable[[Tick], None]) -> None: ...

    def connect(self) -> None: ...

    def close(self) -> None: ...
