"""Beta a la baja de corte transversal diario (idea #21 de 02-DOCS/ideas.md).

Cada vela diaria `t`, entre los símbolos vigentes del universo (miembros del top en el mes de `t`, con
vela en `t` y ATR) se calcula el beta a la baja contra BTC en las últimas `ventana` velas: sólo con los
días en que BTC cayó (retorno < 0), beta = cov(r_s, r_btc) / var(r_btc) condicionados a esos días. Hace
falta un mínimo de `min_dias_baja` días de caída de BTC con retorno propio válido, o no hay beta.
Largo los `k` con mayor beta a la baja (prima por riesgo de cola: pagan de más por cargar con la caída),
corto los `k` con menor beta (sólo si hay al menos `2k` símbolos vigentes). BTC sólo es la referencia; también
rankea si es vigente. Todo usa datos hasta el cierre de `t` inclusive; la entrada es en la apertura de `t+1`
(la hace el motor). Stop a `stop_atr` × ATR(`atr_n`) y trailing a `trailing_atr` × ATR desde el mejor precio
desde la entrada. Sin objetivo: salen el stop/trailing o el timeout (lo fija la spec).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr

CORTE_TRANSVERSAL = True


def beta_baja(
    retornos: pd.DataFrame, ref: pd.Series, ventana: int, min_dias: int
) -> pd.DataFrame:
    """Beta a la baja móvil de cada columna contra `ref` (sólo pasado y presente)."""
    baja = (ref < 0).astype(float)
    out = {}
    for s in retornos.columns:
        y = retornos[s]
        valido = (y.notna() & ref.notna()).astype(float)
        m = baja.where(valido > 0, 0.0)
        x = ref.where(m > 0, 0.0)
        yy = y.where(m > 0, 0.0)

        def suma(v):
            return v.rolling(ventana, min_periods=ventana).sum()

        completa = suma(valido) >= ventana  # ventana completa de retornos válidos, o nada
        n, sx, sy = suma(m), suma(x), suma(yy)
        sxy, sxx = suma(x * yy), suma(x * x)
        cov = sxy / n - sx * sy / n**2
        var = sxx / n - (sx / n) ** 2
        out[s] = (cov / var).where(completa & (n >= min_dias) & (var > 0))
    return pd.DataFrame(out, index=retornos.index)


def senales_corte(
    velas: dict[str, pd.DataFrame], miembros: dict[str, list[str]] | None = None,
    ventana: int = 120, k: int = 3, min_dias_baja: int = 30, referencia: str = "BTCUSDT",
    atr_n: int = 14, stop_atr: float = 2.0, trailing_atr: float = 2.0,
) -> dict[str, pd.DataFrame]:
    simbolos = sorted(velas)
    cierres = pd.DataFrame({s: velas[s]["close"] for s in simbolos})
    diario = cierres / cierres.shift(1) - 1
    if referencia in velas:
        beta = beta_baja(diario, diario[referencia], ventana, min_dias_baja)
    else:  # sin referencia no hay beta: ninguna señal
        beta = pd.DataFrame(np.nan, index=cierres.index, columns=simbolos)
    atrs = pd.DataFrame(
        {s: atr(velas[s].dropna(subset=["close"]), atr_n).reindex(cierres.index) for s in simbolos}
    )
    beta = beta.where(atrs.notna())  # sin ATR no hay stop: no entra ni rankea
    if miembros is not None:
        mes = cierres.index.strftime("%Y-%m")
        vigente = pd.DataFrame(
            {s: np.isin(mes, list(miembros.get(s, ()))) for s in simbolos}, index=cierres.index
        )
        beta = beta.where(vigente)
    orden = beta.rank(axis=1, method="first")  # desempate alfabético: determinista
    n = beta.notna().sum(axis=1)
    hay_corte = n >= 2 * k
    out = {}
    for s in simbolos:
        largo = hay_corte & (orden[s] > n - k)
        corto = hay_corte & (orden[s] <= k)
        sen = pd.DataFrame(index=cierres.index)
        sen["direccion"] = np.where(largo, 1, np.where(corto, -1, 0)).astype(int)
        sen["riesgo"] = stop_atr * atrs[s]
        sen["trailing"] = trailing_atr * atrs[s]
        out[s] = sen
    return out
