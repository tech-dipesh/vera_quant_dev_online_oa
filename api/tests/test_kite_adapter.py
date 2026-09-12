import time
from unittest.mock import MagicMock, patch

import pytest
from kiteconnect.exceptions import NetworkException, TokenException

from app.broker.kite_adapter import KiteMarketDataFeed, KiteOrderGateway
from app.broker.models import OrderRequest
from app.models import Side


def _request() -> OrderRequest:
    return OrderRequest(
        client_order_id="client-1",
        symbol="NIFTY24SEPFUT",
        exchange="NFO",
        side=Side.LONG,
        quantity=1,
    )


@patch("app.broker.kite_adapter.KiteConnect")
def test_place_order_is_idempotent(mock_kite_cls):
    mock_kite = mock_kite_cls.return_value
    mock_kite.place_order.return_value = "KITE-1"
    gateway = KiteOrderGateway(api_key="key", access_token="token")

    first = gateway.place_order(_request())
    second = gateway.place_order(_request())

    assert first == second
    assert mock_kite.place_order.call_count == 1


@patch("app.broker.kite_adapter.time.sleep", lambda seconds: None)
@patch("app.broker.kite_adapter.KiteConnect")
def test_retries_on_network_exception_then_succeeds(mock_kite_cls):
    mock_kite = mock_kite_cls.return_value
    mock_kite.place_order.side_effect = [NetworkException("timeout"), "KITE-2"]
    gateway = KiteOrderGateway(api_key="key", access_token="token")

    ack = gateway.place_order(_request())

    assert ack.broker_order_id == "KITE-2"
    assert mock_kite.place_order.call_count == 2


@patch("app.broker.kite_adapter.KiteConnect")
def test_token_exception_raises_clear_error(mock_kite_cls):
    mock_kite = mock_kite_cls.return_value
    mock_kite.place_order.side_effect = TokenException("expired")
    gateway = KiteOrderGateway(api_key="key", access_token="token")

    with pytest.raises(RuntimeError, match="refresh"):
        gateway.place_order(_request())


@patch("app.broker.kite_adapter.KiteConnect")
def test_reconcile_after_restart_finds_an_order_missing_locally(mock_kite_cls):
    mock_kite = mock_kite_cls.return_value
    mock_kite.orders.return_value = [{"order_id": "1"}, {"order_id": "2"}]
    gateway = KiteOrderGateway(api_key="key", access_token="token")

    report = gateway.reconcile_after_restart()

    assert report.missing_locally == ["1", "2"]
    assert report.missing_at_broker == []
    assert report.is_clean is False


@patch("app.broker.kite_adapter.KiteConnect")
def test_reconcile_after_restart_is_clean_when_local_and_broker_agree(mock_kite_cls):
    mock_kite = mock_kite_cls.return_value
    mock_kite.place_order.return_value = "1"
    mock_kite.orders.return_value = [{"order_id": "1"}]
    gateway = KiteOrderGateway(api_key="key", access_token="token")
    gateway.place_order(_request())

    report = gateway.reconcile_after_restart()

    assert report.known_to_both == ["1"]
    assert report.is_clean is True


@patch("app.broker.kite_adapter.time.sleep", lambda seconds: None)
@patch("app.broker.kite_adapter.KiteConnect")
def test_place_order_is_rate_limited(mock_kite_cls):
    mock_kite = mock_kite_cls.return_value
    mock_kite.place_order.return_value = "KITE-1"
    gateway = KiteOrderGateway(api_key="key", access_token="token", rate_limit_per_second=5)
    gateway._rate_limiter.capacity = 1
    gateway._rate_limiter._tokens = 1

    gateway.place_order(_request())
    second_request = OrderRequest(
        client_order_id="client-2",
        symbol="NIFTY24SEPFUT",
        exchange="NFO",
        side=Side.LONG,
        quantity=1,
    )
    start = time.monotonic()
    gateway.place_order(second_request)
    elapsed = time.monotonic() - start

    assert elapsed >= 0.15


@patch("app.broker.kite_adapter.KiteTicker")
def test_ticks_are_forwarded_to_callback(mock_ticker_cls):
    feed = KiteMarketDataFeed(api_key="key", access_token="token", tokens=[256265])
    received = []
    feed.on_tick(received.append)

    feed._handle_ticks(ws=None, ticks=[{"instrument_token": 256265, "last_price": 99.5}])

    assert len(received) == 1
    assert received[0].price == 99.5


@patch("app.broker.kite_adapter.KiteTicker")
def test_reconnect_triggers_resync(mock_ticker_cls):
    feed = KiteMarketDataFeed(api_key="key", access_token="token", tokens=[256265])
    resynced = []
    feed.on_resync(lambda: resynced.append(True))

    feed._handle_reconnect(attempts_count=1)

    assert resynced == [True]


@patch("app.broker.kite_adapter.KiteTicker")
def test_connect_subscribes_to_configured_tokens(mock_ticker_cls):
    feed = KiteMarketDataFeed(api_key="key", access_token="token", tokens=[256265, 738561])
    mock_ws = MagicMock()

    feed._handle_connect(ws=mock_ws, response=None)

    mock_ws.subscribe.assert_called_once_with([256265, 738561])
