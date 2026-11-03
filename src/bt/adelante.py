"""Prueba hacia adelante: cada aprobada (u observación) corrida sólo con datos POSTERIORES a su evaluación.

El holdout fijo (desde 2025-09-09) se gasta con cada mirada. Lo que pasó después de evaluar una
estrategia no lo vio nadie al diseñarla: es evidencia fuera de muestra de verdad, y crece sola cada
mes. Misma spec, mismos costos, mismo cupo y mismo universo; la ventana empieza en la vela siguiente
al fin del holdout que se miró al evaluarla.

    python -m bt.adelante --bajar        # todas las de approved.json; escribe results/adelante/

No cambia niveles ni approved.json: deja una lectura («candidata a subir / a bajar») para que el
auditor y Felipe decidan, por PR.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

from bt import bitacora, data
from bt.evaluar import RESULTADOS, _tramo, bajar, resolver_universo
from bt.spec import cargar

N_MINIMO = 30
CARPETA = "adelante"


def lectura(n: int, avg: float | None, ic: list | None, dev: float, nivel: str) -> tuple[str, str | None]:
    """(lectura, sugerencia). La sugerencia es sólo eso: el nivel lo cambia Felipe por PR."""
    if n < N_MINIMO or avg is None or not ic:
        return "muestra_chica", None
    if ic[1] < 0:
        return "negativa", "candidata a bajar: rinde negativo fuera de muestra" if nivel else None
    if ic[0] > 0:
        sug = "candidata a subir a aprobada" if nivel == "observacion" else None
        return ("positiva_peor_que_desarrollo" if dev > ic[1] else "positiva"), sug
    return ("incierta_peor_que_desarrollo" if dev > ic[1] else "incierta"), None


def correr(entrada: dict, base: Path = RESULTADOS, specs: Path = Path("specs"), cargar_velas=data.cargar,
           cargar_funding=data.cargar_funding, hoy: dt.date | None = None) -> dict:
    """Una foto de la prueba hacia adelante de una entrada de approved.json."""
    hoy = hoy or dt.date.today()
    sid = entrada["id"]
    ev = json.loads((base / "evaluaciones" / f"{sid}.json").read_text(encoding="utf-8"))
    spec = resolver_universo(cargar(specs / f"{sid}.yaml"))
    fin = pd.Timestamp(ev["holdout"]["ventana"][1])
    desde = (fin + pd.Timedelta(minutes=spec.minutos_por_vela)).isoformat()
    foto = {"fecha": hoy.isoformat(), "commit": bitacora.commit_actual(), "desde": desde}
    try:
        t = _tramo(spec, cargar_velas, cargar_funding, holdout=True, desde_forzado=desde, nota=f"adelante {sid}")
    except ValueError as e:  # todavía no hay velas después del holdout
        return foto | {"n": 0, "lectura": "sin_datos", "detalle": str(e), "filas": []}
    g = t["global"]
    dev = ev["desarrollo"]["global"]["avgRNeto"]
    lec, sug = lectura(g["n"], g["avgRNeto"], g.get("ic95"), dev, entrada.get("nivel", "aprobada"))
    return foto | {
        "ventana": t["ventana"], "n": g["n"], "avgRNeto": g["avgRNeto"], "ic95": g.get("ic95"),
        "maxDrawdownR": t["maxDrawdownR"], "porSimbolo": {s: m["n"] for s, m in t["porSimbolo"].items()},
        "referencia": {"desarrollo": dev, "holdout": ev["holdout"]["global"]["avgRNeto"]},
        "lectura": lec, "sugerencia": sug, "filas": t["filas"],
    }


def guardar(sid: str, nivel: str, foto: dict, base: Path = RESULTADOS) -> Path:
    for f in foto.pop("filas", []):
        bitacora.registrar(f, base / "mediciones.jsonl")
    ruta = base / CARPETA / f"{sid}.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    actual = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {"id": sid, "historial": []}
    actual["nivel"] = nivel
    actual["historial"] = [h for h in actual["historial"] if h["fecha"] != foto["fecha"]] + [foto]
    ruta.write_text(json.dumps(actual, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ruta


def _r(x) -> str:
    return "—" if x is None else f"{x:+.3f}"


def resumen_md(base: Path = RESULTADOS) -> str:
    lineas = ["# Prueba hacia adelante", "",
              "Cada aprobada u observación, corrida sólo con datos posteriores a su evaluación (`bt.adelante`). "
              f"Con menos de {N_MINIMO} operaciones no se concluye. Las sugerencias las decide Felipe por PR.", "",
              "| Estrategia | Nivel | Desde | n | avgR neto ±2 EE | Desarrollo / holdout | Lectura | Sugerencia |",
              "|---|---|---|---|---|---|---|---|"]
    for ruta in sorted((base / CARPETA).glob("*.json")):
        d = json.loads(ruta.read_text(encoding="utf-8"))
        h = d["historial"][-1]
        ic = h.get("ic95")
        ref = h.get("referencia") or {}
        lineas.append(
            f"| `{d['id']}` | {d.get('nivel')} | {h['desde'][:10]} | {h['n']} "
            f"| {_r(h.get('avgRNeto'))} {f'[{ic[0]:+.3f}, {ic[1]:+.3f}]' if ic else ''} "
            f"| {_r(ref.get('desarrollo'))} / {_r(ref.get('holdout'))} | {h['lectura']} "
            f"| {h.get('sugerencia') or '—'} |")
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bajar", action="store_true")
    a = p.parse_args(argv)
    ruta = RESULTADOS / "approved.json"
    entradas = json.loads(ruta.read_text())["estrategias"] if ruta.exists() else []
    for e in entradas:
        if a.bajar:
            bajar(cargar(Path("specs") / f"{e['id']}.yaml"))
        foto = correr(e)
        guardar(e["id"], e.get("nivel", "aprobada"), foto)
        print(f"{e['id']}: n={foto['n']} {_r(foto.get('avgRNeto'))} → {foto['lectura']}"
              + (f" ({foto['sugerencia']})" if foto.get("sugerencia") else ""))
    (RESULTADOS / "reports").mkdir(parents=True, exist_ok=True)
    (RESULTADOS / "reports" / "adelante.md").write_text(resumen_md(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
