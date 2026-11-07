"""De GitHub al grupo de Telegram del proyecto, a través del operador (OPERACION.md §5 y §8).

Arma el texto de las tarjetas y del cierre del día y los manda con `POST /tarjeta`. Lo usan
`tarjetas.yml` (cuando un issue pide decisión o un PR queda listo) y `cierre.yml` (21:00 Chile).

    OPERADOR_URL=... OPERADOR_KEY=... python -m bt.operador issue evento.json
    python -m bt.operador pr pr.json
    python -m bt.operador cierre --issues issues.json --prs prs.json --hechos hechos.json [--enviar]

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
    cuerpo = _corto(issue.get("body"))
    return (f"🗂 <b>#{issue['number']} {e(issue['title'])}</b>\n<i>{e(meta)}</i>\n\n{e(cuerpo)}\n\n"
            f"<b>{QUE_DECIDIR.get(estado, '')}</b>").strip()


def texto_pr(pr: dict) -> str:
    e = html.escape
    cambios = f"+{pr.get('additions', 0)} −{pr.get('deletions', 0)} en {pr.get('changed_files', '?')} archivos"
    cuerpo = e(_corto(pr.get("body"), 500))
    return f"🔀 <b>PR #{pr['number']} {e(pr['title'])}</b>\n<i>CI ✅ · {cambios}</i>\n\n{cuerpo}\n\n<b>¿Se fusiona?</b>"


def texto_cierre(issues: list[dict], prs: list[dict], hechos: list[str], hoy: dt.date) -> str | None:
    """Cierre del día: qué avanzó y qué espera a Felipe. None si no hubo nada (no se manda)."""
    e = html.escape
    abiertos = [i for i in issues if (i.get("state") or "").upper() == "OPEN"]
    espera = [i for i in abiertos if _etq(i, "estado") in ("propuesta", "diseñada", "en-revision")]
    prs_abiertos = [p for p in prs if not p.get("title", "").startswith("[rutina]")]
    marcha = [i for i in abiertos if _etq(i, "estado") in ("aprobada", "en-curso")]
    if not (hechos or espera or prs_abiertos):
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
    elif a.cmd == "pr":
        pr = leer(a.pr)
        enviar("pr", texto_pr(pr), pr["number"], pr.get("html_url"))
    else:
        # El cierre corre a las 00:00 UTC, que en Chile todavía es el día anterior (21:00).
        hoy = dt.datetime.now(ZoneInfo("America/Santiago")).date()
        texto = texto_cierre(leer(a.issues), leer(a.prs), leer(a.hechos), hoy)
        if texto is None:
            print("sin movimiento ni pendientes: no se manda cierre")
            return 0
        enviar("aviso", texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
