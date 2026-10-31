"""Indicadores. Todos causales: el valor en `t` usa sólo velas hasta `t` inclusive."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rango_verdadero(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1)
    return tr.max(axis=1)  # en la primera vela, high - low (prev no existe)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """ATR de Wilder sembrado con la media simple de los primeros `n` rangos (válido desde n−1).

    Misma construcción que `btc-signal-web/scripts/backtest-tendencia-diaria.py`.
    """
    tr = rango_verdadero(df).to_numpy(dtype=float)
    out = np.full(len(tr), np.nan)
    if len(tr) >= n:
        a = tr[:n].mean()
        out[n - 1] = a
        for i in range(n, len(tr)):
            a = (a * (n - 1) + tr[i]) / n
            out[i] = a
    return pd.Series(out, index=df.index)


def ema(s: pd.Series, n: int) -> pd.Series:
    """EMA sembrada con el primer valor, k = 2/(n+1); válida desde la vela n−1."""
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def maximo_previo(s: pd.Series, n: int) -> pd.Series:
    """Máximo de las `n` velas ANTERIORES (excluye la actual)."""
    return s.shift(1).rolling(n, min_periods=n).max()


def minimo_previo(s: pd.Series, n: int) -> pd.Series:
    return s.shift(1).rolling(n, min_periods=n).min()
