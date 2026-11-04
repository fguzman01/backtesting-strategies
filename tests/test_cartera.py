import json

from bt import cartera


def ev(sid, ops, holdout=None):
    return {"id": sid, "desarrollo": {"curva": ops}, "holdout": {"curva": holdout} if holdout else None}


def test_cartera_ventana_comun_caida_y_correlacion():
    a = ev("2026-01-01-a", [["2020-01-05", 1.0, "2020-01-10"], ["2020-02-05", -2.0, "2020-02-10"],
                            ["2020-03-05", 1.0, "2020-03-10"], ["2020-04-05", 1.0, "2020-04-10"]])
    b = ev("2026-01-01-b", [["2020-02-01", 1.0, "2020-02-20"], ["2020-03-01", -1.0, "2020-03-20"],
                            ["2020-04-01", 1.0, "2020-04-20"], ["2020-05-01", 5.0, "2020-05-20"]])
    sim = cartera.simular({"2026-01-01-a": a, "2026-01-01-b": b})
    assert sim["ventana"] == ["2020-02", "2020-04"] and sim["meses"] == 3   # sólo donde están las dos
    assert sim["estrategias"]["2026-01-01-a"]["n"] == 3 and sim["cartera"]["n"] == 6
    assert sim["cartera"]["sumaR"] == 1.0 and sim["fechasDeCierreExactas"]
    assert sim["correlacionMensual"]["2026-01-01-a"]["2026-01-01-b"] < 0      # se compensan
    md = cartera.reporte_md(sim)
    assert "Cartera" in md and "Correlación mensual" in md


def test_peor_caida_por_cierre_y_curva_vieja():
    assert cartera.peor_caida([("2020-01-01", 2.0, "2020-01-09"), ("2020-01-02", -3.0, "2020-01-03")]) == -3.0
    ops, exacto = cartera.operaciones(ev("x", [["2020-01-01", 1.0]]))  # evaluación vieja: sin cierre
    assert ops == [("2020-01-01", 1.0, "2020-01-01")] and not exacto


def test_marginal_y_una_sola():
    a = ev("a", [["2020-01-01", 1.0, "2020-01-02"], ["2020-02-01", -1.0, "2020-02-02"],
                 ["2020-03-01", 1, "2020-03-02"]])
    b = dict(ev("b", [["2020-01-01", -1.0, "2020-01-02"], ["2020-02-01", 1.0, "2020-02-02"],
                      ["2020-03-01", -1, "2020-03-02"]]), id="b")
    m = cartera.marginal(b, {"a": a})
    assert m["correlacionMensual"]["a"] < 0 and m["peorCaidaDespues"] >= m["peorCaidaAntes"]
    assert cartera.marginal(b, {}) is None
    assert "una sola estrategia" in cartera.reporte_md(cartera.simular({"a": a}))


def test_ficha_de_una_aprobada_trae_la_cartera(tmp_path):
    (tmp_path / "evaluaciones").mkdir()
    previa = ev("2026-01-01-a", [["2020-01-05", 1.0, "2020-01-10"], ["2020-02-05", -2.0, "2020-02-10"],
                                 ["2020-03-05", 1.0, "2020-03-10"]])
    (tmp_path / "evaluaciones" / "2026-01-01-a.json").write_text(json.dumps(previa))
    (tmp_path / "approved.json").write_text(json.dumps({"estrategias": [{"id": "2026-01-01-a"}]}))
    from bt.evaluar import _marginal
    nueva = ev("2026-01-02-b", [["2020-01-05", -1.0, "2020-01-10"], ["2020-02-05", 2.0, "2020-02-10"],
                                ["2020-03-05", -1.0, "2020-03-10"]])
    m = _marginal(nueva, tmp_path)
    assert m["peorCaidaDespues"] > m["peorCaidaAntes"]  # se compensan: la cartera cae menos
