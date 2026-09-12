from app.cache.macro_cache import MacroProxyCache

REDIS_URL = "redis://localhost:6379/0"


def test_set_and_get_roundtrip():
    cache = MacroProxyCache(REDIS_URL, ttl_seconds=5)
    cache.set("india_vix_test", 14.2)
    assert cache.get("india_vix_test") == 14.2


def test_get_returns_none_when_missing():
    cache = MacroProxyCache(REDIS_URL, ttl_seconds=5)
    assert cache.get("proxy_that_does_not_exist") is None
