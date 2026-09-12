import time
from collections.abc import Callable
from dataclasses import dataclass, field

from kiteconnect import KiteConnect, KiteTicker
from kiteconnect.exceptions import NetworkException, TokenException

from app.broker.models import OrderAck, OrderRequest, Tick
from app.broker.rate_limiter import TokenBucket


class KiteAuthSession:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self.access_token: str | None = None

    def refresh(self, request_token: str) -> str:
        kite = KiteConnect(api_key=self._api_key)
        session = kite.generate_session(request_token, api_secret=self._api_secret)
        self.access_token = session["access_token"]
        return self.access_token


@dataclass(frozen=True)
class ReconciliationReport:
    known_to_both: list[str] = field(default_factory=list)
    missing_locally: list[str] = field(default_factory=list)
    missing_at_broker: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.missing_locally and not self.missing_at_broker


class KiteOrderGateway:
    def __init__(
        self,
        api_key: str,
        access_token: str,
        max_retries: int = 3,
        rate_limit_per_second: float = 8,
    ) -> None:
        self._kite = KiteConnect(api_key=api_key, access_token=access_token)
        self._max_retries = max_retries
        self._acks: dict[str, OrderAck] = {}
        self._rate_limiter = TokenBucket(rate_per_second=rate_limit_per_second, capacity=10)

    def place_order(self, request: OrderRequest) -> OrderAck:
        if request.client_order_id in self._acks:
            return self._acks[request.client_order_id]

        transaction_type = "BUY" if request.side.value == "long" else "SELL"
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            self._rate_limiter.acquire()
            try:
                broker_order_id = self._kite.place_order(
                    variety=self._kite.VARIETY_REGULAR,
                    exchange=request.exchange,
                    tradingsymbol=request.symbol,
                    transaction_type=transaction_type,
                    quantity=request.quantity,
                    product=self._kite.PRODUCT_MIS,
                    order_type=request.order_type,
                    price=request.price,
                    tag=request.client_order_id,
                )
                ack = OrderAck(
                    client_order_id=request.client_order_id,
                    broker_order_id=broker_order_id,
                    status="PLACED",
                )
                self._acks[request.client_order_id] = ack
                return ack
            except NetworkException as error:
                last_error = error
                time.sleep(2**attempt)
            except TokenException as error:
                raise RuntimeError(
                    "Kite access token has expired, refresh it with KiteAuthSession before retrying"
                ) from error

        raise RuntimeError(
            f"order placement failed after {self._max_retries} retries"
        ) from last_error

    def get_positions(self) -> dict:
        return self._kite.positions()

    def reconcile_after_restart(self) -> ReconciliationReport:
        broker_orders = self._kite.orders()
        broker_ids = {order["order_id"] for order in broker_orders}
        local_ids = {ack.broker_order_id for ack in self._acks.values()}
        return ReconciliationReport(
            known_to_both=sorted(broker_ids & local_ids),
            missing_locally=sorted(broker_ids - local_ids),
            missing_at_broker=sorted(local_ids - broker_ids),
        )


class KiteMarketDataFeed:
    def __init__(self, api_key: str, access_token: str, tokens: list[int]) -> None:
        self._ticker = KiteTicker(api_key, access_token)
        self._tokens = tokens
        self._callback: Callable[[Tick], None] | None = None
        self._on_resync: Callable[[], None] | None = None
        self._ticker.on_ticks = self._handle_ticks
        self._ticker.on_connect = self._handle_connect
        self._ticker.on_reconnect = self._handle_reconnect

    def on_tick(self, callback: Callable[[Tick], None]) -> None:
        self._callback = callback

    def on_resync(self, callback: Callable[[], None]) -> None:
        self._on_resync = callback

    def connect(self) -> None:
        self._ticker.connect(threaded=True)

    def close(self) -> None:
        self._ticker.close()

    def _handle_connect(self, ws, response) -> None:
        ws.subscribe(self._tokens)

    def _handle_reconnect(self, attempts_count: int) -> None:
        if self._on_resync is not None:
            self._on_resync()

    def _handle_ticks(self, ws, ticks: list[dict]) -> None:
        if self._callback is None:
            return
        for tick in ticks:
            self._callback(Tick(symbol=str(tick["instrument_token"]), price=tick["last_price"]))
