import time

from app.broker.rate_limiter import TokenBucket


def test_allows_burst_up_to_capacity_without_waiting():
    bucket = TokenBucket(rate_per_second=1, capacity=3)
    start = time.monotonic()
    for _ in range(3):
        bucket.acquire()
    assert time.monotonic() - start < 0.1


def test_blocks_once_capacity_is_exhausted():
    bucket = TokenBucket(rate_per_second=20, capacity=1)
    bucket.acquire()
    start = time.monotonic()
    bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.03
