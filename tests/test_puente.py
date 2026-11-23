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


def _velas_sinteticas(semilla, n=400):
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(semilla)
    c = 100 * np.exp(np.cumsum(rng.normal(0.002, 0.03, n)))
    idx = pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC", name="time")
    df = pd.DataFrame({"open": np.r_[c[0], c[:-1]], "close": c}, index=idx)
    df["high"] = df[["open", "close"]].max(axis=1) * 1.01
    df["low"] = df[["open", "close"]].min(axis=1) * 0.99
    df["volume"] = 1.0
    return df


def _spec_sintetica(n_simbolos=8):
    from bt.spec import desde_dict

    return desde_dict({
        "id": "2026-11-02-trend4h-tope-7d", "estado": "pre-registrada", "hipotesis": "x",
        "horizonte": {"tipo": "diario"},
        "estrategia": {"modulo": "tendencia_donchian", "params": {"entrada": 10, "salida": 5}},
        "universo": {"mercado": "futures", "simbolos": [f"S{i}USDT" for i in range(n_simbolos)],
                     "intervalo": "1d", "funding": False},
        "config": {"fee_pct_por_lado": 0.001, "timeout_velas": 7},
        "ventana_desarrollo": {"desde": "2024-01-01"},
        "criterio_aprobacion": {"n_minimo": 10, "ic95_excluye_cero": False, "concluyente": False,
                                "supera_nulo_p95": False, "holdout": {"avgRNeto_positivo": True}},
    })


def _cargar_sintetico(simbolo, intervalo, mercado="futures"):
    return _velas_sinteticas(int(simbolo[1]))


def test_cupo_3_cambia_el_numero_del_backtest():
    spec = _spec_sintetica()
    kw = dict(cargar_velas=_cargar_sintetico, cargar_funding=lambda s: None)
    con = puente.backtest_con_cupo(spec, "2024-03-01", "2024-12-31", 3, **kw)
    sin = puente.backtest_con_cupo(spec, "2024-03-01", "2024-12-31", 99, **kw)
    assert con["maxPorDireccion"] == 3 and sin["maxPorDireccion"] == 99
    assert con["global"]["n"] < sin["global"]["n"]
    assert con["global"]["avgRNeto"] != sin["global"]["avgRNeto"]
    assert spec.max_por_direccion is None  # la spec original no se toca


def test_la_ventana_del_paper_recorta():
    kw = dict(cargar_velas=_cargar_sintetico, cargar_funding=lambda s: None)
    bt = puente.backtest_con_cupo(_spec_sintetica(), "2024-06-01", "2024-09-01", 3, **kw)
    assert "2024-06-01" <= bt["ventana"][0][:10] and bt["ventana"][1][:10] <= "2024-09-01"
    assert all("2024-06-01" <= c[0] and c[2] <= "2024-09-01" for c in bt["curva"])


def test_paridad_cupo_md_imprime_backtest_y_paper(tmp_path):
    import yaml

    inf = informe()
    inf["estrategias"][0]["paper"]["desde"] = "2024-03-01"
    spec = _spec_sintetica()
    d = {"id": spec.id, "estado": "pre-registrada", "hipotesis": "x", "horizonte": {"tipo": "diario"},
         "estrategia": {"modulo": "tendencia_donchian", "params": {"entrada": 10, "salida": 5}},
         "universo": {"mercado": "futures", "simbolos": [f"S{i}USDT" for i in range(8)], "intervalo": "1d"},
         "config": {"fee_pct_por_lado": 0.001, "timeout_velas": 7}, "ventana_desarrollo": {"desde": "2024-01-01"},
         "criterio_aprobacion": {"n_minimo": 10, "ic95_excluye_cero": False, "concluyente": False,
                                 "supera_nulo_p95": False, "holdout": {"avgRNeto_positivo": True}}}
    (tmp_path / f"{spec.id}.yaml").write_text(yaml.safe_dump(d), encoding="utf-8")
    inf["generado"] = "2024-12-31T12:00:00Z"
    md = puente.paridad_cupo_md(inf, 3, None, None, specs=tmp_path, cargar_velas=_cargar_sintetico,
                                cargar_funding=lambda s: None)
    assert "cupo 3 por dirección" in md and "backtest n=" in md and "paper n=40" in md
    inf["estrategias"][0]["paper"].pop("desde")
    with pytest.raises(puente.InformeInvalido):
        puente.paridad_cupo_md(inf, 3, None, None, specs=tmp_path)


def test_ventana_en_el_holdout_se_pide_explicita_y_no_se_recorta():
    kw = dict(cargar_velas=lambda s, i, m="futures": _velas_sinteticas(int(s[1]), 800), cargar_funding=lambda s: None)
    bt = puente.backtest_con_cupo(_spec_sintetica(), "2025-10-01", "2026-02-01", 3, **kw)
    assert bt["ventana"][0][:10] >= "2025-10-01" and bt["global"]["n"] > 0


def test_main_cupo_invalido_o_spec_inexistente_sale_con_2(tmp_path, capsys, monkeypatch):
    import json

    monkeypatch.setattr(puente, "bajar_faltantes", lambda s: [])  # sin red en los tests

    ruta = tmp_path / "inf.json"
    ruta.write_text(json.dumps(informe()), encoding="utf-8")
    assert puente.main([str(ruta), "--cupo", "0", "--desde", "2024-01-01"]) == 2
    assert puente.main([str(ruta), "--cupo", "3", "--desde", "2024-01-01"]) == 2  # no hay specs/<id>.yaml en tmp


def _spec_con_funding():
    import dataclasses
    return dataclasses.replace(_spec_sintetica(3), funding=True)


def test_bajar_faltantes_baja_solo_lo_que_falta(tmp_path):
    from bt import data

    spec = _spec_con_funding()
    velas, fund = tmp_path / "klines", tmp_path / "funding"
    llamadas = []

    def desc(s, i, desde, mercado, base):
        llamadas.append(("velas", s))
        data.ruta_local(s, i, mercado, base).parent.mkdir(parents=True, exist_ok=True)
        data.ruta_local(s, i, mercado, base).write_text("time\n")

    def desc_f(s, desde, base):
        llamadas.append(("funding", s))
        base.mkdir(parents=True, exist_ok=True)
        (base / f"{s}.csv").write_text("time,rate\n")

    kw = dict(descargar=desc, descargar_funding=desc_f, base_velas=velas, base_funding=fund)
    bajado = puente.bajar_faltantes(spec, **kw)
    assert len(bajado) == 2 * len(spec.simbolos)
    assert {c[1] for c in llamadas} == set(spec.simbolos)
    # segunda pasada: todo está, no se baja nada
    llamadas.clear()
    assert puente.bajar_faltantes(spec, **kw) == [] and llamadas == []
    # falta un solo archivo: sólo ese
    (fund / f"{spec.simbolos[0]}.csv").unlink()
    assert puente.bajar_faltantes(spec, **kw) == [f"funding {spec.simbolos[0]}"]


def test_cupo_en_clon_sin_klines_baja_y_termina_con_informe(tmp_path, monkeypatch):
    import json

    from bt import data

    monkeypatch.chdir(tmp_path)  # clon limpio: no hay data/klines
    spec = _spec_sintetica()
    bajados = []

    def falso(spec_):
        bajados.append(spec_.id)
        return [f"velas {s}" for s in spec_.simbolos]

    kw = dict(cargar_velas=_cargar_sintetico, cargar_funding=lambda s: None)
    assert not data.DIR_DATOS.exists()
    bt = puente.backtest_con_cupo(spec, "2024-03-01", "2024-12-31", 3, bajar_faltantes_fn=falso, **kw)
    assert bajados == [spec.id] and bt["global"]["n"] > 0
    # sin cargadores inyectados, el camino real pide la descarga de faltantes antes de cargar
    llamado = []
    monkeypatch.setattr(puente, "bajar_faltantes", lambda s: llamado.append(s.id) or [])
    with pytest.raises(FileNotFoundError):
        puente.backtest_con_cupo(spec, "2024-03-01", "2024-12-31", 3)
    assert llamado == [spec.id]
    json.dumps(bt["global"])


def test_main_cupo_con_descarga_fallida_sale_con_2(tmp_path, monkeypatch):
    import json

    def falla(s):
        raise RuntimeError("sin datos")

    monkeypatch.setattr(puente, "bajar_faltantes", falla)
    ruta = tmp_path / "inf.json"
    ruta.write_text(json.dumps(informe()), encoding="utf-8")
    assert puente.main([str(ruta), "--cupo", "3", "--desde", "2024-01-01"]) == 2
