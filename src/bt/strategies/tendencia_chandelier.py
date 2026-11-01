"""TREND_1D con salida chandelier (trailing en ATR sin estado) y tope de tiempo del motor.

Pregunta nueva (idea #1 de 02-DOCS/ideas.md): ¿dejar correr las tendencias con un trailing en ATR,
cortando a los 14 días, conserva el edge de TREND_1D dentro del alcance? Hija de
`2026-10-31-trend1d-tope-7d` (rechazada al borde); el mecanismo cambia: no es un tope más largo
sino reemplazar el canal corto de 10 velas por un trailing que se ajusta a la volatilidad.

Reglas (entrada y stop inicial idénticos a `tendencia_donchian`):
- Largo si el cierre supera el máximo de las `entrada` velas anteriores Y está sobre la EMA;
  corto simétrico. Entrada a la apertura siguiente; stop inicial a `stop_atr` × ATR.
- Salida chandelier: largo sale a la apertura siguiente si el cierre cae por debajo de
  (máximo de los `salida_n` últimos máximos − `salida_atr` × ATR); corto simétrico. Es una
  aproximación sin estado del trailing (la ventana móvil reemplaza al "máximo desde la entrada"):
  el contrato del motor no le pasa a la estrategia la posición abierta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr, ema, maximo_previo, minimo_previo


def senales(
    df: pd.DataFrame, entrada: int = 20, salida_n: int = 22, salida_atr: float = 3.0,
    atr_n: int = 20, ema_n: int = 200, stop_atr: float = 2.0,
) -> pd.DataFrame:
    c = df["close"]
    e = ema(c, ema_n)
    a = atr(df, atr_n)
    largo = (c > maximo_previo(df["high"], entrada)) & (c > e)
    corto = (c < minimo_previo(df["low"], entrada)) & (c < e)

    direccion = np.where(largo, 1, np.where(corto, -1, 0))
    direccion[: max(ema_n, entrada + 1)] = 0
    direccion[(e.isna() | a.isna()).to_numpy()] = 0

    techo = df["high"].rolling(salida_n, min_periods=salida_n).max()
    piso = df["low"].rolling(salida_n, min_periods=salida_n).min()

    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["riesgo"] = stop_atr * a
    out["salida_largo"] = c < (techo - salida_atr * a)
    out["salida_corto"] = c > (piso + salida_atr * a)
    return out
