"""TREND_1D: tendencia sin techo (Donchian 20/10, stop 2×ATR20, filtro EMA200).

Port de `btc-signal-web/scripts/backtest-tendencia-diaria.py` (aprobada en 14 tokens el
2026-10-20; rechazada en oro el 2026-10-24, ver 02-DOCS/decisiones.md). Reglas:

- Largo si el cierre supera el máximo de las `entrada` velas anteriores Y está sobre la EMA;
  corto si perfora el mínimo Y está bajo la EMA.
- Entrada a la apertura siguiente; stop a `stop_atr` × ATR (de la vela de la señal) desde esa
  entrada. Sin objetivo: la salida es el stop o el canal corto.
- Sale a la apertura siguiente si el cierre cruza el canal de `salida` velas en contra.

Para reproducir los números de btc-signal-web: Config(fee_pct_por_lado=0.001, cerrar_al_final=True)
(su costo por lado es comisión 0.05% + deslizamiento 0.05%) y el funding del símbolo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr, ema, maximo_previo, minimo_previo


def senales(
    df: pd.DataFrame, entrada: int = 20, salida: int = 10, atr_n: int = 20, ema_n: int = 200,
    stop_atr: float = 2.0,
) -> pd.DataFrame:
    c = df["close"]
    e = ema(c, ema_n)
    a = atr(df, atr_n)
    largo = (c > maximo_previo(df["high"], entrada)) & (c > e)
    corto = (c < minimo_previo(df["low"], entrada)) & (c < e)

    direccion = np.where(largo, 1, np.where(corto, -1, 0))
    direccion[: max(ema_n, entrada + 1)] = 0  # mismo arranque que el script original
    direccion[(e.isna() | a.isna()).to_numpy()] = 0

    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["riesgo"] = stop_atr * a
    # La salida por canal depende del lado de la posición abierta.
    out["salida_largo"] = c < minimo_previo(df["low"], salida)
    out["salida_corto"] = c > maximo_previo(df["high"], salida)
    return out
