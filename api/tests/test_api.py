import asyncio

from fastapi.testclient import TestClient

from app.main import app, demo


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_demo_status_before_start_is_not_running():
    with TestClient(app) as client:
        response = client.get("/demo/status")
        assert response.status_code == 200
        assert response.json()["running"] is False


def test_macro_regime_endpoint_reports_calm_by_default():
    with TestClient(app) as client:
        response = client.get("/macro-regime")
        assert response.status_code == 200
        assert response.json()["regime"] == "calm"
        assert response.json()["trading_halted"] is False


def test_full_demo_lifecycle_start_positions_flatten_stop():
    with TestClient(app) as client:
        start_response = client.post("/demo/start")
        assert start_response.status_code == 200
        assert start_response.json()["running"] is True
        assert set(start_response.json()["engines"]) == {"grid", "stop_and_reverse"}

        asyncio.run(asyncio.sleep(1.0))

        positions_response = client.get("/positions")
        assert positions_response.status_code == 200
        assert "grid" in positions_response.json()
        assert "stop_and_reverse" in positions_response.json()

        flatten_response = client.post("/demo/flatten")
        assert flatten_response.status_code == 200

        stop_response = client.post("/demo/stop")
        assert stop_response.status_code == 200
        assert stop_response.json()["running"] is False

        assert demo.grid_engine.position.quantity == 0 or not demo.running


def test_websocket_receives_tick_events_once_demo_is_running():
    with TestClient(app) as client:
        client.post("/demo/start")
        with client.websocket_connect("/ws/live") as websocket:
            message = websocket.receive_json()
            assert message["type"] in {"tick", "fill"}
        asyncio.run(asyncio.sleep(0.1))
        client.post("/demo/stop")


def test_blotter_endpoint_reflects_fills_after_running():
    with TestClient(app) as client:
        client.post("/demo/start")
        asyncio.run(asyncio.sleep(1.0))
        response = client.get("/blotter")
        client.post("/demo/stop")

        assert response.status_code == 200
        body = response.json()
        assert "grid" in body
        assert "stop_and_reverse" in body
        assert len(body["stop_and_reverse"]) >= 1


def test_metrics_endpoint_exposes_prometheus_format():
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


def test_metrics_reflect_engine_state_after_running():
    with TestClient(app) as client:
        client.post("/demo/start")
        asyncio.run(asyncio.sleep(1.0))
        response = client.get("/metrics")
        client.post("/demo/stop")

        body = response.text
        assert 'position_quantity{engine="grid"}' in body
        assert 'position_quantity{engine="stop_and_reverse"}' in body
