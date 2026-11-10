"""Continuación tras shock de volumen con retorno previo (idea #13 de 02-DOCS/ideas.md).

Fuente: Bianchi, Babiak & Dickerson (J. Banking & Finance 142, 2022): el volumen anormal
combinado con el retorno previo predice el retorno siguiente en la misma dirección; el volumen solo
casi no predice. Reglas (todo con datos hasta el cierre de la vela `t`; entrada en la apertura de t+1):

- Volumen anormal: el volumen de `t` supera el percentil `pct_volumen` del volumen de las `ventana_vol`
  velas ANTERIORES (la vela actual no entra en su propia referencia).
- Retorno previo: el movimiento de las últimas `retorno_velas` velas (cierre de `t` contra cierre de
  `t − retorno_velas`) vale al menos `umbral_atr` × ATR en valor absoluto. Normalizar por ATR hace que
  un único umbral sirva para todos los tokens del universo dinámico.
- Dirección: la del retorno previo (continuación). Largo si subió, corto si cayó.
- Stop inicial a `stop_atr` × ATR de la entrada; trailing a `trailing_atr` × ATR desde el mejor precio
  desde la entrada (lo mueve el motor, `bt.engine`). Sin objetivo ni canal de salida: salen el
  stop/trailing o el timeout de la spec.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr


def senales(
    df: pd.DataFrame, ventana_vol: int = 180, pct_volumen: float = 0.9, retorno_velas: int = 6,
    umbral_atr: float = 2.0, atr_n: int = 14, stop_atr: float = 2.0, trailing_atr: float = 2.0,
) -> pd.DataFrame:
    c = df["close"]
    a = atr(df, atr_n)
    ref_vol = df["volume"].shift(1).rolling(ventana_vol, min_periods=ventana_vol).quantile(pct_volumen)
    anormal = df["volume"] > ref_vol
    mov = c - c.shift(retorno_velas)
    fuerte = mov.abs() >= umbral_atr * a

    direccion = np.where(anormal & fuerte, np.sign(mov), 0).astype(int)
    direccion[(a.isna() | ref_vol.isna() | mov.isna()).to_numpy()] = 0

    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["riesgo"] = stop_atr * a
    out["trailing"] = trailing_atr * a
    return out
