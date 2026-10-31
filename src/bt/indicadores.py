"""Indicadores. Todos causales: el valor en `t` usa sólo velas hasta `t` inclusive."""

from __future__ import annotations

import pandas as pd


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """ATR de Wilder."""
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(
        axis=1
    )
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def maximo_previo(s: pd.Series, n: int) -> pd.Series:
    """Máximo de las `n` velas ANTERIORES (excluye la actual)."""
    return s.shift(1).rolling(n, min_periods=n).max()


def minimo_previo(s: pd.Series, n: int) -> pd.Series:
    return s.shift(1).rolling(n, min_periods=n).min()
