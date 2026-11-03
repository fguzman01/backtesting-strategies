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


def test_cola_vacia_avisa(tmp_path):
    (tmp_path / "02-DOCS").mkdir()
    (tmp_path / "02-DOCS" / "ideas.md").write_text("| 1 | x | a | b | c | descartada |\n")
    assert "La cola está vacía" in resumen.armar(tmp_path, dt.date(2026, 11, 9))
