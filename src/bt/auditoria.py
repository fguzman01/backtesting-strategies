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
