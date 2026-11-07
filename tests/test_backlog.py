from bt import backlog
from bt.resumen import recomendadas


def i(n, titulo, estado=None, prio=None, abierto=True, cerrado=None, tipo="mejora"):
    labels = [f"tipo:{tipo}"] + ([f"estado:{estado}"] if estado else []) + ([f"prio:{prio}"] if prio else [])
    return {"number": n, "title": titulo, "labels": [{"name": x} for x in labels],
            "state": "OPEN" if abierto else "CLOSED", "closedAt": cerrado, "url": f"u/{n}"}


def test_backlog_generado(tmp_path):
    issues = [i(1, "Propuesta P3", "propuesta", "P3"), i(2, "Aprobada", "aprobada", "P2"),
              i(3, "Propuesta P1", "propuesta", "P1"), i(4, "En revisión", "en-revision", "P1"),
              i(5, "Vieja", "hecha", abierto=False, cerrado="2026-11-01T00:00:00Z"),
              i(6, "No", "descartada", abierto=False, cerrado="2026-11-02T00:00:00Z")]
    md = backlog.generar(issues)
    rec = md.split("## Recomendadas para esta semana")[1].split("## ")[0]
    assert rec.index("#4") < rec.index("#2") < rec.index("#3") and "#1" not in rec
    espera = md.split("## Espera tu decisión")[1].split("## ")[0]
    assert "fusionar o rechazar" in espera and "#2" not in espera
    fila = next(x for x in espera.splitlines() if "#4" in x)
    assert fila.endswith("fusionar o rechazar el PR |") and fila.count("|") == 8  # 7 columnas, dentro de la tabla
    assert "## Pendientes" not in md and md.count("[#1]") == 1                    # cada tarea aparece una vez
    assert "Vieja" in md.split("## Hechas")[1] and "No" in md.split("## Descartadas")[1]
    (tmp_path / "02-DOCS").mkdir()
    (tmp_path / "02-DOCS" / "backlog.md").write_text(md)
    assert recomendadas(tmp_path)[0].startswith("#4 ")


def test_etiquetas_del_operador():
    import importlib.util
    spec = importlib.util.spec_from_file_location("etq", "scripts/etiquetas.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    nombres = [n for n, _, _ in m.etiquetas()]
    assert "estado:propuesta" in nombres and "riesgo:alto" in nombres and len(nombres) == len(set(nombres))
