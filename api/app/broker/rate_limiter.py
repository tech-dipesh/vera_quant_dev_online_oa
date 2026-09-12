import time


class TokenBucket:
    def __init__(self, rate_per_second: float, capacity: int) -> None:
        self.rate_per_second = rate_per_second
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate_per_second)
        self._last_refill = now

    def acquire(self) -> None:
        self._refill()
        while self._tokens < 1:
            wait_time = (1 - self._tokens) / self.rate_per_second
            time.sleep(max(wait_time, 0.0))
            self._refill()
        self._tokens -= 1
