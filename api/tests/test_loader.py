from app.data.loader import load_daily_closes, load_daily_ohlc


def test_falls_back_to_synthetic_data_when_the_network_is_unreachable():
    frame = load_daily_ohlc("^NSEI", fallback_steps=12)

    assert len(frame) == 12
    assert {"close", "high", "low", "volume"}.issubset(frame.columns)
    assert (frame["high"] >= frame["close"]).all()
    assert (frame["low"] <= frame["close"]).all()
    assert (frame["volume"] > 0).all()


def test_load_daily_closes_returns_a_plain_list():
    closes = load_daily_closes("^NSEI", fallback_steps=8)
    assert len(closes) == 8
    assert all(isinstance(price, float) for price in closes)
