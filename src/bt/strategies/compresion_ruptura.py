"""Ruptura tras compresión de volatilidad en 4h (idea #12 de 02-DOCS/ideas.md).

La volatilidad se agrupa: tras un período de rango muy estrecho el rango siguiente tiende a ser
mayor. La dirección no se predice: se espera a que el precio salga de la caja comprimida. Reglas
(todo con datos hasta el cierre de la vela `t`; entrada en la apertura de t+1):

- Ancho de Bollinger: (banda superior − inferior) / media = 2·`bb_k`·σ / media, con `bb_n` velas.
- Compresión en la vela `s`: su ancho está en o por debajo del percentil `pct_ancho` de los anchos de
  las `ventana_pct` velas ANTERIORES (la vela no entra en su propia referencia).
- Caja: máximo y mínimo de las `bb_n` velas que terminan en la última vela comprimida `s`. Sigue
  vigente hasta `vigencia` velas después de `s`.
- Señal en `t`: el cierre de `t` sale de la caja vigente (calculada con velas hasta t−1) y el de t−1
  no estaba fuera de ella del mismo lado. Largo arriba, corto abajo. Una señal por cruce.
- Stop: al otro lado de la caja, o a `stop_min_atr` × ATR del cierre si la caja es más estrecha que
  eso (para que la comisión no pese de más en R). Trailing a `trailing_atr` × ATR desde el mejor precio
  desde la entrada (lo mueve el motor, `bt.engine`). Sin objetivo: salen el stop/trailing o el timeout.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr


def senales(
    df: pd.DataFrame, bb_n: int = 20, bb_k: float = 2.0, ventana_pct: int = 180,
    pct_ancho: float = 0.10, vigencia: int = 6, atr_n: int = 14, stop_min_atr: float = 1.0,
    trailing_atr: float = 2.0,
) -> pd.DataFrame:
    c = df["close"]
    a = atr(df, atr_n)
    media = c.rolling(bb_n, min_periods=bb_n).mean()
    sigma = c.rolling(bb_n, min_periods=bb_n).std(ddof=0)
    ancho = 2 * bb_k * sigma / media
    ref = ancho.shift(1).rolling(ventana_pct, min_periods=ventana_pct).quantile(pct_ancho)
    comprimida = (ancho <= ref) & ref.notna()

    hi = df["high"].rolling(bb_n, min_periods=bb_n).max()
    lo = df["low"].rolling(bb_n, min_periods=bb_n).min()
    # Caja de la última vela comprimida, vigente `vigencia` velas después; en `t` se usa la de t−1.
    caja_hi = hi.where(comprimida).ffill(limit=vigencia).shift(1)
    caja_lo = lo.where(comprimida).ffill(limit=vigencia).shift(1)

    arriba = c > caja_hi
    abajo = c < caja_lo
    largo = arriba & ~(c.shift(1) > caja_hi.shift(1)).fillna(False)
    corto = abajo & ~(c.shift(1) < caja_lo.shift(1)).fillna(False)

    direccion = np.where(largo, 1, np.where(corto, -1, 0)).astype(int)
    direccion[(a.isna() | caja_hi.isna() | caja_lo.isna()).to_numpy()] = 0

    stop = np.where(
        direccion == 1, np.minimum(caja_lo, c - stop_min_atr * a),
        np.where(direccion == -1, np.maximum(caja_hi, c + stop_min_atr * a), np.nan),
    )

    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["stop"] = stop
    out["trailing"] = trailing_atr * a
    return out
