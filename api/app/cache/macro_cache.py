import json

import redis


class MacroProxyCache:
    def __init__(self, redis_url: str, ttl_seconds: int = 60) -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds

    def set(self, name: str, value: float) -> None:
        self._client.set(f"macro:{name}", json.dumps(value), ex=self._ttl_seconds)

    def get(self, name: str) -> float | None:
        raw = self._client.get(f"macro:{name}")
        return json.loads(raw) if raw is not None else None
