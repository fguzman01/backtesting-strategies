"""TREND_1D con trailing en ATR REAL (desde la entrada), sin canal de salida.

Pregunta nueva (idea #3 de 02-DOCS/ideas.md): ¿un stop que sigue al mejor precio desde la entrada,
a `trailing_atr` × ATR, deja correr las tendencias buenas y corta las malas antes que el tope fijo?
A diferencia de `tendencia_chandelier` (máximo móvil sin estado, que casi nunca actuó), aquí la
estrategia devuelve la columna `trailing` y es el motor (`bt.engine`) quien mueve el stop detrás
del mejor precio DESDE LA ENTRADA.

Reglas (entrada y stop inicial idénticos a `tendencia_donchian`):
- Largo si el cierre supera el máximo de las `entrada` velas anteriores Y está sobre la EMA;
  corto simétrico. Entrada a la apertura siguiente; stop inicial a `stop_atr` × ATR.
- Trailing: distancia `trailing_atr` × ATR (de la vela de cada cierre). Sin canal corto de salida:
  salen el stop/trailing o el timeout del motor.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr, ema, maximo_previo, minimo_previo


def senales(
    df: pd.DataFrame, entrada: int = 20, atr_n: int = 20, ema_n: int = 200,
    stop_atr: float = 2.0, trailing_atr: float = 2.0,
) -> pd.DataFrame:
    c = df["close"]
    e = ema(c, ema_n)
    a = atr(df, atr_n)
    largo = (c > maximo_previo(df["high"], entrada)) & (c > e)
    corto = (c < minimo_previo(df["low"], entrada)) & (c < e)

    direccion = np.where(largo, 1, np.where(corto, -1, 0))
    direccion[: max(ema_n, entrada + 1)] = 0
    direccion[(e.isna() | a.isna()).to_numpy()] = 0

    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["riesgo"] = stop_atr * a
    out["trailing"] = trailing_atr * a
    return out
