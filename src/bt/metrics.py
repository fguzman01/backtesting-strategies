"""Agregación de trades. Mismas reglas que `btc-signal-web/src/lib/backtest/metrics.ts`.

`avgRNeto` decide; el win rate es contexto. Un resultado no es concluyente si: la muestra es corta,
la brecha entre modelos de llenado supera al propio avgR, los tramos temporales no coinciden en
signo, o la dispersión entre tramos supera el doble del avgR.
"""

from __future__ import annotations

import math
from statistics import median

import numpy as np

from bt.engine import Trade

MIN_PARA_LEER = 10
MIN_PARA_SIGNO = 3


def intervalo(rs: list[float]) -> tuple[float, float] | None:
    """Media ± 2 errores estándar (varianza muestral). None con n < 2."""
    if len(rs) < 2:
        return None
    m = sum(rs) / len(rs)
    var = sum((x - m) ** 2 for x in rs) / (len(rs) - 1)
    ee = math.sqrt(var) / math.sqrt(len(rs))
    return (m - 2 * ee, m + 2 * ee)


def calcular(trades: list[Trade]) -> dict:
    res = [t for t in trades if t.resuelto]
    n = len(res)
    if n == 0:
        return {
            "n": 0, "suficiente": False, "avgR": 0.0, "avgRNeto": 0.0, "ic95": None, "winRatePct": 0.0,
            "profitFactor": None, "totalRNeto": 0.0, "maeMedianoR": 0.0, "velasMediana": 0,
            "porMotivo": {},
        }
    netos = [t.r_neto for t in res]
    ganancias = sum(x for x in netos if x > 0)
    perdidas = -sum(x for x in netos if x < 0)
    por_motivo: dict[str, int] = {}
    for t in res:
        por_motivo[t.motivo] = por_motivo.get(t.motivo, 0) + 1
    return {
        "n": n,
        "suficiente": n >= MIN_PARA_LEER,
        "avgR": sum(t.r_bruto for t in res) / n,
        "avgRNeto": sum(netos) / n,
        "ic95": intervalo(netos),
        "winRatePct": 100 * sum(1 for x in netos if x > 0) / n,
        "profitFactor": ganancias / perdidas if perdidas > 0 else None,
        "totalRNeto": sum(netos),
        "maeMedianoR": median(t.mae_r for t in res),
        "velasMediana": median(t.velas for t in res),
        "porMotivo": por_motivo,
    }


def robustez(trades: list[Trade], factor_costos: float = 1.5, sacar_mejores: int = 10) -> dict:
    """Dos pruebas de fragilidad que no deciden, informan (las pidió la auditoría del 2026-11-01).

    - costos × `factor_costos`: ¿el resultado sobrevive a una comisión/deslizamiento peor que lo asumido?
    - sin las `sacar_mejores` mejores operaciones: ¿el edge depende de unas pocas colas grandes?
    """
    res = [t for t in trades if t.resuelto]
    caros = [t.r_bruto - factor_costos * t.fee_r - t.funding_r for t in res]
    netos = sorted((t.r_neto for t in res), reverse=True)
    sin_top = netos[sacar_mejores:]
    return {
        "costosX": factor_costos,
        "costos": {"n": len(caros), "avgRNeto": sum(caros) / len(caros) if caros else 0.0,
                   "ic95": intervalo(caros)},
        "sinMejores": sacar_mejores,
        "sinTop": {"n": len(sin_top), "avgRNeto": sum(sin_top) / len(sin_top) if sin_top else 0.0,
                   "ic95": intervalo(sin_top)},
    }


def cuantos_tramos(n: int) -> int:
    return max(2, min(4, n // MIN_PARA_SIGNO))


def tramos(trades: list[Trade]) -> list[dict]:
    res = sorted((t for t in trades if t.resuelto), key=lambda t: t.abierto_en)
    if not res:
        return []
    out = []
    for grupo in np.array_split(np.arange(len(res)), cuantos_tramos(len(res))):
        if len(grupo) == 0:
            continue
        sub = [res[i] for i in grupo]
        out.append({"desde": sub[0].abierto_en[:10], "hasta": sub[-1].abierto_en[:10], **calcular(sub)})
    return out


def informe(modelos: dict[str, list[Trade]]) -> dict:
    cons, opt = modelos["conservador"], modelos["optimista"]
    g = calcular(cons)
    brecha = calcular(opt)["avgRNeto"] - g["avgRNeto"]
    por_tramo = tramos(cons)

    por_que: list[str] = []
    if not g["suficiente"]:
        por_que.append(f"muestra corta: {g['n']} trades resueltos, se necesitan {MIN_PARA_LEER}")
    if abs(brecha) > abs(g["avgRNeto"]):
        por_que.append(
            f"los dos modelos de llenado difieren en {brecha:.3f}R, más que el avgR de "
            f"{g['avgRNeto']:.3f}R: el signo depende del orden intra-vela"
        )
    con_signo = [t for t in por_tramo if t["n"] >= MIN_PARA_SIGNO]
    if len(con_signo) >= 2:
        signos = {math.copysign(1, t["avgRNeto"]) for t in con_signo}
        if len(signos) > 1:
            det = " ".join(f"{t['desde']}:{t['avgRNeto']:+.2f}R" for t in con_signo)
            por_que.append(f"los tramos no coinciden en signo ({det}): depende del régimen")
        vals = [t["avgRNeto"] for t in con_signo]
        disp = max(vals) - min(vals)
        if disp > 2 * abs(g["avgRNeto"]):
            por_que.append(
                f"la dispersión entre tramos ({disp:.2f}R) supera el doble del avgR ({g['avgRNeto']:.3f}R)"
            )

    return {
        "global": g,
        "porTramo": por_tramo,
        "brechaEntreModelosR": brecha,
        "concluyente": not por_que,
        "porQueNoConcluyente": por_que,
        "descartadas": sum(1 for t in cons if not t.resuelto),
    }
