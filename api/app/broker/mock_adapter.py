from collections.abc import Callable, Iterable

from app.broker.models import OrderAck, OrderRequest, Tick


class MockOrderGateway:
    def __init__(self) -> None:
        self._acks: dict[str, OrderAck] = {}
        self._orders: list[OrderRequest] = []

    def place_order(self, request: OrderRequest) -> OrderAck:
        if request.client_order_id in self._acks:
            return self._acks[request.client_order_id]

        broker_order_id = f"MOCK-{len(self._orders) + 1}"
        self._orders.append(request)
        ack = OrderAck(
            client_order_id=request.client_order_id,
            broker_order_id=broker_order_id,
            status="COMPLETE",
        )
        self._acks[request.client_order_id] = ack
        return ack

    def get_positions(self) -> list[OrderRequest]:
        return list(self._orders)


class MockMarketDataFeed:
    def __init__(self, symbol: str, prices: Iterable[float]) -> None:
        self._symbol = symbol
        self._prices = list(prices)
        self._callback: Callable[[Tick], None] | None = None

    def on_tick(self, callback: Callable[[Tick], None]) -> None:
        self._callback = callback

    def connect(self) -> None:
        if self._callback is None:
            return
        for price in self._prices:
            self._callback(Tick(symbol=self._symbol, price=price))

    def close(self) -> None:
        self._prices = []
