"""Ruptura de Donchian (ejemplo de referencia del motor, no una candidata).

Entra cuando el cierre supera el máximo de las `entrada` velas anteriores; stop a `atr_mult` ATR
del cierre; sale cuando el cierre perfora el mínimo de las `salida` velas anteriores. Sólo largos
salvo `cortos=True`.

Ojo: TREND_1D (Donchian 20/10) ya se rechazó en ORO en btc-signal-web (02-DOCS/decisiones.md).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr, maximo_previo, minimo_previo


def senales(
    df: pd.DataFrame, entrada: int = 20, salida: int = 10, atr_n: int = 14, atr_mult: float = 2.0,
    cortos: bool = False,
) -> pd.DataFrame:
    c = df["close"]
    a = atr(df, atr_n)
    sube = c > maximo_previo(df["high"], entrada)
    baja = c < minimo_previo(df["low"], entrada)

    direccion = np.where(sube, 1, np.where(baja & cortos, -1, 0))
    stop = np.where(direccion == 1, c - atr_mult * a, np.where(direccion == -1, c + atr_mult * a, np.nan))
    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["stop"] = stop
    # Cierra si el precio cruza el canal corto en contra de la posición abierta.
    out["salida_largo"] = c < minimo_previo(df["low"], salida)
    out["salida_corto"] = c > maximo_previo(df["high"], salida)
    out.loc[a.isna(), ["direccion"]] = 0
    return out
