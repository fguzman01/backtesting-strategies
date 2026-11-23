"""Idea #21: beta a la baja (spec 2026-11-23-beta-baja-1d), con los params de la spec."""
import numpy as np
import pandas as pd

from bt import run
from bt.checks import chequear_lookahead_corte
from bt.engine import Config
from bt.strategies import beta_baja

IDX = pd.date_range("2024-01-01", periods=200, freq="1D", tz="UTC", name="time")
PARAMS = dict(ventana=120, k=3, min_dias_baja=30, referencia="BTCUSDT", atr_n=14, stop_atr=2.0, trailing_atr=2.0)


def _df(cierres):
    c = np.asarray(cierres, dtype=float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) * 1.005, "low": np.minimum(o, c) * 0.995, "close": c, "volume": 1.0},
        index=IDX,
    )


def _retornos_btc(seed=1):
    return np.random.default_rng(seed).normal(0, 0.02, len(IDX))


def _universo(n_alts=7):
    """Cada alt tiene beta a la baja conocido (b0 > b1 > ...): r = b·r_btc cuando BTC cae, 0.5·r_btc si sube."""
    rb = _retornos_btc()
    out = {"BTCUSDT": _df(100 * np.cumprod(1 + rb))}
    for i in range(n_alts):
        b = 2.0 - 0.25 * i
        r = np.where(rb < 0, b * rb, 0.5 * rb)
        out[f"A{i}"] = _df(100 * np.cumprod(1 + r))
    return out


def _aleatorio(seed=3):
    rng = np.random.default_rng(seed)
    base = {f"S{i}": _df(100 * np.exp(np.cumsum(rng.normal(0, 0.02, len(IDX))))) for i in range(7)}
    base["BTCUSDT"] = _df(100 * np.exp(np.cumsum(rng.normal(0, 0.02, len(IDX)))))
    return base


def test_sin_lookahead_con_los_params_de_la_spec():
    assert chequear_lookahead_corte(beta_baja.senales_corte, _aleatorio(), **PARAMS) == []


def test_beta_baja_recupera_el_beta_conocido():
    rb = pd.Series(_retornos_btc(), index=IDX)
    ret = pd.DataFrame({"X": np.where(rb < 0, 1.7 * rb, 0.3 * rb)}, index=IDX)
    b = beta_baja.beta_baja(ret, rb, 120, 30)
    assert abs(b["X"].iloc[-1] - 1.7) < 1e-9
    assert b["X"].iloc[:119].isna().all()


def test_largo_los_k_de_mayor_beta_y_corto_los_k_de_menor():
    sen = beta_baja.senales_corte(run.alinear(_universo()), **PARAMS)
    fila = {s: d["direccion"].iloc[150] for s, d in sen.items()}
    # 8 símbolos: BTC (beta 1.0) y A0..A6 (2.0 … 0.5): largo A0-A2, corto A5, A6 y A4 (0.75 < BTC 1.0)
    assert [fila[f"A{i}"] for i in range(3)] == [1, 1, 1]
    assert [fila[f"A{i}"] for i in (4, 5, 6)] == [-1, -1, -1]
    assert fila["A3"] == 0 and fila["BTCUSDT"] == 0


def test_sin_ventana_completa_no_hay_senal():
    sen = beta_baja.senales_corte(run.alinear(_universo()), **PARAMS)
    assert all((d["direccion"].iloc[:120] == 0).all() for d in sen.values())


def test_sin_btc_no_hay_senal():
    u = _universo()
    u.pop("BTCUSDT")
    sen = beta_baja.senales_corte(run.alinear(u), **PARAMS)
    assert all((d["direccion"] == 0).all() for d in sen.values())


def test_simbolo_fuera_del_universo_no_rankea():
    meses = sorted(set(IDX.strftime("%Y-%m")))
    miembros = {s: meses for s in _universo()}
    miembros["A0"] = meses[:5]
    sen = beta_baja.senales_corte(run.alinear(_universo()), miembros, **PARAMS)
    assert (sen["A0"]["direccion"][sen["A0"].index >= "2024-07-01"] == 0).all()


def test_stop_y_trailing_son_multiplos_del_atr_y_positivos():
    d = beta_baja.senales_corte(run.alinear(_universo()), **PARAMS)["A0"].iloc[150]
    assert d["riesgo"] > 0 and d["trailing"] == d["riesgo"]


def test_flujo_completo_entra_en_t_mas_1():
    r = run.correr_corte("beta_baja", _universo(), intervalo="1d", cfg=Config(), params=PARAMS)
    t = r["A0"].trades["conservador"][0]
    assert t.direccion == 1
    assert r["BTCUSDT"].trades["conservador"] == []
