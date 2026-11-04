"""Simulador de cartera: las estrategias aprobadas juntas, no una por una.

Cada evaluación se mide sola. Pero en el bot corren juntas: si dos aprobadas pierden en los mismos
meses, la cartera cae el doble. Este módulo junta las operaciones que ya guardó cada evaluación
(`curva`: apertura, R neto, cierre), sin volver a correr nada, y mide en la ventana común:

- R por mes de cada estrategia y de la cartera (1R por operación, como en las evaluaciones);
- peor caída de la cartera, con las operaciones ordenadas por su CIERRE;
- correlación mensual entre estrategias (cuánto se parecen sus meses buenos y malos).

    python -m bt.cartera                 # todo lo de results/approved.json → results/reports/cartera.md
    python -m bt.cartera --ids a b c     # cualquier conjunto de evaluaciones (explorar, no decide nada)

Evaluaciones viejas guardaban sólo la apertura: ahí la peor caída usa la apertura (aproximación, se
indica). No hay cupo entre estrategias: en el bot cada una tiene el suyo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

RESULTADOS = Path("results")


def operaciones(ev: dict) -> tuple[list[tuple[str, float, str]], bool]:
    """[(apertura, R, cierre)] de desarrollo + holdout, y si las fechas de cierre son reales."""
    filas, exacto = [], True
    for tramo in ("desarrollo", "holdout"):
        for c in (ev.get(tramo) or {}).get("curva", []):
            if len(c) < 3:
                exacto = False
            filas.append((c[0], float(c[1]), c[2] if len(c) > 2 else c[0]))
    return filas, exacto


def _mensual(ops: list[tuple[str, float, str]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for _, r, cierre in ops:
        out[cierre[:7]] = out.get(cierre[:7], 0.0) + r
    return out


def peor_caida(ops: list[tuple[str, float, str]]) -> float:
    """Peor caída del R acumulado, neteando por día de cierre (el orden dentro de un día no se sabe)."""
    por_dia: dict[str, float] = {}
    for _, r, cierre in ops:
        por_dia[cierre] = por_dia.get(cierre, 0.0) + r
    acum = pico = caida = 0.0
    for _, r in sorted(por_dia.items()):
        acum += r
        pico = max(pico, acum)
        caida = min(caida, acum - pico)
    return round(caida, 2)


def simular(evs: dict[str, dict]) -> dict:
    """Cartera de las evaluaciones dadas, en la ventana común (meses donde todas tienen datos)."""
    por_est = {sid: operaciones(ev) for sid, ev in evs.items()}
    rangos = {sid: (min(o[2] for o in ops)[:7], max(o[2] for o in ops)[:7]) for sid, (ops, _) in por_est.items() if ops}
    if not rangos:
        return {"estrategias": {}, "ventana": None}
    desde, hasta = max(r[0] for r in rangos.values()), min(r[1] for r in rangos.values())
    en_ventana = {sid: [o for o in ops if desde <= o[2][:7] <= hasta] for sid, (ops, _) in por_est.items()}
    meses = sorted({m for ops in en_ventana.values() for m in _mensual(ops)})
    series = {sid: [(_mensual(ops)).get(m, 0.0) for m in meses] for sid, ops in en_ventana.items()}
    todas = [o for ops in en_ventana.values() for o in ops]
    cartera_mes = [sum(v[i] for v in series.values()) for i in range(len(meses))]
    ids = sorted(series)
    corr = {}
    if len(ids) > 1 and len(meses) > 2:
        m = np.corrcoef(np.array([series[s] for s in ids]))
        corr = {a: {b: round(float(m[i, j]), 2) for j, b in enumerate(ids)} for i, a in enumerate(ids)}
    return {
        "ventana": [desde, hasta],
        "meses": len(meses),
        "fechasDeCierreExactas": all(ex for _, ex in por_est.values()),
        "estrategias": {sid: {"n": len(ops), "sumaR": round(sum(o[1] for o in ops), 2),
                              "peorCaidaR": peor_caida(ops),
                              "mesesPositivos": sum(1 for x in series[sid] if x > 0)}
                        for sid, ops in en_ventana.items()},
        "cartera": {"n": len(todas), "sumaR": round(sum(o[1] for o in todas), 2), "peorCaidaR": peor_caida(todas),
                    "mesesPositivos": sum(1 for x in cartera_mes if x > 0),
                    "peorMesR": round(min(cartera_mes), 2) if cartera_mes else None},
        "sumaDePeoresCaidas": round(sum(peor_caida(ops) for ops in en_ventana.values()), 2),
        "correlacionMensual": corr,
    }


def marginal(nueva: dict, existentes: dict[str, dict]) -> dict | None:
    """¿Qué le hace una estrategia nueva a la cartera aprobada? Para la ficha de una aprobada."""
    if not existentes:
        return None
    antes = simular(existentes)
    despues = simular(existentes | {nueva["id"]: nueva})
    corr = despues["correlacionMensual"].get(nueva["id"], {})
    return {"ventana": despues["ventana"], "peorCaidaAntes": antes["cartera"]["peorCaidaR"],
            "peorCaidaDespues": despues["cartera"]["peorCaidaR"],
            "correlacionMensual": {k: v for k, v in corr.items() if k != nueva["id"]}}


def cargar(ids: list[str], base: Path = RESULTADOS) -> dict[str, dict]:
    return {sid: json.loads((base / "evaluaciones" / f"{sid}.json").read_text(encoding="utf-8")) for sid in ids}


def reporte_md(sim: dict) -> str:
    if not sim.get("ventana"):
        return "# Cartera\n\nTodavía no hay estrategias aprobadas con operaciones.\n"
    lineas = ["# Cartera de lo aprobado", "",
              f"Ventana común {sim['ventana'][0]} → {sim['ventana'][1]} ({sim['meses']} meses), 1R por operación, "
              "sin cupo entre estrategias. Generado por `bt.cartera`.", ""]
    if not sim["fechasDeCierreExactas"]:
        lineas += ["Alguna evaluación es anterior a que se guardara el cierre de cada operación: su peor caída usa "
                   "la fecha de apertura (aproximación).", ""]
    lineas += ["| Estrategia | n | Suma R | Peor caída R | Meses positivos |", "|---|---|---|---|---|"]
    for sid, e in sim["estrategias"].items():
        lineas.append(f"| `{sid}` | {e['n']} | {e['sumaR']:+.1f} | {e['peorCaidaR']:+.1f} | {e['mesesPositivos']} |")
    c = sim["cartera"]
    lineas.append(f"| **Cartera** | {c['n']} | {c['sumaR']:+.1f} | {c['peorCaidaR']:+.1f} | {c['mesesPositivos']} |")
    lineas += ["", f"Peor mes de la cartera: {c['peorMesR']:+.1f} R. Suma de las peores caídas por separado: "
               f"{sim['sumaDePeoresCaidas']:+.1f} R (si la cartera cae menos, la diversificación ayuda)."]
    if sim["correlacionMensual"]:
        ids = list(sim["correlacionMensual"])
        corto = {i: i[11:][:24] or i for i in ids}  # sin la fecha: el slug distingue mejor
        lineas += ["", "**Correlación mensual** (cerca de +1: ganan y pierden en los mismos meses; cerca de 0 o "
                   "negativa: se compensan)", "",
                   "| | " + " | ".join(f"`{corto[i]}`" for i in ids) + " |", "|---|" + "---|" * len(ids)]
        lineas += [f"| `{corto[a]}` | " + " | ".join(f"{sim['correlacionMensual'][a][b]:+.2f}" for b in ids) + " |"
                   for a in ids]
    else:
        lineas += ["", "Con una sola estrategia no hay correlación que medir: la cartera es esa estrategia."]
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ids", nargs="*")
    a = p.parse_args(argv)
    ids = a.ids
    if not ids:
        ruta = RESULTADOS / "approved.json"
        ids = [e["id"] for e in json.loads(ruta.read_text())["estrategias"]] if ruta.exists() else []
    sim = simular(cargar(ids))
    md = reporte_md(sim)
    print(md)
    if not a.ids:
        (RESULTADOS / "reports").mkdir(parents=True, exist_ok=True)
        (RESULTADOS / "reports" / "cartera.md").write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
