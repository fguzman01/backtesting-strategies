"""Auditor determinista del proceso: ¿se está cumpliendo la metodología?

    python -m bt.auditoria                 # imprime el informe; sale con 1 si hay violaciones
    python -m bt.auditoria --md results/auditoria.md --json results/auditoria.json

Cada chequeo da ✅ (cumple), ⚠️ (advertencia: no rompe una regla pero conviene mirarlo) o ❌ (viola
una regla de CLAUDE.md). El auditor con criterio (`.claude/agents/auditor.md`) parte de este
informe para lo que el código no puede juzgar.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bt.spec import SpecInvalida, cargar, listar

OK, AVISO, FALLA = "ok", "aviso", "falla"
ICONO = {OK: "✅", AVISO: "⚠️", FALLA: "❌"}
# Con criterio "±2 EE fuera del cero" (≈ una cola al 2.3%), cuántas aprobaciones en desarrollo se
# esperan por puro azar sobre estrategias sin edge.
FALSOS_POSITIVOS_POR_PRUEBA = 0.023
MAX_VARIANTES_MISMO_MODULO = 5
# Metodología de la ventana. La comisión ida y vuelta pesa ~0.05-0.2R: un intervalo más ancho que eso no
# distingue un edge real de uno que se come la comisión.
MDE_MAX_R = 0.10
ANIOS_MIN_DESARROLLO = 3
N_MIN_POR_TRAMO = 30
BAJISTA = ("2022-01-01", "2022-12-31")  # el único año bajista completo de la historia disponible
HUECOS_MAX_PCT = 0.5
EVALUACIONES_CON_HOLDOUT_MAX = 10
MARGEN_AL_BORDE_R = 0.03


@dataclass
class Chequeo:
    nombre: str
    regla: str
    estado: str
    detalle: list[str] = field(default_factory=list)


def _git(raiz: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _hay_git(raiz: Path) -> bool:
    return _git(raiz, "rev-parse", "--is-inside-work-tree") == "true"


def _evaluaciones(raiz: Path) -> dict[str, dict]:
    out = {}
    for p in sorted((raiz / "results" / "evaluaciones").glob("*.json")):
        try:
            out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            out[p.stem] = {}
    return out


def chequear_specs(raiz: Path) -> Chequeo:
    malas = []
    for ruta in listar(raiz / "specs"):
        try:
            cargar(ruta)
        except SpecInvalida as e:
            malas.append(str(e))
    return Chequeo("Specs válidas y dentro del alcance", "Regla 1 + alcance.md",
                   FALLA if malas else OK, malas)


def chequear_preregistro(raiz: Path, evs: dict[str, dict]) -> Chequeo:
    """La spec existía antes de la evaluación y no se tocó después."""
    regla = "Regla 1: pre-registro primero; cambiar el criterio después de ver el número invalida"
    if not _hay_git(raiz):
        return Chequeo("Pre-registro antes de evaluar", regla, AVISO, ["sin historia de git: no se pudo verificar"])
    if _git(raiz, "rev-parse", "--is-shallow-repository") == "true" and evs:
        # Un clon superficial (p. ej. actions/checkout por defecto) no tiene los commits que agregaron las
        # specs: concluir que "no estaban antes" sería una violación falsa.
        return Chequeo("Pre-registro antes de evaluar", regla, AVISO,
                       ["clon sin historia completa (fetch-depth: 0 para verificarlo): no se pudo verificar"])
    problemas = []
    for sid in evs:
        spec = f"specs/{sid}.yaml"
        ev = f"results/evaluaciones/{sid}.json"
        if not (raiz / spec).exists():
            problemas.append(f"{sid}: hay evaluación pero no existe {spec}")
            continue
        alta_ev = _git(raiz, "log", "--diff-filter=A", "--format=%H", "--", ev).splitlines()
        alta_spec = _git(raiz, "log", "--diff-filter=A", "--format=%H", "--", spec).splitlines()
        if not alta_ev:
            continue  # evaluación todavía sin commit
        c_ev, c_spec = alta_ev[-1], alta_spec[-1] if alta_spec else ""
        if not c_spec or not _es_ancestro(raiz, c_spec, c_ev) or c_spec == c_ev:
            problemas.append(f"{sid}: la spec no estaba commiteada antes de la evaluación")
        despues = _git(raiz, "log", "--format=%h %s", f"{c_ev}..HEAD", "--", spec).splitlines()
        if despues:
            problemas.append(f"{sid}: la spec se modificó después de evaluarse ({'; '.join(despues)})")
    return Chequeo("Pre-registro antes de evaluar", regla, FALLA if problemas else OK, problemas)


def _es_ancestro(raiz: Path, a: str, b: str) -> bool:
    r = subprocess.run(["git", "-C", str(raiz), "merge-base", "--is-ancestor", a, b], capture_output=True)
    return r.returncode == 0


def chequear_holdout(raiz: Path, evs: dict[str, dict], bitacora: list[dict]) -> Chequeo:
    """El holdout se mira sólo si pasó desarrollo, y una sola vez."""
    problemas, avisos = [], []
    for sid, ev in evs.items():
        if not ev:
            problemas.append(f"{sid}: evaluación ilegible")
            continue
        ho = ev.get("holdout")
        dev_ok = all(c["ok"] for c in ev.get("criterios", []) if not c["criterio"].startswith("holdout"))
        if ho is not None and not dev_ok:
            problemas.append(f"{sid}: se miró el holdout sin pasar desarrollo")
        if any("--forzar" in m for m in ev.get("motivos", [])):
            avisos.append(f"{sid}: re-evaluada con --forzar (el holdout ya se había mirado antes)")
        simbolos = len(ev.get("spec", {}).get("universo", {}).get("simbolos", []))
        miradas = sum(1 for f in bitacora if f.get("nota") == f"evaluacion {sid} (holdout)")
        if simbolos and miradas > simbolos:
            problemas.append(f"{sid}: el holdout aparece {miradas // simbolos} veces en la bitácora")
    estado = FALLA if problemas else AVISO if avisos else OK
    return Chequeo("Holdout: sólo si pasa desarrollo, una vez", "Regla 2", estado, problemas + avisos)


def chequear_aprobadas(raiz: Path, evs: dict[str, dict]) -> Chequeo:
    ruta = raiz / "results" / "approved.json"
    en_archivo = {e["id"] for e in json.loads(ruta.read_text())["estrategias"]} if ruta.exists() else set()
    aprobadas = {sid for sid, ev in evs.items() if ev.get("veredicto") == "APROBADA"}
    problemas = [f"{s}: está en approved.json sin evaluación APROBADA" for s in sorted(en_archivo - aprobadas)]
    avisos = [f"{s}: APROBADA pero no está en approved.json (¿PR pendiente?)" for s in sorted(aprobadas - en_archivo)]
    estado = FALLA if problemas else AVISO if avisos else OK
    return Chequeo("approved.json coincide con las evaluaciones", "Regla 7", estado, problemas + avisos)


def chequear_lookahead_tests(raiz: Path) -> Chequeo:
    tests = "\n".join(p.read_text(encoding="utf-8") for p in (raiz / "tests").glob("test_*.py"))
    faltan = []
    for mod in sorted((raiz / "src" / "bt" / "strategies").glob("*.py")):
        if mod.stem == "__init__":
            continue
        patron = re.compile(rf"chequear_lookahead\(\s*{mod.stem}\.senales")
        if not patron.search(tests):
            faltan.append(f"{mod.stem}: ningún test le corre chequear_lookahead")
    return Chequeo("Toda estrategia tiene test de look-ahead", "Regla 5", FALLA if faltan else OK, faltan)


def chequear_brain(raiz: Path, evs: dict[str, dict]) -> Chequeo:
    ruta = raiz / "02-DOCS" / "decisiones.md"
    texto = ruta.read_text(encoding="utf-8") if ruta.exists() else ""
    faltan = [f"{sid}: evaluada pero sin línea en 02-DOCS/decisiones.md" for sid in evs if sid not in texto]
    return Chequeo("Brain actualizado con cada evaluación", "Regla 0", AVISO if faltan else OK, faltan)


def chequear_bitacora(bitacora: list[dict]) -> Chequeo:
    """Misma ventana, misma config y mismo commit con números distintos = no determinista."""
    grupos: dict[str, set] = defaultdict(set)
    for f in bitacora:
        if str(f.get("commit", "")).endswith("+cambios"):
            continue  # código sin commitear: no comparable
        clave = json.dumps([f.get("commit"), f.get("strategy"), f.get("symbol"), f.get("interval"),
                            f.get("desde"), f.get("hasta"), f.get("config")], sort_keys=True)
        grupos[clave].add((f.get("n"), round(float(f.get("avgRNeto") or 0), 9)))
    malos = [f"{json.loads(k)[1]} {json.loads(k)[2]} ({json.loads(k)[0]}): resultados {sorted(v)}"
             for k, v in grupos.items() if len(v) > 1]
    return Chequeo("Bitácora: misma config, mismo número", "Regla 6 (determinismo)", FALLA if malos else OK, malos)


def chequear_snooping(evs: dict[str, dict]) -> Chequeo:
    n = len(evs)
    por_modulo: dict[str, list[str]] = defaultdict(list)
    for sid, ev in evs.items():
        por_modulo[ev.get("spec", {}).get("estrategia", {}).get("modulo", "?")].append(sid)
    aprobadas = sum(1 for ev in evs.values() if ev.get("veredicto") == "APROBADA")
    detalle = [f"{n} evaluaciones en total; por azar se esperan ~{n * FALSOS_POSITIVOS_POR_PRUEBA:.1f} que pasen "
               f"desarrollo sin tener edge (hay {aprobadas} aprobadas, que además pasaron holdout)"]
    estado = OK
    for mod, ids in sorted(por_modulo.items()):
        if len(ids) >= MAX_VARIANTES_MISMO_MODULO:
            estado = AVISO
            detalle.append(f"{mod}: {len(ids)} variantes evaluadas — elegir la mejor entre muchas sobreajusta; "
                           "el holdout de las últimas vale menos")
    return Chequeo("Cuántas pruebas se hicieron (data snooping)", "reglas-de-medicion.md", estado, detalle)


def chequear_ventana(evs: dict[str, dict]) -> Chequeo:
    """¿Alcanzan los datos para la pregunta? Años, régimen bajista, muestra por tramo y potencia."""
    avisos = []
    for sid, ev in evs.items():
        dev = ev.get("desarrollo") or {}
        g, ventana = dev.get("global") or {}, dev.get("ventana")
        if not ventana:
            continue
        desde, hasta = ventana[0][:10], ventana[1][:10]
        anios = (int(hasta[:4]) - int(desde[:4])) + (int(hasta[5:7]) - int(desde[5:7])) / 12
        if anios < ANIOS_MIN_DESARROLLO:
            avisos.append(f"{sid}: desarrollo de {anios:.1f} años (< {ANIOS_MIN_DESARROLLO}): pocos regímenes")
        if not (desde <= BAJISTA[0] and hasta >= BAJISTA[1]):
            avisos.append(f"{sid}: el desarrollo no cubre 2022 completo, el único año bajista: "
                          "no se sabe cómo se comporta en caída")
        ic = g.get("ic95")
        if ic and (ic[1] - ic[0]) / 2 > MDE_MAX_R:
            avisos.append(f"{sid}: ±2 EE = ±{(ic[1] - ic[0]) / 2:.3f}R (> {MDE_MAX_R}R): con esta muestra no se "
                          "distingue un edge del tamaño de la comisión; hace falta más historia o más símbolos")
        chicos = [t for t in dev.get("porTramo", []) if t.get("n", 0) < N_MIN_POR_TRAMO]
        if chicos:
            avisos.append(f"{sid}: {len(chicos)} tramo(s) con menos de {N_MIN_POR_TRAMO} operaciones")
    return Chequeo("Ventana y potencia estadística", "reglas-de-medicion.md", AVISO if avisos else OK, avisos)


def chequear_calidad_datos(evs: dict[str, dict]) -> Chequeo:
    problemas, avisos = [], []
    for sid, ev in evs.items():
        for s, c in ((ev.get("desarrollo") or {}).get("calidadDatos") or {}).items():
            if c.get("duplicadas") or c.get("saltos"):
                problemas.append(f"{sid} {s}: {c.get('duplicadas', 0)} velas duplicadas, {c.get('saltos', 0)} "
                                 "saltos > 50% en una vela")
            elif c.get("huecosPct", 0) > HUECOS_MAX_PCT:
                avisos.append(f"{sid} {s}: {c['huecosPct']}% de velas faltantes ({c['huecos']})")
    sin_dato = [sid for sid, ev in evs.items() if "calidadDatos" not in (ev.get("desarrollo") or {})]
    if sin_dato:
        avisos.append(f"sin registro de calidad de datos (evaluadas antes de que existiera): {', '.join(sin_dato)}")
    estado = FALLA if problemas else AVISO if avisos else OK
    return Chequeo("Calidad de los datos usados", "02-DOCS/datos.md", estado, problemas + avisos)


def chequear_rechazos_al_borde(evs: dict[str, dict]) -> Chequeo:
    """Rechazadas por un solo criterio y por poco: candidatas a que el auditor con criterio las revise.

    No es una invitación a re-evaluarlas: una mejora sólo entra como spec NUEVA, con un mecanismo
    escrito antes de correr, y cuenta como una prueba más (data snooping).
    """
    borde = []
    for sid, ev in evs.items():
        if ev.get("veredicto") != "RECHAZADA":
            continue
        fallidos = [c for c in ev.get("criterios", []) if not c["ok"]]
        if len(fallidos) != 1:
            continue
        g = (ev.get("desarrollo") or {}).get("global") or {}
        nulo = ((ev.get("desarrollo") or {}).get("nulo") or {}).get("p95")
        criterio = fallidos[0]["criterio"]
        margen = None
        if "fuera del cero" in criterio and g.get("ic95"):
            margen = -g["ic95"][0]
        elif "nulo" in criterio and nulo is not None:
            margen = nulo - g.get("avgRNeto", 0)
        if margen is not None and margen <= MARGEN_AL_BORDE_R:
            borde.append(f"{sid}: falló sólo «{criterio}» por {margen:.3f}R")
    return Chequeo("Rechazos al borde (para revisión con criterio)", "auditor.md: revisión de rechazadas",
                   AVISO if borde else OK, borde)


def chequear_desgaste_holdout(evs: dict[str, dict]) -> Chequeo:
    miradas = sorted(sid for sid, ev in evs.items() if ev.get("holdout") is not None)
    detalle = [f"el holdout (desde 2025-09-09) se miró en {len(miradas)} evaluación(es)"]
    estado = OK
    if len(miradas) >= EVALUACIONES_CON_HOLDOUT_MAX:
        estado = AVISO
        detalle.append("cada mirada lo gasta: planificar su renovación (un holdout nuevo con datos posteriores)")
    return Chequeo("Desgaste del holdout", "Regla 2", estado, detalle)


def auditar(raiz: Path = Path(".")) -> list[Chequeo]:
    evs = _evaluaciones(raiz)
    ruta_b = raiz / "results" / "mediciones.jsonl"
    bitacora = [json.loads(x) for x in ruta_b.read_text().splitlines() if x.strip()] if ruta_b.exists() else []
    return [
        chequear_specs(raiz),
        chequear_preregistro(raiz, evs),
        chequear_holdout(raiz, evs, bitacora),
        chequear_aprobadas(raiz, evs),
        chequear_lookahead_tests(raiz),
        chequear_brain(raiz, evs),
        chequear_bitacora(bitacora),
        chequear_snooping(evs),
        chequear_ventana(evs),
        chequear_calidad_datos(evs),
        chequear_rechazos_al_borde(evs),
        chequear_desgaste_holdout(evs),
    ]


def informe_md(chequeos: list[Chequeo]) -> str:
    fallas = sum(c.estado == FALLA for c in chequeos)
    avisos = sum(c.estado == AVISO for c in chequeos)
    lineas = ["# Auditoría del proceso", "",
              f"{len(chequeos)} chequeos · {fallas} violaciones · {avisos} advertencias", "",
              "| | Chequeo | Regla |", "|---|---|---|"]
    lineas += [f"| {ICONO[c.estado]} | {c.nombre} | {c.regla} |" for c in chequeos]
    for c in chequeos:
        if c.detalle:
            lineas += ["", f"### {ICONO[c.estado]} {c.nombre}", ""] + [f"- {d}" for d in c.detalle]
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raiz", type=Path, default=Path("."))
    p.add_argument("--md", type=Path, help="escribir el informe en markdown")
    p.add_argument("--json", type=Path, help="escribir el informe en JSON (lo lee el dashboard)")
    a = p.parse_args(argv)
    chequeos = auditar(a.raiz)
    texto = informe_md(chequeos)
    print(texto)
    if a.md:
        a.md.parent.mkdir(parents=True, exist_ok=True)
        a.md.write_text(texto, encoding="utf-8")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps([asdict(c) for c in chequeos], ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if any(c.estado == FALLA for c in chequeos) else 0


if __name__ == "__main__":
    sys.exit(main())
