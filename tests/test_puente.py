import pytest

from bt import auditoria, puente


def informe(fecha="2026-11-09", lectura="coherente", paper_avg=0.1):
    return {"generado": f"{fecha}T12:00:00Z", "ambiente": "PROD", "commit": "abc1234", "estrategias": [{
        "id": "2026-11-02-trend4h-tope-7d", "implementadaComo": "TREND_4H_T7", "nivel": "observacion",
        "abiertas": 2, "sinR": 0, "lectura": lectura,
        "paper": {"n": 40, "avgRNeto": paper_avg, "ic95": [paper_avg - 0.2, paper_avg + 0.2], "sumaR": 4,
                  "porMotivo": {}},
        "backtest": {"desarrollo": {"n": 4631, "avgRNeto": 0.245, "ic95": [0.18, 0.31]},
                     "holdout": {"n": 916, "avgRNeto": 0.036, "ic95": [-0.09, 0.17]}},
        "madre": {"estrategia": "TREND_4H", "paper": {"n": 38, "avgRNeto": 0.05, "ic95": None},
                  "diferencia": 0.05, "ic95": [-0.2, 0.3]},
    }]}


def test_resumen_y_validacion():
    md = puente.resumen_md(informe())
    assert "TREND_4H_T7" in md and "coherente" in md and "TREND_4H: n=38" in md and "Alertas" not in md
    with pytest.raises(puente.InformeInvalido):
        puente.resumen_md({"estrategias": []})


def test_anotar_es_idempotente_y_lo_nuevo_va_arriba(tmp_path):
    doc = tmp_path / "retro.md"
    assert puente.anotar(informe("2026-11-09"), doc)
    assert not puente.anotar(informe("2026-11-09"), doc)
    assert puente.anotar(informe("2026-11-16", lectura="peor_que_backtest", paper_avg=-0.5), doc)
    texto = doc.read_text()
    assert texto.startswith("# Retroalimentación del bot")
    assert texto.index("2026-11-16") < texto.index("2026-11-09")
    assert puente.alertas_vigentes(doc) == ["2026-11-02-trend4h-tope-7d"]


def test_el_auditor_avisa_si_el_paper_va_peor(tmp_path):
    (tmp_path / "02-DOCS").mkdir()
    doc = tmp_path / "02-DOCS" / "retroalimentacion.md"
    assert auditoria.chequear_paper(tmp_path).estado == auditoria.OK
    puente.anotar(informe(lectura="peor_que_backtest", paper_avg=-0.5), doc)
    assert auditoria.chequear_paper(tmp_path).estado == auditoria.AVISO
