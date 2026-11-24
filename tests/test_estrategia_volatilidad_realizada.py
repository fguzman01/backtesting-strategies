"""Idea #23: volatilidad realizada (spec 2026-11-24-volatilidad-realizada-1d), con los params de la spec."""
import numpy as np
import pandas as pd

from bt import run
from bt.checks import chequear_lookahead_corte
from bt.engine import Config
from bt.strategies import volatilidad_realizada

IDX = pd.date_range("2024-01-01", periods=80, freq="1D", tz="UTC", name="time")
PARAMS = dict(ventana=30, k=3, atr_n=14, stop_atr=2.0, trailing_atr=2.0)


def _df(cierres):
    c = np.asarray(cierres, dtype=float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) * 1.005, "low": np.minimum(o, c) * 0.995, "close": c, "volume": 1.0},
        index=IDX,
    )


def _universo(n_sim=8):
    """S0 tiene la menor volatilidad diaria, S7 la mayor (retornos alternados ±amplitud)."""
    amps = np.linspace(0.002, 0.05, n_sim)
    signo = np.where(np.arange(len(IDX)) % 2 == 0, 1.0, -1.0)
    return {f"S{i}": _df(100 * np.cumprod(1 + amps[i] * signo)) for i in range(n_sim)}


def _aleatorio(n_sim=8, seed=3):
    rng = np.random.default_rng(seed)
    return {f"S{i}": _df(100 * np.exp(np.cumsum(rng.normal(0, 0.02, len(IDX))))) for i in range(n_sim)}


def test_sin_lookahead_con_los_params_de_la_spec():
    assert chequear_lookahead_corte(volatilidad_realizada.senales_corte, _aleatorio(), **PARAMS) == []


def test_largo_los_k_de_menor_volatilidad_y_corto_los_k_de_mayor():
    sen = volatilidad_realizada.senales_corte(run.alinear(_universo()), **PARAMS)
    fila = {s: d["direccion"].iloc[40] for s, d in sen.items()}
    assert [fila[f"S{i}"] for i in range(8)] == [1, 1, 1, 0, 0, -1, -1, -1]


def test_sin_ventana_completa_no_hay_senal():
    sen = volatilidad_realizada.senales_corte(run.alinear(_universo()), **PARAMS)
    assert all((d["direccion"].iloc[:30] == 0).all() for d in sen.values())


def test_stop_y_trailing_son_multiplos_del_atr_y_positivos():
    d = volatilidad_realizada.senales_corte(run.alinear(_universo()), **PARAMS)["S0"].iloc[40]
    assert d["riesgo"] > 0 and d["trailing"] == d["riesgo"]


def test_simbolo_fuera_del_universo_no_rankea():
    meses = ["2024-01", "2024-02", "2024-03"]
    miembros = {f"S{i}": meses for i in range(8)}
    miembros["S0"] = ["2024-01"]
    sen = volatilidad_realizada.senales_corte(run.alinear(_universo()), miembros, **PARAMS)
    mar = sen["S0"].index >= "2024-03-01"
    assert (sen["S0"]["direccion"][mar] == 0).all()


def test_flujo_completo_entra_en_t_mas_1():
    r = run.correr_corte("volatilidad_realizada", _universo(), intervalo="1d", cfg=Config(), params=PARAMS)
    t = r["S0"].trades["conservador"][0]
    assert t.direccion == 1
    assert t.abierto_en.startswith(str(IDX[31].date()))  # 1.ª señal con 30 retornos: vela 30; entrada en la 31
    assert r["S3"].trades["conservador"] == []
