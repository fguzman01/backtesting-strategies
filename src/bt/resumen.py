"""Resumen semanal de la factory para Felipe, por Telegram.

Qué se evaluó, qué quedó en la cola, cómo va lo aprobado en el paper del bot y hacia adelante, qué
dice el auditor y qué decisiones esperan a Felipe. Lo manda `resumen.yml` los lunes.

    python -m bt.resumen                                  # imprime el resumen de los últimos 7 días
    python -m bt.resumen --informe-bot f.json --prs p.json --enviar   # y lo manda

Para enviar necesita TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en el entorno.

Sólo lee el repo; no cambia nada.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

LIMITE = 4000  # Telegram corta en 4096
PAGINA = "https://fguzman01.github.io/backtesting-strategies/"
ICONO = {"APROBADA": "✅", "OBSERVACION": "◐", "RECHAZADA": "✕", "NO_CONCLUYENTE": "?"}


def _r(x) -> str:
    return "—" if x is None else f"{x:+.3f}"


def evaluadas(raiz: Path, desde: dt.date) -> list[dict]:
    out = []
    for p in sorted((raiz / "results" / "evaluaciones").glob("*.json")):
        ev = json.loads(p.read_text(encoding="utf-8"))
        if dt.date.fromisoformat(ev["fecha"][:10]) >= desde:
            out.append(ev)
    return out


def cola(raiz: Path) -> dict[str, list[str]]:
    """{estado: ['#n idea', ...]} de 02-DOCS/ideas.md."""
    ruta = raiz / "02-DOCS" / "ideas.md"
    out: dict[str, list[str]] = {}
    if not ruta.exists():
        return out
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+)\|.*\|\s*([^|]*)\|\s*$", linea)
        if not m:
            continue
        estado = m.group(3).strip().strip("*").lower()
        clave = next((e for e in ("en cola", "propuesta", "pre-registrada", "rechazada", "descartada")
                      if estado.startswith(e)), "otro")
        out.setdefault(clave, []).append(f"#{m.group(1)} {m.group(2).replace('**', '').strip()[:70]}")
    return out


def recomendadas(raiz: Path) -> list[str]:
    """Las del PO para esta semana (02-DOCS/backlog.md), con su nombre."""
    ruta = raiz / "02-DOCS" / "backlog.md"
    if not ruta.exists():
        return []
    texto = ruta.read_text(encoding="utf-8")
    bloque = texto.split("## Recomendadas para esta semana", 1)[-1].split("\n## ", 1)[0]
    return [re.sub(r"\*\*", "", m).strip() for m in re.findall(r"^\d+\.\s+(.+)$", bloque, re.M)][:3]


def armar(raiz: Path = Path("."), hoy: dt.date | None = None, informe_bot: dict | None = None,
          prs: list[dict] | None = None, auditoria: list | None = None,
          issues: list[dict] | None = None) -> str:
    hoy = hoy or dt.date.today()
    desde = hoy - dt.timedelta(days=7)
    e = html.escape
    lineas = [f"🏭 <b>Factory de backtesting</b> · semana {desde:%d-%m} → {hoy:%d-%m}", ""]

    evs = evaluadas(raiz, desde)
    lineas.append(f"<b>Evaluadas: {len(evs)}</b>")
    for ev in evs:
        g = ev["desarrollo"]["global"]
        ic = g.get("ic95")
        ho = ev.get("holdout")
        ver = "OBSERVACION" if ev.get("nivel") == "observacion" else ev["veredicto"]
        lineas.append(f"{ICONO.get(ver, '·')} {e(ev['id'])}: {ver.lower()} · desarrollo "
                      f"{_r(g['avgRNeto'])}" + (f" [{ic[0]:+.2f}, {ic[1]:+.2f}]" if ic else "") + f" n={g['n']}"
                      + (f" · holdout {_r(ho['global']['avgRNeto'])}" if ho else ""))
    if not evs:
        lineas.append("Ninguna esta semana.")

    c = cola(raiz)
    lineas += ["", f"<b>Cola de ideas:</b> {len(c.get('en cola', []))} en cola, "
               f"{len(c.get('propuesta', []))} propuestas esperando tu visto bueno"]
    lineas += [f"▸ {e(x)}" for x in c.get("en cola", [])[:3]]
    if not c.get("en cola"):
        lineas.append("⚠️ La cola está vacía: la rutina va a proponer en vez de evaluar. Pasá alguna a «en cola».")

    ruta_ap = raiz / "results" / "approved.json"
    aprobadas = json.loads(ruta_ap.read_text())["estrategias"] if ruta_ap.exists() else []
    if aprobadas:
        bot = {x["id"]: x for x in (informe_bot or {}).get("estrategias", [])}
        lineas += ["", "<b>Lo aprobado</b>"]
        for a in aprobadas:
            b = bot.get(a["id"])
            paper = (f"paper n={b['paper']['n']} {_r(b['paper']['avgRNeto'])} ({b['lectura'].replace('_', ' ')})"
                     if b else "paper: sin informe del bot")
            f = raiz / "results" / "adelante" / f"{a['id']}.json"
            ad = json.loads(f.read_text())["historial"][-1] if f.exists() else None
            adel = (f"adelante n={ad['n']} {_r(ad.get('avgRNeto'))} ({ad['lectura'].replace('_', ' ')})"
                    if ad else "adelante: todavía sin correr")
            lineas.append(f"• {e(a['id'])} [{a.get('nivel', 'aprobada')}]: {paper}; {adel}")
            if ad and ad.get("sugerencia"):
                lineas.append(f"  👉 {e(ad['sugerencia'])}")

    if auditoria is not None:
        fallas = [ch for ch in auditoria if ch.estado == "falla"]
        avisos = [ch for ch in auditoria if ch.estado == "aviso"]
        lineas += ["", f"<b>Auditor:</b> {len(fallas)} violaciones, {len(avisos)} avisos"]
        lineas += [f"❌ {e(ch.nombre)}" for ch in fallas]
        lineas += [f"⚠️ {e(ch.nombre)}" for ch in avisos[:4]]

    rec = recomendadas(raiz)
    if rec:
        lineas += ["", "<b>Backlog: el PO recomienda</b>"] + [f"{i}. {e(x)}" for i, x in enumerate(rec, 1)]

    pendientes = [p for p in (prs or []) if not p.get("title", "").startswith("[rutina]")]
    lineas += ["", f"<b>Te esperan: {len(pendientes)} PR</b>"]
    lineas += [f"▸ #{p['number']} {e(p['title'][:80])}" for p in pendientes[:6]]
    if issues is not None:
        esperan = [i for i in issues if any((x if isinstance(x, str) else x.get("name")) == "estado:diseñada"
                                            for x in i.get("labels", []))]
        lineas.append(f"Issues abiertos: {len(issues)}" + (f" ({len(esperan)} esperan tu ✅)" if esperan else ""))
    if c.get("propuesta"):
        lineas.append(f"▸ {len(c['propuesta'])} ideas propuestas para revisar en 02-DOCS/ideas.md")
    lineas += ["", f"📊 {PAGINA}"]
    texto = "\n".join(lineas)
    return texto if len(texto) <= LIMITE else texto[: LIMITE - 20] + "\n… (recortado)"


def enviar(texto: str, token: str, chat: str) -> None:
    datos = json.dumps({"chat_id": chat, "text": texto, "parse_mode": "HTML",
                        "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=datos,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        if json.loads(r.read()).get("ok") is not True:
            raise RuntimeError("Telegram no aceptó el mensaje")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--informe-bot", type=Path, help="factory-paper.json de btc-signal-web")
    p.add_argument("--prs", type=Path, help="PRs abiertos (JSON de `gh pr list --json number,title`)")
    p.add_argument("--issues", type=Path, help="issues abiertos (JSON de `gh issue list --json number,title,labels`)")
    p.add_argument("--enviar", action="store_true")
    a = p.parse_args(argv)
    from bt.auditoria import auditar

    leer = lambda r: json.loads(r.read_text()) if r and r.exists() and r.stat().st_size else None  # noqa: E731
    texto = armar(informe_bot=leer(a.informe_bot), prs=leer(a.prs), issues=leer(a.issues), auditoria=auditar())
    print(texto)
    if a.enviar:
        token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
        if not token or not chat:
            print("::warning::faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID: no se envió", file=sys.stderr)
            return 0
        enviar(texto, token, chat)
        print("enviado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
