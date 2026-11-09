import datetime as dt
import json

from bt import resumen
from bt.auditoria import AVISO, FALLA, Chequeo


def test_resumen_semanal(tmp_path):
    (tmp_path / "results" / "evaluaciones").mkdir(parents=True)
    (tmp_path / "02-DOCS").mkdir()
    ev = {"id": "2026-11-03-x", "fecha": "2026-11-03T06:00:00+00:00", "veredicto": "APROBADA", "nivel": "observacion",
          "desarrollo": {"global": {"n": 100, "avgRNeto": 0.2, "ic95": [0.1, 0.3]}},
          "holdout": {"global": {"n": 20, "avgRNeto": 0.05}}}
    vieja = dict(ev, id="2026-10-01-vieja", fecha="2026-10-01T00:00:00+00:00")
    for e in (ev, vieja):
        (tmp_path / "results" / "evaluaciones" / f"{e['id']}.json").write_text(json.dumps(e))
    (tmp_path / "results" / "approved.json").write_text(json.dumps({"estrategias": [{"id": "2026-11-03-x",
                                                                                     "nivel": "observacion"}]}))
    (tmp_path / "02-DOCS" / "ideas.md").write_text(
        "| # | Idea | a | b | c | Estado |\n|---|---|---|---|---|---|\n"
        "| 3 | Tendencia **real** | x | y | z | en cola (Felipe) |\n| 4 | Otra | x | y | z | propuesta |\n")
    bot = {"estrategias": [{"id": "2026-11-03-x", "paper": {"n": 4, "avgRNeto": 0.1}, "lectura": "muestra_chica"}]}
    texto = resumen.armar(tmp_path, dt.date(2026, 11, 9), bot,
                          [{"number": 30, "title": "Algo para Felipe"}, {"number": 31, "title": "[rutina] x"}],
                          [Chequeo("Holdout", "r", FALLA), Chequeo("Ventana", "r", AVISO)])
    assert "Evaluadas: 1" in texto and "2026-10-01-vieja" not in texto and "◐ 2026-11-03-x: observacion" in texto
    assert "#3 Tendencia real" in texto and "1 propuestas" in texto
    assert "paper n=4 +0.100 (muestra chica)" in texto and "todavía sin correr" in texto
    assert "1 violaciones" in texto and "#30" in texto and "#31" not in texto
    assert len(texto) <= resumen.LIMITE


def test_recomendadas_del_po(tmp_path):
    (tmp_path / "02-DOCS").mkdir()
    (tmp_path / "02-DOCS" / "backlog.md").write_text(
        "# B\n\n## Recomendadas para esta semana\n\nTexto.\n\n1. **B-01** Cartera\n2. **B-02** Pruebas\n"
        "3. **B-03** Sesgos\n4. **B-04** Sobra\n\n## Pendientes\n\n1. no cuenta\n")
    assert resumen.recomendadas(tmp_path) == ["B-01 Cartera", "B-02 Pruebas", "B-03 Sesgos"]
    assert "el PO recomienda" in resumen.armar(tmp_path)


def test_cola_vacia_avisa(tmp_path):
    (tmp_path / "02-DOCS").mkdir()
    (tmp_path / "02-DOCS" / "ideas.md").write_text("| 1 | x | a | b | c | descartada |\n")
    assert "La cola está vacía" in resumen.armar(tmp_path, dt.date(2026, 11, 9))


def test_auditor_exige_revision_de_specs_nuevas(tmp_path):
    from bt.auditoria import AVISO, OK, chequear_revisiones
    (tmp_path / "specs" / "revisiones").mkdir(parents=True)
    (tmp_path / "specs" / "2026-11-01-vieja.yaml").write_text("x")
    assert chequear_revisiones(tmp_path, {}).estado == OK                 # anterior a la regla
    (tmp_path / "specs" / "2026-11-06-nueva.yaml").write_text("x")
    assert chequear_revisiones(tmp_path, {}).estado == AVISO
    (tmp_path / "specs" / "revisiones" / "2026-11-06-nueva.md").write_text("veredicto: bloquea\nx")
    assert chequear_revisiones(tmp_path, {}).estado == OK
    assert chequear_revisiones(tmp_path, {"2026-11-06-nueva": {}}).estado == AVISO


def test_resumen_cuenta_issues_abiertos(tmp_path):
    (tmp_path / "02-DOCS").mkdir()
    issues = [{"number": 1, "title": "a", "labels": [{"name": "estado:diseñada"}]},
              {"number": 2, "title": "b", "labels": [{"name": "estado:en-curso"}]}]
    hoy = dt.date(2026, 11, 9)
    assert "Issues abiertos: 2 (1 esperan tu ✅)" in resumen.armar(tmp_path, hoy, issues=issues)
    assert "Issues abiertos: 0" in resumen.armar(tmp_path, hoy, issues=[])
    assert "Issues abiertos" not in resumen.armar(tmp_path, hoy)
