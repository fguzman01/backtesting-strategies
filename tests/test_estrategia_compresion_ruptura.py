import numpy as np
import pandas as pd

from bt.checks import chequear_lookahead
from bt.strategies import compresion_ruptura

PARAMS = dict(bb_n=20, bb_k=2.0, ventana_pct=180, pct_ancho=0.10, vigencia=6, atr_n=14,
              stop_min_atr=1.0, trailing_atr=2.0)


def _cuatro_h(n=500, seed=5):
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
    assert chequear_lookahead(compresion_ruptura.senales, df, **PARAMS) == []
    assert chequear_lookahead(compresion_ruptura.senales, df, pct_ancho=0.2, vigencia=3) == []


def _velas(c, mecha=0.05):
    c = np.asarray(c, dtype=float)
    df = pd.DataFrame({"close": c})
    df["open"] = np.concatenate([[c[0]], c[:-1]])
    df["high"] = np.maximum(df.open, df.close) + mecha
    df["low"] = np.minimum(df.open, df.close) - mecha
    df["volume"] = 10.0
    df.index = pd.date_range("2024-01-01", periods=len(c), freq="4h", tz="UTC", name="time")
    return df


def _oscila(n, desde=0):
    """Cierres que alternan arriba/abajo de 100 con amplitud que crece apenas: el ancho de Bollinger
    sube siempre, así que nunca queda en su percentil bajo (no hay compresión)."""
    t = np.arange(desde, desde + n)
    return 100 + (-1.0) ** t * (1 + 0.001 * t)


def _caja(n=340, i_comp=(260, 290), seed=1):
    """Cierres que oscilan ±1 salvo una caja comprimida (cierres ±0.1, mechas hasta 98–102)."""
    rng = np.random.default_rng(seed)
    c = _oscila(n)
    a, b = i_comp
    c[a:b] = 100 + rng.uniform(-0.1, 0.1, b - a)
    df = _velas(c)
    df.iloc[a:b, df.columns.get_loc("high")] = 102.0
    df.iloc[a:b, df.columns.get_loc("low")] = 98.0
    return df


def _poner_cierres(df, desde, cierres):
    c = df["close"].to_numpy().copy()
    c[desde:desde + len(cierres)] = cierres
    nuevo = _velas(c)
    # Conservar las mechas de la caja
    for col in ("high", "low"):
        nuevo[col] = np.where(df.index < df.index[desde], df[col], nuevo[col])
    return nuevo


def test_ruptura_de_la_caja_comprimida_largo_y_corto():
    for signo in (1, -1):
        df = _caja()
        i = 290  # primera vela tras la caja: rompe y se queda lejos, con rango ancho
        df = _poner_cierres(df, i, signo * 5 + _oscila(len(df) - i, i))
        s = compresion_ruptura.senales(df, **PARAMS)
        assert s["direccion"].iloc[i] == signo
        # Una sola señal: el cruce, no cada vela que sigue fuera de la caja.
        assert (s["direccion"].iloc[i + 1:] == 0).all()
        assert (s["direccion"].iloc[:i] == 0).all()
        # Stop al otro lado de la caja (98 / 102), más lejos si la caja fuera más chica que 1 ATR.
        stop = s["stop"].iloc[i]
        assert (stop <= 98.0) if signo == 1 else (stop >= 102.0)
        assert s["trailing"].iloc[i] > 0


def test_ruptura_sin_compresion_no_opera():
    c = _oscila(320)
    c[300] = 110.0
    s = compresion_ruptura.senales(_velas(c), **PARAMS)
    assert s["direccion"].iloc[300] == 0


def test_la_caja_vence_tras_la_vigencia():
    df = _caja()
    # Dentro de la vigencia la ruptura cuenta...
    dentro = _poner_cierres(df, 290, np.concatenate([_oscila(3, 290), [105.0]]))
    assert compresion_ruptura.senales(dentro, **PARAMS)["direccion"].iloc[293] == 1
    # ...40 velas después de la caja, ya no: la compresión pasó y la caja venció.
    fuera = _poner_cierres(df, 290, np.concatenate([_oscila(40, 290), [105.0]]))
    s = compresion_ruptura.senales(fuera, **PARAMS)
    assert s["direccion"].iloc[330] == 0
    assert (s["direccion"] == 0).all()


def test_sin_historia_no_hay_senal():
    df = _poner_cierres(_caja(i_comp=(30, 60)), 60, [110.0])
    s = compresion_ruptura.senales(df, **PARAMS)
    assert (s["direccion"].iloc[:200] == 0).all()
