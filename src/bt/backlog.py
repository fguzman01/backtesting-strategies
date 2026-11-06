"""`02-DOCS/backlog.md` generado desde los GitHub Issues (marco de operación, OPERACION.md §3).

Los issues son la fuente de verdad de las tareas del sistema; este archivo es una vista para el
dashboard, el resumen y quien lea el repo. No se edita a mano: lo regenera `backlog.yml`.

    gh issue list --state all --limit 500 --json number,title,labels,state,closedAt,url > issues.json
    python -m bt.backlog issues.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DOC = Path("02-DOCS") / "backlog.md"
ORDEN_PRIO = {"P1": 0, "P2": 1, "P3": 2}
EN_MARCHA = ("aprobada", "diseñada", "en-curso", "en-revision")
ESPERA_FELIPE = {"propuesta": "aprobar o descartar", "diseñada": "aprobar el plan",
                 "en-revision": "fusionar o rechazar el PR"}


def _etq(issue: dict, grupo: str) -> str | None:
    for e in issue.get("labels", []):
        nombre = e["name"] if isinstance(e, dict) else e
        if nombre.startswith(f"{grupo}:"):
            return nombre.split(":", 1)[1]
    return None


def _clave(i: dict) -> tuple:
    return (ORDEN_PRIO.get(_etq(i, "prio") or "", 9), i["number"])


def _fila(i: dict) -> str:
    return (f"| [#{i['number']}]({i.get('url', '')}) | {i['title'].replace('|', '/')} | {_etq(i, 'tipo') or '—'} "
            f"| {_etq(i, 'prio') or '—'} | {_etq(i, 'riesgo') or '—'} | {_etq(i, 'estado') or '—'} |")


def generar(issues: list[dict]) -> str:
    abiertos = [i for i in issues if i.get("state", "").upper() == "OPEN"]
    cerrados = sorted((i for i in issues if i.get("state", "").upper() != "OPEN"),
                      key=lambda i: i.get("closedAt") or "", reverse=True)
    estado = {i["number"]: _etq(i, "estado") or "propuesta" for i in abiertos}
    # Recomendadas: primero lo que ya está en marcha, después las propuestas P1; como mucho 3.
    marcha = sorted((i for i in abiertos if estado[i["number"]] in EN_MARCHA), key=_clave)
    props = sorted((i for i in abiertos if estado[i["number"]] == "propuesta" and _etq(i, "prio") == "P1"), key=_clave)
    rec = (marcha + props)[:3]
    cab = "| # | Tarea | Tipo | Prio | Riesgo | Estado |\n|---|---|---|---|---|---|"
    out = ["# Backlog del sistema", "",
           "**Generado desde los GitHub Issues** (`bt.backlog`, `backlog.yml`): no se edita a mano. Las tareas se "
           "crean y se mueven en los issues; Felipe decide con ✅/❌ (OPERACION.md). Lo anterior a los issues está "
           "en `backlog-historico.md`.", "",
           "## Recomendadas para esta semana", ""]
    out += [f"{n}. **#{i['number']}** {i['title']}" for n, i in enumerate(rec, 1)] or ["Nada pendiente."]
    espera = sorted((i for i in abiertos if estado[i["number"]] in ESPERA_FELIPE), key=_clave)
    out += ["", "## Espera tu decisión", ""]
    out += ([cab] + [_fila(i) + f" ← {ESPERA_FELIPE[estado[i['number']]]}" for i in espera]) if espera else ["Nada."]
    trab = sorted((i for i in abiertos if estado[i["number"]] in ("aprobada", "en-curso")), key=_clave)
    out += ["", "## En marcha", ""] + (([cab] + [_fila(i) for i in trab]) if trab else ["Nada."])
    ses = [i for i in abiertos if estado[i["number"]] == "requiere-sesion"]
    if ses:
        out += ["", "## Requiere sesión con Felipe", "", cab] + [_fila(i) for i in sorted(ses, key=_clave)]
    out += ["", "## Pendientes", ""]
    resto = sorted((i for i in abiertos if estado[i["number"]] == "propuesta"), key=_clave)
    out += ([cab] + [_fila(i) for i in resto]) if resto else ["Nada."]
    hechas = [i for i in cerrados if _etq(i, "estado") != "descartada"][:20]
    desc = [i for i in cerrados if _etq(i, "estado") == "descartada"][:20]
    out += ["", "## Hechas (últimas 20)", ""] + (
        [f"- [#{i['number']}]({i.get('url', '')}) {i['title']} ({(i.get('closedAt') or '')[:10]})" for i in hechas]
        or ["Todavía ninguna desde que se usan issues."])
    if desc:
        out += ["", "## Descartadas (últimas 20)", ""]
        out += [f"- [#{i['number']}]({i.get('url', '')}) {i['title']}" for i in desc]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("issues", type=Path)
    a = p.parse_args(argv)
    issues = [i for i in json.loads(a.issues.read_text(encoding="utf-8")) if "pull_request" not in i]
    DOC.write_text(generar(issues), encoding="utf-8")
    print(f"{DOC}: {sum(1 for i in issues if i.get('state', '').upper() == 'OPEN')} abiertos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
