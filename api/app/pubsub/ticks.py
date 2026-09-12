import json
from collections.abc import AsyncIterator, Iterator

import redis
import redis.asyncio as aioredis

from app.broker.models import Tick

CHANNEL = "live-events"


class TickPublisher:
    def __init__(self, redis_url: str) -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def publish(self, tick: Tick) -> None:
        self._client.publish(
            CHANNEL, json.dumps({"type": "tick", "symbol": tick.symbol, "price": tick.price})
        )

    def publish_fill(
        self, engine: str, symbol: str, side: str, price: float, quantity: int
    ) -> None:
        payload = {
            "type": "fill",
            "engine": engine,
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
        }
        self._client.publish(CHANNEL, json.dumps(payload))


class TickSubscriber:
    def __init__(self, redis_url: str) -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._pubsub = self._client.pubsub()
        self._pubsub.subscribe(CHANNEL)

    def listen(self) -> Iterator[Tick]:
        for message in self._pubsub.listen():
            if message["type"] != "message":
                continue
            payload = json.loads(message["data"])
            if payload.get("type") != "tick":
                continue
            yield Tick(symbol=payload["symbol"], price=payload["price"])

    def close(self) -> None:
        self._pubsub.close()


class AsyncEventSubscriber:
    def __init__(self, redis_url: str) -> None:
        self._client = aioredis.from_url(redis_url, decode_responses=True)
        self._pubsub = self._client.pubsub()

    async def subscribe(self) -> None:
        await self._pubsub.subscribe(CHANNEL)

    async def events(self) -> AsyncIterator[dict]:
        async for message in self._pubsub.listen():
            if message["type"] != "message":
                continue
            yield json.loads(message["data"])

    async def close(self) -> None:
        await self._pubsub.aclose()
        await self._client.aclose()
