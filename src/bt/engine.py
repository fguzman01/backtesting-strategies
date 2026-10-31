"""Simulador por barras.

Contrato con las estrategias (`bt.strategies`): `senales(df, **params)` devuelve un DataFrame con el
mismo índice que `df` y estas columnas, calculadas SÓLO con datos hasta el cierre de cada vela:

- `direccion`: +1 largo, −1 corto, 0 nada. Se ejecuta en la APERTURA de la vela siguiente.
- `stop`: precio del stop; o bien
- `riesgo`: distancia del stop medida desde la entrada REAL (stop = entrada − dirección × riesgo).
  Si están las dos, manda `riesgo`.
- `objetivo` (opcional): precio objetivo. Si falta y `Config.objetivo_r` está, se usa
  entrada ± objetivo_r × riesgo.
- `salida` (opcional, bool): cerrar la posición abierta en la apertura de la vela siguiente
  (salidas por regla, p. ej. el canal corto de Donchian). Si la salida depende del lado, usar
  `salida_largo` / `salida_corto`, que mandan sobre `salida` para su lado.

Una posición a la vez. Dos modelos de llenado para lo que no se sabe dentro de una vela
(ver 02-DOCS/reglas-de-medicion.md): `conservador` (el adverso primero, el que se reporta) y
`optimista`. El deslizamiento mueve sólo el precio de entrada; NO filtra operaciones (la confusión
compuerta/llenado sesgó a btc-signal-web hasta el 2026-10-11).

Funding (futuros perpetuos): se le cobra al trade la suma de las tasas con instante en
(apertura, cierre], con signo según la dirección. El instante del cierre sigue esta convención,
la misma de btc-signal-web: salida a la apertura de una vela → esa apertura; stop/objetivo dentro
de la vela → mitad de la vela; salida al cierre → fin de la vela.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

MOTIVOS_RESUELTOS = frozenset({"SL", "TP", "TIMEOUT", "SALIDA", "FIN"})


@dataclass(frozen=True)
class Config:
    fee_pct_por_lado: float = 0.0005
    deslizamiento_pct: float = 0.0
    timeout_velas: int | None = None
    objetivo_r: float | None = None
    # Una posición abierta al terminar los datos se cierra al último cierre (motivo FIN) y cuenta.
    # Si es False queda SIN_RESOLVER y no cuenta (lo que hace el motor TS de btc-signal-web).
    cerrar_al_final: bool = False

    def como_dict(self) -> dict:
        return asdict(self)


@dataclass
class Trade:
    direccion: int
    senal_en: str
    abierto_en: str
    cerrado_en: str | None
    entrada: float
    stop: float
    objetivo: float | None
    salida: float | None
    motivo: str  # SL | TP | TIMEOUT | SALIDA | FIN | SIN_RESOLVER | STOP_INVALIDO
    r_bruto: float
    fee_r: float
    r_neto: float
    mae_r: float
    velas: int
    funding_r: float = 0.0

    @property
    def resuelto(self) -> bool:
        return self.motivo in MOTIVOS_RESUELTOS


def _col(sen: pd.DataFrame, nombre: str, defecto) -> np.ndarray:
    if nombre in sen:
        return sen[nombre].to_numpy()
    return np.full(len(sen), defecto)


class _Funding:
    """Suma de tasas de funding con instante en (a, b], en ms."""

    def __init__(self, serie: pd.Series | None):
        self.ts = None
        if serie is None or len(serie) == 0:
            return
        s = serie.sort_index()
        idx = pd.DatetimeIndex(s.index)
        idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
        self.ts = idx.as_unit("ms").asi8
        self.acum = np.concatenate([[0.0], np.cumsum(s.to_numpy(dtype=float))])

    def entre(self, a_ms: int, b_ms: int) -> float:
        if self.ts is None:
            return 0.0
        hasta = self.acum[np.searchsorted(self.ts, b_ms, "right")]
        return float(hasta - self.acum[np.searchsorted(self.ts, a_ms, "right")])


def simular(
    df: pd.DataFrame, sen: pd.DataFrame, cfg: Config, modelo: str = "conservador",
    funding: pd.Series | None = None,
) -> list[Trade]:
    if modelo not in ("conservador", "optimista"):
        raise ValueError(modelo)
    if not sen.index.equals(df.index):
        raise ValueError("las señales deben tener el mismo índice que las velas")

    o, h, lo, c = (df[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    t = df.index
    t_ms = pd.DatetimeIndex(t).as_unit("ms").asi8
    paso = int(np.median(np.diff(t_ms))) if len(t) > 1 else 0
    direc = np.nan_to_num(_col(sen, "direccion", 0).astype(float)).astype(int)
    stops = _col(sen, "stop", np.nan).astype(float)
    riesgos = _col(sen, "riesgo", np.nan).astype(float)
    objs = _col(sen, "objetivo", np.nan).astype(float)
    salida_comun = _col(sen, "salida", False).astype(bool)
    salida_por_lado = {
        1: _col(sen, "salida_largo", False).astype(bool) if "salida_largo" in sen else salida_comun,
        -1: _col(sen, "salida_corto", False).astype(bool) if "salida_corto" in sen else salida_comun,
    }
    fund = _Funding(funding)
    adverso_primero = modelo == "conservador"
    n = len(df)
    trades: list[Trade] = []

    i = 0
    while i < n - 1:
        d = direc[i]
        if d == 0 or not (math.isfinite(riesgos[i]) or math.isfinite(stops[i])):
            i += 1
            continue
        j = i + 1
        entrada = o[j] * (1 + d * cfg.deslizamiento_pct)
        stop = entrada - d * riesgos[i] if math.isfinite(riesgos[i]) else stops[i]
        riesgo = (entrada - stop) * d
        if riesgo <= 0:
            trades.append(_trade(d, t[i], t[j], None, entrada, stop, None, None, "STOP_INVALIDO", 0, 0, 0, 0))
            i += 1
            continue
        obj = objs[i] if math.isfinite(objs[i]) else None
        if obj is None and cfg.objetivo_r:
            obj = entrada + d * cfg.objetivo_r * riesgo
        fee_r = cfg.fee_pct_por_lado * 2 * entrada / riesgo

        salidas = salida_por_lado[d]
        peor = entrada
        salida = motivo = None
        momento = 0  # ms del cierre, para el funding
        k = j
        while k < n:
            # Gap: la vela abre ya pasada del stop/objetivo (no aplica a la vela de entrada).
            if k > j:
                if (o[k] - stop) * d <= 0:
                    salida, motivo = o[k], "SL"
                elif obj is not None and (o[k] - obj) * d >= 0:
                    salida, motivo = o[k], "TP"
                if motivo:
                    peor = min(peor, o[k]) if d > 0 else max(peor, o[k])
                    momento = t_ms[k]
                    break
            peor = min(peor, lo[k]) if d > 0 else max(peor, h[k])
            toca_stop = (lo[k] if d > 0 else h[k]) * d <= stop * d
            toca_obj = obj is not None and (h[k] if d > 0 else lo[k]) * d >= obj * d
            momento = t_ms[k] + paso // 2
            if toca_stop and toca_obj:
                salida, motivo = (stop, "SL") if adverso_primero else (obj, "TP")
            elif toca_stop:
                salida, motivo = stop, "SL"
            elif toca_obj:
                salida, motivo = obj, "TP"
            elif cfg.timeout_velas and k - j + 1 >= cfg.timeout_velas:
                salida, motivo, momento = c[k], "TIMEOUT", t_ms[k] + paso
            elif salidas[k] and k + 1 < n:
                k += 1
                salida, motivo, momento = o[k], "SALIDA", t_ms[k]
                peor = min(peor, o[k]) if d > 0 else max(peor, o[k])
            if motivo:
                break
            k += 1

        if motivo is None:
            if not cfg.cerrar_al_final:
                trades.append(
                    _trade(d, t[i], t[j], None, entrada, stop, obj, None, "SIN_RESOLVER", 0, fee_r, 0, n - j)
                )
                break
            k = n - 1
            salida, motivo, momento = c[k], "FIN", t_ms[k] + paso
        r_bruto = (salida - entrada) * d / riesgo
        f_r = d * fund.entre(t_ms[j], momento) * entrada / riesgo
        mae_r = max(0.0, (entrada - peor) * d / riesgo)
        velas = k - j + 1
        trades.append(
            _trade(d, t[i], t[j], t[k], entrada, stop, obj, salida, motivo, r_bruto, fee_r, mae_r, velas, f_r)
        )
        if motivo == "FIN":
            break
        # La vela de salida puede generar una señal nueva (se ejecutaría en la siguiente).
        i = k
    return trades


def _trade(d, ts, ta, tc, entrada, stop, obj, salida, motivo, r_bruto, fee_r, mae_r, velas, f_r=0.0) -> Trade:
    resuelto = motivo in MOTIVOS_RESUELTOS
    return Trade(
        direccion=int(d),
        senal_en=ts.isoformat(),
        abierto_en=ta.isoformat(),
        cerrado_en=tc.isoformat() if tc is not None else None,
        entrada=float(entrada),
        stop=float(stop),
        objetivo=float(obj) if obj is not None else None,
        salida=float(salida) if salida is not None else None,
        motivo=motivo,
        r_bruto=float(r_bruto),
        fee_r=float(fee_r),
        r_neto=float(r_bruto - fee_r - f_r) if resuelto else 0.0,
        mae_r=float(mae_r),
        velas=int(velas),
        funding_r=float(f_r),
    )


def simular_ambos(
    df: pd.DataFrame, sen: pd.DataFrame, cfg: Config, funding: pd.Series | None = None
) -> dict[str, list[Trade]]:
    return {m: simular(df, sen, cfg, m, funding) for m in ("conservador", "optimista")}
