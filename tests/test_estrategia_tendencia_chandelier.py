import numpy as np
import pandas as pd

from bt.checks import chequear_lookahead
from bt.indicadores import atr
from bt.strategies import tendencia_chandelier

PARAMS = dict(entrada=20, salida_n=22, salida_atr=3.0, atr_n=20, ema_n=200, stop_atr=2.0)


def test_sin_lookahead(paseo):
    assert chequear_lookahead(tendencia_chandelier.senales, paseo, **PARAMS) == []
    assert chequear_lookahead(tendencia_chandelier.senales, paseo, entrada=55, salida_n=30) == []


def _tendencia():
    # 260 velas planas con ruido mínimo, ruptura al alza en la 260, sube hasta la 280 y cae.
    rng = np.random.default_rng(1)
    base = 100 + rng.normal(0, 0.2, 260)
    alza = 100 + np.arange(1, 21) * 2.0
    caida = alza[-1] - np.arange(1, 16) * 4.0
    c = np.concatenate([base, alza, caida])
    idx = pd.date_range("2024-01-01", periods=len(c), freq="1D", tz="UTC", name="time")
    df = pd.DataFrame({"open": np.concatenate([[c[0]], c[:-1]]), "close": c}, index=idx)
    df["high"] = np.maximum(df.open, df.close) + 0.5
    df["low"] = np.minimum(df.open, df.close) - 0.5
    df["volume"] = 1.0
    return df


def test_caso_sintetico_entra_en_la_ruptura_y_sale_por_chandelier():
    df = _tendencia()
    s = tendencia_chandelier.senales(df, **PARAMS)
    assert s["direccion"].iloc[260] == 1  # primera vela de la ruptura
    assert not s["salida_largo"].iloc[260:280].any()  # la tendencia sana no dispara la salida
    caida = s["salida_largo"].iloc[280:]
    assert caida.any()  # la caída cruza máximo − 3 ATR
    a = atr(df, 20)
    i = 280 + int(np.argmax(caida.to_numpy()))
    assert df["close"].iloc[i] < df["high"].iloc[i - 22 + 1 : i + 1].max() - 3.0 * a.iloc[i]
    assert (s.loc[s["direccion"] != 0, "riesgo"] > 0).all()
