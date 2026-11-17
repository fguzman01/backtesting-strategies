import numpy as np
import pandas as pd

from bt import run
from bt.checks import chequear_lookahead_corte
from bt.engine import Config
from bt.strategies import _corte_ejemplo, cargar, cargar_corte, es_corte

IDX = pd.date_range("2024-01-01", periods=60, freq="1D", tz="UTC", name="time")


def _df(cierres, idx=IDX):
    c = np.asarray(cierres, dtype=float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) * 1.001, "low": np.minimum(o, c) * 0.999, "close": c, "volume": 1.0},
        index=idx,
    )


def _universo():
    n = len(IDX)
    t = np.arange(n)
    return {
        "AAA": _df(100 * 1.02**t),  # sube más rápido
        "BBB": _df(100 * 1.005**t),
        "CCC": _df(100 * 0.999**t),
        "DDD": _df(100 * 0.98**t),  # baja más rápido
    }


def test_ranking_conocido_da_las_entradas_esperadas():
    sen = _corte_ejemplo.senales_corte(run.alinear(_universo()))
    # Desde la vela 2 hay retorno de 2 días: largo el mejor (AAA), corto el peor (DDD).
    assert (sen["AAA"]["direccion"].iloc[2:] == 1).all()
    assert (sen["DDD"]["direccion"].iloc[2:] == -1).all()
    assert (sen["BBB"]["direccion"] == 0).all() and (sen["CCC"]["direccion"] == 0).all()
    assert (sen["AAA"]["direccion"].iloc[:2] == 0).all()


def test_el_flujo_completo_simula_por_simbolo_y_entra_en_t_mas_1():
    r = run.correr_corte("_corte_ejemplo", _universo(), intervalo="1d", cfg=Config(), params={"dias": 2})
    assert set(r) == {"AAA", "BBB", "CCC", "DDD"}
    assert r["BBB"].trades["conservador"] == []
    t = r["AAA"].trades["conservador"][0]
    assert t.direccion == 1
    # señal en la vela 2 (cierre del 03-01), entrada en la apertura de la vela 3
    assert t.abierto_en.startswith("2024-01-04")
    assert r["DDD"].trades["conservador"][0].direccion == -1


def test_sin_lookahead_y_lookahead_plantado_detectado():
    assert chequear_lookahead_corte(_corte_ejemplo.senales_corte, _universo()) == []

    def tramposa(velas, miembros=None):
        sen = _corte_ejemplo.senales_corte(velas, miembros)
        for s, d in sen.items():  # mira el cierre de mañana
            d["direccion"] = (velas[s]["close"].shift(-1) > velas[s]["close"]).astype(int)
        return sen

    assert chequear_lookahead_corte(tramposa, _universo())


def test_un_simbolo_fuera_del_universo_deja_de_rankear():
    # AAA (el mejor) sólo es miembro en enero; después el largo pasa a BBB.
    miembros = {"AAA": ["2024-01"], "BBB": ["2024-01", "2024-02"], "CCC": ["2024-01", "2024-02"],
                "DDD": ["2024-01", "2024-02"]}
    sen = _corte_ejemplo.senales_corte(run.alinear(_universo()), miembros)
    feb = sen["AAA"].index >= "2024-02-01"
    assert (sen["AAA"]["direccion"][feb] == 0).all()
    assert (sen["BBB"]["direccion"][feb] == 1).all()
    ene = (sen["AAA"].index >= "2024-01-03") & ~feb
    assert (sen["AAA"]["direccion"][ene] == 1).all()


def test_alinear_deja_nan_donde_no_hay_vela():
    u = _universo()
    u["CCC"] = u["CCC"].iloc[10:]
    a = run.alinear(u)
    assert len(a["CCC"]) == len(IDX) and a["CCC"]["close"].iloc[:10].isna().all()


def test_las_estrategias_de_un_simbolo_no_cambian():
    assert not es_corte("donchian_breakout")
    assert es_corte("_corte_ejemplo")
    assert cargar_corte("_corte_ejemplo") is _corte_ejemplo.senales_corte
    assert cargar("donchian_breakout")


def test_tramo_de_evaluar_usa_el_corte_transversal():
    import dataclasses

    from bt import evaluar
    from bt.spec import desde_dict

    rng = np.random.default_rng(7)
    idx = pd.date_range("2024-01-01", "2025-06-30", freq="1D", tz="UTC", name="time")
    datos = {s: _df(100 * np.exp(np.cumsum(rng.normal(0.001, 0.03, len(idx)))), idx) for s in "ABCD"}
    spec = desde_dict({
        "id": "2026-11-17-corte-test", "estado": "pre-registrada", "hipotesis": "x",
        "horizonte": {"tipo": "diario"},
        "estrategia": {"modulo": "_corte_ejemplo", "params": {"dias": 2}},
        "universo": {"mercado": "futures", "simbolos": list(datos), "intervalo": "1d", "funding": False},
        "config": {"fee_pct_por_lado": 0.001, "timeout_velas": 7},
        "ventana_desarrollo": {"desde": "2024-01-01"},
        "criterio_aprobacion": {"n_minimo": 5},
    })
    t = evaluar._tramo(dataclasses.replace(spec, simbolos=list(datos)), lambda s, i, m: datos[s],
                       lambda s: None, holdout=False)
    assert set(t["porSimbolo"]) == set(datos)
    assert t["global"]["n"] > 0
