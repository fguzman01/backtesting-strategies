"""El motor reproduce operación por operación el script con el que se aprobó TREND_1D."""

import bisect

import numpy as np
import pandas as pd
import pytest

from bt import run
from bt.engine import Config
from bt.splits import HOLDOUT_DESDE
from referencia.tendencia_diaria_ref import operar

CORTE = int(HOLDOUT_DESDE.value // 10**6)
FIN = int(pd.Timestamp("2026-10-19", tz="UTC").value // 10**6)
CFG = Config(fee_pct_por_lado=0.001, cerrar_al_final=True)
MOTIVO = {"STOP": "SL", "STOP_APERTURA": "SL", "CANAL": "SALIDA", "FIN_DE_TRAMO": "FIN"}


def mercado(semilla, inicio="2020-01-01", deriva=0.0008, vol=0.04):
    rng = np.random.default_rng(semilla)
    idx = pd.date_range(inicio, "2026-10-30", freq="1D", tz="UTC", name="time")
    close = 100 * np.exp(np.cumsum(rng.normal(deriva, vol, len(idx))))
    # Aperturas con gaps para ejercitar STOP_APERTURA.
    open_ = np.concatenate([[100.0], close[:-1] * np.exp(rng.normal(0, 0.01, len(idx) - 1))])
    rango = np.abs(rng.normal(0, 0.025, len(idx))) * close
    df = pd.DataFrame({"open": open_, "high": np.maximum(open_, close) + rango,
                       "low": np.minimum(open_, close) - rango, "close": close, "volume": 1.0}, index=idx)
    pagos = pd.date_range(inicio, "2026-10-30", freq="8h", tz="UTC")
    funding = pd.Series(rng.normal(0.0001, 0.0003, len(pagos)), index=pagos)
    return df, funding


def referencia(df, funding, tramo):
    v = [(int(t.value // 10**6), r.open, r.high, r.low, r.close) for t, r in df.iterrows()]
    ts = [int(t.value // 10**6) for t in funding.index]
    acum = [0.0]
    for r in funding.to_numpy():
        acum.append(acum[-1] + r)

    def fund(a, b):
        return acum[bisect.bisect_right(ts, b)] - acum[bisect.bisect_right(ts, a)]

    return operar(v, fund, tramo, CORTE, FIN)


def nuestro(df, funding, tramo):
    if tramo == "desarrollo":
        kw = dict(desde=None, hasta=None)
    else:
        kw = dict(desde="2025-09-09", hasta="2026-10-19", holdout=True)
    r = run.correr("tendencia_donchian", df, simbolo="X", intervalo="1d", cfg=CFG, funding=funding, **kw)
    return [t for t in r.trades["conservador"] if t.resuelto], r


@pytest.mark.parametrize("semilla", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("tramo", ["desarrollo", "holdout"])
def test_misma_operacion_por_operacion(semilla, tramo):
    df, funding = mercado(semilla)
    ref = referencia(df, funding, tramo)
    nos, r = nuestro(df, funding, tramo)
    assert len(ref) > 3, "el mercado sintético debería generar operaciones"
    assert len(nos) == len(ref)
    for a, b in zip(ref, nos, strict=True):
        assert pd.Timestamp(b.abierto_en).value // 10**6 == a["t_in"]
        assert b.direccion == a["dir"]
        assert MOTIVO[a["motivo"]] == b.motivo
        assert b.entrada == pytest.approx(a["entrada"], rel=1e-12)
        assert b.salida == pytest.approx(a["salida"], rel=1e-12)
        assert b.r_neto == pytest.approx(a["r"], abs=1e-9)
    avg = sum(x["r"] for x in ref) / len(ref)
    assert r.fila["avgRNeto"] == pytest.approx(avg, abs=1e-9)
    assert r.fila["tramo"] == tramo


def test_tambien_sin_funding_y_con_activo_que_empieza_tarde():
    df, _ = mercado(7, inicio="2020-08-15")
    vacio = pd.Series(dtype=float)
    ref = referencia(df, vacio, "desarrollo")
    nos, _ = nuestro(df, None, "desarrollo")
    assert len(nos) == len(ref) > 0
    assert [round(t.r_neto, 9) for t in nos] == [round(x["r"], 9) for x in ref]
