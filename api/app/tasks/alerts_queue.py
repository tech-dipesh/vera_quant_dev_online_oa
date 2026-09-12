import redis
from rq import Queue


def get_alert_queue(redis_url: str) -> Queue:
    connection = redis.Redis.from_url(redis_url)
    return Queue("alerts", connection=connection)


def dispatch_alert_job(level: str, message: str) -> None:
    print(f"[ALERT:{level}] {message}")
