"""Evalúa un pre-registro: desarrollo → criterio → (sólo si pasa) holdout, una vez.

    python -m bt.evaluar specs/2026-11-01-algo.yaml --bajar
    python -m bt.evaluar --pendientes --bajar          # todas las pre-registradas sin evaluar

Escribe:
- `results/evaluaciones/<id>.json`: todo lo medido. Su existencia marca la spec como evaluada:
  el holdout se mira UNA vez, así que no se vuelve a correr (salvo `--forzar`, que queda anotado).
- `results/reports/<id>.md`: el reporte legible.
- `results/approved.json`: se agrega la estrategia si sale APROBADA (va por PR, lo aprueba Felipe).
- una fila por símbolo y tramo en `results/mediciones.jsonl`.

Veredictos: APROBADA, RECHAZADA, NO_CONCLUYENTE (muestra menor que `n_minimo`: no hay con qué decidir).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Callable
from pathlib import Path
from statistics import median

import pandas as pd

from bt import bitacora, data, metrics, run
from bt.engine import Trade
from bt.nulo import control_nulo
from bt.spec import DURACION_MEDIANA_MAX_DIAS, Spec, SpecInvalida, cargar, listar
from bt.splits import HOLDOUT_DESDE

RESULTADOS = Path("results")
DECISIONES = Path("02-DOCS") / "decisiones.md"
APROBADAS = "APROBADA"
RECHAZADA = "RECHAZADA"
NO_CONCLUYENTE = "NO_CONCLUYENTE"

CargarVelas = Callable[[str, str, str], pd.DataFrame]
CargarFunding = Callable[[str], pd.Series]


def _tramo(spec: Spec, cargar_velas: CargarVelas, cargar_funding: CargarFunding, holdout: bool) -> dict:
    desde, hasta = (HOLDOUT_DESDE, None) if holdout else (spec.desde, None)
    por_simbolo: dict[str, list[Trade]] = {}
    optimistas: list[Trade] = []
    datos: dict = {}
    filas: list[dict] = []
    ventana: list[pd.Timestamp] = []
    calidad: dict[str, dict] = {}
    for s in spec.simbolos:
        df = cargar_velas(s, spec.intervalo, spec.mercado)
        fund = cargar_funding(s) if spec.funding else None
        r = run.correr(
            spec.modulo, df, simbolo=s, intervalo=spec.intervalo, mercado=spec.mercado, desde=desde,
            hasta=hasta, holdout=holdout, cfg=spec.cfg, params=spec.params, funding=fund,
            nota=f"evaluacion {spec.id} ({'holdout' if holdout else 'desarrollo'})",
        )
        por_simbolo[s] = r.trades["conservador"]
        optimistas += r.trades["optimista"]
        datos[s] = (df, fund)
        filas.append(r.fila)
        ventana += [pd.Timestamp(r.fila["desde"]), pd.Timestamp(r.fila["hasta"])]
        calidad[s] = data.calidad(df, spec.minutos_por_vela, r.fila["desde"], r.fila["hasta"])

    todos = [t for ts in por_simbolo.values() for t in ts]
    inf = metrics.informe({"conservador": todos, "optimista": optimistas})
    v_desde, v_hasta = min(ventana), max(ventana)
    nulo = control_nulo(por_simbolo, datos, v_desde, v_hasta + pd.Timedelta(1, "ns"), spec.cfg)
    resueltos = sorted((t for t in todos if t.resuelto), key=lambda t: t.abierto_en)
    duraciones = [t.velas * spec.minutos_por_vela / 1440 for t in resueltos]
    return {
        "ventana": [v_desde.isoformat(), v_hasta.isoformat()],
        "global": inf["global"],
        "porTramo": inf["porTramo"],
        "brechaEntreModelosR": inf["brechaEntreModelosR"],
        "concluyente": inf["concluyente"],
        "porQueNoConcluyente": inf["porQueNoConcluyente"],
        "nulo": nulo,
        "duracionMedianaDias": median(duraciones) if duraciones else None,
        "porSimbolo": {s: metrics.calcular(ts) | {"porMotivo": None} for s, ts in por_simbolo.items()},
        "calidadDatos": calidad,
        "curva": [[t.abierto_en[:10], round(t.r_neto, 4)] for t in resueltos],
        "filas": filas,
    }


def _criterios_desarrollo(spec: Spec, d: dict) -> list[dict]:
    c, g = spec.criterio, d["global"]
    out = [{"criterio": f"n ≥ {c.n_minimo}", "valor": g["n"], "ok": g["n"] >= c.n_minimo, "clave": "n"}]
    if c.ic95_excluye_cero:
        ic = g["ic95"]
        out.append({"criterio": "avgR neto > 0 y ±2 EE fuera del cero",
                    "valor": f"{g['avgRNeto']:+.3f} [{ic[0]:+.3f}, {ic[1]:+.3f}]" if ic else f"{g['avgRNeto']:+.3f}",
                    "ok": bool(ic and ic[0] > 0)})
    else:
        out.append({"criterio": "avgR neto > 0", "valor": f"{g['avgRNeto']:+.3f}", "ok": g["avgRNeto"] > 0})
    if c.concluyente:
        out.append({"criterio": "concluyente (muestra, modelos, tramos)",
                    "valor": "sí" if d["concluyente"] else "; ".join(d["porQueNoConcluyente"]),
                    "ok": d["concluyente"]})
    if c.tramos_positivos_minimo:
        pos = sum(1 for t in d["porTramo"] if t["avgRNeto"] > 0)
        out.append({"criterio": f"tramos positivos ≥ {c.tramos_positivos_minimo}",
                    "valor": f"{pos}/{len(d['porTramo'])}", "ok": pos >= c.tramos_positivos_minimo})
    if c.supera_nulo_p95:
        p95 = d["nulo"]["p95"]
        out.append({"criterio": "supera el percentil 95 del control nulo",
                    "valor": f"{g['avgRNeto']:+.3f} vs p95 {p95:+.3f}" if p95 is not None else "sin nulo",
                    "ok": p95 is not None and g["avgRNeto"] > p95})
    dm = d["duracionMedianaDias"]
    out.append({"criterio": f"alcance: duración mediana ≤ {DURACION_MEDIANA_MAX_DIAS} días",
                "valor": f"{dm:.1f} días" if dm is not None else "—",
                "ok": dm is not None and dm <= DURACION_MEDIANA_MAX_DIAS})
    return out


def evaluar(
    spec: Spec,
    cargar_velas: CargarVelas = data.cargar,
    cargar_funding: CargarFunding = data.cargar_funding,
) -> dict:
    """Evalúa sin escribir nada. Devuelve el dict que se guarda en results/evaluaciones/<id>.json."""
    dev = _tramo(spec, cargar_velas, cargar_funding, holdout=False)
    criterios = _criterios_desarrollo(spec, dev)
    motivos = [f"desarrollo: falla «{c['criterio']}» ({c['valor']})" for c in criterios if not c["ok"]]
    holdout = None
    if dev["global"]["n"] < spec.criterio.n_minimo:
        veredicto = NO_CONCLUYENTE
    elif motivos:
        veredicto = RECHAZADA
    else:
        # Pasó desarrollo: recién ahora, y una sola vez, el holdout.
        holdout = _tramo(spec, cargar_velas, cargar_funding, holdout=True)
        avg = holdout["global"]["avgRNeto"]
        ok = holdout["global"]["n"] > 0 and (avg > 0 or not spec.criterio.holdout_avg_positivo)
        criterios.append({"criterio": "holdout: avgR neto > 0", "valor": f"{avg:+.3f} (n={holdout['global']['n']})",
                          "ok": ok})
        veredicto = APROBADAS if ok else RECHAZADA
        if not ok:
            motivos.append(f"holdout: avgR neto {avg:+.3f}")
    return {
        "id": spec.id,
        "fecha": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "commit": bitacora.commit_actual(),
        "veredicto": veredicto,
        "motivos": motivos,
        "criterios": criterios,
        "spec": spec.crudo,
        "desarrollo": dev,
        "holdout": holdout,
    }


def _fmt_ic(g: dict) -> str:
    return f"[{g['ic95'][0]:+.3f}, {g['ic95'][1]:+.3f}]" if g.get("ic95") else "—"


def _fmt_dias(x: float | None) -> str:
    return f"{x:.1f} días" if x is not None else "—"


def reporte_md(ev: dict) -> str:
    s, dev, ho = ev["spec"], ev["desarrollo"], ev["holdout"]
    u = s["universo"]
    lineas = [
        f"# {ev['id']} — {ev['veredicto']}",
        "",
        f"- **Estrategia:** `{s['estrategia']['modulo']}` {json.dumps(s['estrategia'].get('params') or {})}",
        f"- **Universo:** {u.get('mercado', 'futures')} · {u['intervalo']} · {', '.join(u['simbolos'])}",
        f"- **Evaluada:** {ev['fecha']} · commit `{ev['commit']}`",
        "",
        "## Hipótesis",
        "",
        str(s.get("hipotesis", "")).strip(),
        "",
        "## Criterio pre-registrado",
        "",
        "| Criterio | Valor | |",
        "|---|---|---|",
    ]
    lineas += [f"| {c['criterio']} | {c['valor']} | {'✅' if c['ok'] else '❌'} |" for c in ev["criterios"]]
    if ev["motivos"]:
        lineas += ["", "**Motivos:** " + "; ".join(ev["motivos"])]
    for nombre, t in (("Desarrollo", dev), ("Holdout", ho)):
        if t is None:
            if nombre == "Holdout":
                lineas += ["", "## Holdout", "", "No se miró: desarrollo no pasó el criterio."]
            continue
        g = t["global"]
        nulo = t["nulo"]
        lineas += [
            "", f"## {nombre}", "",
            f"Ventana {t['ventana'][0][:10]} → {t['ventana'][1][:10]} · n={g['n']} · "
            f"avgR neto {g['avgRNeto']:+.3f} {_fmt_ic(g)} · bruto {g['avgR']:+.3f} · "
            f"acierto {g['winRatePct']:.0f}% · duración mediana " + _fmt_dias(t["duracionMedianaDias"]),
            "",
            f"Control nulo: media {nulo['media']:+.3f}, p95 {nulo['p95']:+.3f}"
            if nulo["media"] is not None else "Control nulo: sin datos",
            "", "| Tramo | n | avgR neto |", "|---|---|---|",
        ]
        lineas += [f"| {x['desde']} → {x['hasta']} | {x['n']} | {x['avgRNeto']:+.3f} |" for x in t["porTramo"]]
        lineas += ["", "| Símbolo | n | avgR neto | ±2 EE |", "|---|---|---|---|"]
        lineas += [f"| {k} | {m['n']} | {m['avgRNeto']:+.3f} | {_fmt_ic(m)} |" for k, m in t["porSimbolo"].items()]
    return "\n".join(lineas) + "\n"


def _entrada_aprobada(ev: dict) -> dict:
    s = ev["spec"]
    resumen = lambda t: {"ventana": t["ventana"], "n": t["global"]["n"],  # noqa: E731
                         "avgRNeto": t["global"]["avgRNeto"], "ic95": t["global"]["ic95"]}
    return {
        "id": ev["id"],
        "estrategia": s["estrategia"]["modulo"],
        "params": s["estrategia"].get("params") or {},
        "mercado": s["universo"].get("mercado", "futures"),
        "intervalo": s["universo"]["intervalo"],
        "simbolos": s["universo"]["simbolos"],
        "config": s.get("config") or {},
        "desarrollo": resumen(ev["desarrollo"]),
        "holdout": resumen(ev["holdout"]),
        "aprobada_en": ev["fecha"],
        "commit": ev["commit"],
        "reporte": f"results/reports/{ev['id']}.md",
    }


def guardar(ev: dict, base: Path = RESULTADOS) -> None:
    (base / "evaluaciones").mkdir(parents=True, exist_ok=True)
    (base / "reports").mkdir(parents=True, exist_ok=True)
    filas = [f for t in (ev["desarrollo"], ev["holdout"]) if t for f in t["filas"]]
    for f in filas:
        bitacora.registrar(f, base / "mediciones.jsonl")
    sin_filas = json.loads(json.dumps(ev, default=str))
    for t in (sin_filas["desarrollo"], sin_filas["holdout"]):
        if t:
            t.pop("filas", None)
    (base / "evaluaciones" / f"{ev['id']}.json").write_text(
        json.dumps(sin_filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (base / "reports" / f"{ev['id']}.md").write_text(reporte_md(ev), encoding="utf-8")
    if ev["veredicto"] == APROBADAS:
        ruta = base / "approved.json"
        actual = json.loads(ruta.read_text()) if ruta.exists() else {"estrategias": []}
        actual["estrategias"] = [e for e in actual["estrategias"] if e["id"] != ev["id"]]
        actual["estrategias"].append(_entrada_aprobada(sin_filas))
        actual["actualizado"] = ev["fecha"]
        ruta.write_text(json.dumps(actual, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def linea_decisiones(ev: dict) -> str:
    """Una línea para la tabla «Medidas en este repo» de 02-DOCS/decisiones.md (regla 0)."""
    s, g = ev["spec"], ev["desarrollo"]["global"]
    pregunta = str(s.get("pregunta") or s.get("hipotesis", "")).strip().split(". ")[0].replace("|", "/")
    if len(pregunta) > 160:
        pregunta = pregunta[:157] + "..."
    partes = [f"desarrollo n={g['n']} {g['avgRNeto']:+.3f} {_fmt_ic(g)}"]
    if ev["holdout"]:
        h = ev["holdout"]["global"]
        partes.append(f"holdout n={h['n']} {h['avgRNeto']:+.3f}")
    if ev["motivos"]:
        partes.append("No pasa: " + "; ".join(m.split(": ", 1)[-1].removeprefix("falla ") for m in ev["motivos"]))
    detalle = ". ".join(partes).replace("|", "/")
    return (f"| {pregunta} (`{ev['id']}`) | **{ev['veredicto']}.** {detalle} | {ev['fecha'][:10]} | "
            f"`results/reports/{ev['id']}.md` |")


def anotar_en_decisiones(ev: dict, ruta: Path = DECISIONES) -> None:
    texto = ruta.read_text(encoding="utf-8")
    if f"`{ev['id']}`" in texto:
        return
    texto = texto.replace("| _(ninguna todavía)_ | | | |\n", "")
    ruta.write_text(texto.rstrip("\n") + "\n" + linea_decisiones(ev) + "\n", encoding="utf-8")


def evaluada(sid: str, base: Path = RESULTADOS) -> bool:
    return (base / "evaluaciones" / f"{sid}.json").exists()


def pendientes(directorio: Path = Path("specs"), base: Path = RESULTADOS) -> list[Spec]:
    out = []
    for ruta in listar(directorio):
        spec = cargar(ruta)
        if spec.estado == "pre-registrada" and not evaluada(spec.id, base):
            out.append(spec)
    return out


def bajar(spec: Spec) -> None:
    """Velas (y funding) de todos los símbolos, en paralelo. Completa lo que ya haya en caché."""
    from concurrent.futures import ThreadPoolExecutor

    tareas = [lambda s=s: data.descargar(s, spec.intervalo, "2020-01", spec.mercado) for s in spec.simbolos]
    if spec.funding:
        tareas += [lambda s=s: data.descargar_funding(s, "2020-01") for s in spec.simbolos]
    with ThreadPoolExecutor(4) as ex:
        for ruta in ex.map(lambda f: f(), tareas):
            print(f"  {ruta}", flush=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("specs", nargs="*", type=Path)
    p.add_argument("--pendientes", action="store_true", help="evaluar las pre-registradas sin evaluación")
    p.add_argument("--bajar", action="store_true", help="bajar velas (y funding) antes de evaluar")
    p.add_argument("--forzar", action="store_true", help="re-evaluar aunque ya exista (mira el holdout de nuevo)")
    p.add_argument("--salida-github", type=Path, help="archivo $GITHUB_OUTPUT para el workflow")
    a = p.parse_args(argv)

    try:
        specs = pendientes() if a.pendientes else [cargar(r) for r in a.specs]
    except SpecInvalida as e:
        print(f"spec inválida: {e}", file=sys.stderr)
        return 2
    evaluaciones = []
    for spec in specs:
        if evaluada(spec.id) and not a.forzar:
            print(f"{spec.id}: ya evaluada (results/evaluaciones/{spec.id}.json). El holdout se mira una vez.")
            continue
        if spec.estado == "borrador":
            print(f"{spec.id}: es un borrador; pasala a `pre-registrada` antes de evaluar.")
            continue
        if a.bajar:
            bajar(spec)
        ev = evaluar(spec)
        if a.forzar:
            ev["motivos"].append("re-evaluada con --forzar: el holdout ya se había mirado")
        guardar(ev)
        if DECISIONES.exists():
            anotar_en_decisiones(ev)
        evaluaciones.append(ev)
        print(f"{spec.id}: {ev['veredicto']}" + (f" — {'; '.join(ev['motivos'])}" if ev["motivos"] else ""))

    if a.salida_github:
        aprobadas = [e["id"] for e in evaluaciones if e["veredicto"] == APROBADAS]
        with a.salida_github.open("a") as f:
            f.write(f"evaluadas={len(evaluaciones)}\n")
            f.write(f"aprobadas={len(aprobadas)}\n")
            f.write(f"ids={' '.join(e['id'] for e in evaluaciones)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
