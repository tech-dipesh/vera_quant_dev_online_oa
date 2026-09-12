from app.tasks.alerts_queue import dispatch_alert_job, get_alert_queue

REDIS_URL = "redis://localhost:6379/0"


def test_alert_job_gets_enqueued():
    queue = get_alert_queue(REDIS_URL)
    job = queue.enqueue(dispatch_alert_job, "critical", "test alert")
    assert job.get_status() in {"queued", "started", "finished"}
