"""Control nulo: ¿la regla le gana a entrar en fechas al azar?

Por cada operación real se sortea una fecha de entrada al azar en el mismo símbolo y la misma
ventana, con la misma dirección, la misma duración (en velas) y el mismo riesgo como fracción del
precio; se entra a la apertura y se sale a la apertura `duración` velas después, con la misma
comisión y el funding del período. Se repite `iteraciones` veces y se compara el avgR real con la
distribución de los promedios al azar.

Es el control que rechazó TREND_1D en oro (el azar rendía más que la regla). Esta versión usa el
riesgo de cada operación real en vez de recalcular el ATR en la fecha sorteada, así funciona con
cualquier estrategia; por eso sus números no son idénticos a los de los scripts de btc-signal-web.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bt.engine import Config, Trade


def _acumulado(funding: pd.Series | None):
    if funding is None or len(funding) == 0:
        return None, None
    s = funding.sort_index()
    idx = pd.DatetimeIndex(s.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    return idx.as_unit("ms").asi8, np.concatenate([[0.0], np.cumsum(s.to_numpy(dtype=float))])


def control_nulo(
    trades: dict[str, list[Trade]],
    datos: dict[str, tuple[pd.DataFrame, pd.Series | None]],
    desde: pd.Timestamp,
    hasta: pd.Timestamp,
    cfg: Config,
    iteraciones: int = 1000,
    semilla: int = 20261031,
) -> dict:
    rng = np.random.default_rng(semilla)
    filas = []  # una fila de `iteraciones` R al azar por operación real
    for sim, ops in trades.items():
        df, funding = datos[sim]
        idx = pd.DatetimeIndex(df.index)
        t_ms = idx.as_unit("ms").asi8
        o = df["open"].to_numpy(dtype=float)
        dentro = np.flatnonzero((idx >= desde) & (idx < hasta))
        if len(dentro) == 0:
            continue
        f_ts, f_acum = _acumulado(funding)
        for t in ops:
            if not t.resuelto:
                continue
            dur = max(1, t.velas)
            riesgo_frac = (t.entrada - t.stop) * t.direccion / t.entrada
            ks = dentro[dentro + dur <= dentro[-1]]
            if len(ks) == 0 or riesgo_frac <= 0:
                continue
            k = rng.choice(ks, size=iteraciones)
            p_in, p_out = o[k], o[k + dur]
            ret = t.direccion * (p_out - p_in) / p_in - 2 * cfg.fee_pct_por_lado
            if f_ts is not None:
                a = f_acum[np.searchsorted(f_ts, t_ms[k], "right")]
                b = f_acum[np.searchsorted(f_ts, t_ms[k + dur], "right")]
                ret = ret - t.direccion * (b - a)
            filas.append(ret / riesgo_frac)
    if not filas:
        return {"iteraciones": 0, "media": None, "p95": None}
    promedios = np.vstack(filas).mean(axis=0)
    return {
        "iteraciones": iteraciones,
        "media": float(promedios.mean()),
        "p95": float(np.quantile(promedios, 0.95)),
    }
