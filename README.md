# README:
- The Vera Quant Developer Online Assessment.
- Make a System with a High Frequency Trading Tech Role


# Quant System

<p align="center">
  <img src="docs/homepage.png" width="720" alt="Live demo run: engines placing fills as ticks stream in" />
</p>

*Replace `docs/demo.gif` with a 5-8s cropped, auto-playing capture: hit
`/demo/start`, let a few fills land on the grid and stop-and-reverse rows,
then flatten. That's the whole story in one loop — no narration needed.*

## Data flow

```
yfinance ──▶ loader ──▶ ATR/EMA/RSI (pandas-ta-classic)
   │ (offline)                   │
   └─▶ synthetic walk ───────────┘
                                  ▼
                     reference price + volatility
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                  ▼
            Grid Engine                  Stop-and-Reverse Engine
                 │                                  │
        MacroRegimeEngine ──▶ spacing/size overrides, or refuse to start
                 │                                  │
                 └──────────────┬───────────────────┘
                                 ▼
                    shared RiskGuard (one kill switch, both engines)
                                 │
                                 ▼
                          EnginePipeline
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
        Postgres            Redis pub/sub        Blotter + RQ
     (fills, snapshots)     (ticks, fills)         (alerts)
              │                  │                   │
              └──────────────────┼───────────────────┘
                                  ▼
                  FastAPI REST  +  /ws/live WebSocket
                                  │
                                  ▼
                          Next.js dashboard
```

Backtests run the identical `Grid Engine` / `Stop-and-Reverse Engine` classes
against historical bars instead of a live feed — same code, different clock.

## Why this stack, not another
- **FastAPI over Flask/Django** — the engines run as `asyncio` tasks pushing
  ticks through a pipeline while the API stays responsive; native
  async + WebSocket support isn't bolted on here, it's load-bearing.
- **Postgres + Alembic over SQLite** — fills and position snapshots are
  written from the pipeline task and read from the API concurrently;
  SQLite's single-writer model isn't built for that.
- **Redis pub/sub + RQ, not in-process queues** — ticks fan out to the
  WebSocket independent of the HTTP request cycle, and alert delivery runs
  on RQ so a slow notification channel can never stall the trading loop.
- **pandas-ta-classic, not pandas-ta** — upstream pandas-ta is unmaintained
  and breaks on numpy ≥ 2.0 (`numpy.NaN` removed); the classic fork is a
  drop-in with active fixes.
- **Mock broker as a first-class adapter, not a test stub** — `/demo/*`
  never needs Kite credentials to exist. Most sample trading repos hardcode
  the broker call and make you fake an entire SDK to run them locally.

## What's not typical here

- One `RiskGuard` instance is shared across both engines, not one per
  strategy. A loss anywhere trips the same switch — most reference
  implementations size-limit each strategy independently and miss the
  case where two "small" strategies compound into one large loss.
- `MacroRegimeEngine` can rewrite engine config (spacing, size) or refuse to
  start trading at all, driven by an external proxy indicator — regime
  awareness usually lives in a notebook, not in the runtime path.
- Backtest and live share engine code by construction, not by convention —
  there is no second implementation to drift out of sync.

## Setup

```
cd api && pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload
cd dashboard && pnpm install && pnpm dev
```
Set `DATABASE_URL` (`postgresql+psycopg://…`) and `REDIS_URL` in `api/.env` first.

## Deploy on Render

| Resource | Root dir | Build | Start |
|---|---|---|---|
| Postgres | — | — | — |
| Redis (Key Value) | — | — | — |
| API (Python) | `api` | `pip install -r requirements.txt` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Dashboard (Node) | `dashboard` | `pnpm install && pnpm build` | `pnpm start` |

- API pre-deploy command: `alembic upgrade head`
- API env: `DATABASE_URL` (add `+psycopg`), `REDIS_URL`, `CORS_ORIGINS=<dashboard URL>`
- Dashboard env: `NEXT_PUBLIC_API_URL=<api URL>`, `NEXT_PUBLIC_WS_URL=wss://<api host>/ws/live`
- After both are live, point `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` at each
  other's real URLs and redeploy — free-tier services sleep, so the first
  request after idle time will be slow to wake.