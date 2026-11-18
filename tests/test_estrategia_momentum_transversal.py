import numpy as np
import pandas as pd

from bt import run
from bt.checks import chequear_lookahead_corte
from bt.engine import Config
from bt.strategies import momentum_transversal

PARAMS = dict(lookback=7, k=3, atr_n=14, stop_atr=2.0, trailing_atr=2.0)
IDX = pd.date_range("2024-01-01", periods=80, freq="1D", tz="UTC", name="time")


def _df(cierres, idx=IDX):
    c = np.asarray(cierres, dtype=float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) * 1.005, "low": np.minimum(o, c) * 0.995, "close": c, "volume": 1.0},
        index=idx,
    )


def _universo(n_sim=8, seed=1):
    t = np.arange(len(IDX))
    # tendencias ordenadas: 0 sube más rápido ... n_sim-1 baja más rápido
    pend = np.linspace(0.02, -0.02, n_sim)
    return {f"S{i}": _df(100 * (1 + pend[i]) ** t) for i in range(n_sim)}


def _aleatorio(n_sim=8, seed=3):
    rng = np.random.default_rng(seed)
    return {f"S{i}": _df(100 * np.exp(np.cumsum(rng.normal(0, 0.02, len(IDX))))) for i in range(n_sim)}


def test_sin_lookahead():
    assert chequear_lookahead_corte(momentum_transversal.senales_corte, _aleatorio(), **PARAMS) == []
    assert chequear_lookahead_corte(momentum_transversal.senales_corte, _aleatorio(), lookback=5, k=2) == []


def test_largo_los_k_mejores_y_corto_los_k_peores():
    sen = momentum_transversal.senales_corte(run.alinear(_universo()), **PARAMS)
    fila = {s: d["direccion"].iloc[40] for s, d in sen.items()}
    assert [fila[f"S{i}"] for i in range(8)] == [1, 1, 1, 0, 0, -1, -1, -1]
    # antes de tener retorno de 7 velas y ATR de 14, no hay señal
    assert all((d["direccion"].iloc[:13] == 0).all() for d in sen.values())


def test_stop_y_trailing_son_multiplos_del_atr_y_positivos():
    sen = momentum_transversal.senales_corte(run.alinear(_universo()), **PARAMS)
    d = sen["S0"].iloc[40]
    assert d["riesgo"] > 0 and d["trailing"] == d["riesgo"]  # los dos a 2 ATR


def test_con_menos_de_2k_simbolos_no_hay_corte():
    sen = momentum_transversal.senales_corte(run.alinear(_universo(5)), **PARAMS)  # 5 < 6
    assert all((d["direccion"] == 0).all() for d in sen.values())


def test_simbolo_fuera_del_universo_no_rankea():
    meses = ["2024-01", "2024-02", "2024-03"]
    miembros = {f"S{i}": meses for i in range(8)}
    miembros["S0"] = ["2024-01"]  # el mejor sólo es miembro en enero
    sen = momentum_transversal.senales_corte(run.alinear(_universo()), miembros, **PARAMS)
    mar = sen["S0"].index >= "2024-03-01"
    assert (sen["S0"]["direccion"][mar] == 0).all()
    assert (sen["S1"]["direccion"][mar] == 1).all()


def test_flujo_completo_entra_en_t_mas_1():
    r = run.correr_corte("momentum_transversal", _universo(), intervalo="1d", cfg=Config(), params=PARAMS)
    t = r["S0"].trades["conservador"][0]
    assert t.direccion == 1
    # primera señal en la vela 13 (ATR válido), entrada en la apertura de la 14
    assert t.abierto_en.startswith(str(IDX[14].date()))
    assert r["S3"].trades["conservador"] == []
    assert r["S7"].trades["conservador"][0].direccion == -1
