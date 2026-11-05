import numpy as np
import pandas as pd

from bt.checks import chequear_lookahead
from bt.strategies import overnight_max

PARAMS = dict(max_dias=10, atr_n=24, stop_atr=6.0, hora_entrada=16, hora_salida=10)


def _horaria(n=24 * 30, inicio="2024-01-01", tendencia=0.0):
    rng = np.random.default_rng(5)
    c = 100 + np.cumsum(rng.normal(tendencia, 0.2, n))
    o = np.concatenate([[c[0]], c[:-1]])
    df = pd.DataFrame({"open": o, "close": c})
    df["high"] = np.maximum(df.open, df.close) + 0.1
    df["low"] = np.minimum(df.open, df.close) - 0.1
    df["volume"] = 10.0
    df.index = pd.date_range(inicio, periods=n, freq="1h", tz="UTC", name="time")
    return df


def test_sin_lookahead():
    df = _horaria(24 * 40)
    assert chequear_lookahead(overnight_max.senales, df, **PARAMS) == []
    assert chequear_lookahead(overnight_max.senales, df, max_dias=5, stop_atr=4.0) == []


def test_senal_a_las_16_et_con_cambio_de_hora():
    # Tendencia alcista fuerte: todo cierre es máximo de 10 días → una señal por día a las 16:00 ET.
    df = _horaria(24 * 60, inicio="2024-02-01", tendencia=0.5)
    s = overnight_max.senales(df, **PARAMS)
    idx = s.index[s["direccion"] == 1]
    assert len(idx) > 30
    hora_cierre = (idx + pd.Timedelta(hours=1)).tz_convert("America/New_York")
    assert set(hora_cierre.hour) == {16} and set(hora_cierre.minute) == {0}
    # 16:00 ET = 21:00 UTC en invierno y 20:00 UTC en verano (EDT desde 2024-03-10)
    assert {(i + pd.Timedelta(hours=1)).hour for i in idx if i < pd.Timestamp("2024-03-08", tz="UTC")} == {21}
    assert {(i + pd.Timedelta(hours=1)).hour for i in idx if i > pd.Timestamp("2024-03-20", tz="UTC")} == {20}
    assert (s.loc[idx, "riesgo"] > 0).all()


def test_sin_maximo_no_opera():
    # Caída sostenida: ningún cierre es máximo de 10 días.
    df = _horaria(24 * 60, tendencia=-0.5)
    s = overnight_max.senales(df, **PARAMS)
    assert (s["direccion"] == 0).all()


def test_salida_en_apertura_de_las_10_et():
    df = _horaria(24 * 20, inicio="2024-01-01")
    s = overnight_max.senales(df, **PARAMS)
    marcadas = s.index[s["salida_largo"]]
    # la vela marcada abre a las 09:00 ET: el motor cierra en la apertura siguiente (10:00 ET)
    assert set((marcadas + pd.Timedelta(hours=1)).tz_convert("America/New_York").hour) == {10}
    assert len(marcadas) == 20


def test_solo_largo_y_sin_senal_antes_de_tener_ventana():
    df = _horaria(24 * 60, tendencia=0.5)
    s = overnight_max.senales(df, **PARAMS)
    assert (s["direccion"] >= 0).all()
    assert (s["direccion"].iloc[: 24 * 10 - 1] == 0).all()
