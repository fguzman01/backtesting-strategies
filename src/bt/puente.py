"""Puente con btc-signal-web: lee el informe diario del paper y lo compara contra lo que predijo la factory.

El bot (producción) escribe una vez por día `factory-paper.json` en la rama `factory-paper` de
fguzman01/btc-signal-web (`src/lib/factory/informePaper.ts`). Este módulo lo lee, lo resume en
markdown y lo anota en `02-DOCS/retroalimentacion.md`, que es lo que lee el auditor.

    git -C ../btc-signal-web fetch origin factory-paper
    git -C ../btc-signal-web show origin/factory-paper:factory-paper.json > /tmp/informe.json
    python -m bt.puente /tmp/informe.json            # imprime el resumen
    python -m bt.puente /tmp/informe.json --anotar   # además lo agrega a retroalimentacion.md

    python -m bt.puente /tmp/informe.json --cupo 3 --desde 2026-10-01   # backtest con cupo del bot

`--cupo` corre la spec de cada estrategia del informe con `max_por_direccion=N` en la ventana del paper
(`--desde` si el informe no la trae; `--hasta` por defecto es la fecha del informe) y muestra su avgR ±2 EE
junto al del paper. Es una medición de paridad (queda en `results/mediciones.jsonl`): no escribe
evaluaciones ni toca approved.json, y no alimenta ninguna decisión de aprobación.

No decide nada: no cambia veredictos ni approved.json. Marca, para que alguien mire, cuando el paper
queda por debajo de lo que predijo el backtest con una muestra que ya alcanza para decirlo.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

SPECS = Path("specs")
DOC = Path("02-DOCS") / "retroalimentacion.md"
LECTURAS = {
    "muestra_chica": "muestra chica: no se concluye",
    "coherente": "coherente con el backtest",
    "peor_que_backtest": "⚠️ PEOR que el backtest",
    "mejor_que_backtest": "mejor que el backtest",
}
ALERTA = "peor_que_backtest"
CABECERA = """# Retroalimentación del bot

Lo que vuelve de btc-signal-web: el paper de cada aprobada contra lo que predijo la factory, una vez
por semana (agente Puente, `.claude/agents/puente.md`; datos de `bt.puente`). Una línea marcada
⚠️ PEOR es una alerta para el auditor, no un veredicto: con muestra suficiente, el holdout del
backtest quedó por encima del intervalo de ±2 EE del paper.

Además se anotan acá los issues `retro` de la factory (comentarios del bot sobre una ficha o una
aprobada) y qué se hizo con cada uno.
"""


class InformeInvalido(ValueError):
    pass


def validar(inf: dict) -> list[dict]:
    if not isinstance(inf, dict) or not isinstance(inf.get("estrategias"), list) or "generado" not in inf:
        raise InformeInvalido("el informe tiene que traer `generado` y la lista `estrategias`")
    for e in inf["estrategias"]:
        for campo in ("id", "implementadaComo", "paper", "backtest", "lectura"):
            if campo not in e:
                raise InformeInvalido(f"{e.get('id', '?')}: falta `{campo}`")
    return inf["estrategias"]


def _r(x: float | None) -> str:
    return "—" if x is None else f"{x:+.3f}"


def _ic(ic: list | None) -> str:
    return "—" if not ic else f"[{ic[0]:+.3f}, {ic[1]:+.3f}]"


def resumen_md(inf: dict) -> str:
    estrategias = validar(inf)
    origen = f"{inf.get('ambiente', '?')}, commit {inf.get('commit') or '—'}"
    lineas = [f"## Informe del {inf['generado'][:10]} ({origen})", ""]
    if not estrategias:
        return "\n".join(lineas + ["Ninguna aprobada implementada en el bot todavía.", ""])
    lineas += ["| Estrategia | Nivel | Paper n | Paper avgR ±2 EE | Holdout backtest | Lectura "
               "| Madre en la misma ventana |", "|---|---|---|---|---|---|---|"]
    for e in estrategias:
        p, h, m = e["paper"], e["backtest"]["holdout"], e.get("madre")
        madre = "—"
        if m:
            madre = (f"{m['estrategia']}: n={m['paper']['n']} {_r(m['paper']['avgRNeto'])}; "
                     f"diferencia {_r(m.get('diferencia'))} {_ic(m.get('ic95'))}")
        lineas.append(
            f"| `{e['id']}` → {e['implementadaComo']} | {e.get('nivel', '—')} "
            f"| {p['n']} (+{e.get('abiertas', 0)} abiertas) "
            f"| {_r(p['avgRNeto'])} {_ic(p.get('ic95'))} | {_r(h['avgRNeto'])} (n={h['n']}) "
            f"| {LECTURAS.get(e['lectura'], e['lectura'])} | {madre} |")
    alertas = alertas_de(inf)
    if alertas:
        lineas += ["", "**Alertas para el auditor:** " + ", ".join(f"`{a}`" for a in alertas)]
    if any(e.get("sinR") for e in estrategias):
        lineas += ["", "Posiciones cerradas sin R en las notas (no cuentan): "
                   + ", ".join(f"{e['implementadaComo']} {e['sinR']}" for e in estrategias if e.get("sinR"))]
    return "\n".join(lineas) + "\n"


def alertas_de(inf: dict) -> list[str]:
    return [e["id"] for e in validar(inf) if e["lectura"] == ALERTA]


def anotar(inf: dict, ruta: Path = DOC) -> bool:
    """Agrega el resumen arriba de los anteriores. Devuelve False si ese informe ya estaba."""
    texto = ruta.read_text(encoding="utf-8") if ruta.exists() else CABECERA
    marca = f"## Informe del {inf['generado'][:10]} "
    if marca in texto:
        return False
    if CABECERA.strip() not in texto:
        texto = CABECERA + "\n" + texto
    cab, _, resto = texto.partition("\n## ")
    nuevo = cab.rstrip("\n") + "\n\n" + resumen_md(inf) + ("\n## " + resto if resto else "")
    ruta.write_text(nuevo.rstrip("\n") + "\n", encoding="utf-8")
    return True


def alertas_vigentes(ruta: Path = DOC) -> list[str]:
    """Las alertas del informe más reciente anotado (lo usa el auditor determinista)."""
    if not ruta.exists():
        return []
    _, _, resto = ruta.read_text(encoding="utf-8").partition("\n## Informe del ")
    ultimo = resto.split("\n## ", 1)[0]
    linea = next((x for x in ultimo.splitlines() if x.startswith("**Alertas para el auditor:**")), "")
    return [p.strip("`, ") for p in linea.split(":**", 1)[-1].split(",") if p.strip("`, ")]


def backtest_con_cupo(spec, desde: str, hasta: str, cupo: int = 3, cargar_velas=None, cargar_funding=None) -> dict:
    """Backtest de `spec` con cupo de cartera `cupo` por dirección, sólo en [desde, hasta).

    La ventana del paper cae en el holdout: se pide de forma explícita (`holdout=True`) cuando cruza el
    corte y la corrida queda en la bitácora con su tramo. No guarda nada más: es paridad, no evaluación.
    """
    from bt import data, evaluar
    from bt.splits import clasificar

    if cupo < 1:
        raise ValueError("el cupo tiene que ser ≥ 1")
    spec = dataclasses.replace(spec, max_por_direccion=cupo)
    return evaluar._tramo(
        spec, cargar_velas or data.cargar, cargar_funding or data.cargar_funding,
        holdout=clasificar(desde, hasta) != "desarrollo", desde_forzado=desde, hasta_forzado=hasta,
        nota=f"paridad-cupo {spec.id} cupo={cupo} {desde}→{hasta}",
    )


def comparacion_cupo_md(e: dict, bt: dict, cupo: int, desde: str, hasta: str) -> str:
    g, p = bt["global"], e["paper"]
    return (f"- `{e['id']}` ({e['implementadaComo']}), {desde} → {hasta}, cupo {cupo} por dirección: "
            f"backtest n={g['n']} {_r(g['avgRNeto'])} {_ic(g.get('ic95'))} · "
            f"paper n={p['n']} {_r(p['avgRNeto'])} {_ic(p.get('ic95'))}")


def paridad_cupo_md(inf: dict, cupo: int, desde: str | None, hasta: str | None, specs: Path = SPECS, **cargas) -> str:
    from bt import spec as spec_mod

    hasta = hasta or inf["generado"][:10]
    lineas = [f"### Paridad con el cupo del bot ({cupo} por dirección)", ""]
    for e in validar(inf):
        d = desde or (e["paper"].get("desde") or "")[:10]
        if not d:
            raise InformeInvalido(f"{e['id']}: el informe no trae la ventana del paper; pasá --desde")
        bt = backtest_con_cupo(spec_mod.cargar(specs / f"{e['id']}.yaml"), d, hasta, cupo, **cargas)
        lineas.append(comparacion_cupo_md(e, bt, cupo, d, hasta))
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("informe", type=Path)
    p.add_argument("--anotar", action="store_true", help=f"agregar el resumen a {DOC}")
    p.add_argument("--cupo", type=int, help="backtest con este cupo por dirección en la ventana del paper")
    p.add_argument("--desde", help="inicio de la ventana del paper (si el informe no la trae)")
    p.add_argument("--hasta", help="fin de la ventana (default: fecha del informe)")
    a = p.parse_args(argv)
    try:
        inf = json.loads(a.informe.read_text(encoding="utf-8"))
        print(resumen_md(inf))
        if a.cupo:
            print(paridad_cupo_md(inf, a.cupo, a.desde, a.hasta))
    except (json.JSONDecodeError, InformeInvalido) as e:
        print(f"informe inválido: {e}", file=sys.stderr)
        return 2
    if a.anotar:
        print(f"{DOC}: {'anotado' if anotar(inf) else 'ese informe ya estaba anotado'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
