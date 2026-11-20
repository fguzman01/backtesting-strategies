"""Efecto MAX de corte transversal diario (idea #20 de 02-DOCS/ideas.md).

Cada vela diaria `t`, entre los símbolos vigentes del universo (miembros del top en el mes de `t` y con
vela en `t`) se calcula MAX = el mayor retorno diario (cierre_s / cierre_{s-1} − 1) de las últimas
`ventana` velas, hasta el cierre de `t` inclusive. Largo los `k` con MAX más alto (demanda por activos
«lotería»: siguen unos días, signo de la fuente), corto los `k` con MAX más bajo (sólo si hay al menos
`2k` símbolos vigentes). La entrada es en la apertura de `t+1` (la hace el motor). Stop a `stop_atr` ×
ATR(`atr_n`) desde la entrada real y trailing a `trailing_atr` × ATR desde el mejor precio desde la
entrada. Sin objetivo: salen el stop/trailing o el timeout (lo fija la spec).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr

CORTE_TRANSVERSAL = True


def senales_corte(
    velas: dict[str, pd.DataFrame], miembros: dict[str, list[str]] | None = None,
    ventana: int = 30, k: int = 3, atr_n: int = 14, stop_atr: float = 2.0, trailing_atr: float = 2.0,
) -> dict[str, pd.DataFrame]:
    simbolos = sorted(velas)
    cierres = pd.DataFrame({s: velas[s]["close"] for s in simbolos})
    diario = cierres / cierres.shift(1) - 1  # sólo el pasado y el presente
    # Ventana completa o nada: con huecos o historia corta el MAX no se calcula.
    maximo = diario.rolling(ventana, min_periods=ventana).max()
    atrs = pd.DataFrame(
        {s: atr(velas[s].dropna(subset=["close"]), atr_n).reindex(cierres.index) for s in simbolos}
    )
    maximo = maximo.where(atrs.notna())  # sin ATR no hay stop: no entra ni rankea
    if miembros is not None:
        mes = cierres.index.strftime("%Y-%m")
        vigente = pd.DataFrame(
            {s: np.isin(mes, list(miembros.get(s, ()))) for s in simbolos}, index=cierres.index
        )
        maximo = maximo.where(vigente)
    orden = maximo.rank(axis=1, method="first")  # desempate alfabético: determinista
    n = maximo.notna().sum(axis=1)
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
