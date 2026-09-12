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
def test_reconcile_after_restart_returns_broker_order_history(mock_kite_cls):
    mock_kite = mock_kite_cls.return_value
    mock_kite.orders.return_value = [{"order_id": "1"}]
    gateway = KiteOrderGateway(api_key="key", access_token="token")

    assert gateway.reconcile_after_restart() == [{"order_id": "1"}]


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
