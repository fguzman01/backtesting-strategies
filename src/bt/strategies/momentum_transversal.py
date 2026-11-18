"""Momentum de corte transversal diario (idea #17 de 02-DOCS/ideas.md).

Cada vela diaria `t`, entre los símbolos vigentes del universo (miembros del top en el mes de `t` y con
vela en `t`) se rankea el retorno de `lookback` cierres (cierre_t / cierre_{t-lookback} − 1), sólo con
datos hasta el cierre de `t`. Largo los `k` mejores, corto los `k` peores (sólo si hay al menos `2k`
símbolos vigentes, para que no se solapen). La entrada es en la apertura de `t+1` (la hace el motor).
Stop a `stop_atr` × ATR(`atr_n`) desde la entrada real y trailing a `trailing_atr` × ATR desde el mejor
precio desde la entrada. Sin objetivo: salen el stop/trailing o el timeout (lo fija la spec).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.indicadores import atr

CORTE_TRANSVERSAL = True


def senales_corte(
    velas: dict[str, pd.DataFrame], miembros: dict[str, list[str]] | None = None,
    lookback: int = 7, k: int = 3, atr_n: int = 14, stop_atr: float = 2.0, trailing_atr: float = 2.0,
) -> dict[str, pd.DataFrame]:
    simbolos = sorted(velas)
    cierres = pd.DataFrame({s: velas[s]["close"] for s in simbolos})
    retorno = cierres / cierres.shift(lookback) - 1  # sólo el pasado y el presente
    # ATR de cada símbolo sobre sus propias velas (las filas sin vela no entran) y vuelto al índice común.
    atrs = pd.DataFrame(
        {s: atr(velas[s].dropna(subset=["close"]), atr_n).reindex(cierres.index) for s in simbolos}
    )
    # Sin ATR no hay stop: ese símbolo no puede entrar ni rankear.
    retorno = retorno.where(atrs.notna())
    if miembros is not None:
        mes = cierres.index.strftime("%Y-%m")
        vigente = pd.DataFrame(
            {s: np.isin(mes, list(miembros.get(s, ()))) for s in simbolos}, index=cierres.index
        )
        retorno = retorno.where(vigente)
    orden = retorno.rank(axis=1, method="first")  # desempate por orden alfabético: determinista
    n = retorno.notna().sum(axis=1)
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
