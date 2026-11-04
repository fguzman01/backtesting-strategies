"""Dashboard estático para GitHub Pages: `python -m bt.sitio` → `_site/index.html`.

Lee `results/evaluaciones/*.json` y `results/approved.json`. Una sola página, sin dependencias:
fichas de resumen, la tabla de evaluaciones y, por evaluación, la curva de R acumulado
(desarrollo + holdout, con el corte marcado) y la tabla del criterio pre-registrado.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ESTADO = {
    "APROBADA": ("good", "✓", "Aprobada"),
    "OBSERVACION": ("warning", "◐", "En observación"),
    "RECHAZADA": ("critical", "✕", "Rechazada"),
    "NO_CONCLUYENTE": ("warning", "?", "No concluyente"),
}

CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f3f2ee;--text-primary:#0b0b0b;
--text-secondary:#52514e;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--series-1:#2a78d6;
--good:#0ca30c;--warning:#fab219;--critical:#d03b3b}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
--surface-1:#1a1a19;--surface-2:#232321;--text-primary:#f0efec;--text-secondary:#c3c2b7;--grid:#2c2c2a;
--axis:#383835;--border:rgba(255,255,255,.10);--series-1:#3987e5}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--surface-2:#232321;
--text-primary:#f0efec;--text-secondary:#c3c2b7;--grid:#2c2c2a;--axis:#383835;
--border:rgba(255,255,255,.10);--series-1:#3987e5}
body{margin:0}
.viz-root{background:var(--surface-1);color:var(--text-primary);min-height:100vh;
font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:24px;box-sizing:border-box}
.wrap{max-width:1100px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 8px}
.sub{color:var(--text-secondary);margin:0 0 20px}
.nav{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 4px;font-size:13px}
.nav a{color:var(--text-secondary)}
.doc ul{padding-left:18px}.doc p{max-width:75ch}.doc h3,.doc h4{font-size:14px;margin:16px 0 6px}
.ancho{overflow-x:auto}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:24px}
.tile{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.tile .v{font-size:28px;font-weight:650}.tile .l{color:var(--text-secondary);font-size:12px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--grid);vertical-align:top}
th{color:var(--text-secondary);font-weight:600;font-size:12px}
.num{text-align:right}
.badge{display:inline-flex;gap:6px;align-items:center;white-space:nowrap}
.dot{display:inline-flex;width:16px;height:16px;border-radius:50%;color:#fff;font-size:11px;
font-weight:700;align-items:center;justify-content:center}
.eval{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:16px;margin-top:16px}
.eval h3{margin:0 0 4px;font-size:15px}.meta{color:var(--text-secondary);font-size:12px;margin-bottom:8px}
.chart{position:relative}.chart svg{display:block;width:100%;height:auto}
.tip{position:absolute;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);
border-radius:6px;padding:6px 8px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,.15);display:none}
.tip strong{font-size:13px}.tip span{color:var(--text-secondary)}
a{color:var(--series-1)}
"""

JS = """
document.querySelectorAll('.chart').forEach(function(box){
  var d=JSON.parse(box.dataset.puntos), svg=box.querySelector('svg'), tip=box.querySelector('.tip'),
      hair=svg.querySelector('.hair'), dot=svg.querySelector('.hdot'), W=+svg.dataset.w, L=+svg.dataset.l,
      R=+svg.dataset.r;
  function mover(ev){
    var b=svg.getBoundingClientRect(), x=(ev.clientX-b.left)*W/b.width;
    var i=Math.round((x-L)/(W-L-R)*(d.length-1)); i=Math.max(0,Math.min(d.length-1,i));
    var p=d[i]; hair.setAttribute('x1',p[2]); hair.setAttribute('x2',p[2]); hair.style.display='';
    dot.setAttribute('cx',p[2]); dot.setAttribute('cy',p[3]); dot.style.display='';
    tip.textContent=''; var s=document.createElement('strong');
    s.textContent=(p[1]>=0?'+':'')+p[1].toFixed(2)+' R acumulado'; tip.appendChild(s);
    tip.appendChild(document.createElement('br'));
    var sp=document.createElement('span'); sp.textContent=p[0]+' · operación '+(i+1)+' · '+p[4]; tip.appendChild(sp);
    tip.style.display='block'; var px=p[2]*b.width/W; tip.style.left=Math.min(px+12,b.width-170)+'px';
    tip.style.top='8px';
  }
  svg.addEventListener('pointermove',mover);
  svg.addEventListener('pointerleave',function(){tip.style.display='none';hair.style.display='none';
    dot.style.display='none';});
});
"""


def _e(x) -> str:
    return html.escape(str(x), quote=True)


def _n_simbolos(e: dict) -> int:
    return len(e["spec"]["universo"].get("simbolos") or (e.get("universoDinamico") or {}).get("simbolos", []))


def _simbolos_txt(e: dict) -> str:
    din = e.get("universoDinamico")
    if din:
        return f"dinámico: top {din['top']} de cada mes, con retirados ({len(din['simbolos'])} símbolos)"
    return ", ".join(e["spec"]["universo"]["simbolos"])


def _badge(veredicto: str) -> str:
    rol, icono, texto = ESTADO.get(veredicto, ("warning", "?", veredicto))
    return (f'<span class="badge"><span class="dot" style="background:var(--{rol})" aria-hidden="true">'
            f"{icono}</span>{_e(texto)}</span>")


def _ic(g: dict | None) -> str:
    if not g or not g.get("ic95"):
        return "—"
    return f"{g['avgRNeto']:+.3f} [{g['ic95'][0]:+.2f}, {g['ic95'][1]:+.2f}]"


def _grafico(ev: dict) -> str:
    """Una serie: R acumulado por operación. El corte del holdout es una línea punteada rotulada."""
    curva = [(c[0], c[1], "desarrollo") for c in ev["desarrollo"]["curva"]]
    if ev.get("holdout"):
        curva += [(c[0], c[1], "holdout") for c in ev["holdout"]["curva"]]
    if len(curva) < 2:
        return '<p class="meta">Sin operaciones suficientes para graficar.</p>'
    acum, s = [], 0.0
    for _, r, _ in curva:
        s += r
        acum.append(s)
    W, H, L, R, T, B = 760, 260, 52, 16, 16, 28
    lo, hi = min(0.0, *acum), max(0.0, *acum)
    if hi - lo < 1e-9:
        hi = lo + 1
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad
    xs = [L + i * (W - L - R) / (len(acum) - 1) for i in range(len(acum))]
    ys = [T + (hi - v) * (H - T - B) / (hi - lo) for v in acum]
    y0 = T + hi * (H - T - B) / (hi - lo)
    paso = _paso_eje(hi - lo)
    ticks, v = [], (lo // paso + 1) * paso
    while v < hi:
        ticks.append(v)
        v += paso
    partes = [f'<svg viewBox="0 0 {W} {H}" data-w="{W}" data-l="{L}" data-r="{R}" role="img" '
              f'aria-label="R acumulado de {_e(ev["id"])}: termina en {acum[-1]:+.1f} R">']
    for tv in ticks:
        ty = T + (hi - tv) * (H - T - B) / (hi - lo)
        partes.append(f'<line x1="{L}" x2="{W - R}" y1="{ty:.1f}" y2="{ty:.1f}" stroke="var(--grid)"/>')
        partes.append(f'<text x="{L - 6}" y="{ty + 4:.1f}" text-anchor="end" font-size="11" '
                      f'fill="var(--text-secondary)">{"0" if abs(tv) < 1e-9 else f"{tv:+g}"}</text>')
    partes.append(f'<line x1="{L}" x2="{W - R}" y1="{y0:.1f}" y2="{y0:.1f}" stroke="var(--axis)"/>')
    corte = next((i for i, c in enumerate(curva) if c[2] == "holdout"), None)
    if corte is not None:
        cx = (xs[corte - 1] + xs[corte]) / 2 if corte > 0 else xs[0]
        partes.append(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{T}" y2="{H - B}" stroke="var(--text-secondary)" '
                      f'stroke-dasharray="3 3"/>')
        partes.append(f'<text x="{cx + 4:.1f}" y="{T + 10}" font-size="11" fill="var(--text-secondary)">'
                      f"holdout →</text>")
    partes.append(f'<text x="{L}" y="{H - 8}" font-size="11" fill="var(--text-secondary)">{_e(curva[0][0])}</text>')
    partes.append(f'<text x="{W - R}" y="{H - 8}" text-anchor="end" font-size="11" fill="var(--text-secondary)">'
                  f"{_e(curva[-1][0])}</text>")
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys, strict=True))
    partes.append(f'<polyline points="{pts}" fill="none" stroke="var(--series-1)" stroke-width="2" '
                  f'stroke-linejoin="round" stroke-linecap="round"/>')
    partes.append(f'<line class="hair" y1="{T}" y2="{H - B}" stroke="var(--text-secondary)" style="display:none"/>')
    partes.append('<circle class="hdot" r="4.5" fill="var(--series-1)" stroke="var(--surface-2)" stroke-width="2" '
                  'style="display:none"/>')
    partes.append(f'<rect x="{L}" y="{T}" width="{W - L - R}" height="{H - T - B}" fill="transparent"/>')
    partes.append("</svg>")
    puntos = [[c[0], round(a, 3), round(x, 1), round(y, 1), c[2]]
              for c, a, x, y in zip(curva, acum, xs, ys, strict=True)]
    return (f'<div class="chart" data-puntos="{_e(json.dumps(puntos))}">{"".join(partes)}'
            f'<div class="tip" role="status"></div></div>')


def _paso_eje(rango: float) -> float:
    crudo = rango / 5
    mag = 10 ** int(f"{crudo:e}".split("e")[1])
    for m in (1, 2, 5, 10):
        if crudo <= m * mag:
            return m * mag
    return 10 * mag


AUDITORIA = {"ok": ("good", "✓", "Cumple"), "aviso": ("warning", "!", "Advertencia"),
             "falla": ("critical", "✕", "Violación")}


def _seccion_auditoria(ruta: Path) -> str:
    if not ruta.exists():
        return ""
    chequeos = json.loads(ruta.read_text(encoding="utf-8"))
    filas = []
    for c in chequeos:
        rol, icono, texto = AUDITORIA.get(c["estado"], AUDITORIA["aviso"])
        estado = (f'<span class="badge"><span class="dot" style="background:var(--{rol})" aria-hidden="true">'
                  f"{icono}</span>{texto}</span>")
        detalle = "<br>".join(_e(d) for d in c["detalle"]) or "—"
        filas.append(f"<tr><td>{estado}</td><td>{_e(c['nombre'])}</td><td>{_e(c['regla'])}</td>"
                     f'<td class="meta">{detalle}</td></tr>')
    return ("<h2>Auditoría del proceso</h2><p class=\"sub\">Chequeos automáticos de la metodología "
            "(<code>bt.auditoria</code>). El auditor con criterio propone mejoras en "
            "<code>02-DOCS/auditorias/</code>.</p><table><thead><tr><th>Estado</th><th>Chequeo</th>"
            f"<th>Regla</th><th>Detalle</th></tr></thead><tbody>{''.join(filas)}</tbody></table>")


def _inline(t: str) -> str:
    """Escapa y convierte lo poco de markdown que usan las docs: **negrita** y `código`."""
    import re

    t = _e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", t)


def md_a_html(texto: str) -> str:
    """Markdown mínimo → HTML: títulos, tablas, listas y párrafos. Todo el texto se escapa."""
    out, tabla, lista, parrafo = [], [], [], []

    def cerrar():
        if tabla:
            filas = [f for f in tabla if not set(f.replace("|", "").strip()) <= set("-: ")]
            celdas = [[c.strip() for c in f.strip().strip("|").split("|")] for f in filas]
            cab = "".join(f"<th>{_inline(c)}</th>" for c in celdas[0])
            cuerpo = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in celdas[1:])
            out.append(f'<div class="ancho"><table><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table></div>')
            tabla.clear()
        if lista:
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in lista) + "</ul>")
            lista.clear()
        if parrafo:
            out.append(f"<p>{_inline(' '.join(parrafo))}</p>")
            parrafo.clear()

    import re

    for linea in texto.splitlines():
        s = linea.strip()
        if s.startswith("|"):
            if lista or parrafo:
                cerrar()
            tabla.append(s)
        elif re.match(r"^(-|\d+\.)\s+", s):
            if tabla or parrafo:
                cerrar()
            lista.append(re.sub(r"^(-|\d+\.)\s+", "", s))
        elif s.startswith("#"):
            cerrar()
            nivel = min(4, len(s) - len(s.lstrip("#")) + 1)
            out.append(f"<h{nivel}>{_inline(s.lstrip('#').strip())}</h{nivel}>")
        elif not s:
            cerrar()
        else:
            if tabla or lista:
                cerrar()
            parrafo.append(s)
    cerrar()
    return "".join(out)


def _leer(ruta: Path) -> str | None:
    return ruta.read_text(encoding="utf-8") if ruta.exists() else None


def _sin_titulo(md: str) -> str:
    return "\n".join(x for x in md.splitlines() if not x.startswith("# "))


def _seccion(ancla: str, titulo: str, sub: str, md: str | None) -> str:
    if not md:
        return ""
    return f'<h2 id="{ancla}">{_e(titulo)}</h2><p class="sub">{sub}</p><div class="doc">{md_a_html(md)}</div>'


def secciones_extra(base: Path) -> tuple[str, list[tuple[str, str]]]:
    """Lo aprobado (hacia adelante y cartera), lo que vuelve del bot, la cola y el backlog."""
    docs = base.parent / "02-DOCS"
    partes, nav = [], []

    def agregar(ancla, titulo, sub, md):
        html_ = _seccion(ancla, titulo, sub, md)
        if html_:
            partes.append(html_)
            nav.append((ancla, titulo))

    adel = _leer(base / "reports" / "adelante.md")
    cart = _leer(base / "reports" / "cartera.md")
    agregar("adelante", "Prueba hacia adelante", "Lo aprobado con datos posteriores a su evaluación "
            "(<code>bt.adelante</code>, mensual).", _sin_titulo(adel).split("\n", 2)[-1] if adel else None)
    agregar("cartera", "Cartera de lo aprobado", "Las aprobadas juntas (<code>bt.cartera</code>).",
            _sin_titulo(cart) if cart else None)
    retro = _leer(docs / "retroalimentacion.md")
    if retro and "\n## Informe del " in retro:
        ultimo = "## Informe del " + retro.split("\n## Informe del ", 1)[1].split("\n## ", 1)[0]
        agregar("bot", "Lo que vuelve del bot", "El paper de btc-signal-web contra lo que predijo la factory "
                "(agente puente, semanal).", ultimo)
    ideas = _leer(docs / "ideas.md")
    if ideas:
        filas = [x for x in ideas.splitlines() if x.startswith("| ") and not x.startswith("| #")]
        vivas = []
        for x in filas:
            c = [y.strip() for y in x.strip().strip("|").split("|")]
            if len(c) >= 6 and c[-1].lstrip("*").lower().startswith(("en cola", "propuesta")):
                estado = c[-1] if len(c[-1]) < 140 else c[-1][:137].replace("`", "") + "..."
                vivas.append(f"| {c[0]} | {c[1]} | {estado} |")
        md = "| # | Idea | Estado |\n|---|---|---|\n" + "\n".join(vivas) if vivas else (
            "La cola está vacía: la rutina diaria va a proponer en vez de evaluar.")
        agregar("cola", "Cola de ideas", "Las que esperan: <code>en cola</code> se pre-registran solas; las "
                "<code>propuesta</code> esperan el visto bueno de Felipe.", md)
    back = _leer(docs / "backlog.md")
    if back:
        rec = back.split("## Recomendadas para esta semana", 1)[-1].split("\n## ", 1)[0]
        pend = back.split("## Pendientes", 1)[-1].split("\n## ", 1)[0] if "## Pendientes" in back else ""
        agregar("backlog", "Backlog del sistema", "Mejoras de la factory misma, priorizadas por el PO "
                "(semanal); Felipe decide.", "### Recomendadas\n" + rec + "\n### Pendientes\n" + pend)
    return "".join(partes), nav


def generar(base: Path = Path("results")) -> str:
    evs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((base / "evaluaciones").glob("*.json"))]
    evs.sort(key=lambda e: e["fecha"], reverse=True)
    for e in evs:  # una aprobada reclasificada a observación se muestra como tal
        if e.get("nivel") == "observacion":
            e["veredicto"] = "OBSERVACION"
    cuenta = {k: sum(1 for e in evs if e["veredicto"] == k) for k in ESTADO}
    filas = []
    for e in evs:
        s, dev, ho = e["spec"], e["desarrollo"], e.get("holdout")
        nulo = dev["nulo"]["p95"]
        filas.append(
            f'<tr><td><a href="#{_e(e["id"])}">{_e(e["id"])}</a></td><td>{_e(s["estrategia"]["modulo"])}</td>'
            f'<td>{_e(s["universo"]["intervalo"])}</td><td class="num">{_n_simbolos(e)}</td>'
            f'<td>{_badge(e["veredicto"])}</td><td class="num">{dev["global"]["n"]}</td>'
            f'<td class="num">{_ic(dev["global"])}</td>'
            f'<td class="num">{"—" if nulo is None else f"{nulo:+.3f}"}</td>'
            f'<td class="num">{_ic(ho["global"]) if ho else "no se miró"}</td></tr>'
        )
    detalles = []
    for e in evs:
        s = e["spec"]
        crit = "".join(f'<tr><td>{_e(c["criterio"])}</td><td>{_e(c["valor"])}</td>'
                       f'<td>{"✅ cumple" if c["ok"] else "❌ no cumple"}</td></tr>' for c in e["criterios"])
        detalles.append(
            f'<section class="eval" id="{_e(e["id"])}"><h3>{_e(e["id"])} · {_badge(e["veredicto"])}</h3>'
            f'<div class="meta">{_e(s["estrategia"]["modulo"])} {_e(json.dumps(s["estrategia"].get("params") or {}))}'
            f' · {_e(s["universo"].get("mercado", "futures"))} {_e(s["universo"]["intervalo"])} · '
            f'{_e(_simbolos_txt(e))} · evaluada {_e(e["fecha"][:10])} · commit {_e(e["commit"])}'
            f'</div><p>{_e(str(s.get("hipotesis", "")).strip())}</p>'
            f'<div class="meta">R acumulado por operación, neto de comisión y funding</div>{_grafico(e)}'
            f'<table><thead><tr><th>Criterio pre-registrado</th><th>Valor</th><th></th></tr></thead>'
            f"<tbody>{crit}</tbody></table></section>"
        )
    auditoria = _seccion_auditoria(base / "auditoria.json")
    extra, nav = secciones_extra(base)
    nav_html = ('<nav class="nav"><a href="#evaluaciones">Evaluaciones</a>'
                + "".join(f'<a href="#{a}">{_e(t)}</a>' for a, t in nav) + "</nav>")
    tiles = [("Evaluadas", len(evs)), ("Aprobadas", cuenta["APROBADA"]), ("En observación", cuenta["OBSERVACION"]),
             ("Rechazadas", cuenta["RECHAZADA"]),
             ("No concluyentes", cuenta["NO_CONCLUYENTE"])]
    cuerpo_tabla = "".join(filas) or '<tr><td colspan="9">Todavía no hay evaluaciones.</td></tr>'
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>backtesting-strategies</title><style>{CSS}</style></head>
<body><div class="viz-root"><div class="wrap">
<h1>Factory de backtesting</h1>
<p class="sub">Cada estrategia se evalúa contra un criterio escrito antes de correr. El holdout (desde 2025-09-09)
se mira una vez y sólo si pasa desarrollo. Resultados en R, netos de comisión y funding.</p>
<div class="tiles">{"".join(f'<div class="tile"><div class="v">{v}</div><div class="l">{_e(k)}</div></div>'
                            for k, v in tiles)}</div>
{nav_html}
<h2 id="evaluaciones">Evaluaciones</h2>
<table><thead><tr><th>Spec</th><th>Estrategia</th><th>TF</th><th class="num">Símbolos</th><th>Veredicto</th>
<th class="num">n dev</th><th class="num">avgR dev [±2 EE]</th><th class="num">Nulo p95</th>
<th class="num">avgR holdout</th></tr></thead><tbody>{cuerpo_tabla}</tbody></table>
{extra}
{auditoria}
{"".join(detalles)}
</div></div><script>{JS}</script></body></html>
"""


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salida", type=Path, default=Path("_site"))
    a = p.parse_args(argv)
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "index.html").write_text(generar(), encoding="utf-8")
    print(a.salida / "index.html")


if __name__ == "__main__":
    main()
