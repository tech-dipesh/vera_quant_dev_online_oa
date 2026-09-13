# Quant System — Core
Python Service Excution Engine with a Ta Moduel and Backtest Harnes, from a Macro Regine Engine to Broker Adapter.

## Quick start

```
pip install -e ".[dev]"
pytest
```


## Build:
- `app/models.py` — shared `Position`/`Fill` types and P&L math, used by both engines
  so the math isn't duplicated between them
- `app/ta/indicators.py` — ATR, EMA, RSI, wrapping pandas-ta rather than
  reimplementing the math
- `app/engines/common.py` — `RiskGuard`: shared kill-switch and position-cap logic
- `app/engines/grid.py` — grid engine: ATR-based level spacing, pyramiding, kill
  switch, position cap
- `app/engines/stop_and_reverse.py` — stop-and-reverse engine: ATR-based stop
  distance, closes and flips on stop, same shared risk guard
