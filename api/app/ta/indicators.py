import pandas as pd
import pandas_ta as ta


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return ta.atr(df["high"], df["low"], df["close"], length=length)


def ema(df: pd.DataFrame, length: int = 20) -> pd.Series:
    return ta.ema(df["close"], length=length)


def rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return ta.rsi(df["close"], length=length)
