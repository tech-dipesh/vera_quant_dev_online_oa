import time

from app.broker.models import Tick
from app.pubsub.ticks import TickPublisher, TickSubscriber

REDIS_URL = "redis://localhost:6379/0"


def test_publish_and_subscribe_roundtrip():
    subscriber = TickSubscriber(REDIS_URL)
    publisher = TickPublisher(REDIS_URL)
    time.sleep(0.1)

    publisher.publish(Tick(symbol="NIFTY", price=100.5))
    received = next(subscriber.listen())

    assert received.symbol == "NIFTY"
    assert received.price == 100.5

    subscriber.close()
