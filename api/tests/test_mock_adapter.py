from app.broker.mock_adapter import MockMarketDataFeed, MockOrderGateway
from app.broker.models import OrderRequest
from app.models import Side


def test_place_order_is_idempotent_on_client_order_id():
    gateway = MockOrderGateway()
    request = OrderRequest(
        client_order_id="abc",
        symbol="NIFTY",
        exchange="NFO",
        side=Side.LONG,
        quantity=1,
    )

    first = gateway.place_order(request)
    second = gateway.place_order(request)

    assert first == second
    assert len(gateway.get_positions()) == 1


def test_market_data_feed_replays_prices_to_callback():
    feed = MockMarketDataFeed("NIFTY", [100, 101, 99])
    received = []
    feed.on_tick(lambda tick: received.append(tick.price))

    feed.connect()

    assert received == [100, 101, 99]
