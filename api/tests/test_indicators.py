import pandas as pd

from app.ta.indicators import atr, ema, rsi


def _sample_df(rows: int = 30) -> pd.DataFrame:
    close = [100 + i * 0.5 for i in range(rows)]
    high = [c + 1 for c in close]
    low = [c - 1 for c in close]
    return pd.DataFrame({"high": high, "low": low, "close": close})


def test_atr_returns_series_matching_length():
    df = _sample_df()
    result = atr(df, length=14)
    assert len(result) == len(df)
    assert result.iloc[-1] > 0


def test_ema_tracks_uptrend():
    df = _sample_df()
    result = ema(df, length=10)
    assert result.iloc[-1] > result.iloc[15]


def test_rsi_bounded_between_0_and_100():
    df = _sample_df()
    result = rsi(df, length=14)
    valid = result.dropna()
    assert (valid >= 0).all()
    assert (valid <= 100).all()
