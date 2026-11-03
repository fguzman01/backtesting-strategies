import numpy as np
import pandas as pd

from bt.checks import chequear_lookahead
from bt.strategies import reversion_salto

PARAMS = dict(atr_n=24, salto_atr=4.0, vol_n=24, vol_mult=2.0, stop_atr=3.0)


def test_sin_lookahead(paseo):
    assert chequear_lookahead(reversion_salto.senales, paseo, **PARAMS) == []
    assert chequear_lookahead(reversion_salto.senales, paseo, salto_atr=3.0, vol_mult=1.5) == []


def _serie():
    rng = np.random.default_rng(3)
    c = 100 + np.cumsum(rng.normal(0, 0.2, 120))
    o = np.concatenate([[c[0]], c[:-1]])
    df = pd.DataFrame({"open": o, "close": c})
    df["high"] = np.maximum(df.open, df.close) + 0.1
    df["low"] = np.minimum(df.open, df.close) - 0.1
    df["volume"] = 10.0
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="1h", tz="UTC", name="time")
    return df


def _con_salto(i, signo, volumen):
    df = _serie()
    o = df["open"].iloc[i]
    df.iloc[i, df.columns.get_loc("close")] = o + signo * 10.0
    df.iloc[i, df.columns.get_loc("high")] = max(o, o + signo * 10.0) + 0.1
    df.iloc[i, df.columns.get_loc("low")] = min(o, o + signo * 10.0) - 0.1
    df.iloc[i, df.columns.get_loc("volume")] = volumen
    return df


def test_salto_abajo_con_volumen_da_largo_y_arriba_corto():
    s = reversion_salto.senales(_con_salto(80, -1, 50.0), **PARAMS)
    assert s["direccion"].iloc[80] == 1 and s["direccion"].abs().sum() == 1
    assert s["riesgo"].iloc[80] > 0
    s = reversion_salto.senales(_con_salto(80, +1, 50.0), **PARAMS)
    assert s["direccion"].iloc[80] == -1 and s["direccion"].abs().sum() == 1


def test_salto_sin_volumen_no_opera():
    s = reversion_salto.senales(_con_salto(80, -1, 10.0), **PARAMS)
    assert (s["direccion"] == 0).all()
