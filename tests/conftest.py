import numpy as np
import pandas as pd
import pytest


def velas(filas, inicio="2024-01-01", freq="1D") -> pd.DataFrame:
    """filas: lista de (open, high, low, close)."""
    idx = pd.date_range(inicio, periods=len(filas), freq=freq, tz="UTC", name="time")
    df = pd.DataFrame(filas, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    df["volume"] = 1.0
    return df


def senal(df, en: dict) -> pd.DataFrame:
    """en: {posición: dict(direccion=..., stop=..., objetivo=..., salida=...)}"""
    s = pd.DataFrame(index=df.index)
    s["direccion"] = 0
    s["stop"] = np.nan
    s["objetivo"] = np.nan
    s["salida"] = False
    for pos, vals in en.items():
        for k, v in vals.items():
            s.iloc[pos, s.columns.get_loc(k)] = v
    return s


@pytest.fixture
def paseo():
    """Paseo aleatorio determinista tipo BTC diario, 2019-01 → 2026-10."""
    rng = np.random.default_rng(42)
    idx = pd.date_range("2019-01-01", "2026-10-30", freq="1D", tz="UTC", name="time")
    ret = rng.normal(0.0008, 0.035, len(idx))
    close = 4000 * np.exp(np.cumsum(ret))
    open_ = np.concatenate([[close[0]], close[:-1]])
    rango = np.abs(rng.normal(0, 0.02, len(idx))) * close
    df = pd.DataFrame(
        {
            "open": open_,
            "high": np.maximum(open_, close) + rango,
            "low": np.minimum(open_, close) - rango,
            "close": close,
            "volume": 1.0,
        },
        index=idx,
    )
    return df
