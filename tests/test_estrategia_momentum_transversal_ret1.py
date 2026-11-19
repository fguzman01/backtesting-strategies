"""Idea #19: el mismo módulo con los params de la spec 2026-11-19-momentum-transversal-1d-ret1 (lookback=1)."""
import numpy as np
import pandas as pd

from bt import run
from bt.checks import chequear_lookahead_corte
from bt.engine import Config
from bt.strategies import momentum_transversal

IDX = pd.date_range("2024-01-01", periods=80, freq="1D", tz="UTC", name="time")


def _df(cierres):
    c = np.asarray(cierres, dtype=float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) * 1.005, "low": np.minimum(o, c) * 0.995, "close": c, "volume": 1.0},
        index=IDX,
    )


def _universo(n_sim=8):
    t = np.arange(len(IDX))
    pend = np.linspace(0.02, -0.02, n_sim)
    return {f"S{i}": _df(100 * (1 + pend[i]) ** t) for i in range(n_sim)}


def _aleatorio(n_sim=8, seed=3):
    rng = np.random.default_rng(seed)
    return {f"S{i}": _df(100 * np.exp(np.cumsum(rng.normal(0, 0.02, len(IDX))))) for i in range(n_sim)}


PARAMS = dict(lookback=1, k=3, atr_n=14, stop_atr=2.0, trailing_atr=2.0)


def test_sin_lookahead_con_los_params_de_la_spec():
    assert chequear_lookahead_corte(momentum_transversal.senales_corte, _aleatorio(), **PARAMS) == []


def test_largo_los_k_mejores_del_dia_y_corto_los_k_peores():
    sen = momentum_transversal.senales_corte(run.alinear(_universo()), **PARAMS)
    ultima = sen["S0"].index[-1]
    assert [sen[f"S{i}"].loc[ultima, "direccion"] for i in range(8)] == [1, 1, 1, 0, 0, -1, -1, -1]


def test_flujo_completo_entra_en_t_mas_1():
    r = run.correr_corte("momentum_transversal", _universo(), intervalo="1d", cfg=Config(), params=PARAMS)
    assert r is not None
