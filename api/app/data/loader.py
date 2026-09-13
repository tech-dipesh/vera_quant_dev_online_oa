import logging
import random

import pandas as pd

from app.data.synthetic import generate_price_walk

logger = logging.getLogger("data.loader")


def load_daily_closes(symbol: str, period: str = "6mo", fallback_steps: int = 120) -> list[float]:
    return load_daily_ohlc(symbol, period, fallback_steps)["close"].tolist()


def load_daily_ohlc(symbol: str, period: str = "6mo", fallback_steps: int = 120) -> pd.DataFrame:
    try:
        import yfinance as yf

        data = yf.download(symbol, period=period, interval="1d", progress=False)
        if data.empty:
            raise ValueError("no data returned for symbol")
        frame = pd.DataFrame(
            {
                "high": data["High"].to_numpy().flatten(),
                "low": data["Low"].to_numpy().flatten(),
                "close": data["Close"].to_numpy().flatten(),
                "volume": data["Volume"].to_numpy().flatten(),
            }
        ).dropna()
        if frame.empty:
            raise ValueError("no usable rows after dropping missing data")
        return frame
    except Exception as error:
        logger.warning("falling back to synthetic data for %s: %s", symbol, error)
        closes = generate_price_walk(start_price=100.0, steps=fallback_steps)
        rng = random.Random(11)
        return pd.DataFrame(
            {
                "close": closes,
                "high": [price + 0.5 for price in closes],
                "low": [price - 0.5 for price in closes],
                "volume": [rng.randint(10_000, 50_000) for _ in closes],
            }
        )
