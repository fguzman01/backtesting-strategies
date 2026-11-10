"""De GitHub al grupo de Telegram del proyecto, a través del operador (OPERACION.md §5 y §8).

Arma el texto de las tarjetas y del cierre del día y los manda con `POST /tarjeta`. Lo usan
`tarjetas.yml` (cuando un issue pide decisión o un PR queda listo) y `cierre.yml` (21:00 Chile).

    OPERADOR_URL=... OPERADOR_KEY=... python -m bt.operador issue evento.json
    python -m bt.operador pr pr.json
    python -m bt.operador cierre --issues issues.json --prs prs.json --hechos hechos.json \
        [--runs runs.json] [--recordar]

Sin OPERADOR_URL / OPERADOR_KEY imprime lo que mandaría y no falla.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = os.environ.get("GITHUB_REPOSITORY", "fguzman01/backtesting-strategies")
QUE_DECIDIR = {"propuesta": "¿Se hace?", "diseñada": "¿Se implementa este plan?"}


def _etq(item: dict, grupo: str) -> str | None:
    for e in item.get("labels", []):
        nombre = e["name"] if isinstance(e, dict) else e
        if nombre.startswith(f"{grupo}:"):
            return nombre.split(":", 1)[1]
    return None


def _corto(texto: str | None, n: int = 600) -> str:
    t = (texto or "").replace("\r", "").strip()
    t = t.split("\n---\n")[0].strip()  # sin el pie de atribución
    return t if len(t) <= n else t[: n - 1] + "…"


def texto_issue(issue: dict, estado: str) -> str:
    e = html.escape
    meta = " · ".join(x for x in (_etq(issue, "tipo"), _etq(issue, "prio"), _etq(issue, "riesgo") and
                                  f"riesgo {_etq(issue, 'riesgo')}") if x)
    cuerpo = issue.get("body") or ""
    if estado == "diseñada" and "## Plan" in cuerpo:  # la tarjeta del plan muestra el plan
        cuerpo = "## Plan" + cuerpo.split("## Plan", 1)[1]
    cuerpo = _corto(cuerpo, 900 if estado == "diseñada" else 600)
    return (f"🗂 <b>#{issue['number']} {e(issue['title'])}</b>\n<i>{e(meta)}</i>\n\n{e(cuerpo)}\n\n"
            f"<b>{QUE_DECIDIR.get(estado, '')}</b>").strip()


def texto_pr(pr: dict) -> str:
    e = html.escape
    cambios = f"+{pr.get('additions', 0)} −{pr.get('deletions', 0)} en {pr.get('changed_files', '?')} archivos"
    cuerpo = e(_corto(pr.get("body"), 500))
    return f"🔀 <b>PR #{pr['number']} {e(pr['title'])}</b>\n<i>CI ✅ · {cambios}</i>\n\n{cuerpo}\n\n<b>¿Se fusiona?</b>"


MARCA_TELEGRAM = "<!-- telegram -->"


def texto_comentario(issue: dict, comentario: dict) -> str | None:
    """Respuestas de los agentes que empiezan con la marca: le llegan a Felipe al grupo."""
    cuerpo = (comentario.get("body") or "").strip()
    if not cuerpo.startswith(MARCA_TELEGRAM):
        return None
    e = html.escape
    return f"💬 <b>#{issue['number']} {e(issue['title'])}</b>\n\n{e(_corto(cuerpo[len(MARCA_TELEGRAM):], 1200))}"


def recordatorios(issues: list[dict], prs: list[dict], maximo: int = 5) -> list[tuple]:
    """Tarjetas con botones de lo que sigue esperando a Felipe (se reenvían en el cierre)."""
    out = []
    for i in sorted(issues, key=lambda x: x["number"]):
        est = _etq(i, "estado")
        if (i.get("state") or "OPEN").upper() == "OPEN" and est in QUE_DECIDIR:
            out.append(("issue", "🔁 " + texto_issue(i, est), i["number"], i.get("html_url") or i.get("url")))
    for p in prs:
        if not p.get("title", "").startswith("[rutina]"):
            out.append(("pr", f"🔁 🔀 <b>PR #{p['number']} {html.escape(p['title'])}</b>\n\n<b>¿Se fusiona?</b>",
                        p["number"], p.get("html_url") or p.get("url")))
    return out[:maximo]


# Salud del proceso (Felipe, 2026-11-10): lo que se trabó, sin gastar Claude. Días que puede estar un
# issue sin movimiento en cada estado antes de avisar. `en-curso` no avisa: es la cola del desarrollador.
TRABADO_DIAS = {"aprobada": 1, "propuesta": 3, "diseñada": 3, "en-revision": 3, "requiere-sesion": 3}
PR_ABIERTO_HORAS = 24


def _fecha(texto: str | None) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat((texto or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def salud(issues: list[dict], prs: list[dict], runs: list[dict], ahora: dt.datetime) -> list[str]:
    """Avisos de proceso: issues quietos más de lo esperado, PRs abiertos hace más de un día y workflows
    que fallaron (la lista `runs` ya viene filtrada a las fallas de las últimas 24 h)."""
    out = []
    for i in sorted(issues, key=lambda x: x["number"]):
        est, cuando = _etq(i, "estado"), _fecha(i.get("updatedAt") or i.get("updated_at"))
        if est in TRABADO_DIAS and cuando and (ahora - cuando).days >= TRABADO_DIAS[est]:
            out.append(f"#{i['number']} lleva {(ahora - cuando).days} días en {est} sin movimiento")
    for p in sorted(prs, key=lambda x: x["number"]):
        cuando = _fecha(p.get("createdAt") or p.get("created_at"))
        if cuando and (ahora - cuando).total_seconds() >= PR_ABIERTO_HORAS * 3600:
            out.append(f"PR #{p['number']} abierto hace {int((ahora - cuando).total_seconds() // 3600)} h")
    for nombre in sorted({r.get("workflowName") or r.get("name") or "?" for r in runs}):
        n = sum(1 for r in runs if (r.get("workflowName") or r.get("name") or "?") == nombre)
        out.append(f"workflow «{nombre}» falló {n} {'veces' if n > 1 else 'vez'} en 24 h")
    return out


def texto_cierre(issues: list[dict], prs: list[dict], hechos: list[str], hoy: dt.date,
                 avisos: list[str] | None = None) -> str | None:
    """Cierre del día: qué avanzó, qué espera a Felipe y si algo se trabó. None si no hubo nada."""
    e = html.escape
    avisos = avisos or []
    abiertos = [i for i in issues if (i.get("state") or "").upper() == "OPEN"]
    espera = [i for i in abiertos if _etq(i, "estado") in ("propuesta", "diseñada", "en-revision")]
    prs_abiertos = [p for p in prs if not p.get("title", "").startswith("[rutina]")]
    marcha = [i for i in abiertos if _etq(i, "estado") in ("aprobada", "en-curso")]
    if not (hechos or espera or prs_abiertos or avisos):
        return None
    lineas = [f"🌙 <b>Cierre del día</b> · {hoy:%d-%m}", ""]
    lineas += ["<b>Avanzó hoy</b>"] + ([f"• {e(h)}" for h in hechos] or ["• nada nuevo"])
    if espera or prs_abiertos:
        lineas += ["", f"<b>Espera tu decisión ({len(espera) + len(prs_abiertos)})</b>"]
        lineas += [f"• #{i['number']} {e(i['title'])} — {_etq(i, 'estado')}" for i in espera]
        lineas += [f"• PR #{p['number']} {e(p['title'])}" for p in prs_abiertos]
    if marcha:
        lineas += ["", "<b>Mañana se trabaja</b>"]
        lineas += [f"• #{i['number']} {e(i['title'])} — {_etq(i, 'estado')}" for i in marcha[:3]]
    lineas += ["", "<b>Salud del proceso</b>"] + ([f"⚠️ {e(a)}" for a in avisos] or ["✅ nada trabado"])
    return "\n".join(lineas)


def enviar(tipo: str, texto: str, numero: int | None = None, url: str | None = None) -> bool:
    base, clave = os.environ.get("OPERADOR_URL"), os.environ.get("OPERADOR_KEY")
    if not base or not clave:
        print("sin OPERADOR_URL / OPERADOR_KEY: no se envía\n" + texto)
        return False
    datos = json.dumps({"repo": REPO, "tipo": tipo, "numero": numero, "texto": texto, "url": url}).encode()
    req = urllib.request.Request(f"{base.rstrip('/')}/tarjeta", data=datos, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {clave}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("ok") is True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("issue", help="evento `issues` de GitHub (labeled)")
    pi.add_argument("evento", type=Path)
    pp = sub.add_parser("pr", help="PR (JSON de la API)")
    pp.add_argument("pr", type=Path)
    pc = sub.add_parser("cierre")
    pc.add_argument("--issues", type=Path, required=True)
    pc.add_argument("--prs", type=Path, required=True)
    pc.add_argument("--hechos", type=Path, required=True)
    pc.add_argument("--recordar", action="store_true", help="reenviar las tarjetas de lo pendiente")
    pc.add_argument("--runs", type=Path, help="workflows fallidos de las últimas 24 h (gh run list --json)")
    pm = sub.add_parser("comentario", help="evento `issue_comment` de GitHub")
    pm.add_argument("evento", type=Path)
    a = p.parse_args(argv)
    leer = lambda r: json.loads(r.read_text(encoding="utf-8"))  # noqa: E731
    if a.cmd == "issue":
        ev = leer(a.evento)
        estado = (ev.get("label") or {}).get("name", "").removeprefix("estado:")
        if estado not in QUE_DECIDIR:
            print(f"etiqueta {estado!r}: no pide decisión")
            return 0
        i = ev["issue"]
        enviar("issue", texto_issue(i, estado), i["number"], i.get("html_url"))
    elif a.cmd == "comentario":
        ev = leer(a.evento)
        texto = texto_comentario(ev["issue"], ev["comment"])
        if texto is None:
            print("comentario sin la marca de Telegram: no se reenvía")
            return 0
        enviar("aviso", texto, url=ev["comment"].get("html_url"))
    elif a.cmd == "pr":
        pr = leer(a.pr)
        enviar("pr", texto_pr(pr), pr["number"], pr.get("html_url"))
    else:
        # El cierre corre a las 00:00 UTC, que en Chile todavía es el día anterior (21:00).
        ahora = dt.datetime.now(ZoneInfo("America/Santiago"))
        avisos = salud(leer(a.issues), leer(a.prs), leer(a.runs) if a.runs else [], ahora)
        texto = texto_cierre(leer(a.issues), leer(a.prs), leer(a.hechos), ahora.date(), avisos)
        if texto is None:
            print("sin movimiento ni pendientes: no se manda cierre")
            return 0
        enviar("aviso", texto)
        if a.recordar:
            for tipo, t, n, url in recordatorios(leer(a.issues), leer(a.prs)):
                enviar(tipo, t, n, url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
