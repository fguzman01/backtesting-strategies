"""Evalúa un pre-registro: desarrollo → criterio → (sólo si pasa) holdout, una vez.

    python -m bt.evaluar specs/2026-11-01-algo.yaml --bajar
    python -m bt.evaluar --pendientes --bajar          # todas las pre-registradas sin evaluar

Escribe:
- `results/evaluaciones/<id>.json`: todo lo medido. Su existencia marca la spec como evaluada:
  el holdout se mira UNA vez, así que no se vuelve a correr (salvo `--forzar`, que queda anotado).
- `results/reports/<id>.md`: el reporte legible.
- `results/approved.json`: se agrega si sale APROBADA u OBSERVACION, con su `nivel` (va por PR, lo
  aprueba Felipe). `observacion` = sólo paper.
- una fila por símbolo y tramo en `results/mediciones.jsonl`.

Veredictos: APROBADA, OBSERVACION, RECHAZADA, NO_CONCLUYENTE (muestra menor que `n_minimo`).
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
from bt.spec import DURACION_MEDIANA_MAX_DIAS, FAMILIA_POR_MODULO, Spec, SpecInvalida, cargar, listar
from bt.splits import HOLDOUT_DESDE

RESULTADOS = Path("results")
DECISIONES = Path("02-DOCS") / "decisiones.md"
IDEAS = Path("02-DOCS") / "ideas.md"
APROBADAS = "APROBADA"
RECHAZADA = "RECHAZADA"
NO_CONCLUYENTE = "NO_CONCLUYENTE"
# Desarrollo sólido pero holdout no concluyente o contaminado (retroalimentación de btc-signal-web,
# 2026-11-02): entra a approved.json con nivel «observacion» → sólo paper, para observar.
OBSERVACION = "OBSERVACION"
NIVEL = {APROBADAS: "aprobada", OBSERVACION: "observacion"}

CargarVelas = Callable[[str, str, str], pd.DataFrame]
CargarFunding = Callable[[str], pd.Series]


def resolver_universo(spec: Spec, tabla: dict | None = None) -> Spec:
    """Universo dinámico → la lista de símbolos que alguna vez estuvieron entre los `top` (desde la
    ventana de desarrollo) y en qué meses. Una spec con lista fija vuelve igual."""
    import dataclasses

    from bt import universo

    if not spec.dinamico_top or spec.miembros is not None:
        return spec
    tabla = tabla if tabla is not None else universo.cargar_tabla()
    desde = (spec.desde or "2020-01-01")[:7]
    m = universo.miembros(spec.dinamico_top, tabla, desde)
    return dataclasses.replace(spec, simbolos=sorted(m), miembros={s: sorted(v) for s, v in m.items()})


def _en_universo(spec: Spec, s: str, trades: list[Trade]) -> list[Trade]:
    """Con universo dinámico, sólo cuentan las señales de los meses en que el símbolo era del top."""
    if spec.miembros is None:
        return trades
    meses = set(spec.miembros.get(s, ()))
    return [t for t in trades if (t.senal_en or t.abierto_en)[:7] in meses]


def _tramo(spec: Spec, cargar_velas: CargarVelas, cargar_funding: CargarFunding, holdout: bool,
           desde_forzado: str | None = None, nota: str | None = None) -> dict:
    desde, hasta = (HOLDOUT_DESDE, None) if holdout else (spec.desde, None)
    if desde_forzado is not None:
        desde = desde_forzado
    nota = nota or f"evaluacion {spec.id} ({'holdout' if holdout else 'desarrollo'})"
    por_simbolo: dict[str, list[Trade]] = {}
    opt_por_simbolo: dict[str, list[Trade]] = {}
    datos: dict = {}
    filas: list[dict] = []
    ventana: list[pd.Timestamp] = []
    calidad: dict[str, dict] = {}
    sin_datos: list[str] = []
    for s in spec.simbolos:
        try:
            if spec.historia_spot and cargar_velas is data.cargar:
                df = data.cargar_extendida(s, spec.intervalo)
            else:
                df = cargar_velas(s, spec.intervalo, spec.mercado)
            fund = cargar_funding(s) if spec.funding else None
            r = run.correr(
                spec.modulo, df, simbolo=s, intervalo=spec.intervalo, mercado=spec.mercado, desde=desde,
                hasta=hasta, holdout=holdout, cfg=spec.cfg, params=spec.params, funding=fund, nota=nota,
            )
        except (ValueError, FileNotFoundError) as e:
            # Con universo dinámico, un retirado puede no tener velas en este tramo: no es un error.
            if spec.miembros is None:
                raise
            sin_datos.append(f"{s}: {e}")
            continue
        por_simbolo[s] = _en_universo(spec, s, r.trades["conservador"])
        opt_por_simbolo[s] = _en_universo(spec, s, r.trades["optimista"])
        datos[s] = (df, fund)
        filas.append(r.fila)
        ventana += [pd.Timestamp(r.fila["desde"]), pd.Timestamp(r.fila["hasta"])]
        calidad[s] = data.calidad(df, spec.minutos_por_vela, r.fila["desde"], r.fila["hasta"])

    por_simbolo = aplicar_cupo(por_simbolo, spec.max_por_direccion)
    opt_por_simbolo = aplicar_cupo(opt_por_simbolo, spec.max_por_direccion)
    todos = [t for ts in por_simbolo.values() for t in ts]
    optimistas = [t for ts in opt_por_simbolo.values() for t in ts]
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
        "robustez": metrics.robustez(todos),
        "maxDrawdownR": peor_caida(todos),
        "maxPorDireccion": spec.max_por_direccion,
        "simbolosSinDatos": sin_datos,
        # [apertura, R neto, cierre]: el cierre lo usa bt.cartera para la peor caída de la cartera.
        "curva": [[t.abierto_en[:10], round(t.r_neto, 4), (t.cerrado_en or t.abierto_en)[:10]] for t in resueltos],
        "filas": filas,
    }


def aplicar_cupo(por_simbolo: dict[str, list[Trade]], cupo: int | None) -> dict[str, list[Trade]]:
    """Cupo de cartera como el bot: como mucho `cupo` posiciones abiertas por dirección entre todos los
    símbolos. Se recorren las entradas en orden de tiempo (y de símbolo, alfabético, como el bot) y se
    descartan las que encuentran el cupo lleno.

    Aproximación conocida: cada símbolo se simuló por separado, así que una señal que llegó mientras
    ese símbolo tenía una operación que el cupo descartó no se reconsidera. Sin cupo, no cambia nada.
    """
    if not cupo:
        return por_simbolo
    candidatos = sorted(((t.abierto_en, s, t) for s, ts in por_simbolo.items() for t in ts if t.resuelto),
                        key=lambda x: (x[0], x[1]))
    abiertas: dict[int, list[str]] = {1: [], -1: []}
    out: dict[str, list[Trade]] = {s: [] for s in por_simbolo}
    for abierto, s, t in candidatos:
        lista = abiertas[t.direccion]
        lista[:] = [c for c in lista if c > abierto]  # las que cerraron antes de esta entrada liberan cupo
        if len(lista) < cupo:
            lista.append(t.cerrado_en or "9999")
            out[s].append(t)
    return out


def peor_caida(trades: list[Trade]) -> float:
    """Peor caída del R acumulado (en R), ordenando las operaciones por su cierre."""
    acum = pico = caida = 0.0
    for t in sorted((t for t in trades if t.resuelto), key=lambda t: t.cerrado_en or ""):
        acum += t.r_neto
        pico = max(pico, acum)
        caida = min(caida, acum - pico)
    return round(caida, 4)


def antecedentes(spec: Spec, base: Path = RESULTADOS) -> list[dict]:
    """Evaluaciones previas de la misma familia: cuántas variantes se probaron antes que esta."""
    out = []
    for p in sorted((base / "evaluaciones").glob("*.json")):
        try:
            ev = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if ev.get("id") == spec.id:
            continue
        s = ev.get("spec") or {}
        modulo = (s.get("estrategia") or {}).get("modulo")
        familia = s.get("familia") or FAMILIA_POR_MODULO.get(modulo, modulo)
        if familia != spec.familia:
            continue
        g = (ev.get("desarrollo") or {}).get("global") or {}
        out.append({"id": ev.get("id"), "veredicto": ev.get("veredicto"), "avgRNetoDesarrollo": g.get("avgRNeto"),
                    "holdoutMirado": ev.get("holdout") is not None})
    return out


def preregistro(spec: Spec) -> dict | None:
    """Commit y fecha en que la spec entró al repo: verificable contra la fecha de la evaluación."""
    if spec.ruta is None:
        return None
    import subprocess

    r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h|%cI", "--", str(spec.ruta)],
                       capture_output=True, text=True)
    lineas = [x for x in r.stdout.strip().splitlines() if "|" in x]
    if r.returncode != 0 or not lineas:
        return None
    commit, fecha = lineas[-1].split("|", 1)
    return {"commit": commit, "fecha": fecha}


def _spec_madre(spec: Spec) -> Spec:
    import dataclasses

    m = spec.madre or {}
    campos = {f.name for f in dataclasses.fields(spec.cfg)}
    cfg = dataclasses.replace(spec.cfg, **{k: v for k, v in (m.get("config") or {}).items() if k in campos})
    return dataclasses.replace(spec, modulo=m.get("modulo", spec.modulo), params=m.get("params", spec.params),
                               cfg=cfg, madre=None, id=f"{spec.id}-madre", max_por_direccion=spec.max_por_direccion)


def comparar_con_madre(hija: dict, madre: dict, nombre: str) -> dict:
    """Diferencia de avgR hija − madre con ±2 EE. Las muestras se solapan (correlación positiva), así que
    sumar varianzas da un intervalo más ancho que el real: es conservador."""
    gh, gm = hija["global"], madre["global"]
    ee = lambda g: (g["ic95"][1] - g["ic95"][0]) / 4 if g.get("ic95") else 0.0  # noqa: E731
    dif = gh["avgRNeto"] - gm["avgRNeto"]
    e = (ee(gh) ** 2 + ee(gm) ** 2) ** 0.5
    return {"madre": nombre, "nMadre": gm["n"], "avgRNetoMadre": gm["avgRNeto"], "nHija": gh["n"],
            "avgRNetoHija": gh["avgRNeto"], "diferencia": dif, "ic95": [dif - 2 * e, dif + 2 * e],
            "peorCaidaHija": hija.get("maxDrawdownR"), "peorCaidaMadre": madre.get("maxDrawdownR")}


FACTORES_ESTABILIDAD = (0.8, 1.2)


def perturbar(params: dict, factor: float) -> dict:
    """Todos los parámetros numéricos × factor. Un entero que no cambiaría al redondear se mueve en 1
    (en la dirección del factor), nunca por debajo de 1. Los booleanos y textos quedan igual."""
    out = {}
    for k, v in params.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            out[k] = v
        elif isinstance(v, int):
            nuevo = max(1, round(v * factor))
            if nuevo == v:
                nuevo = max(1, v + (1 if factor > 1 else -1))
            out[k] = nuevo
        else:
            out[k] = v * factor
    return out


def estabilidad(spec: Spec, dev: dict, cargar_velas: CargarVelas, cargar_funding: CargarFunding) -> dict | None:
    """La misma spec en desarrollo con los parámetros ×0.8 y ×1.2. Nunca toca el holdout."""
    import dataclasses

    base = dev["global"]["avgRNeto"]
    vecinos, filas = [], []
    for f in FACTORES_ESTABILIDAD:
        params = perturbar(spec.params, f)
        if params == spec.params:
            return None  # sin parámetros numéricos: no hay vecindario que medir
        t = _tramo(dataclasses.replace(spec, params=params), cargar_velas, cargar_funding, holdout=False,
                   nota=f"estabilidad {spec.id} (x{f})")
        g = t["global"]
        vecinos.append({"factor": f, "params": params, "n": g["n"], "avgRNeto": g["avgRNeto"], "ic95": g.get("ic95"),
                        "fraccion": g["avgRNeto"] / base if base else None})
        filas += t["filas"]
    return {"base": base, "vecinos": vecinos, "peorFraccion": min(v["fraccion"] or 0 for v in vecinos),
            "filas": filas}


def z_por_pruebas(n_pruebas: int, alfa: float = 0.05) -> float:
    """Cuántos errores estándar sobre el cero exigir con `n_pruebas` variantes de la familia
    (Bonferroni, dos colas): 1 prueba → 1.96 (≈ los ±2 EE de siempre); 8 → 2.73; 20 → 3.02."""
    from statistics import NormalDist

    return NormalDist().inv_cdf(1 - alfa / (2 * max(1, n_pruebas)))


def _criterios_desarrollo(spec: Spec, d: dict, n_pruebas: int = 1) -> list[dict]:
    c, g = spec.criterio, d["global"]
    out = [{"criterio": f"n ≥ {c.n_minimo}", "valor": g["n"], "ok": g["n"] >= c.n_minimo, "clave": "n"}]
    if c.ic95_excluye_cero:
        ic = g["ic95"]
        out.append({"criterio": "avgR neto > 0 y ±2 EE fuera del cero",
                    "valor": f"{g['avgRNeto']:+.3f} [{ic[0]:+.3f}, {ic[1]:+.3f}]" if ic else f"{g['avgRNeto']:+.3f}",
                    "ok": bool(ic and ic[0] > 0)})
    if c.ajuste_por_pruebas:
        ic = g.get("ic95")
        z = z_por_pruebas(n_pruebas)
        ee = (ic[1] - ic[0]) / 4 if ic else None
        piso = g["avgRNeto"] - z * ee if ee is not None else None
        out.append({"criterio": f"ajustado por {n_pruebas} prueba(s) de la familia: avgR − {z:.2f} EE > 0",
                    "valor": f"{g['avgRNeto']:+.3f} − {z:.2f}×{ee:.3f} = {piso:+.3f}" if piso is not None else "sin EE",
                    "ok": piso is not None and piso > 0})
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


def _criterios_holdout(spec: Spec, dev: dict, ho: dict) -> list[dict]:
    c, g, n = spec.criterio, ho["global"], ho["global"]["n"]
    avg = g["avgRNeto"]
    out = [{"criterio": "holdout: hay operaciones", "valor": f"n={n}", "ok": n > 0}]
    if c.holdout_avg_positivo:
        out.append({"criterio": "holdout: avgR neto > 0", "valor": f"{avg:+.3f} (n={n})", "ok": avg > 0})
    rob = ho.get("robustez") or {}
    if c.holdout_aguanta_costos and rob:
        v = rob["costos"]["avgRNeto"]
        out.append({"criterio": f"holdout: con costos ×{rob['costosX']} avgR > 0", "valor": f"{v:+.3f}", "ok": v > 0})
    if c.holdout_sin_mejores_no_negativo and rob:
        v = rob["sinTop"]["avgRNeto"]
        out.append({"criterio": f"holdout: sin las {rob['sinMejores']} mejores avgR ≥ 0", "valor": f"{v:+.3f}",
                    "ok": v >= 0})
    if c.holdout_fraccion_desarrollo:
        base = dev["global"]["avgRNeto"]
        minimo = c.holdout_fraccion_desarrollo * base
        out.append({"criterio": f"holdout: conserva ≥ {c.holdout_fraccion_desarrollo:.0%} del avgR de desarrollo",
                    "valor": f"{avg:+.3f} vs mínimo {minimo:+.3f}", "ok": avg >= minimo})
    return out


def evaluar(
    spec: Spec,
    cargar_velas: CargarVelas = data.cargar,
    cargar_funding: CargarFunding = data.cargar_funding,
    base: Path = RESULTADOS,
) -> dict:
    """Evalúa sin escribir nada. Devuelve el dict que se guarda en results/evaluaciones/<id>.json.

    Dos niveles cuando pasa desarrollo (retroalimentación de btc-signal-web, 2026-11-02):
    - APROBADA: el holdout cumple TODOS los criterios y nadie de la familia lo había mirado antes.
    - OBSERVACION: holdout positivo pero débil (falla algún criterio estricto) o contaminado. Va a
      approved.json con `nivel: observacion`: sólo paper, para observar; no es candidata a real.
    - RECHAZADA: holdout sin operaciones o con avgR neto ≤ 0.
    """
    spec = resolver_universo(spec)
    previas = antecedentes(spec, base)
    contaminado = spec.holdout_contaminado or any(a["holdoutMirado"] for a in previas)
    dev = _tramo(spec, cargar_velas, cargar_funding, holdout=False)
    criterios = _criterios_desarrollo(spec, dev, len(previas) + spec.pruebas_previas + 1)
    motivos = [f"desarrollo: falla «{c['criterio']}» ({c['valor']})" for c in criterios if not c["ok"]]
    holdout = None
    estab = None
    veredicto_previo = (NO_CONCLUYENTE if dev["global"]["n"] < spec.criterio.n_minimo
                        else RECHAZADA if motivos else None)
    if veredicto_previo is None:
        # Pasó desarrollo: antes de gastar el holdout, ¿funciona también con parámetros vecinos?
        estab = estabilidad(spec, dev, cargar_velas, cargar_funding)
        minimo = spec.criterio.estabilidad_minima
        if estab is not None and minimo is not None:
            ok = estab["peorFraccion"] >= minimo
            c = {"criterio": f"estabilidad: con parámetros ×0.8 y ×1.2 conserva ≥ {minimo:.0%} del avgR",
                 "valor": " / ".join(f"×{v['factor']}: {v['avgRNeto']:+.3f}" for v in estab["vecinos"]), "ok": ok}
            criterios.append(c)
            if not ok:
                motivos.append(f"desarrollo: falla «{c['criterio']}» ({c['valor']})")
    if veredicto_previo:
        veredicto = veredicto_previo
    elif motivos:
        veredicto = RECHAZADA
    elif spec.solo_desarrollo:
        # Medición sólo en desarrollo: el holdout no se carga ni para la hija ni para la madre.
        veredicto = NO_CONCLUYENTE
        motivos.append("holdout no mirado (solo_desarrollo): sin holdout no hay veredicto de aprobación")
    else:
        # Pasó desarrollo: recién ahora, y una sola vez, el holdout.
        holdout = _tramo(spec, cargar_velas, cargar_funding, holdout=True)
        nuevos = _criterios_holdout(spec, dev, holdout)
        criterios += nuevos
        fallan = [c for c in nuevos if not c["ok"]]
        g = holdout["global"]
        if g["n"] == 0 or g["avgRNeto"] <= 0:
            veredicto = RECHAZADA
        elif fallan or contaminado:
            veredicto = OBSERVACION
        else:
            veredicto = APROBADAS
        motivos += [f"{c['criterio']} ({c['valor']})" for c in fallan]
        if contaminado and veredicto == OBSERVACION:
            motivos.append("holdout contaminado: ese período ya se miró con una estrategia emparentada")
    madre = None
    if spec.madre:
        # La madre en el mismo período, tokens y cupo: ¿la variante agrega algo o sólo es la madre?
        sm = _spec_madre(spec)
        madre = {"filas": []}
        for nombre, t in (("desarrollo", dev), ("holdout", holdout)):
            if t is not None:
                tm = _tramo(sm, cargar_velas, cargar_funding, holdout=nombre == "holdout")
                madre[nombre] = comparar_con_madre(t, tm, spec.madre["nombre"])
                madre["filas"] += tm["filas"]
    resultado = {
        "id": spec.id,
        "fecha": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "commit": bitacora.commit_actual(),
        "veredicto": veredicto,
        "nivel": NIVEL.get(veredicto),
        "motivos": motivos,
        "criterios": criterios,
        "spec": spec.crudo,
        "familia": spec.familia,
        "nPruebas": len(previas) + spec.pruebas_previas + 1,
        "pruebasPrevias": spec.pruebas_previas,
        "variantes": previas,
        "holdoutContaminado": contaminado,
        "preregistro": preregistro(spec),
        "maxPorDireccion": spec.max_por_direccion,
        "universoDinamico": {"top": spec.dinamico_top, "simbolos": spec.simbolos} if spec.dinamico_top else None,
        "comparacionMadre": madre,
        "estabilidad": estab,
        "desarrollo": dev,
        "holdout": holdout,
    }
    if spec.solo_desarrollo:
        resultado["soloDesarrollo"] = True
    if spec.medicion:
        resultado["soloMedicion"] = True
    if veredicto in NIVEL and not spec.medicion:
        resultado["carteraMarginal"] = _marginal(resultado, base)
    return resultado


def _marginal(ev: dict, base: Path) -> dict | None:
    """Qué le hace esta aprobada a la cartera de lo ya aprobado (correlación y peor caída)."""
    from bt import cartera

    ruta = base / "approved.json"
    ids = [e["id"] for e in json.loads(ruta.read_text())["estrategias"]] if ruta.exists() else []
    ids = [i for i in ids if i != ev["id"] and (base / "evaluaciones" / f"{i}.json").exists()]
    return cartera.marginal(ev, cartera.cargar(ids, base)) if ids else None


def _fmt_ic(g: dict) -> str:
    return f"[{g['ic95'][0]:+.3f}, {g['ic95'][1]:+.3f}]" if g.get("ic95") else "—"


def _fmt_dias(x: float | None) -> str:
    return f"{x:.1f} días" if x is not None else "—"


def _universo_txt(ev: dict) -> str:
    u, din = ev["spec"]["universo"], ev.get("universoDinamico")
    if din:
        return (f"dinámico: los {din['top']} más operados de cada mes, incluidos los retirados "
                f"({len(din['simbolos'])} símbolos en total)")
    return ", ".join(u["simbolos"])


def reporte_md(ev: dict) -> str:
    s, dev, ho = ev["spec"], ev["desarrollo"], ev["holdout"]
    u = s["universo"]
    lineas = [
        f"# {ev['id']} — {ev['veredicto']}",
        "",
        f"- **Estrategia:** `{s['estrategia']['modulo']}` {json.dumps(s['estrategia'].get('params') or {})}",
        f"- **Universo:** {u.get('mercado', 'futures')} · {u['intervalo']} · " + _universo_txt(ev),
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
    rec = ev.get("reclasificacion")
    if rec:
        lineas += ["", f"**Reclasificada {rec['fecha']}: {rec['de']} → {rec['a']}.** {rec['motivo']}"]
    lineas += ["", "## Ficha", ""] + ficha_md(ev)
    est = ev.get("estabilidad")
    if est:
        lineas += ["", "## Estabilidad de parámetros", "",
                   "Misma spec en desarrollo con todos los parámetros numéricos movidos a la vez. "
                   "Si sólo funciona con los números exactos, es sobreajuste.", "",
                   "| Parámetros | n | avgR neto | ±2 EE | Conserva |", "|---|---|---|---|---|",
                   f"| como se pre-registraron | {ev['desarrollo']['global']['n']} | {est['base']:+.3f} "
                   f"| {_fmt_ic(ev['desarrollo']['global'])} | 100% |"]
        lineas += [f"| ×{v['factor']} {json.dumps(v['params'])} | {v['n']} | {v['avgRNeto']:+.3f} | {_fmt_ic(v)} "
                   f"| {(v['fraccion'] or 0):.0%} |" for v in est["vecinos"]]
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
        ]
        rob = t.get("robustez")
        if rob:
            lineas += ["", "**Robustez** (informativa, no decide): "
                       f"costos ×{rob['costosX']} → {rob['costos']['avgRNeto']:+.3f} {_fmt_ic(rob['costos'])} · "
                       f"sin las {rob['sinMejores']} mejores → "
                       f"{rob['sinTop']['avgRNeto']:+.3f} {_fmt_ic(rob['sinTop'])}"]
        lineas += ["", "| Tramo | n | avgR neto |", "|---|---|---|"]
        lineas += [f"| {x['desde']} → {x['hasta']} | {x['n']} | {x['avgRNeto']:+.3f} |" for x in t["porTramo"]]
        lineas += ["", "| Símbolo | n | avgR neto | ±2 EE |", "|---|---|---|---|"]
        con = {k: m for k, m in t["porSimbolo"].items() if m["n"]}
        lineas += [f"| {k} | {m['n']} | {m['avgRNeto']:+.3f} | {_fmt_ic(m)} |" for k, m in con.items()]
        if len(con) < len(t["porSimbolo"]):
            lineas += ["", f"{len(t['porSimbolo']) - len(con)} símbolos del universo sin operaciones en este tramo."]
    return "\n".join(lineas) + "\n"


def ficha_md(ev: dict) -> list[str]:
    """Lo que btc-signal-web pidió ver junto al veredicto: cuántas pruebas, contaminación, pre-registro,
    madre y cupo."""
    pre = ev.get("preregistro")
    out = [
        f"- **Nivel:** {ev.get('nivel') or '—'}",
        f"- **Pruebas en la familia `{ev.get('familia', '—')}`:** {ev.get('nPruebas', 1)} (esta incluida"
        + (f"; {ev['pruebasPrevias']} medidas fuera de este repo" if ev.get("pruebasPrevias") else "") + ")",
    ]
    out += [f"  - `{v['id']}`: {v['veredicto']}, desarrollo "
            + (f"{v['avgRNetoDesarrollo']:+.3f}" if v.get("avgRNetoDesarrollo") is not None else "—")
            + (", holdout mirado" if v.get("holdoutMirado") else "") for v in ev.get("variantes") or []]
    out.append(f"- **Holdout contaminado:** {'sí' if ev.get('holdoutContaminado') else 'no'}")
    out.append(f"- **Pre-registro:** commit `{pre['commit']}` del {pre['fecha']}" if pre
               else "- **Pre-registro:** no verificable (sin historia de git)")
    cupo = ev.get("maxPorDireccion")
    out.append(f"- **Cupo de cartera:** máx {cupo} por dirección" if cupo else "- **Cupo de cartera:** sin cupo")
    for nombre in ("desarrollo", "holdout"):
        t = ev.get(nombre)
        if t and t.get("maxDrawdownR") is not None:
            out.append(f"- **Peor caída ({nombre}):** {t['maxDrawdownR']:+.2f} R")
    cm = ev.get("carteraMarginal")
    if cm:
        corr = ", ".join(f"`{k}` {v:+.2f}" for k, v in cm["correlacionMensual"].items()) or "—"
        out.append(f"- **En la cartera de lo aprobado** ({cm['ventana'][0]} → {cm['ventana'][1]}): peor caída "
                   f"{cm['peorCaidaAntes']:+.1f} R → {cm['peorCaidaDespues']:+.1f} R; correlación mensual: {corr}")
    m = ev.get("comparacionMadre") or {}
    for nombre in ("desarrollo", "holdout"):
        c = m.get(nombre)
        if c:
            out.append(f"- **Contra la madre `{c['madre']}` ({nombre}):** "
                       f"hija {c['avgRNetoHija']:+.3f} (n={c['nHija']}) "
                       f"vs madre {c['avgRNetoMadre']:+.3f} (n={c['nMadre']}) → diferencia {c['diferencia']:+.3f} "
                       f"[{c['ic95'][0]:+.3f}, {c['ic95'][1]:+.3f}]; peor caída {c['peorCaidaHija']:+.2f} vs "
                       f"{c['peorCaidaMadre']:+.2f} R")
    return out


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
        "simbolos": s["universo"].get("simbolos") or (ev.get("universoDinamico") or {}).get("simbolos", []),
        "universo_dinamico_top": (ev.get("universoDinamico") or {}).get("top"),
        "config": s.get("config") or {},
        "desarrollo": resumen(ev["desarrollo"]),
        "holdout": resumen(ev["holdout"]),
        "aprobada_en": ev["fecha"],
        "commit": ev["commit"],
        "reporte": f"results/reports/{ev['id']}.md",
        "nivel": ev.get("nivel") or "aprobada",
        "n_pruebas": ev.get("nPruebas", 1),
        "variantes": [v["id"] for v in ev.get("variantes") or []],
        "holdout_contaminado": bool(ev.get("holdoutContaminado")),
        "preregistro": ev.get("preregistro"),
        "max_por_direccion": ev.get("maxPorDireccion"),
        "max_drawdown_r": {k: ev[k].get("maxDrawdownR") for k in ("desarrollo", "holdout") if ev.get(k)},
        "comparacion_madre": {k: v for k, v in (ev.get("comparacionMadre") or {}).items() if k != "filas"} or None,
    }


def guardar(ev: dict, base: Path = RESULTADOS) -> None:
    (base / "evaluaciones").mkdir(parents=True, exist_ok=True)
    (base / "reports").mkdir(parents=True, exist_ok=True)
    filas = [f for t in (ev["desarrollo"], ev["holdout"]) if t for f in t["filas"]]
    filas += (ev.get("comparacionMadre") or {}).get("filas", [])
    filas += (ev.get("estabilidad") or {}).get("filas", [])
    for f in filas:
        bitacora.registrar(f, base / "mediciones.jsonl")
    sin_filas = json.loads(json.dumps(ev, default=str))
    for t in (sin_filas["desarrollo"], sin_filas["holdout"], sin_filas.get("comparacionMadre"),
              sin_filas.get("estabilidad")):
        if t:
            t.pop("filas", None)
    (base / "evaluaciones" / f"{ev['id']}.json").write_text(
        json.dumps(sin_filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (base / "reports" / f"{ev['id']}.md").write_text(reporte_md(ev), encoding="utf-8")
    if ev["veredicto"] in NIVEL and not ev.get("soloMedicion"):
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


def anotar_en_ideas(ev: dict, ruta: Path = IDEAS) -> bool:
    """Cierra en la cola la idea que originó esta spec: a la fila cuyo estado dice «pre-registrada (<id>)»
    le agrega «→ <veredicto>» con el número de desarrollo. Sin esa fila, o si ya está anotada, no hace nada."""
    if not ruta.exists():
        return False
    lineas = ruta.read_text(encoding="utf-8").split("\n")
    for i, linea in enumerate(lineas):
        if not linea.startswith("| "):
            continue
        estado = linea.rstrip().rstrip("|").rsplit(" | ", 1)[-1]
        if "pre-registrada" not in estado or f"({ev['id']}" not in estado or "→ **" in estado:
            continue
        g = ev["desarrollo"]["global"]
        nivel = f", nivel {ev['nivel']}" if ev.get("nivel") == "observacion" else ""
        veredicto = ev["veredicto"].lower().replace("_", " ")
        nota = (f" → **{veredicto}**{nivel} ({ev['fecha'][:10]}): desarrollo n={g['n']} "
                f"{g['avgRNeto']:+.3f} {_fmt_ic(g)}")
        if ev["holdout"]:
            nota += f", holdout n={ev['holdout']['global']['n']} {ev['holdout']['global']['avgRNeto']:+.3f}"
        else:
            nota += ", holdout no mirado"
        lineas[i] = linea.rstrip().rstrip("|").rstrip() + nota.replace("|", "/") + " |"
        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return True
    return False


def evaluada(sid: str, base: Path = RESULTADOS) -> bool:
    return (base / "evaluaciones" / f"{sid}.json").exists()


def pendientes(directorio: Path = Path("specs"), base: Path = RESULTADOS) -> list[Spec]:
    out = []
    for ruta in listar(directorio):
        spec = cargar(ruta)
        if spec.estado == "pre-registrada" and not evaluada(spec.id, base):
            out.append(spec)
    return out


def _spot_si_existe(simbolo: str, intervalo: str) -> str:
    try:
        return str(data.descargar(simbolo, intervalo, "2017-01", "spot"))
    except RuntimeError:
        return f"{simbolo}: sin spot en data.binance.vision (se usa sólo futuros)"


def bajar(spec: Spec) -> None:
    """Velas (y funding) de todos los símbolos, en paralelo. Completa lo que ya haya en caché."""
    from concurrent.futures import ThreadPoolExecutor

    spec = resolver_universo(spec)
    tareas = [lambda s=s: data.descargar(s, spec.intervalo, "2020-01", spec.mercado) for s in spec.simbolos]
    if spec.funding:
        tareas += [lambda s=s: data.descargar_funding(s, "2020-01") for s in spec.simbolos]
    if spec.historia_spot:
        tareas += [lambda s=s: _spot_si_existe(s, spec.intervalo) for s in spec.simbolos]
    with ThreadPoolExecutor(8) as ex:
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
        ev = evaluar(spec, base=RESULTADOS)
        if a.forzar:
            ev["motivos"].append("re-evaluada con --forzar: el holdout ya se había mirado")
        guardar(ev)
        if DECISIONES.exists():
            anotar_en_decisiones(ev)
        anotar_en_ideas(ev)
        evaluaciones.append(ev)
        print(f"{spec.id}: {ev['veredicto']}" + (f" — {'; '.join(ev['motivos'])}" if ev["motivos"] else ""))

    if a.salida_github:
        aprobadas = [e["id"] for e in evaluaciones if e["veredicto"] in NIVEL and not e.get("soloMedicion")]
        with a.salida_github.open("a") as f:
            f.write(f"evaluadas={len(evaluaciones)}\n")
            f.write(f"aprobadas={len(aprobadas)}\n")
            f.write(f"ids={' '.join(e['id'] for e in evaluaciones)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
