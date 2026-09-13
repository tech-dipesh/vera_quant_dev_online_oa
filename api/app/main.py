import logging

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.demo import DemoManager
from app.api.schemas import DemoStatusOut, FlattenResultOut
from app.config import load_settings
from app.observability.logging import configure_logging
from app.pubsub.ticks import AsyncEventSubscriber

configure_logging()
logger = logging.getLogger("api.main")

settings = load_settings()
app = FastAPI(title="Quant System Core")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
demo = DemoManager(settings.database_url, settings.redis_url)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/demo/start", response_model=DemoStatusOut)
async def start_demo() -> DemoStatusOut:
    await demo.start()
    return DemoStatusOut(**demo.status())


@app.post("/demo/stop", response_model=DemoStatusOut)
async def stop_demo() -> DemoStatusOut:
    await demo.stop()
    return DemoStatusOut(**demo.status())


@app.post("/demo/flatten", response_model=FlattenResultOut)
async def flatten_demo() -> FlattenResultOut:
    fills = demo.flatten()
    return FlattenResultOut(closed=len(fills))


@app.get("/demo/status", response_model=DemoStatusOut)
async def demo_status() -> DemoStatusOut:
    return DemoStatusOut(**demo.status())


@app.get("/positions")
async def get_positions() -> dict:
    return demo.positions()


@app.get("/blotter")
async def get_blotter() -> dict:
    return {name: blotter.as_rows() for name, blotter in demo.blotters.items()}


@app.get("/macro-regime")
async def macro_regime() -> dict:
    overrides = demo.macro_engine.overrides()
    return {
        "regime": demo.macro_engine.current_regime().value,
        "trading_halted": overrides.trading_halted,
        "spacing_multiplier": overrides.spacing_multiplier,
        "size_multiplier": overrides.size_multiplier,
    }


@app.websocket("/ws/live")
async def live_updates(websocket: WebSocket) -> None:
    await websocket.accept()
    subscriber = AsyncEventSubscriber(settings.redis_url)
    await subscriber.subscribe()
    try:
        async for event in subscriber.events():
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await subscriber.close()
