"""Reversión tras salto de liquidaciones: contra una vela de rango/volumen extremos.

Mecanismo (De Nicola 2021; Wen et al. 2022): una vela con cuerpo enorme y volumen anómalo suele ser
una cascada de liquidaciones apalancadas, no información; el precio devuelve parte del movimiento.
Se opera CONTRA el salto, con stop ancho (la lección de la reversión: un stop corto corta las
excursiones antes de que el precio vuelva).

Reglas (todo con datos hasta el cierre de la vela `t`; entrada en la apertura de `t+1`):
- Salto abajo: cierre − apertura ≤ −`salto_atr` × ATR(`atr_n`) de la vela previa Y volumen ≥
  `vol_mult` × media del volumen de las `vol_n` velas previas → largo. Salto arriba: simétrico → corto.
- Riesgo: `stop_atr` × ATR de la vela previa, medido desde la entrada real. Objetivo: lo pone la spec
  con `config.objetivo_r`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr


def senales(
    df: pd.DataFrame, atr_n: int = 24, salto_atr: float = 4.0, vol_n: int = 24, vol_mult: float = 2.0,
    stop_atr: float = 3.0,
) -> pd.DataFrame:
    a_prev = atr(df, atr_n).shift(1)  # el tamaño del salto se mide contra la volatilidad ANTERIOR
    cuerpo = df["close"] - df["open"]
    vol_prev = df["volume"].rolling(vol_n).mean().shift(1)
    vol_ok = df["volume"] >= vol_mult * vol_prev
    abajo = (cuerpo <= -salto_atr * a_prev) & vol_ok
    arriba = (cuerpo >= salto_atr * a_prev) & vol_ok

    direccion = np.where(abajo, 1, np.where(arriba, -1, 0))
    direccion[(a_prev.isna() | vol_prev.isna()).to_numpy()] = 0

    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["riesgo"] = stop_atr * a_prev
    return out
