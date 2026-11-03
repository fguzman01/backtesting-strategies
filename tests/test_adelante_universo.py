import json

import numpy as np
import pandas as pd
import yaml

from bt import adelante, universo
from bt import evaluar as ev_mod
from bt.spec import SpecInvalida, desde_dict


def test_tabla_del_universo_sin_lookahead_y_con_historia_minima():
    vol = {
        "AAAUSDT": {"2019-09": 5, "2019-10": 5, "2019-11": 5, "2019-12": 5, "2020-01": 1},
        "BBBUSDT": {"2019-09": 1, "2019-10": 1, "2019-11": 1, "2019-12": 9, "2020-01": 9},
        "NUEVOUSDT": {"2019-11": 100, "2019-12": 100, "2020-01": 100},  # menos de 3 meses de historia en dic
    }
    t = universo.armar_tabla(vol, "2020-02", top=1)
    assert t["2019-12"] == ["AAAUSDT"]      # manda el volumen de NOVIEMBRE, no el de diciembre
    assert t["2020-01"] == ["BBBUSDT"]      # diciembre: BBB 9 > AAA 5; NUEVO todavía sin historia
    assert t["2020-02"] == ["NUEVOUSDT"]    # ya tiene nov, dic, ene
    assert universo.miembros(1, t, "2020-01") == {"BBBUSDT": {"2020-01"}, "NUEVOUSDT": {"2020-02"}}


def test_candidatos():
    assert universo.es_candidato("LUNAUSDT") and not universo.es_candidato("USDCUSDT")
    assert not universo.es_candidato("BTCUSDT_230331") and not universo.es_candidato("BTCBUSD")


def _spec(**cambios):
    d = {"id": "2026-11-03-din", "estado": "pre-registrada", "hipotesis": "x", "horizonte": {"tipo": "diario"},
         "estrategia": {"modulo": "tendencia_donchian", "params": {"entrada": 20, "salida": 10}},
         "universo": {"mercado": "futures", "dinamico": {"top": 1}, "intervalo": "1d", "funding": False},
         "config": {"fee_pct_por_lado": 0.001, "timeout_velas": 7}, "ventana_desarrollo": {"desde": "2020-01-01"},
         "criterio_aprobacion": {"n_minimo": 5, "ic95_excluye_cero": False, "concluyente": False,
                                 "supera_nulo_p95": False,
                                 "holdout": {"avgRNeto_positivo": True, "sin_mejores_no_negativo": False,
                                             "aguanta_costos": False, "fraccion_desarrollo_minima": 0}}}
    d.update(cambios)
    return d


def test_spec_dinamica_se_valida():
    s = desde_dict(_spec())
    assert s.dinamico_top == 1 and s.simbolos == []
    malo = _spec()
    malo["universo"] = {"mercado": "futures", "dinamico": {"top": 99}, "intervalo": "1d"}
    try:
        desde_dict(malo)
        raise AssertionError("tenía que fallar")
    except SpecInvalida:
        pass


def _mercado(semilla, fin="2026-10-30"):
    rng = np.random.default_rng(semilla)
    idx = pd.date_range("2019-06-01", fin, freq="1D", tz="UTC", name="time")
    close = 100 * np.exp(np.cumsum(rng.normal(0.002, 0.03, len(idx))))
    open_ = np.concatenate([[100.0], close[:-1]])
    r = np.abs(rng.normal(0, 0.015, len(idx))) * close
    return pd.DataFrame({"open": open_, "high": np.maximum(open_, close) + r, "low": np.minimum(open_, close) - r,
                         "close": close, "volume": 1.0}, index=idx)


def test_universo_dinamico_solo_cuenta_los_meses_de_miembro_y_tolera_retirados(tmp_path):
    datos = {"AAAUSDT": _mercado(1), "MUERTOUSDT": _mercado(2, fin="2022-05-10")}
    meses = [f"{y}-{m:02d}" for y in range(2020, 2027) for m in range(1, 13) if f"{y}-{m:02d}" <= "2026-11"]
    tabla = {m: (["MUERTOUSDT"] if m <= "2022-05" else ["AAAUSDT"]) for m in meses}
    spec = ev_mod.resolver_universo(desde_dict(_spec()), tabla)
    assert spec.simbolos == ["AAAUSDT", "MUERTOUSDT"]
    t = ev_mod._tramo(spec, lambda s, i, m: datos[s], lambda s: None, holdout=True)
    assert "MUERTOUSDT" not in t["porSimbolo"]                # en el holdout ya no existía
    assert any("MUERTOUSDT" in x for x in t["simbolosSinDatos"])
    d = ev_mod._tramo(spec, lambda s, i, m: datos[s], lambda s: None, holdout=False)
    assert d["porSimbolo"]["MUERTOUSDT"]["n"] > 0 and d["porSimbolo"]["AAAUSDT"]["n"] > 0


def test_prueba_hacia_adelante(tmp_path):
    from bt.evaluar import _tramo
    base, specs = tmp_path / "results", tmp_path / "specs"
    (base / "evaluaciones").mkdir(parents=True)
    specs.mkdir()
    d = _spec(id="2026-11-03-fija")
    d["universo"] = {"mercado": "futures", "simbolos": ["AAAUSDT"], "intervalo": "1d", "funding": False}
    (specs / "2026-11-03-fija.yaml").write_text(yaml.safe_dump(d))
    df = _mercado(3)
    cv = lambda s, i, m: df  # noqa: E731
    spec = desde_dict(d)
    ho = _tramo(spec, cv, lambda s: None, holdout=True)
    ho["ventana"][1] = "2026-03-01T00:00:00+00:00"  # como si se hubiera evaluado en marzo
    ev = {"id": "2026-11-03-fija", "desarrollo": {"global": {"avgRNeto": 0.2}}, "holdout": ho}
    (base / "evaluaciones" / "2026-11-03-fija.json").write_text(json.dumps(ev, default=str))
    foto = adelante.correr({"id": "2026-11-03-fija", "nivel": "observacion"}, base, specs, cv, lambda s: None)
    assert foto["desde"].startswith("2026-03-02") and foto["ventana"][0] >= "2026-03-02"
    assert foto["lectura"] in {"muestra_chica", "positiva", "incierta", "negativa", "positiva_peor_que_desarrollo",
                               "incierta_peor_que_desarrollo"}
    adelante.guardar("2026-11-03-fija", "observacion", foto, base)
    adelante.guardar("2026-11-03-fija", "observacion", dict(foto, filas=[]), base)  # misma fecha: reemplaza
    h = json.loads((base / "adelante" / "2026-11-03-fija.json").read_text())["historial"]
    assert len(h) == 1 and "filas" not in h[0]
    assert "2026-11-03-fija" in adelante.resumen_md(base)


def test_lectura():
    assert adelante.lectura(10, 0.5, [0.1, 0.9], 0.2, "observacion")[0] == "muestra_chica"
    assert adelante.lectura(50, 0.3, [0.1, 0.5], 0.2, "observacion") == ("positiva", "candidata a subir a aprobada")
    assert adelante.lectura(50, -0.3, [-0.5, -0.1], 0.2, "aprobada")[1].startswith("candidata a bajar")
    assert adelante.lectura(50, 0.0, [-0.1, 0.1], 0.3, "aprobada")[0] == "incierta_peor_que_desarrollo"
