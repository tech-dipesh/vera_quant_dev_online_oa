# NIFTY Grid & SAR Terminal
Live dashboard for the grid and stop-and-reverse execution engines. Consumes the
FastAPI core over REST and WebSocket

## Quick start
```
pnpm install
cp .env.local.example .env.local
pnpm dev
```
Need to first Run Backend Server and it'll run on: `http://localhost:3000`

## Features:
- Live price, connection status, and start/stop/flatten controls
- Grid and stop-and-reverse position panels (side, quantity, avg price, realized P&L)
- Macro regime badge (calm/elevated/crisis, halts reflected live)
- Combined realized P&L sparkline, sampled on each poll
- Trade blotter fed by WebSocket fill events

## Architecture notes
- All API responses and WebSocket messages are validated with Zod (`src/lib/schemas.ts`)
  before touching component state — a malformed payload is dropped, not crashed on.
- The WebSocket hook (`src/hooks/useLiveFeed.ts`) reconnects automatically on close.
- Positions/status/macro-regime are polled every 2s; ticks and fills stream live over
  the WebSocket rather than being polled.
