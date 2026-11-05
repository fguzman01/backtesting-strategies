"""Overnight de sesión NYSE con filtro de máximo reciente (MAX(10)), en velas de 1h.

Mecanismo (Quantpedia, resumen de Gemini 2015–2024): la subida de BTC se concentra fuera del horario
bursátil de EE. UU.; si además el precio está en su máximo de las últimas `max_dias` jornadas, la
inercia refuerza la deriva nocturna. Sólo largo.

Reglas (todo con datos hasta el cierre de la vela `t`; entrada en la apertura de `t+1`):
- Hora de EE. UU. (`America/New_York`, con cambio de hora). La vela cuyo cierre cae a las 16:00 ET
  (la que abrió a las 15:00 ET) es la señal; se entra en la apertura de las 16:00 ET.
- Condición: el cierre de esa vela es ≥ el máximo de los cierres de las `max_dias` × 24 velas
  anteriores (incluida ella; no usa nada posterior).
- Salida por regla: la vela que abre a las 09:00 ET manda cerrar en la apertura de las 10:00 ET.
- Riesgo: `stop_atr` × ATR(`atr_n`) de la vela de la señal, medido desde la entrada real.
- Rige todos los días (cripto no cierra los fines de semana): una sola regla fija.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr

ZONA = "America/New_York"


def senales(
    df: pd.DataFrame, max_dias: int = 10, atr_n: int = 24, stop_atr: float = 6.0,
    hora_entrada: int = 16, hora_salida: int = 10,
) -> pd.DataFrame:
    """`hora_entrada`/`hora_salida`: hora ET de la APERTURA donde se entra / se sale."""
    hora_apertura = df.index.tz_convert(ZONA).hour  # hora ET en que ABRE cada vela
    cierre = df["close"]
    ventana = max_dias * 24
    maximo = cierre.rolling(ventana).max()  # incluye la vela actual: sólo el pasado y el presente
    en_maximo = (cierre >= maximo) & maximo.notna()

    # La señal es la vela que abrió una hora antes de `hora_entrada`.
    es_senal = np.asarray(hora_apertura == (hora_entrada - 1) % 24)
    a = atr(df, atr_n)

    direccion = np.where(es_senal & en_maximo.to_numpy() & a.notna().to_numpy(), 1, 0)

    out = pd.DataFrame(index=df.index)
    out["direccion"] = direccion
    out["riesgo"] = stop_atr * a
    out["salida_largo"] = np.asarray(hora_apertura == (hora_salida - 1) % 24)
    return out
