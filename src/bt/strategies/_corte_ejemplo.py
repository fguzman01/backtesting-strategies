"""Ejemplo mínimo de estrategia de corte transversal. Sólo para los tests: no está pre-registrada
ni se puede evaluar.

Cada vela `t`: entre los símbolos vigentes (miembros del universo en el mes de `t`, con vela en `t`),
se rankea el retorno de `dias` velas con cierres hasta `t`; largo el primero, corto el último. La
ejecución es en la apertura de `t+1` (la hace el motor).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CORTE_TRANSVERSAL = True


def senales_corte(
    velas: dict[str, pd.DataFrame], miembros: dict[str, list[str]] | None = None,
    dias: int = 2, riesgo_pct: float = 0.05,
) -> dict[str, pd.DataFrame]:
    simbolos = sorted(velas)
    cierres = pd.DataFrame({s: velas[s]["close"] for s in simbolos})
    retorno = cierres / cierres.shift(dias) - 1  # sólo el pasado y el presente
    if miembros is not None:
        mes = cierres.index.strftime("%Y-%m")
        vigente = pd.DataFrame(
            {s: np.isin(mes, list(miembros.get(s, ()))) for s in simbolos}, index=cierres.index
        )
        retorno = retorno.where(vigente)
    # `rank` con desempate por orden alfabético: determinista.
    orden = retorno.rank(axis=1, method="first")
    n = retorno.notna().sum(axis=1)
    out = {}
    for s in simbolos:
        direccion = np.where(orden[s] == n, 1, np.where((orden[s] == 1) & (n >= 2), -1, 0))
        sen = pd.DataFrame(index=cierres.index)
        sen["direccion"] = direccion
        sen["riesgo"] = riesgo_pct * cierres[s]
        out[s] = sen
    return out
