import numpy as np
import pandas as pd

from bt.checks import chequear_lookahead
from bt.strategies import continuacion_volumen

PARAMS = dict(ventana_vol=180, pct_volumen=0.9, retorno_velas=6, umbral_atr=2.0, atr_n=14,
              stop_atr=2.0, trailing_atr=2.0)


def _cuatro_h(n=400, seed=3):
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 0.5, n))
    o = np.concatenate([[c[0]], c[:-1]])
    df = pd.DataFrame({"open": o, "close": c})
    df["high"] = np.maximum(df.open, df.close) + 0.2
    df["low"] = np.minimum(df.open, df.close) - 0.2
    df["volume"] = rng.uniform(5, 15, n)
    df.index = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC", name="time")
    return df


def test_sin_lookahead():
    df = _cuatro_h()
    assert chequear_lookahead(continuacion_volumen.senales, df, **PARAMS) == []
    assert chequear_lookahead(continuacion_volumen.senales, df, pct_volumen=0.8, umbral_atr=1.5) == []


def _plano(n=300):
    df = _cuatro_h(n)
    df["close"] = 100.0
    df["open"] = 100.0
    df["high"] = 100.5
    df["low"] = 99.5
    df["volume"] = 10.0
    return df


def test_largo_con_volumen_y_retorno_y_corto_simetrico():
    for signo in (1, -1):
        df = _plano()
        i = 250
        df.iloc[i - 5:i + 1, df.columns.get_loc("close")] = 100.0 + signo * np.arange(1, 7) * 2.0
        df.iloc[i, df.columns.get_loc("volume")] = 50.0
        s = continuacion_volumen.senales(df, **PARAMS)
        assert s["direccion"].iloc[i] == signo
        assert (s["direccion"].drop(df.index[i]) == 0).all()
        assert s["riesgo"].iloc[i] > 0 and s["trailing"].iloc[i] > 0


def test_retorno_fuerte_sin_volumen_no_opera():
    df = _plano()
    i = 250
    df.iloc[i - 5:i + 1, df.columns.get_loc("close")] = 100.0 + np.arange(1, 7) * 2.0
    s = continuacion_volumen.senales(df, **PARAMS)
    assert (s["direccion"] == 0).all()


def test_volumen_sin_retorno_no_opera_y_sin_historia_no_hay_senal():
    df = _plano()
    df.iloc[250, df.columns.get_loc("volume")] = 50.0
    assert (continuacion_volumen.senales(df, **PARAMS)["direccion"] == 0).all()
    df = _plano()
    df.iloc[100, df.columns.get_loc("close")] = 130.0
    df.iloc[100, df.columns.get_loc("volume")] = 50.0
    s = continuacion_volumen.senales(df, **PARAMS)
    assert (s["direccion"].iloc[:180] == 0).all()
